import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

function setup({ blocked = false, status = 200, detail = null } = {}) {
  const calls = [];
  const notes = [];
  const context = vm.createContext({ Headers, URLSearchParams, AbortController, setTimeout, clearTimeout,
    document: { body: { prepend(note) { notes.push(note); } },
      getElementById() { return notes[0]; }, createElement() { return { setAttribute() {} }; } },
    window: { location: { hash: '', pathname: '/', search: '' }, sessionStorage: {
      getItem() { if (blocked) throw Error('Blocked'); return null; },
      setItem() { if (blocked) throw Error('Blocked'); },
      removeItem() { if (blocked) throw Error('Blocked'); },
    } },
    fetch: async (path, options) => {
      calls.push({ path, options });
      const session = path === '/api/session';
      return { ok: session || status < 400, status: session ? 200 : status,
        json: async () => session ? { csrf_token: 'test-csrf' } : { detail } };
    },
  });
  const source = readFileSync(new URL('../app/static/js/api.js', import.meta.url), 'utf8').replace('export { request, CVE_LOOKUP_TIMEOUT_MS };', '');
  vm.runInContext(source, context);
  return { context, calls, notes, request: (code) => vm.runInContext(code, context) };
}

test('validation arrays become readable field messages without echoing input values', async () => {
  const app = setup({ status: 422, detail: [{ loc: ['body', 'allowed_network'], msg: 'Value error, enter a private network range', input: 'private-value' }] });
  await assert.rejects(app.request("request('/api/settings')"), (error) => {
    assert.equal(error.message, 'Network range: enter a private network range');
    assert.equal(error.status, 422); return true;
  });
});

test('unknown error objects never become object Object', async () => {
  const app = setup({ status: 503, detail: { unexpected: 'shape' } });
  await assert.rejects(app.request("request('/api/status')"), /Request failed \(503\)/);
});

test('blocked browser storage still authenticates and sends CSRF on writes', async () => {
  const app = setup({ blocked: true });
  await app.request("request('/api/settings', { method: 'PATCH', body: '{}' })");
  assert.equal(app.calls[1].options.headers.get('X-CSRF-Token'), 'test-csrf');
  assert.equal(app.notes.length, 1);
  assert.match(app.notes[0].textContent, /Browser storage is unavailable/);
});

test('expired session with blocked storage gives its original error and can reconnect', async () => {
  const app = setup({ blocked: true, status: 401 });
  await assert.rejects(app.request("request('/api/status')"), /session has expired/);
  await assert.rejects(app.request("request('/api/status')"), /session has expired/);
  assert.equal(app.calls.filter((call) => call.path === '/api/session').length, 2);
});

test('a stalled session request times out without retrying or starting a scan', async () => {
  const app = setup();
  let requests = 0;
  app.context.setTimeout = (fn) => { queueMicrotask(fn); return 1; };
  app.context.clearTimeout = () => {};
  app.context.fetch = async (_path, options) => {
    requests += 1;
    return new Promise((_resolve, reject) => options.signal.addEventListener('abort', () => reject(new Error('aborted'))));
  };
  await assert.rejects(app.request("request('/api/status')"), /took too long/);
  assert.equal(requests, 1);
});

test('API calls explicitly bypass browser response caches', async () => {
  const app = setup();
  await app.request("request('/api/status')");
  assert.ok(app.calls.every((call) => call.options.cache === 'no-store'));
});

test('stale API contract keeps reads and cancellation working but never submits CVE research', async () => {
  const app = setup();
  app.context.document.querySelector = () => ({ content: '2' });
  await app.request("request('/api/status')");
  assert.equal(app.notes.length, 1);
  assert.match(app.notes[0].textContent, /different versions.*Saved reports remain readable/);
  await assert.rejects(app.request("request('/api/live-scans/scan/services/service/cves', {method:'POST'})"), /needs restarting/);
  assert.equal(app.calls.filter(call => call.path.endsWith('/cves')).length, 0);
  for (const path of ['/api/live-scans', '/api/scans', '/api/live-scans/scan/retry-hosts']) {
    await assert.rejects(app.request(`request('${path}', {method:'POST'})`), /needs restarting/);
    assert.equal(app.calls.filter(call => call.path === path).length, 0);
  }
  await app.request("request('/api/live-scans/scan', {method:'DELETE'})");
  assert.equal(app.calls.at(-1).options.method, 'DELETE');
  assert.equal(app.notes.length, 1);
});

