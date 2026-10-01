import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { analysisProgressText, readScanSetup } from '../app/static/js/report.mjs';

const scanId = '11111111-1111-4111-8111-111111111111';
const key = 'network-assessor-pending-scan';
function setup(request, saved = null, hash = '', pathname = '/') {
  const elements = new Map();
  class Element {
    constructor() { this.events = {}; this.textContent = ''; this.style = {}; this.dataset = {}; }
    addEventListener(name, fn) { this.events[name] = fn; }
    querySelector() { return this.label ||= new Element(); }
    replaceChildren() { this.children = []; }
    append(child) { (this.children ||= []).push(child); }
  }
  const storage = new Map(saved ? [[key, saved]] : []);
  const timers = [];
  const window = { location: { hash, pathname, replace(url) { this.href = url; } }, history: { replaceState(_a, _b, url) { window.location.hash = url.slice(url.indexOf('#')); } }, setTimeout(fn) { timers.push(fn); }, sessionStorage: {
    getItem(k) { return storage.get(k); }, setItem(k, v) { storage.set(k, v); }, removeItem(k) { storage.delete(k); },
  } };
  const document = { createElement() { return new Element(); }, querySelector(id) { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); }, querySelectorAll() { return []; } };
  const context = vm.createContext({ document, window, request, analysisProgressText, readScanSetup, URLSearchParams, configurePicker() {}, startSetupTools() {} });
  const source = readFileSync(new URL('../app/static/js/dashboard.js', import.meta.url), 'utf8')
    .replace(/^import[^\n]*\n/gm, '').replace(/\nloadStatus\(\);\s*$/, '');
  vm.runInContext(source, context);
  return { elements, storage, window, timers, context, load: () => vm.runInContext('loadStatus()', context) };
}
const ready = { ui_contract_version: 1, scanner_available: true, allowed_network: '192.168.0.0/24', storage_status: 'ok', ai_available: true };

test('outdated backend explains restart and never submits a scan', async () => {
  const calls = [];
  const app = setup(async (path) => { calls.push(path); return { ...ready, ui_contract_version: undefined }; });
  await app.load();
  assert.match(app.elements.get('#scan-config').textContent, /page and backend versions do not match/);
  await app.elements.get('#scanLaunchButton').events.click();
  assert.ok(calls.every(path => path === '/api/status'));
  assert.match(app.elements.get('#scanError').textContent, /restart the NetGuard backend/);
});

test('version warning does not prevent recovery of an already running scan', async () => {
  const calls = [];
  const app = setup(async (path) => {
    calls.push(path);
    return path === '/api/status'
      ? { ...ready, ui_contract_version: undefined, active_scan_ids: [scanId] }
      : { state: 'running', phase: 'analysis' };
  }, scanId);
  await app.load();
  assert.equal(app.elements.get('#progressPhase').textContent, 'Making your results easier to understand.');
  assert.deepEqual(calls, ['/api/status', `/api/live-scans/${scanId}/progress`]);
});
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

test('AI progress shows saved completed counts and distinguishes waiting', async () => {
  const app = setup(async (path) => path === '/api/status' ? ready : {
    state: 'running', phase: 'analysis',
    analysis_progress: { state: 'preparing', total: 9, completed: 6, active: 3, attempt: 1 },
  }, scanId);
  await app.load();
  assert.match(app.elements.get('#progressDetail').textContent, /Prepared 6 of 9 explanations/);
  assert.match(app.elements.get('#progressDetail').textContent, /Working on 3/);
  assert.equal(app.elements.get('#progressPercent').textContent, '96%');
  assert.match(analysisProgressText({ analysis_progress: { state: 'waiting', total: 9 } }), /Waiting for local AI/);
});
test('backend active scan is recovered even without browser storage', async () => {
  const app = setup(async (path) => path === '/api/status' ? { ...ready, active_scan_ids: [scanId] } : { state: 'running', phase: 'service_scan' });
  await app.load();
  assert.equal(app.storage.get(key), scanId);
});

