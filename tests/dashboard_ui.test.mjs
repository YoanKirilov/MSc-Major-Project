import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const scanId = '11111111-1111-4111-8111-111111111111';
const key = 'network-assessor-pending-scan';
function setup(request, saved = null) {
  const elements = new Map();
  class Element {
    constructor() { this.events = {}; this.textContent = ''; this.style = {}; this.dataset = {}; }
    addEventListener(name, fn) { this.events[name] = fn; }
    querySelector() { return this.label ||= new Element(); }
  }
  const storage = new Map(saved ? [[key, saved]] : []);
  const timers = [];
  const window = { location: {}, setTimeout(fn) { timers.push(fn); }, sessionStorage: {
    getItem(k) { return storage.get(k); }, setItem(k, v) { storage.set(k, v); }, removeItem(k) { storage.delete(k); },
  } };
  const document = { querySelector(id) { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); }, querySelectorAll() { return []; } };
  const context = vm.createContext({ document, window, request });
  const source = readFileSync(new URL('../app/static/js/dashboard.js', import.meta.url), 'utf8')
    .replace(/^import[^\n]*\n/gm, '').replace(/\nloadStatus\(\);\s*$/, '');
  vm.runInContext(source, context);
  return { elements, storage, window, timers, context, load: () => vm.runInContext('loadStatus()', context) };
}
const ready = { scanner_available: true, allowed_network: '192.168.0.0/24', storage_status: 'ok', ai_available: true };
test('Scan stays disabled until scanner status is loaded', async () => {
  const app = setup(async () => ready);
  assert.equal(app.elements.get('#scanLaunchButton').disabled, true);
  await app.load();
  assert.equal(app.elements.get('#scanLaunchButton').disabled, false);
});
test('session/status failures never become a missing-Nmap message', async () => {
  const app = setup(async () => { throw Object.assign(new Error('Session expired'), { status: 401 }); });
  await app.load();
  await app.elements.get('#scanLaunchButton').events.click();
  assert.match(app.elements.get('#scanError').textContent, /Session expired/);
  assert.doesNotMatch(app.elements.get('#scanError').textContent, /Nmap/);
});
test('storage failure is reported as storage, not Nmap', async () => {
  const app = setup(async () => ({ ...ready, storage_status: 'not_writable' }));
  await app.load();
  await app.elements.get('#scanLaunchButton').events.click();
  assert.match(app.elements.get('#scanError').textContent, /folder is not writable/);
});
test('refresh recovers saved AI progress without starting another scan', async () => {
  const calls = [];
  const app = setup(async (path) => { calls.push(path); return path === '/api/status' ? ready : { state: 'running', phase: 'analysis' }; }, scanId);
  await app.load();
  assert.equal(app.elements.get('#progressPhase').textContent, 'Making your results easier to understand.');
  assert.equal(app.elements.get('#scanLaunchButton').disabled, true);
  assert.deepEqual(calls, ['/api/status', `/api/live-scans/${scanId}/progress`]);
});
test('backend active scan is recovered even without browser storage', async () => {
  const app = setup(async (path) => path === '/api/status' ? { ...ready, active_scan_ids: [scanId] } : { state: 'running', phase: 'service_scan' });
  await app.load();
  assert.equal(app.storage.get(key), scanId);
});
test('scan completed while tab was closed opens its saved report', async () => {
  const app = setup(async (path) => path === '/api/status' ? ready : { state: 'completed', phase: 'finished' }, scanId);
  await app.load();
  assert.equal(app.window.location.href, `/scans/${scanId}`);
  assert.equal(app.storage.has(key), false);
});
test('temporary polling failure preserves scan and retries only the same report', async () => {
  let fail = true;
  const app = setup(async (path) => {
    if (path === '/api/status') return ready;
    if (fail) throw new Error('Temporary disconnection');
    return { state: 'running', phase: 'analysis' };
  }, scanId);
  await app.load();
  assert.equal(app.storage.get(key), scanId);
  assert.equal(app.elements.get('#scanLaunchButton').disabled, true);
  assert.match(app.elements.get('#scanError').textContent, /Reconnecting to the same scan/);
  fail = false;
  await app.timers.shift()();
  assert.equal(app.elements.get('#scanError').hidden, true);
});
