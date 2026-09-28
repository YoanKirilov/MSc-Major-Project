import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

function setup({ blocked = false, status = 200, detail = null } = {}) {
  const calls = [];
  const notes = [];
  const context = vm.createContext({ Headers, URLSearchParams,
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
  const source = readFileSync(new URL('../app/static/js/api.js', import.meta.url), 'utf8').replace('export { request };', '');
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