test('refresh recovers device-details progress without starting another scan', async () => {
  const calls = [];
  const app = setup(async (path) => {
    calls.push(path);
    return path === '/api/status' ? ready : { state: 'running', phase: 'enrichment' };
  }, scanId);
  await app.load();
  assert.equal(app.elements.get('#progressPhase').textContent, 'Gathering device details');
  assert.equal(app.elements.get('#scanLaunchButton').disabled, true);
  assert.deepEqual(calls, ['/api/status', `/api/live-scans/${scanId}/progress`]);
  assert.equal(app.window.location.href, undefined);
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

test('explicit setup clears stale completed-scan storage without automatically scanning', async () => {
  const calls = [];
  const app = setup(async (path) => { calls.push(path); return ready; }, scanId, '#setup=1&profile=deep-tcp-v1&hosts=192.168.0.53');
  await app.load();
  assert.deepEqual(calls, ['/api/status']);
  assert.equal(app.storage.has(key), false);
  assert.equal(app.elements.get('#deepHostInput').value, '192.168.0.53');
  assert.equal(app.elements.get('#deepHostInput').hidden, false);
  assert.equal(app.window.location.href, undefined);
});

test('explicit setup still resumes a real active backend job', async () => {
  const app = setup(async (path) => path === '/api/status' ? { ...ready, active_scan_id: scanId } : { state: 'running', phase: 'analysis' }, null, '#setup=1');
  await app.load();
  assert.equal(app.storage.get(key), scanId);
  assert.equal(app.elements.get('#scanLaunchButton').disabled, true);
});

test('Light known-host setup preserves hosts until an explicit Scan click', async () => {
  const calls = [];
  const app = setup(async (path, options) => {
    calls.push({ path, options });
    if (path === '/api/status') return ready;
    if (options?.method === 'POST') return { scan_id: scanId };
    return { state: 'running', phase: 'service_scan' };
  }, null, '#setup=1&profile=light&hosts=192.168.0.53,192.168.0.54');
  await app.load();
  assert.equal(calls.length, 1);
  assert.match(app.elements.get('#scanSetupNote').textContent, /192.168.0.54/);
  await app.elements.get('#scanLaunchButton').events.click();
  const body = JSON.parse(calls.find((call) => call.options?.method === 'POST').options.body);
  assert.equal(body.mode, 'known_hosts');
  assert.deepEqual(body.hosts, ['192.168.0.53', '192.168.0.54']);
});

test('choosing a different Deep device requires an address, not an automatic scan', async () => {
  const calls = [];
  const app = setup(async (path) => { calls.push(path); return ready; }, null, '#setup=1&profile=deep-tcp-v1');
  await app.load();
  await app.elements.get('#scanLaunchButton').events.click();
  assert.match(app.elements.get('#scanError').textContent, /Enter one authorised device/);
  assert.deepEqual(calls, ['/api/status']);
});

test('explicit second-tab setup ignores copied pending storage and leaves the first job alone', async () => {
  const calls = [];
  const app = setup(async (path) => { calls.push(path); return { ...ready, active_scan_ids: [scanId] }; }, scanId, '#setup=1&new=1');
  await app.load();
  assert.deepEqual(calls, ['/api/status']);
  assert.equal(app.elements.get('#scanLaunchButton').disabled, false);
  assert.equal(app.storage.has(key), false);
  assert.equal(app.window.location.href, undefined);
});

test('a pinned tab resumes its own scan even if storage points to another scan', async () => {
  const second = '22222222-2222-4222-8222-222222222222';
  const calls = [];
  const app = setup(async (path) => {
    calls.push(path);
    return path === '/api/status' ? { ...ready, active_scan_ids: [scanId, second] } : { state: 'running', phase: 'service_scan' };
  }, scanId, `#scan=${second}`);
  await app.load();
  assert.deepEqual(calls, ['/api/status', `/api/live-scans/${second}/progress`]);
  assert.equal(app.storage.get(key), second);
  await app.elements.get('#scanCancelButton').events.click();
  assert.equal(calls.at(-1), `/api/live-scans/${second}`);
});

test('multiple running jobs are offered explicitly rather than choosing the first', async () => {
  const second = '22222222-2222-4222-8222-222222222222';
  const calls = [];
  const app = setup(async (path) => { calls.push(path); return { ...ready, active_scan_ids: [scanId, second] }; });
  await app.load();
  assert.deepEqual(calls, ['/api/status']);
  assert.equal(app.window.location.href, undefined);
});

test('direct Deep page ignores another running job and launches only Deep', async () => {
  const calls = [];
  const app = setup(async (path, options) => {
    calls.push({ path, options });
    if (path === '/api/status') return { ...ready, active_scan_ids: [scanId] };
    if (options?.method === 'POST') return { scan_id: scanId };
    if (path === `/api/scans/${scanId}`) return { policy: { profile: 'deep-tcp-v1' } };
    return { state: 'running', phase: 'service_scan' };
  }, scanId, '#setup=1&profile=light&hosts=192.168.0.54', '/deep');
  await app.load();
  assert.equal(calls.length, 1);
  assert.equal(app.elements.get('#deepHostInput').hidden, false);
  assert.equal(app.elements.get('#deepHostInput').value, '');
  app.elements.get('#deepHostInput').value = '192.168.0.53';
  await app.elements.get('#scanLaunchButton').events.click();
  const body = JSON.parse(calls.find(call => call.options?.method === 'POST').options.body);
  assert.equal(body.profile, 'deep-tcp-v1');
  assert.deepEqual(body.hosts, ['192.168.0.53']);
  assert.equal(app.storage.get(`${key}:deep-tcp-v1`), scanId);
});

test('direct Light page uses its own pending key and preserves its URL on refresh', async () => {
  const calls = [];
  const app = setup(async path => {
    calls.push(path);
    if (path === '/api/status') return ready;
    if (path === `/api/scans/${scanId}`) return { policy: { profile: 'light' } };
    return { state: 'running', phase: 'service_scan' };
  }, null, '', '/light');
  app.storage.set(`${key}:light`, scanId);
  await app.load();
  assert.deepEqual(calls, ['/api/status', `/api/scans/${scanId}`, `/api/live-scans/${scanId}/progress`]);
  assert.equal(app.window.location.pathname, '/light');
  assert.equal(app.window.location.hash, `#scan=${scanId}`);
});

test('a pinned job of another profile opens the general dashboard without relabelling it', async () => {
  const calls = [];
  const app = setup(async path => {
    calls.push(path);
    return path === '/api/status' ? ready : { policy: { profile: 'light' } };
  }, null, `#scan=${scanId}`, '/deep');
  await app.load();
  assert.equal(app.window.location.href, `/#scan=${scanId}`);
  assert.deepEqual(calls, ['/api/status', `/api/scans/${scanId}`]);
});

test('full capacity waits quietly, checks availability and never automatically submits', async () => {
  let full = true;
  const calls = [];
  const app = setup(async (path, options) => {
    calls.push({ path, options });
    return { ...ready, scan_capacity_available: !full, max_concurrent_scans: 5 };
  }, null, '', '/deep');
  await app.load();
  assert.equal(app.elements.get('#scanLaunchButton').disabled, true);
  assert.match(app.elements.get('#capacityNote').textContent, /All scan slots/);
  assert.notEqual(app.elements.get('#scanError').hidden, false);
  await app.elements.get('#scanLaunchButton').events.click();
  assert.equal(calls.length, 1);
  full = false;
  await app.timers.shift()();
  assert.equal(app.elements.get('#scanLaunchButton').disabled, false);
  assert.equal(app.elements.get('#capacityNote').hidden, true);
  assert.ok(calls.every(call => !call.options?.method));
});

test('last-slot race becomes an inline wait instead of an error or automatic retry', async () => {
  let posts = 0;
  const app = setup(async (path, options) => {
    if (options?.method === 'POST') {
      posts++;
      throw Object.assign(new Error('Scan capacity reached'), { status: 429 });
    }
    return { ...ready, scan_capacity_available: true };
  }, null, '', '/light');
  await app.load();
  await app.elements.get('#scanLaunchButton').events.click();
  assert.equal(posts, 1);
  assert.equal(app.elements.get('#scanError').hidden, true);
  assert.equal(app.elements.get('#scanProgress').hidden, true);
  assert.equal(app.elements.get('#scanLaunchButton').disabled, true);
  await app.timers.shift()();
  assert.equal(posts, 1);
  assert.equal(app.elements.get('#scanLaunchButton').disabled, false);
});
