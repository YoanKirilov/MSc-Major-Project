import test from 'node:test';
import assert from 'node:assert/strict';
import { createHistoryFeed, HISTORY_PAGE_SIZE } from '../app/static/js/history-feed.mjs';
import { historyContext, reportIdentity, reportDateLabel } from '../app/static/js/history-context.mjs';
import { recordedUtcDay } from '../app/static/js/presentation.mjs';
import { reportViewport } from '../app/static/js/history-viewport.mjs';

const report = index => ({ scan_id: 'report-' + index, storage_status: 'ok', title: 'Report ' + index });

function viewportSetup(mode = 'normal') {
  const watched = new Set(), callbacks = {}, classes = new Set();
  let callback, disconnected = 0;
  const row = { contains: value => value === 'focused', classList: { add: name => classes.add(name), remove: name => classes.delete(name) } };
  const list = { children: [row], ownerDocument: {activeElement: null}, addEventListener: (name, fn) => { callbacks[name] = fn; } };
  const window = { addEventListener: (name, fn) => { callbacks[name] = fn; } };
  if (mode !== 'absent') window.IntersectionObserver = class {
    constructor(fn) { if (mode === 'throws') throw Error('Unavailable'); callback = fn; }
    observe(row) { watched.add(row); }
    unobserve(row) { watched.delete(row); }
    disconnect() { disconnected += 1; watched.clear(); }
  };
  const viewport = reportViewport({window,list});
  return { viewport,row,list,classes,watched,callbacks,emit: value => callback([{target:row,isIntersecting:value}]), disconnected: () => disconnected };
}
test('viewport observation adds one optional effect, never hides or removes a row', () => {
  const app = viewportSetup(); app.viewport.update();
  assert.equal(app.list.children.length,1); assert.equal(app.classes.size,0);
  app.emit(false); assert.equal(app.classes.size,0);
  app.emit(true); assert.equal(app.classes.has('history-reveal'),true); assert.equal(app.watched.size,0);
  app.viewport.update(); assert.equal(app.watched.size,0);
  app.callbacks.pagehide(); assert.ok(app.disconnected() > 0);
});
test('observer absence and constructor failure leave the complete ordinary list available', () => {
  for (const mode of ['absent','throws']) {
    const app = viewportSetup(mode); app.viewport.update();
    assert.equal(app.list.children.length,1); assert.equal(app.classes.size,0);
  }
});
test('keyboard focus cancels entry movement immediately, including before an observer callback', () => {
  const app = viewportSetup(); app.viewport.update();
  app.callbacks.focusin({target:{closest:()=>app.row}});
  app.emit(true); assert.equal(app.classes.size,0); assert.equal(app.watched.size,0);
  const focused = viewportSetup(); focused.list.ownerDocument.activeElement = 'focused'; focused.viewport.update(); focused.emit(true);
  assert.equal(focused.classes.size,0);
});

test('same-title same-time reports have distinct identities with type, date, target and reference', () => {
  const first = { scan_id: '00000000-0000-4000-8000-000000000001', title: 'Repeated title', profile: 'light', created_at: '2026-10-13T23:25:14Z', target: { cidr: '192.168.56.0/24' } };
  const second = { ...first, scan_id: '00000000-0000-4000-8000-000000000002' };
  assert.notEqual(reportIdentity(first), reportIdentity(second));
  assert.match(reportIdentity(first), /Repeated title.*Light.*192.168.56.0\/24.*00000001/);
  assert.match(reportDateLabel(first), /filter date 2026-10-13 UTC/);
});

test('UTC filter days stay correct at midnight and London DST boundaries without guessing legacy zones', () => {
  for (const [value, day] of [['2026-10-14T00:25:14+01:00', '2026-10-13'], ['2026-03-29T02:01:00+01:00', '2026-03-29'], ['2026-10-25T01:59:00+01:00', '2026-10-25'], ['2026-10-25T01:01:00Z', '2026-10-25'], ['2026-10-13T20:30:00-05:00', '2026-10-14']]) assert.equal(recordedUtcDay(value), day);
  for (const value of ['2026-10-14T01:00:00', '2026-02-30T01:00:00Z', '', null]) assert.equal(recordedUtcDay(value), '');
});

