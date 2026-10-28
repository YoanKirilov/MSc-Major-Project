import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { randomUUID } from 'node:crypto';
import { createStartState } from '../app/static/js/start-state.mjs';
import { analysisProgressText, readScanSetup, ollamaStatusText, progressAnnouncement } from '../app/static/js/report.mjs';

const scanId = '11111111-1111-4111-8111-111111111111';
const key = 'network-assessor-pending-scan';

test('start ownership invalidates old generations even when the same identifier is selected later', () => {
  const state = createStartState(scanId);
  const first = state.generation;
  assert.equal(state.select(scanId), false);
  assert.equal(state.generation, first);
  state.select(null); state.select(scanId);
  assert.equal(state.owns(scanId, first), false);
  assert.equal(state.owns(scanId, state.generation), true);
});

test('only one read owns a generation and an old finalizer cannot clear a newer read', () => {
  const state = createStartState(scanId);
  const old = state.beginRead();
  assert.ok(Object.isFrozen(old));
  assert.equal(state.beginRead(), null);
  state.select('newer');
  const current = state.beginRead();
  assert.equal(state.finishRead(old), false);
  assert.equal(state.beginRead(), null);
  assert.equal(state.finishRead(current), true);
  assert.equal(state.finishRead(current), false);
  assert.ok(state.beginRead());
});

test('automatic recovery stays bounded and only an explicit retry or new intention resets its budget', () => {
  const state = createStartState(scanId);
  const read = state.beginRead();
  state.finishRead(read);
  for (let i = 1; i < 10; i++) assert.equal(state.shouldPoll(read), true);
  state.select(scanId);
  assert.equal(state.shouldPoll(read), false);
  state.resetReads();
  assert.equal(state.shouldPoll(read), true);
  state.select('newer');
  assert.equal(state.shouldPoll(read), false);
  assert.equal(state.shouldPoll(state.beginRead()), true);
});

test('clearing a start prevents read recovery and does not grant any new operation', () => {
  const state = createStartState(scanId);
  const read = state.beginRead();
  state.select(null);
  assert.equal(state.operation, null);
  assert.equal(state.beginRead(), null);
  assert.equal(state.finishRead(read), false);
  assert.equal(state.shouldPoll(read), false);
});

test('progress announcements use meaningful stage changes and bounded milestones, not elapsed ticks', () => {
  const keys = new Set();
  for (let completed = 0; completed <= 100; completed++) {
    const data = { phase: 'service_scan', coverage: { discovered_count: 100, service_completed_count: completed } };
    const speech = progressAnnouncement(data, false);
    keys.add(speech.key);
    assert.deepEqual(progressAnnouncement({ ...data, elapsed_s: 999999 }, false), speech);
    assert.doesNotMatch(speech.message, /passed|secure/);
  }
  assert.equal(keys.size, 5);
  assert.equal(progressAnnouncement({ phase: 'service_scan', coverage: { candidate_count: 1, service_completed_count: 1 } }, true).key, 'service_scan:0');
  for (const completed of [-1, 101, NaN, 1.5]) assert.equal(progressAnnouncement({ phase: 'analysis', analysis_progress: { total: 100, completed } }).key, 'analysis:0');
  assert.match(progressAnnouncement({ phase: 'analysis', analysis_progress: { state: 'waiting' } }).message, /Waiting for local AI/);
  assert.match(progressAnnouncement({ phase: 'analysis', analysis_progress: { total: 4, completed: 2 } }).message, /2 of 4 wording items prepared/);
});
test('Deep uses stage activity during its device check and exact AI counts afterwards', async () => {
  let phase = 'service_scan';
  const app = setup(async path => path === '/api/status' ? { ...ready, active_scan_ids: [scanId] } : path === `/api/scans/${scanId}`
    ? { policy: { profile: 'deep-tcp-v1' } } : { state: 'running', phase, policy: { profile: 'deep-tcp-v1' },
      coverage: { candidate_count: 1 }, analysis_progress: { total: 5, completed: 2, state: 'preparing' } }, null, `#scan=${scanId}`, '/deep');
  await app.load();
  assert.equal(app.elements.get('#progressPercent').textContent, 'Running');
  assert.equal(app.elements.get('#progressTrack').attributes['aria-valuenow'], undefined);
  assert.match(app.elements.get('#scan-config').textContent, /in progress.*Progress is below/);
  assert.doesNotMatch(app.elements.get('#scan-config').textContent, /Ready/);
  assert.match(app.elements.get('#scanStageChecks').textContent, /Current/);
  assert.equal(app.elements.get('#scanStageAnalysis').dataset.state, 'waiting');
  phase = 'analysis';
  await app.timers.shift()();
  assert.match(app.elements.get('#scanStageAnalysis').textContent, /Current/);
  assert.match(app.elements.get('#progressDetail').textContent, /2 of 5/);
  assert.equal(app.elements.get('#progressTrack').attributes['aria-valuenow'], '94');
  assert.match(app.elements.get('#scan-config').textContent, /results are saved.*explanations/);
});

