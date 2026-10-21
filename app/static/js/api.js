function storageNotice() {
  if (typeof document === 'undefined' || !document.body || document.getElementById('session-storage-note')) return;
  const note = document.createElement('p');
  note.id = 'session-storage-note';
  note.setAttribute('role', 'status');
  note.textContent = 'Browser storage is unavailable. Your local session can still work, and saved scans remain on this computer. If asked to sign in again, reopen the session link from the app.';
  document.body.prepend(note);
}

function storedToken(value) {
  try {
    if (value === undefined) return window.sessionStorage.getItem('network-assessor-csrf');
    if (value === null) window.sessionStorage.removeItem('network-assessor-csrf');
    else window.sessionStorage.setItem('network-assessor-csrf', value);
  } catch { storageNotice(); }
  return null;
}

let csrfToken = storedToken();
let runningContract = null;

function expectedContract() {
  if (typeof document === 'undefined' || !document.querySelector) return null;
  const value = Number(document.querySelector('meta[name="netguard-api-contract"]')?.content);
  return Number.isInteger(value) && value > 0 ? value : null;
}

function observeContract(response) {
  const expected = expectedContract();
  if (!expected) return;
  const header = response.headers?.get?.('X-NetGuard-Contract');
  if (!header && runningContract !== null) return;
  const value = Number(header);
  runningContract = Number.isInteger(value) && value > 0 ? value : 0;
  if (runningContract === expected || !document.body || document.getElementById?.('backend-build-note')) return;
  const notice = document.createElement('p');
  notice.id = 'backend-build-note'; notice.className = 'status-message status-warning';
  notice.setAttribute('role', 'status');
  notice.textContent = 'The page files and running app use different versions. Finish active scans, restart the backend task, then reload this page. Saved reports remain readable.';
  document.body.prepend(notice);
}

// CVE research alone includes a 45s NVD budget, 40s local wording budget,
// bounded storage work and response delivery. Ordinary reads remain 20s/60s max.
const CVE_LOOKUP_TIMEOUT_MS = 110000;
const cveLookupPath = /^\/api\/live-scans\/[^/?#]{1,128}\/services\/[^/?#]{1,128}\/cves$/;

function errorMessage(body, status) {
  if (Array.isArray(body?.detail)) {
    const labels = { allowed_network: 'Network range', cidr: 'Network range', hosts: 'Device addresses',
      interface: 'Network adapter', nickname: 'Device nickname', expected_revision: 'Saved version',
      authorised: 'Scan permission', profile: 'Scan type' };
    const messages = body.detail.slice(0, 5).filter((item) => typeof item?.msg === 'string').map((item) => {
      const field = Array.isArray(item.loc) ? item.loc.find((part) => labels[part]) : null;
      const message = item.msg.replace(/^Value error,\s*/i, '');
      return `${labels[field] || 'Input'}: ${message}`;
    });
    if (messages.length) return messages.join(' ');
  }
  const message = body?.detail ?? body?.error?.message;
  return typeof message === 'string' && message ? message : `Request failed (${status}). Please try again.`;
}

async function parseResponse(response) {
  observeContract(response);
  const body = await response.json().catch(() => null);
  if (body?.build?.source_changed && typeof document !== 'undefined' && document.body
      && !document.getElementById?.('backend-build-note')) {
    const notice = document.createElement('p'); notice.id = 'backend-build-note';
    notice.className = 'status-message status-warning'; notice.setAttribute('role', 'status');
    notice.textContent = 'App files changed since the backend started. Finish active work, restart the backend task, then reload. Your saved reports remain on this computer.';
    document.body.prepend(notice);
  }
  if (!response.ok) {
    const message = response.status === 401
      ? 'Your local session has expired or the app restarted. Open the session link printed by the running app, then reopen your saved report.'
      : errorMessage(body, response.status);
    const error = new Error(message);
    error.status = response.status;
    if (response.status === 401) {
      runningContract = null;
      csrfToken = null;
      storedToken(null);
      sessionReady = null;
    }
    throw error;
  }
  return body;
}

async function fetchResponse(path, options = {}) {
  const { timeoutMs = 20000, ...fetchOptions } = options;
  const cveLookup = (options.method || 'GET').toUpperCase() === 'POST' && cveLookupPath.test(path);
  const maximum = cveLookup ? CVE_LOOKUP_TIMEOUT_MS : 60000;
  const deadline = Number.isFinite(timeoutMs) ? Math.min(maximum, Math.max(1000, timeoutMs)) : 20000;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), deadline);
  try {
    return await parseResponse(await fetch(path, { ...fetchOptions, signal: controller.signal, cache: 'no-store' }));
  } catch (error) {
    if (controller.signal.aborted) {
      const timeout = new Error(cveLookup
        ? 'The CVE lookup response took too long. It may still be finishing. Reload saved CVE references before starting another lookup; your scan does not need to run again.'
        : 'The local app took too long to respond. Reopen the dashboard to reconnect. If you already pressed Scan, it may still be running; do not start a duplicate scan.');
      timeout.code = 'request_timeout';
      throw timeout;
    }
    throw error;
  } finally { clearTimeout(timer); }
}

async function bootstrapSession() {
  const fragment = new URLSearchParams(window.location.hash.slice(1));
  const bootstrapToken = fragment.get('token');
  if (bootstrapToken) {
    const body = await fetchResponse('/api/session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ token: bootstrapToken }),
    });
    csrfToken = body.csrf_token;
    storedToken(csrfToken);
    window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}`);
    return;
  }

  {
    const body = await fetchResponse('/api/session', { headers: { Accept: 'application/json' } });
    csrfToken = body.csrf_token;
    storedToken(csrfToken);
  }
}

let sessionReady = null;

async function request(path, options = {}) {
  try {
    await (sessionReady ||= bootstrapSession());
  } catch (error) {
    sessionReady = null;
    throw error;
  }
  const headers = new Headers(options.headers || {});
  headers.set('Accept', 'application/json');
  const method = (options.method || 'GET').toUpperCase();
  if (method === 'POST' && (cveLookupPath.test(path) || /^\/api\/(?:live-scans|scans)$/.test(path)
      || /^\/api\/live-scans\/[^/]+\/retry-hosts$/.test(path)) && expectedContract()
      && runningContract !== expectedContract()) {
    const error = new Error('The running backend needs restarting before this action. Finish active scans, restart the backend task, then reload. Saved reports are unchanged.');
    error.status = 409;
    throw error;
  }
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    if (!headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
    if (!csrfToken) throw new Error('The local session is unavailable. Restart the application.');
    headers.set('X-CSRF-Token', csrfToken);
  }
  return fetchResponse(path, { ...options, headers });
}

export { request, CVE_LOOKUP_TIMEOUT_MS };