test('per-tab History context allowlists fields, expires, and tolerates blocked/malformed storage', () => {
  const values = new Map();
  const storage = { getItem: key => values.get(key), setItem: (key, value) => values.set(key, value) };
  const context = historyContext(storage);
  assert.equal(context.save({ q: 'Private nickname', profile: 'light', token: 'secret' }, 3), true);
  assert.deepEqual(context.read(), { filters: { q: 'Private nickname', profile: 'light' }, page: 3 });
  assert.doesNotMatch(values.get('netguard-history-context-v1'), /secret|token/);
  assert.equal(historyContext(storage, Date.now() + 86400001).read(), null);
  assert.equal(historyContext(null).save({}, 1), false);
  assert.equal(historyContext(null).read(), null);
  storage.setItem('netguard-history-context-v1', '{broken');
  assert.equal(context.read(), null);
  assert.equal(context.save({}, 0), false);
});

const page = (start, count = 24, total = 61, extra = {}) => ({
  items: Array.from({ length: count }, (_, i) => report(start + i)), total, ...extra,
});
function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
function setup(request = path => {
  const offset = Number(new URL(path, 'http://localhost').searchParams.get('offset'));
  return page(offset, Math.min(24, 61 - offset));
}) {
  const calls = [], updates = [];
  const feed = createHistoryFeed({
    request: path => { calls.push(path); return request(path); },
    onChange: state => updates.push(state),
  });
  return { feed, calls, updates };
}
test('one request makes the complete current page accessible without another gesture', async () => {
  const { feed, calls } = setup();
  feed.reset();
  await feed.load();
  assert.equal(calls.length, 1);
  assert.match(calls[0], /offset=0&limit=24$/);
  assert.equal(feed.getState().items.length, 24);
  assert.equal(feed.getState().pageCount, 3);
  assert.equal(feed.getState().phase, 'ready');
  assert.equal(await feed.load(), false);
  assert.equal(calls.length, 1);
});
test('explicit numbered pages replace all rows with correct offsets, never append another page', async () => {
  const { feed, calls } = setup();
  feed.reset(); await feed.load();
  await feed.goToPage(2);
  assert.equal(feed.getState().items[0].scan_id, 'report-24');
  assert.equal(feed.getState().items.length, 24);
  await feed.goToPage(3);
  assert.equal(feed.getState().items.length, 13);
  assert.equal(feed.getState().items[0].scan_id, 'report-48');
  assert.deepEqual(calls.map(path => new URL(path, 'http://localhost').searchParams.get('offset')), ['0','24','48']);
});
test('invalid, current, overlapping and out-of-range page requests do not fetch', async () => {
  const { feed, calls } = setup();
  feed.reset(); await feed.load();
  for (const n of [0,-1,1.5,'2',Infinity,Number.MAX_SAFE_INTEGER,4,1]) assert.equal(await feed.goToPage(n), false);
  assert.equal(calls.length, 1);
});
test('all submitted filters persist across pages, not unsubmitted mutations', async () => {
  const { feed, calls } = setup();
  const filters = { q:'living room', profile:'light', state:'completed', after:'2026-10-01' };
  feed.reset(filters); filters.q = 'other';
  await feed.load(); await feed.goToPage(2);
  const query = new URL(calls[1], 'http://localhost').searchParams;
  assert.equal(query.get('q'), 'living room');
  assert.equal(query.get('offset'), '24');
  assert.equal(query.get('after'), '2026-10-01');
});
test('saved page resumes as a complete bounded page and corrects a disappeared last page', async () => {
  const { feed, calls } = setup();
  feed.reset({ profile:'light' },3);
  await feed.load();
  assert.equal(feed.getState().items.length,13);
  assert.match(calls[0], /offset=48&limit=24/);
  const shrunk = setup(() => page(0, 1, 1));
  shrunk.feed.reset({},3); await shrunk.feed.load();
  assert.equal(shrunk.feed.getState().page,1);
  assert.equal(shrunk.calls.length,2);
});
test('same generation has at most one in-flight request', async () => {
  const pending = deferred();
  const { feed,calls } = setup(() => pending.promise);
  feed.reset();
  const load = feed.load();
  assert.equal(await feed.load(),false);
  assert.equal(await feed.goToPage(2),false);
  assert.equal(calls.length,1);
  pending.resolve(page(0)); await load;
  assert.equal(feed.getState().items.length,24);
});
test('a late old search result or failure cannot replace the current filter page', async () => {
  for (const fails of [false,true]) {
    const pending = deferred();
    const { feed } = setup(path => path.includes('q=old') ? pending.promise : page(20));
    feed.reset({ q:'old' }); const old = feed.load();
    feed.reset({ q:'new' }); await feed.load();
    if (fails) pending.reject(Error('late outage')); else pending.resolve(page(0));
    await old;
    assert.equal(feed.getState().items[0].scan_id,'report-20');
    assert.equal(feed.getState().error,'');
  }
});
test('a failed page keeps existing rows and retries only on explicit request', async () => {
  let fail = true;
  const { feed,calls } = setup(path => {
    const offset = Number(new URL(path,'http://localhost').searchParams.get('offset'));
    if (offset === 24 && fail) throw Error('Temporary outage');
    return page(offset);
  });
  feed.reset(); await feed.load();
  await feed.goToPage(2);
  assert.equal(feed.getState().items.length,24);
  assert.equal(feed.getState().items[0].scan_id,'report-0');
  assert.equal(feed.getState().phase,'error');
  assert.equal(await feed.load(),false);
  assert.equal(calls.length,2);
  fail = false; await feed.retry();
  assert.equal(feed.getState().items[0].scan_id,'report-24');
});
test('a failed initial request stops instead of automatically looping', async () => {
  const { feed,calls } = setup(() => { throw Error('Unavailable'); });
  feed.reset(); await feed.load(); await feed.load();
  assert.equal(calls.length,1);
  assert.equal(feed.getState().items.length,0);
  assert.match(feed.getState().error,/Unavailable/);
});
test('empty/no-match/unreadable states are finite and keep useful warnings', async () => {
  for (const filters of [{},{ q:'nothing' }]) {
    const { feed,calls } = setup(() => page(0,0,0,{ unreadable_count:1,warnings:['Files preserved.'] }));
    feed.reset(filters); await feed.load();
    assert.equal(feed.getState().items.length,0);
    assert.equal(feed.getState().total,0);
    assert.equal(feed.getState().unreadableCount,1);
    assert.deepEqual(feed.getState().warnings,['Files preserved.']);
    await feed.load(); assert.equal(calls.length,1);
  }
});
test('duplicate and short page results are bounded, warned about and not silently chased', async () => {
  const result = page(0); result.items[1] = result.items[0];
  const { feed,calls } = setup(() => result);
  feed.reset(); await feed.load();
  assert.equal(feed.getState().items.length,23);
  assert.equal(feed.getState().changed,true);
  assert.ok(feed.getState().warnings.length);
  assert.equal(calls.length,1);
});
test('invalid and oversized responses cannot partially expose a page', async () => {
  for (const result of [null,{},page(0,25),page(0,24,-1),{items:[null],total:1},{items:[{scan_id:''}],total:1}]) {
    const { feed } = setup(() => result);
    feed.reset(); await feed.load();
    assert.equal(feed.getState().phase,'error');
    assert.equal(feed.getState().items.length,0);
  }
  assert.throws(() => createHistoryFeed({ pageSize:25 }),/at most 24/);
});
test('deletion refresh replaces the complete page and corrects a removed final page', async () => {
  let total = 25;
  const { feed,calls } = setup(path => {
    const offset = Number(new URL(path,'http://localhost').searchParams.get('offset'));
    return page(offset, Math.max(0, Math.min(24,total-offset)),total);
  });
  feed.reset(); await feed.load(); await feed.goToPage(2);
  total = 24; await feed.reloadAfterDelete();
  assert.equal(feed.getState().page,1);
  assert.equal(feed.getState().items.length,24);
  assert.equal(calls.length,4);
  total = 0; await feed.reloadAfterDelete();
  assert.equal(feed.getState().items.length,0);
  assert.equal(feed.getState().page,1);
});
test('library correction is bounded to one retry even when results keep shrinking', async () => {
  let requests = 0;
  const { feed } = setup(() => page(0,0,requests++ === 0 ? 30 : 1));
  feed.reset({},3); await feed.load();
  assert.equal(requests,2);
  assert.equal(feed.getState().phase,'error');
});
test('deletion refresh fences stale in-flight results', async () => {
  const pending = deferred(); let count = 0;
  const { feed } = setup(() => ++count === 1 ? pending.promise : page(10));
  feed.reset(); const old = feed.load();
  await feed.reloadAfterDelete();
  pending.resolve(page(0)); await old;
  assert.equal(feed.getState().items[0].scan_id,'report-10');
});
test('state copies cannot mutate data, warnings or submitted filters', async () => {
  const { feed } = setup();
  feed.reset({q:'saved'}); await feed.load();
  const state = feed.getState();
  state.items.pop(); state.pageItems.pop(); state.warnings.push('extra'); state.filters.q = 'changed';
  assert.equal(feed.getState().items.length,24);
  assert.equal(feed.getState().pageItems.length,24);
  assert.equal(feed.getState().filters.q,'saved');
  assert.deepEqual(feed.getState().warnings,[]);
});