test('queued and discovery progress are indeterminate, with honest state messages', async () => {
  for (const phase of ['queued', 'discovery']) {
    const app = setup(async path => path === '/api/status' ? ready : path === `/api/scans/${scanId}`
      ? { policy: { profile: 'light' } } : { state: 'running', phase, coverage: { candidate_count: 254 } }, scanId);
    await app.load();
    assert.equal(app.elements.get('#progressTrack').attributes['aria-valuenow'], undefined);
    assert.match(app.elements.get('#progressTrack').attributes['aria-valuetext'], /Time remaining is unknown/);
    assert.equal(app.elements.get('#progressPercent').textContent, phase === 'queued' ? 'Waiting' : 'Running');
    assert.doesNotMatch(app.elements.get('#scan-config').textContent, /Ready to scan/);
    assert.equal(app.elements.get('#scanProgress').scrolls || 0, 0);
  }
});

test('reported numeric progress is bounded and never exposes NaN or negative ARIA values', async () => {
  for (const coverage of [
    { candidate_count: 1, service_completed_count: -9 },
    { candidate_count: 1, service_completed_count: NaN },
    { candidate_count: 1, service_completed_count: 9999 },
  ]) {
    const app = setup(async path => path === '/api/status' ? ready : path === `/api/scans/${scanId}`
      ? { policy: { profile: 'light' } } : { state: 'running', phase: 'service_scan', coverage }, scanId);
    await app.load();
    const value = Number(app.elements.get('#progressTrack').attributes['aria-valuenow']);
    assert.ok(Number.isFinite(value) && value >= 0 && value <= 99);
  }
});

test('failed cancellation keeps the same job and a retryable cancel action', async () => {
  let cancelAttempts = 0;
  const app = setup(async (path, options) => {
    if (options?.method === 'DELETE') { cancelAttempts++; throw Object.assign(new Error('Connection unavailable'), { status: 503 }); }
    if (path === '/api/status') return ready;
    if (path === `/api/scans/${scanId}`) return { policy: { profile: 'light' } };
    return { state: 'running', phase: 'service_scan' };
  }, scanId);
  await app.load();
  await app.elements.get('#scanCancelButton').events.click();
  assert.equal(cancelAttempts, 1);
  assert.equal(app.elements.get('#scanLaunchButton').disabled, true);
  assert.equal(app.elements.get('#scanLaunchButton').querySelector('span').textContent, 'Scan in progress');
  assert.equal(app.elements.get('#scanCancelButton').hidden, false);
  assert.equal(app.elements.get('#scanCancelButton').disabled, false);
  assert.equal(app.window.location.hash, `#scan=${scanId}`);
  await app.timers.shift()();
  assert.match(app.elements.get('#scan-config').textContent, /in progress.*Progress is below/);
});

