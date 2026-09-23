let csrfToken = window.sessionStorage.getItem('network-assessor-csrf');

async function parseResponse(response) {
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const message = body?.detail || body?.error?.message || `Request failed (${response.status})`;
    throw new Error(message);
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
    window.sessionStorage.setItem('network-assessor-csrf', csrfToken);
    window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}`);
    return;
  }

  if (!csrfToken) {
    const response = await fetch('/api/session', { headers: { Accept: 'application/json' } });
    const body = await parseResponse(response);
    csrfToken = body.csrf_token;
    window.sessionStorage.setItem('network-assessor-csrf', csrfToken);
  }
}

const sessionReady = bootstrapSession();

async function request(path, options = {}) {
  await sessionReady;
  const headers = new Headers(options.headers || {});
  headers.set('Accept', 'application/json');
  const method = (options.method || 'GET').toUpperCase();
  if (['POST', 'PATCH', 'DELETE'].includes(method)) {
    if (!headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
    if (!csrfToken) throw new Error('The local session is unavailable. Restart the application.');
    headers.set('X-CSRF-Token', csrfToken);
  }
  const response = await fetch(path, { ...options, headers });
  return parseResponse(response);
}

export { request };