test('matching response contract permits a single explicit CVE write', async () => {
  const app = setup();
  app.context.document.querySelector = () => ({ content: '2' });
  app.context.fetch = async (path, options) => {
    app.calls.push({ path, options });
    return { ok: true, headers: new Headers({'X-NetGuard-Contract':'2'}), json: async () => path === '/api/session' ? {csrf_token:'synthetic'} : {saved:true} };
  };
  await app.request("request('/api/live-scans/scan/services/service/cves', {method:'POST'})");
  assert.equal(app.calls.filter(call => call.path.endsWith('/cves')).length, 1);
  assert.equal(app.notes.length, 0);
});

test('ordinary request timeouts stay bounded and are not sent as fetch options', async () => {
  const app = setup();
  const deadlines = [];
  app.context.setTimeout = (_fn, ms) => { deadlines.push(ms); return 1; };
  app.context.clearTimeout = () => {};
  await app.request("request('/api/cve-test', { timeoutMs: 120000 })");
  assert.deepEqual(deadlines, [20000, 60000]);
  assert.ok(app.calls.every(call => !('timeoutMs' in call.options)));
});

test('only an explicit CVE POST gets the full bounded research deadline', async () => {
  const app = setup();
  const deadlines = [];
  app.context.setTimeout = (_fn, ms) => { deadlines.push(ms); return 1; };
  app.context.clearTimeout = () => {};
  await app.request("request('/api/live-scans/scan/services/service/cves', { method: 'POST', timeoutMs: CVE_LOOKUP_TIMEOUT_MS })");
  await app.request("request('/api/live-scans/scan/services/service/cves', { method: 'POST', timeoutMs: 999999 })");
  await app.request("request('/api/live-scans/scan/services/service/cves', { timeoutMs: 110000 })");
  await app.request("request('/api/live-scans/scan/services/service/cves/other', { method: 'POST', timeoutMs: 110000 })");
  assert.deepEqual(deadlines, [20000, 110000, 110000, 60000, 60000]);
});

test('a late CVE response remains pending beyond the old 60-second ceiling', async () => {
  const app = setup();
  const timers = [];
  app.context.setTimeout = (callback, ms) => { timers.push({ callback, ms, cancelled: false }); return timers.length; };
  app.context.clearTimeout = id => { timers[id - 1].cancelled = true; };
  let finish;
  let signal;
  app.context.fetch = async (path, options) => {
    app.calls.push({ path, options });
    if (path === '/api/session') return { ok: true, json: async () => ({ csrf_token: 'test-csrf' }) };
    signal = options.signal;
    return new Promise((resolve, reject) => {
      finish = () => resolve({ ok: true, json: async () => ({ saved: true }) });
      signal.addEventListener('abort', () => reject(new Error('aborted')));
    });
  };
  const work = app.request("request('/api/live-scans/scan/services/service/cves', { method: 'POST', body: '{}', timeoutMs: CVE_LOOKUP_TIMEOUT_MS })");
  while (!finish) await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(timers.map(timer => timer.ms), [20000, 110000]);
  // Advance the synthetic clock past the old ceiling; no wall-clock sleep.
  timers.filter(timer => !timer.cancelled && timer.ms <= 65000).forEach(timer => timer.callback());
  assert.equal(signal.aborted, false);
  finish();
  assert.equal((await work).saved, true);
  assert.equal(app.calls.filter(call => call.options.method === 'POST').length, 1);
});

test('an expired CVE deadline gives recovery advice and does not repeat the write', async () => {
  const app = setup();
  const timers = [];
  app.context.setTimeout = (callback, ms) => { timers.push({ callback, ms }); return timers.length; };
  app.context.clearTimeout = () => {};
  let started;
  app.context.fetch = async (path, options) => {
    app.calls.push({ path, options });
    if (path === '/api/session') return { ok: true, json: async () => ({ csrf_token: 'test-csrf' }) };
    started = true;
    return new Promise((_resolve, reject) => options.signal.addEventListener('abort', () => reject(new Error('aborted'))));
  };
  const work = app.request("request('/api/live-scans/scan/services/service/cves', { method: 'POST', body: '{}', timeoutMs: CVE_LOOKUP_TIMEOUT_MS })");
  while (!started) await new Promise(resolve => setImmediate(resolve));
  const rejected = assert.rejects(work, error => error.code === 'request_timeout' && /Reload saved CVE references/.test(error.message));
  timers.find(timer => timer.ms === 110000).callback();
  await rejected;
  assert.equal(app.calls.filter(call => call.options.method === 'POST').length, 1);
});