test('selecting a saved Deep target clears its old missing-address error', async () => {
  const app = setup(async () => ready, null, '#setup=1&profile=deep-tcp-v1');
  await app.load();
  await app.elements.get('#scanLaunchButton').events.click();
  assert.equal(app.elements.get('#deepHostError').hidden, false);
  app.elements.get('#recentDeviceSelect').events.change();
  assert.equal(app.elements.get('#deepHostError').hidden, true);
  assert.equal(app.elements.get('#deepHostInput').attributes['aria-invalid'], undefined);
});
test('runtime progress distinguishes a responsive app from scanner-check progress', async () => {
  const app = setup(async path => path === '/api/status' ? { ...ready, active_scan_id: scanId } : {
    state: 'running', phase: 'service_scan', coverage: { candidate_count: 1, service_completed_count: 0 },
    runtime: { backend_checked_at: new Date().toISOString(), job_active: true, scanner_checks_running: 1, last_scanner_event: 'started', last_scanner_event_at: new Date().toISOString() },
  }, scanId);
  await app.load();
  const note = app.elements.get('#progressNote').textContent;
  assert.match(note, /App connection confirmed/);
  assert.match(note, /1 check is running/);
  assert.match(note, /time remaining is unknown/);
  assert.match(note, /most recent check started less than a minute ago/);
  assert.match(note, /does not confirm that a device answered/);
  assert.doesNotMatch(note, /lifecycle/);
});

test('progress describes multiple checks and returned activity without promising success', async () => {
  for (const running of [0, 2]) {
    const app = setup(async path => path === '/api/status' ? { ...ready, active_scan_id: scanId } : {
      state: 'running', phase: 'service_scan', runtime: { backend_checked_at: new Date().toISOString(), job_active: true,
        scanner_checks_running: running, last_scanner_event: 'returned', last_scanner_event_at: new Date(Date.now() - 125000).toISOString() },
    }, scanId);
    await app.load();
    const note = app.elements.get('#progressNote').textContent;
    assert.match(note, running ? /2 checks are running/ : /waiting or preparing/);
    assert.match(note, /A check ended 2 minutes ago/);
    assert.match(note, /does not confirm that a device answered/);
  }
});

test('missing activity time and AI phase do not invent scanner timing', async () => {
  for (const phase of ['service_scan', 'analysis']) {
    const app = setup(async path => path === '/api/status' ? { ...ready, active_scan_id: scanId } : {
      state: 'running', phase, runtime: { backend_checked_at: new Date().toISOString(), job_active: true,
        scanner_checks_running: 0, last_scanner_event: 'started', last_scanner_event_at: phase === 'analysis' ? new Date().toISOString() : null },
    }, scanId);
    await app.load();
    const note = app.elements.get('#progressNote').textContent;
    assert.doesNotMatch(note, /check started|check ended|NaN|lifecycle/);
    if (phase === 'analysis') assert.match(note, /observations have been saved/);
  }
});
function setup(request, saved = null, hash = '', pathname = '/') {
  const elements = new Map();
  class Element {
    constructor() { this.events = {}; this.textContent = ''; this.style = {}; this.dataset = {}; this.attributes = {}; this.classList = { toggle() {} }; }
    setAttribute(name, value) { this.attributes[name] = String(value); }
    removeAttribute(name) { delete this.attributes[name]; }
    addEventListener(name, fn) { this.events[name] = fn; }
    querySelector() { return this.label ||= new Element(); }
    replaceChildren() { this.children = []; }
    append(child) { (this.children ||= []).push(child); }
    insertBefore(child, before) { this.inserted = { child, before }; }
    scrollIntoView() { this.scrolls = (this.scrolls || 0) + 1; }
    focus() { this.focused = true; }
  }
  const storage = new Map(saved ? [[key, saved]] : []);
  const timers = [];
  const window = { events:{}, addEventListener(type, handler) { this.events[type]=handler; }, location: { hash, pathname, replace(url) { this.href = url; } }, history: { replaceState(_a, _b, url) { window.location.hash = url.slice(url.indexOf('#')); } }, setTimeout(fn) { timers.push(fn); }, sessionStorage: {
    getItem(k) { return storage.get(k); }, setItem(k, v) { storage.set(k, v); }, removeItem(k) { storage.delete(k); },
  } };
  const document = { createElement() { return new Element(); }, querySelector(id) { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); }, querySelectorAll() { return []; } };
  const context = vm.createContext({ document, window, request, crypto: { randomUUID }, createStartState, analysisProgressText, progressAnnouncement, readScanSetup, ollamaStatusText, URLSearchParams, configurePicker() {}, startSetupTools() {} });
  const source = readFileSync(new URL('../app/static/js/dashboard.js', import.meta.url), 'utf8')
    .replace(/^import[^\n]*\n/gm, '').replace(/\nloadStatus\(\);\s*$/, '');
  vm.runInContext(source, context);
  return { elements, storage, window, timers, context, load: () => vm.runInContext('loadStatus()', context) };
}
const ready = { ui_contract_version: 1, scanner_available: true, allowed_network: '192.168.0.0/24', storage_status: 'ok', ai_available: true };

