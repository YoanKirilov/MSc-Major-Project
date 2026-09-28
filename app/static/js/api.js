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
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const message = response.status === 401
      ? 'Your local session has expired or the app restarted. Open the session link printed by the running app, then reopen your saved report.'
      : errorMessage(body, response.status);
    const error = new Error(message);
    error.status = response.status;
    if (response.status === 401) {
      csrfToken = null;
      storedToken(null);
      sessionReady = null;
    }
    throw error;
  }
  return body;
}

async function bootstrapSession() {
  const fragment = new URLSearchParams(window.location.hash.slice(1));
  const bootstrapToken = fragment.get('token');
  if (bootstrapToken) {
    const response = await fetch('/api/session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ token: bootstrapToken }),
    });
    const body = await parseResponse(response);
    csrfToken = body.csrf_token;
    storedToken(csrfToken);
    window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}`);
    return;
  }

  {
    const response = await fetch('/api/session', { headers: { Accept: 'application/json' } });
    const body = await parseResponse(response);
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
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    if (!headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
    if (!csrfToken) throw new Error('The local session is unavailable. Restart the application.');
    headers.set('X-CSRF-Token', csrfToken);
  }
  const response = await fetch(path, { ...options, headers });
  return parseResponse(response);
}

export { request };