test('retired progress replies cannot redirect or keep polling after page navigation', async () => {
  let release;
  const calls = [];
  const app = setup(async path => {
    calls.push(path);
    if (path === '/api/status') return {...ready,active_scan_ids:[scanId]};
    if (path === `/api/scans/${scanId}`) return {policy:{profile:'light'}};
    return new Promise(resolve=>{release=resolve;});
  }, scanId, `#scan=${scanId}`);
  const loading = app.load();
  while (!release) await new Promise(resolve=>setImmediate(resolve));
  app.window.events.pagehide({persisted:true});
  release({state:'completed',phase:'finished'});
  await loading;
  assert.equal(app.window.location.href, undefined);
  assert.equal(app.timers.length, 0);
  assert.equal(app.storage.get(key), scanId);
  app.window.events.pageshow({persisted:true});
  while (calls.filter(path=>path.endsWith('/progress')).length < 2) await new Promise(resolve=>setImmediate(resolve));
  release({state:'running',phase:'service_scan'});
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(app.timers.length, 1);
  assert.ok(!calls.some(path=>path.includes('/retry')));
});

for (const outcome of ['accepted', 409, 429, 503, 'lost']) {
  for (const newerFinishesFirst of [false, true]) {
    test(`superseded POST ${outcome} cannot change the newer start (newer finished: ${newerFinishesFirst})`, async () => {
      const newerId = '22222222-2222-4222-8222-222222222222';
      const posts = [], calls = [];
      const app = setup(async (path, options) => {
        calls.push({path, options});
        if (path === '/api/status') return ready;
        if (options?.method === 'POST') return new Promise((resolve, reject) => posts.push({resolve, reject, body:JSON.parse(options.body)}));
        if (path.startsWith('/api/scans/')) return {policy:{profile:'light'}};
        assert.ok(!path.startsWith('/api/scan-starts/'), 'a stale failure must not initiate recovery');
        return {state:'running',phase:'service_scan'};
      }, null, '', '/light');
      app.window.confirm = () => true;
      await app.load();
      const first = app.elements.get('#scanLaunchButton').events.click();
      app.elements.get('#scanStartReset').events.click();
      const second = app.elements.get('#scanLaunchButton').events.click();
      assert.equal(posts.length, 2);
      assert.notEqual(posts[0].body.operation_id, posts[1].body.operation_id);
      if (newerFinishesFirst) { posts[1].resolve({scan_id:newerId}); await second; }
      if (outcome === 'accepted') posts[0].resolve({scan_id:scanId});
      else posts[0].reject(Object.assign(new Error('Earlier attempt outcome'), typeof outcome === 'number' ? {status:outcome} : {}));
      await first;
      assert.equal(app.elements.get('#scanLaunchButton').disabled, true);
      assert.equal(app.window.location.hash, newerFinishesFirst ? `#scan=${newerId}` : `#start=${posts[1].body.operation_id}`);
      if (!newerFinishesFirst) {
        assert.equal(app.storage.get(`${key}:light:start`), posts[1].body.operation_id);
        posts[1].resolve({scan_id:newerId}); await second;
      }
      assert.equal(app.window.location.hash, `#scan=${newerId}`);
      assert.equal(calls.filter(call=>call.options?.method === 'POST').length,2);
      assert.ok(calls.every(call=>call.options?.method !== 'DELETE'));
    });
  }
}

test('an older recovery finalizer cannot unlock or replace a newer in-flight recovery', async () => {
  const reads=[], posts=[];
  const entered=[];
  const reading=[0,1].map(index=>new Promise(resolve=>{entered[index]=resolve;}));
  const newerId='22222222-2222-4222-8222-222222222222';
  const app=setup(async (path,options)=>{
    if(path==='/api/status') return ready;
    if(options?.method==='POST') { posts.push(JSON.parse(options.body)); throw new Error('Reply lost'); }
    if(path.startsWith('/api/scan-starts/')) return new Promise(resolve=>{reads.push({path,resolve}); entered[reads.length-1]();});
    if(path.startsWith('/api/scans/')) return {policy:{profile:'light'}};
    return {state:'running',phase:'service_scan'};
  },null,'','/light');
  app.window.confirm=()=>true;
  await app.load();
  const first=app.elements.get('#scanLaunchButton').events.click();
  await reading[0];
  app.elements.get('#scanStartReset').events.click();
  const second=app.elements.get('#scanLaunchButton').events.click();
  await reading[1];
  assert.equal(reads.length,2);
  reads[0].resolve({state:'accepted',scan_id:scanId}); await first;
  assert.equal(app.window.location.hash,`#start=${posts[1].operation_id}`);
  assert.equal(app.elements.get('#scanStartRecover').disabled,true);
  assert.equal(app.elements.get('#scanLaunchButton').disabled,true);
  reads[1].resolve({state:'accepted',scan_id:newerId}); await second;
  assert.equal(app.window.location.hash,`#scan=${newerId}`);
});

test('pinned recovery remains usable without the readiness endpoint and retries only the original GET', async () => {
  const operation='99999999-9999-4999-8999-999999999999', calls=[];
  let available=false;
  const app=setup(async (path,options)=>{
    calls.push({path,options});
    assert.notEqual(path,'/api/status','recovering evidence must not depend on readiness');
    if(path.startsWith('/api/scan-starts/')) {
      if(!available) throw Object.assign(new Error('Temporary outage'),{status:503});
      return {state:'accepted',scan_id:scanId};
    }
    if(path.startsWith('/api/scans/')) return {policy:{profile:'light'}};
    return {state:'running',phase:'service_scan'};
  },null,`#start=${operation}`,'/light');
  await app.load();
  assert.equal(app.elements.get('#scanStartRecover').hidden,false);
  assert.equal(app.elements.get('#scanStartRecover').disabled,false);
  assert.equal(app.elements.get('#scanLaunchButton').disabled,true);
  available=true;
  await app.elements.get('#scanStartRecover').events.click();
  assert.equal(app.window.location.hash,`#scan=${scanId}`);
  assert.ok(calls.every(call=>!call.options?.method));
});

test('expired pending recovery preserves context and stops automatic reads without enabling Scan', async () => {
  const operation='99999999-9999-4999-8999-999999999999';
  const app=setup(async()=>{throw Object.assign(new Error('Session required'),{status:401});},null,`#start=${operation}`);
  await app.load();
  assert.match(app.elements.get('#scanError').textContent,/session has expired.*session link/);
  assert.equal(app.elements.get('#scanStartRecover').hidden,false);
  assert.equal(app.elements.get('#scanLaunchButton').disabled,true);
  assert.equal(app.window.location.hash,`#start=${operation}`);
  assert.equal(app.timers.length,0);
});

test('a rejected receipt cannot leave the next separate start recovery button disabled', async () => {
  const operation='99999999-9999-4999-8999-999999999999';
  let accept;
  const app=setup(async (path,options)=>{
    if(path.startsWith('/api/scan-starts/')) return {state:'rejected'};
    if(path==='/api/status') return ready;
    if(options?.method==='POST') return new Promise(resolve=>{accept=resolve;});
    if(path.startsWith('/api/scans/')) return {policy:{profile:'light'}};
    return {state:'running',phase:'service_scan'};
  },null,`#start=${operation}`,'/light');
  await app.load();
  await app.elements.get('#scanLaunchButton').events.click(); // Recheck readiness first.
  const started=app.elements.get('#scanLaunchButton').events.click();
  assert.equal(app.elements.get('#scanStartRecover').hidden,false);
  assert.equal(app.elements.get('#scanStartRecover').disabled,false);
  accept({scan_id:scanId}); await started;
});

test('lost start reply locks submission and recovers the exact original receipt using GET only', async () => {
  let posts = 0, operation, available = false;
  const app = setup(async (path, options) => {
    if (path === '/api/status') return ready;
    if (options?.method === 'POST') {
      posts++; operation = JSON.parse(options.body).operation_id;
      throw Object.assign(new Error('Reply lost'), {code:'request_timeout'});
    }
    if (path.startsWith('/api/scan-starts/')) {
      assert.equal(path, `/api/scan-starts/${operation}`);
      return available ? {state:'accepted', scan_id:scanId} : {state:'preparing'};
    }
    if (path === `/api/scans/${scanId}`) return {policy:{profile:'light'}};
    return {state:'running',phase:'service_scan'};
  }, null, '', '/light');
  await app.load();
  await app.elements.get('#scanLaunchButton').events.click();
  assert.equal(posts,1);
  assert.equal(app.elements.get('#scanLaunchButton').disabled,true);
  assert.equal(app.window.location.hash,`#start=${operation}`);
  assert.equal(app.elements.get('#deepHostInput').disabled,true);
  await app.elements.get('#scanLaunchButton').events.click();
  assert.equal(posts,1);
  available = true;
  await app.elements.get('#scanStartRecover').events.click();
  assert.equal(app.window.location.hash,`#scan=${scanId}`);
  assert.equal(posts,1);
  assert.equal(app.elements.get('#scanStartRecover').hidden,true);
});

test('a pinned unknown start with blocked browser storage never submits or selects another job', async () => {
  const operation='99999999-9999-4999-8999-999999999999', calls=[];
  const app=setup(async (path,options) => {
    calls.push({path,options});
    if(path==='/api/status') return {...ready,active_scan_ids:[scanId]};
    throw Object.assign(new Error('Not yet recorded'),{status:404});
  },null,`#start=${operation}`,'/light');
  app.window.sessionStorage.getItem=()=>{throw new Error('Blocked');};
  app.window.sessionStorage.setItem=()=>{throw new Error('Blocked');};
  await app.load();
  assert.equal(app.elements.get('#scanLaunchButton').disabled,true);
  assert.equal(app.elements.get('#scanStartRecover').hidden,false);
  assert.equal(app.window.location.hash,`#start=${operation}`);
  assert.deepEqual(calls.map(item=>item.path),[`/api/scan-starts/${operation}`]);
  assert.ok(calls.every(item=>!item.options?.method));
});

test('refresh restores immutable Deep target without moving progress or scrolling, including general page', async () => {
  for (const pathname of ['/deep', '/']) {
    const calls = [];
    const app = setup(async path => {
      calls.push(path);
      if (path === '/api/status') return ready;
      if (path === `/api/scans/${scanId}`) return { policy: { profile: 'deep-tcp-v1' }, target: { hosts: ['192.168.0.216'] } };
      return { state: 'running', phase: 'service_scan', coverage: { candidate_count: 1 } };
    }, null, `#scan=${scanId}`, pathname);
    await app.load();
    assert.equal(app.elements.get('#deepHostInput').value, '192.168.0.216');
    assert.equal(app.elements.get('#deepHostInput').disabled, true);
    assert.equal(app.elements.get('#recentDeviceSelect').disabled, true);
    assert.equal(app.elements.get('#refreshDeviceChoices').disabled, true);
    assert.match(app.elements.get('#progressTarget').textContent, /192\.168\.0\.216.*fixed/);
    const progress = app.elements.get('#scanProgress');
    assert.equal(app.elements.get('.scan-home-main').inserted, undefined);
    assert.equal(progress.scrolls || 0, 0);
    await app.timers.shift()();
    assert.equal(progress.scrolls || 0, 0);
    assert.ok(calls.every(path => path !== '/api/live-scans'));
  }
});

test('metadata outage retains the pinned job and disabled setup while progress stays readable', async () => {
  const app = setup(async path => {
    if (path === '/api/status') return ready;
    if (path === `/api/scans/${scanId}`) throw Object.assign(new Error('storage busy'), { status: 503 });
    return { state: 'running', phase: 'analysis' };
  }, null, `#scan=${scanId}`, '/deep');
  await app.load();
  assert.equal(app.elements.get('#scanLaunchButton').disabled, true);
  assert.equal(app.elements.get('#deepHostInput').disabled, true);
  assert.equal(app.window.location.hash, `#scan=${scanId}`);
  assert.match(app.elements.get('#progressTarget').textContent, /saved target/);
  assert.match(app.elements.get('#progressPhase').textContent, /easier to understand/);
  assert.equal(app.elements.get('.scan-home-main').inserted, undefined);
  assert.equal(app.elements.get('#scanProgress').scrolls || 0, 0);
});

test('missing pinned report returns usable setup instead of leaving the address disabled', async () => {
  const app = setup(async path => {
    if (path === '/api/status') return ready;
    throw Object.assign(new Error('Not found'), { status: 404 });
  }, null, `#scan=${scanId}`, '/deep');
  await app.load();
  assert.equal(app.elements.get('#deepHostInput').disabled, false);
  assert.equal(app.elements.get('#recentDeviceSelect').disabled, false);
  assert.equal(app.elements.get('#scanLaunchButton').disabled, false);
  assert.match(app.elements.get('#scanError').textContent, /could not be found/);
  assert.doesNotMatch(app.elements.get('#scan-config').textContent, /Ready|in progress|Reconnecting/);
  assert.equal(app.elements.get('.scan-home-main').inserted, undefined);
  assert.equal(app.elements.get('#scanProgress').scrolls || 0, 0);
});

test('home markup puts progress after setup and before errors', () => {
  const page = readFileSync(new URL('../app/templates/dashboard.html', import.meta.url), 'utf8');
  const setupIndex = page.indexOf('class="scan-landing"');
  const progressIndex = page.indexOf('id="scanProgress"');
  const errorIndex = page.indexOf('id="scanError"');
  assert.ok(setupIndex >= 0 && setupIndex < progressIndex && progressIndex < errorIndex);
});

test('starting Light or Deep keeps progress below setup without an automatic scroll', async () => {
  for (const pathname of ['/light', '/deep', '/']) {
    let submissions = 0;
    const profile = pathname === '/deep' ? 'deep-tcp-v1' : 'light';
    const app = setup(async (path, options) => {
      if (path === '/api/status') return ready;
      if (path === '/api/live-scans') {
        submissions++;
        const payload = JSON.parse(options.body);
        assert.equal(payload.profile, profile);
        return { scan_id: scanId };
      }
      if (path === `/api/scans/${scanId}`) return { policy: { profile }, target: { hosts: ['192.168.0.216'] } };
      return { state: 'running', phase: 'service_scan' };
    }, null, '', pathname);
    await app.load();
    if (profile === 'deep-tcp-v1') app.elements.get('#deepHostInput').value = '192.168.0.216';
    await app.elements.get('#scanLaunchButton').events.click();
    assert.equal(submissions, 1);
    assert.equal(app.elements.get('#scanProgress').hidden, false);
    assert.equal(app.elements.get('.scan-home-main').inserted, undefined);
    assert.equal(app.elements.get('#scanProgress').scrolls || 0, 0);
    assert.equal(app.window.location.hash, `#scan=${scanId}`);
    await app.elements.get('#scanLaunchButton').events.click();
    assert.equal(submissions, 1);
  }
});

test('network mismatch rechecks status without submitting a scan, then recovers', async () => {
  const calls = [];
  let warning = 'The saved scan range differs from your current network. Open Settings.';
  const app = setup(async (path) => { calls.push(path); return { ...ready, network_warning: warning }; });
  await app.load();
  assert.equal(app.elements.get('#scanLaunchButton').querySelector('span').textContent, 'Check network again');
  await app.elements.get('#scanLaunchButton').events.click();
  assert.equal(app.elements.get('#scan-config').textContent, warning);
  warning = null;
  await app.elements.get('#scanLaunchButton').events.click();
  assert.equal(app.elements.get('#scanLaunchButton').querySelector('span').textContent, 'Scan');
  assert.deepEqual(calls, ['/api/status', '/api/status', '/api/status']);
});

test('a newly detected network asks permission and cancellation sends no scan request', async () => {
  const calls = [];
  const app = setup(async (path) => { calls.push(path); return { ...ready, scope_source: 'automatic', scope_confirmation_supported: true }; });
  app.window.confirm = message => { assert.match(message, /192\.168\.0\.0\/24/); return false; };
  await app.load();
  await app.elements.get('#scanLaunchButton').events.click();
  assert.deepEqual(calls, ['/api/status']);
});

test('confirmed automatic request is pinned to the shown range', async () => {
  let sent;
  const app = setup(async (path, options) => {
    if (path === '/api/status') return { ...ready, scope_source: 'automatic', scope_confirmation_supported: true };
    if (path === '/api/live-scans') { sent = JSON.parse(options.body); return { scan_id: scanId }; }
    return { state: 'running', phase: 'service_scan' };
  });
  app.window.confirm = () => true;
  await app.load();
  await app.elements.get('#scanLaunchButton').events.click();
  assert.equal(sent.confirmed_scope, ready.allowed_network);
  assert.equal(sent.authorised, true);
});

test('slow Ollama readiness uses bounded reads without submitting a scan', async () => {
  let calls = 0;
  const app = setup(async () => { calls++; return { ...ready, ai_available: false, ai_readiness: { state: 'unresponsive' } }; });
  await app.load();
  for (let i = 0; i < 3; i++) await app.timers[i]();
  assert.equal(app.timers.length, 3);
  assert.equal(calls, 4);
  assert.match(app.elements.get('#scan-config').textContent, /starting or busy/);
  assert.doesNotMatch(app.elements.get('#scan-config').textContent, /not installed/);
});

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
  assert.deepEqual(calls, ['/api/status', `/api/scans/${scanId}`, `/api/live-scans/${scanId}/progress`]);
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
  assert.deepEqual(calls, ['/api/status', `/api/scans/${scanId}`, `/api/live-scans/${scanId}/progress`]);
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
  assert.deepEqual(calls, ['/api/status', `/api/scans/${scanId}`, `/api/live-scans/${scanId}/progress`]);
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
  assert.match(app.elements.get('#scanError').textContent, /Enter the address of one device/);
  assert.equal(app.elements.get('#deepHostInput').attributes['aria-invalid'], 'true');
  assert.equal(app.elements.get('#deepHostInput').focused, true);
  assert.equal(app.elements.get('#deepHostError').hidden, false);
  app.elements.get('#deepHostInput').events.input();
  assert.equal(app.elements.get('#deepHostInput').attributes['aria-invalid'], undefined);
  assert.equal(app.elements.get('#deepHostError').hidden, true);
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
  assert.deepEqual(calls, ['/api/status', `/api/scans/${second}`, `/api/live-scans/${second}/progress`]);
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
