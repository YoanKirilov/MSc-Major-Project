import test from 'node:test';
import assert from 'node:assert/strict';
import { createHistoryFeed, HISTORY_PAGE_SIZE } from '../app/static/js/history-feed.mjs';
import { historyContext, reportIdentity, reportDateLabel } from '../app/static/js/history-context.mjs';
import { recordedUtcDay } from '../app/static/js/presentation.mjs';

const report = index => ({ scan_id: 'report-' + index, storage_status: 'ok', title: 'Report ' + index });

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

test('restored page stays empty until deliberate reveal and loads its original bounded offset', async () => {
  const { feed, calls } = setup();
  feed.reset({ q: 'saved' }, 3);
  assert.equal(calls.length, 0);
  assert.equal(feed.getState().items.length, 0);
  await feed.reveal();
  assert.match(calls[0], /q=saved&offset=48&limit=24/);
  assert.equal(feed.getState().items.length, 1);
  assert.equal(feed.getState().page, 3);
});

test('opening history prepares zero reports without fetching a page or a total', async () => {
  const { feed, calls, updates } = setup();
  feed.reset();
  assert.equal(calls.length, 0);
  assert.equal(feed.getState().items.length, 0);
  assert.equal(feed.getState().pageItems.length, 0);
  assert.equal(feed.getState().phase, 'waiting');
  assert.equal(feed.getState().page, 1);
  assert.equal(feed.getState().total, null);
  assert.equal(updates.at(-1).render, 'replace');
  await new Promise(resolve => setTimeout(resolve, 20));
  assert.equal(calls.length, 0);
});

test('first deliberate demand fetches one bounded page and reveals only one row', async () => {
  const { feed, calls, updates } = setup();
  feed.reset();
  await feed.more();
  const state = feed.getState();
  assert.match(calls[0], /offset=0&limit=24$/);
  assert.equal(calls.length, 1);
  assert.equal(state.items.length, 1);
  assert.equal(state.pageItems.length, 24);
  assert.equal(state.revealedCount, 1);
  assert.equal(state.pageSize, HISTORY_PAGE_SIZE);
  assert.equal(state.pageCount, 3);
  assert.equal(state.hasMoreWithinPage, true);
  assert.equal(updates.at(-1).render, 'replace');
  assert.equal(updates.at(-1).added.length, 1);
});

test('each later demand reveals one cached row without additional API calls, capped at 24', async () => {
  const { feed, updates, calls } = setup();
  feed.reset();
  await feed.more();
  for (let expectedCount = 2; expectedCount <= 24; expectedCount += 1) {
    assert.equal(await feed.more(), true);
    assert.equal(feed.getState().items.length, expectedCount);
    assert.equal(updates.at(-1).render, 'append');
    assert.equal(updates.at(-1).added.length, 1);
    assert.equal(calls.length, 1);
  }
  assert.equal(feed.getState().hasMore, false);
  assert.equal(feed.getState().hasMoreWithinPage, false);
  assert.equal(await feed.more(), false);
  assert.equal(feed.getState().items.length, 24);
  assert.equal(calls.length, 1);
});

test('numbered page navigation uses real offsets and replaces rows with the new first row', async () => {
  const { feed, updates, calls } = setup();
  feed.reset();
  await feed.more();
  await feed.more();
  assert.equal(await feed.goToPage(2), true);
  assert.equal(calls.length, 2);
  assert.match(calls[1], /offset=24&limit=24$/);
  assert.equal(feed.getState().page, 2);
  assert.equal(feed.getState().offset, 24);
  assert.equal(feed.getState().pageEndOffset, 48);
  assert.equal(feed.getState().revealedCount, 1);
  assert.deepEqual(feed.getState().items.map(item => item.scan_id), ['report-24']);
  assert.equal(updates.at(-1).render, 'replace');
});

test('the final partial page cannot reveal beyond its available rows', async () => {
  const { feed, calls } = setup();
  feed.reset();
  await feed.more();
  await feed.goToPage(3);
  for (let count = 2; count <= 13; count += 1) await feed.reveal();
  assert.equal(feed.getState().items.length, 13);
  assert.equal(feed.getState().pageItems.length, 13);
  assert.equal(feed.getState().pageEndOffset, 61);
  assert.equal(feed.getState().hasMore, false);
  assert.equal(await feed.reveal(), false);
  assert.equal(calls.length, 2);
});

test('invalid, current and out-of-range page numbers do not fetch or change visible rows', async () => {
  const { feed, calls } = setup();
  feed.reset();
  await feed.more();
  for (const number of [0, -1, 1, 4, 1.5, Infinity, Number.MAX_SAFE_INTEGER, '2']) {
    assert.equal(await feed.goToPage(number), false);
  }
  assert.equal(calls.length, 1);
  assert.equal(feed.getState().page, 1);
  assert.equal(feed.getState().items.length, 1);
});

test('submitted filters are copied and reused by page navigation rather than unsubmitted input', async () => {
  const input = { q: ' Kitchen TV ', state: 'completed', ignored: 'never send' };
  const { feed, calls } = setup();
  feed.reset(input);
  input.q = 'Unsubmitted change';
  assert.equal(calls.length, 0);
  await feed.more();
  await feed.more();
  await feed.goToPage(2);
  for (const path of calls) {
    const params = new URL(path, 'http://localhost').searchParams;
    assert.equal(params.get('q'), 'Kitchen TV');
    assert.equal(params.get('state'), 'completed');
    assert.equal(params.has('ignored'), false);
    assert.equal(params.get('limit'), '24');
  }
});

test('filter reset clears both visible reports and cached reports without fetching', async () => {
  const { feed, calls } = setup();
  feed.reset();
  await feed.more();
  feed.reset({ q: 'new' });
  assert.equal(feed.getState().items.length, 0);
  assert.equal(feed.getState().pageItems.length, 0);
  assert.equal(feed.getState().phase, 'waiting');
  assert.equal(feed.getState().offset, 0);
  assert.equal(feed.getState().pageCount, 0);
  assert.equal(calls.length, 1);
  await new Promise(resolve => setTimeout(resolve, 20));
  assert.equal(calls.length, 1);
});

test('a filter reset ignores a late old page without repopulating the empty list', async () => {
  const pending = deferred();
  const { feed } = setup(path => path.includes('q=new') ? page(90, 1, 1) : pending.promise);
  feed.reset();
  const load = feed.more();
  feed.reset({ q: 'new' });
  pending.resolve(page(0));
  assert.equal(await load, false);
  assert.equal(feed.getState().items.length, 0);
  assert.equal(feed.getState().phase, 'waiting');
  await feed.more();
  assert.deepEqual(feed.getState().items.map(item => item.scan_id), ['report-90']);
});

test('a late failure cannot replace a newer filter page or its cached reports', async () => {
  const pending = deferred();
  const { feed } = setup(path => path.includes('q=first') ? pending.promise : Promise.resolve(page(20, 1, 1)));
  feed.reset({ q: 'first' });
  const old = feed.more();
  feed.reset({ q: 'second' });
  await feed.more();
  pending.reject(new Error('Old failure'));
  assert.equal(await old, false);
  assert.equal(feed.getState().error, '');
  assert.equal(feed.getState().filters.q, 'second');
  assert.deepEqual(feed.getState().pageItems.map(item => item.scan_id), ['report-20']);
});

test('a failed first reveal is explicitly retried and never starts an automatic request loop', async () => {
  let fail = true;
  const { feed, calls } = setup(() => {
    if (fail) throw new Error('Cannot load saved reports');
    return page(0);
  });
  feed.reset({ q: 'submitted' });
  await feed.more();
  assert.equal(feed.getState().items.length, 0);
  assert.equal(feed.getState().phase, 'error');
  assert.equal(await feed.more(), false);
  assert.equal(calls.length, 1);
  fail = false;
  await feed.retry();
  assert.equal(calls[0], calls[1]);
  assert.equal(feed.getState().items.length, 1);
});

test('a page-switch failure keeps the old page available and retries the requested offset', async () => {
  let fail = true;
  const { feed, calls } = setup(path => {
    if (path.includes('offset=24')) {
      if (fail) throw new Error('Temporary local failure');
      return page(24);
    }
    return page(0);
  });
  feed.reset();
  await feed.more();
  await feed.more();
  assert.equal(await feed.goToPage(2), false);
  assert.equal(feed.getState().items.length, 2);
  assert.equal(feed.getState().page, 1);
  assert.equal(feed.getState().retryMode, 'page');
  assert.equal(await feed.more(), false);
  fail = false;
  await feed.retry();
  assert.equal(calls[1], calls[2]);
  assert.equal(feed.getState().page, 2);
  assert.deepEqual(feed.getState().items.map(item => item.scan_id), ['report-24']);
  assert.equal(feed.getState().error, '');
});

test('overlapping reveals and page-navigation demands share one in-flight request', async () => {
  const pending = deferred();
  const { feed, calls } = setup(() => pending.promise);
  feed.reset();
  const first = feed.more();
  assert.equal(await feed.more(), false);
  assert.equal(await feed.goToPage(2), false);
  assert.equal(calls.length, 1);
  pending.resolve(page(0));
  await first;
});

test('duplicate rows are deduplicated before caching and warned about without looping', async () => {
  const { feed, calls } = setup(() => page(0, 3, 3, { items: [report(0), report(0), report(1)] }));
  feed.reset();
  await feed.more();
  await feed.more();
  assert.deepEqual(feed.getState().items.map(item => item.scan_id), ['report-0', 'report-1']);
  assert.equal(feed.getState().pageItems.length, 2);
  assert.equal(feed.getState().changed, true);
  assert.match(feed.getState().warnings.join(' '), /changed while you were browsing/);
  assert.equal(await feed.more(), false);
  assert.equal(calls.length, 1);
});

test('an unexpectedly empty page is warned about and cannot auto-repeat the request', async () => {
  const { feed, calls } = setup(() => page(0, 0, 5));
  feed.reset();
  await feed.more();
  assert.equal(feed.getState().items.length, 0);
  assert.equal(feed.getState().hasMore, false);
  assert.equal(feed.getState().changed, true);
  assert.equal(await feed.more(), false);
  assert.equal(calls.length, 1);
});

test('an unexpectedly short page is warned about rather than silently skipping missing rows', async () => {
  const { feed, calls } = setup(() => page(0, 5, 61));
  feed.reset();
  await feed.more();
  for (let count = 2; count <= 5; count += 1) await feed.more();
  assert.equal(feed.getState().items.length, 5);
  assert.equal(feed.getState().changed, true);
  assert.match(feed.getState().warnings.join(' '), /changed while you were browsing/);
  assert.equal(await feed.more(), false);
  assert.equal(calls.length, 1);
});

test('a total change on a page switch is explicitly noted', async () => {
  let total = 61;
  const { feed } = setup(path => page(Number(new URL(path, 'http://localhost').searchParams.get('offset')), 24, total));
  feed.reset();
  await feed.more();
  total = 62;
  await feed.goToPage(2);
  assert.equal(feed.getState().total, 62);
  assert.equal(feed.getState().changed, true);
});

test('empty unreadable history is evaluated only after deliberate demand', async () => {
  const { feed, calls } = setup(() => page(0, 0, 0, { unreadable_count: 2, warnings: ['Files preserved.'] }));
  feed.reset({ profile: 'light' });
  assert.equal(feed.getState().unreadableCount, 0);
  assert.equal(calls.length, 0);
  await feed.more();
  assert.equal(feed.getState().total, 0);
  assert.equal(feed.getState().pageCount, 0);
  assert.equal(feed.getState().page, 1);
  assert.equal(feed.getState().unreadableCount, 2);
  assert.deepEqual(feed.getState().warnings, ['Files preserved.']);
});

test('invalid and oversized page responses are rejected without exposing any row', async () => {
  for (const response of [{ items: [{}], total: 1 }, page(0, 25), page(0, 1, -1),
    page(0, 1, 0), page(0, 1, 1, { warnings: 'invalid' }),
    { items: [], total: '1' }, { items: [], total: Number.MAX_SAFE_INTEGER + 1 }]) {
    const { feed } = setup(() => response);
    feed.reset();
    assert.equal(await feed.more(), false);
    assert.equal(feed.getState().items.length, 0);
    assert.equal(feed.getState().phase, 'error');
    assert.match(feed.getState().error, /could not be read/);
  }
});

test('history page size is fixed at 24, never an unbounded list', () => {
  assert.equal(HISTORY_PAGE_SIZE, 24);
  for (const pageSize of [0, 1, 8, 25, 51, 1.5]) {
    assert.throws(() => createHistoryFeed({ request() {}, onChange() {}, pageSize }), TypeError);
  }
});

test('state snapshots cannot mutate cached lists, revealed lists, filters or warning arrays', async () => {
  const { feed } = setup();
  feed.reset({ q: 'test' });
  await feed.more();
  const state = feed.getState();
  state.pageItems.length = 0;
  state.items.length = 0;
  state.filters.q = 'different';
  state.warnings.push('not real');
  assert.equal(feed.getState().pageItems.length, 24);
  assert.equal(feed.getState().items.length, 1);
  assert.equal(feed.getState().filters.q, 'test');
  assert.deepEqual(feed.getState().warnings, []);
});

test('deletion refresh reloads the visible page without reintroducing removed reports', async () => {
  let records = [report(0), report(1), report(2), report(3)];
  const { feed, calls } = setup(() => ({ items: records, total: records.length }));
  feed.reset({ profile: 'light' });
  await feed.more();
  await feed.more();
  records = records.filter(item => item.scan_id !== 'report-0');
  await feed.reloadAfterDelete();
  assert.equal(calls.length, 2);
  assert.deepEqual(feed.getState().items.map(item => item.scan_id), ['report-1', 'report-2']);
  assert.equal(feed.getState().total, 3);
  assert.equal(feed.getState().revealedCount, 2);
  assert.equal(feed.getState().filters.profile, 'light');
  assert.equal(feed.getState().changed, false);
});

test('deleting the only report on the last page returns to the last remaining valid page', async () => {
  let total = 25;
  const { feed, calls } = setup(path => {
    const offset = Number(new URL(path, 'http://localhost').searchParams.get('offset'));
    return page(offset, Math.max(0, Math.min(24, total - offset)), total);
  });
  feed.reset();
  await feed.more();
  await feed.goToPage(2);
  total = 24;
  await feed.reloadAfterDelete();
  assert.equal(feed.getState().page, 1);
  assert.equal(feed.getState().pageCount, 1);
  assert.equal(feed.getState().total, 24);
  assert.deepEqual(feed.getState().items.map(item => item.scan_id), ['report-0']);
  assert.match(calls[2], /offset=24&limit=24$/);
  assert.match(calls[3], /offset=0&limit=24$/);
});

test('deleting all matching reports clears cache and rows and returns to page one', async () => {
  let total = 25;
  const { feed, calls } = setup(path => {
    const offset = Number(new URL(path, 'http://localhost').searchParams.get('offset'));
    return page(offset, Math.max(0, Math.min(24, total - offset)), total);
  });
  feed.reset();
  await feed.more();
  await feed.goToPage(2);
  total = 0;
  await feed.reloadAfterDelete();
  assert.equal(feed.getState().page, 1);
  assert.equal(feed.getState().pageCount, 0);
  assert.equal(feed.getState().items.length, 0);
  assert.equal(feed.getState().pageItems.length, 0);
  assert.equal(feed.getState().hasMore, false);
  assert.equal(calls.length, 3);
});

test('deletion refresh cancels a stale in-flight page request', async () => {
  const pending = deferred();
  let requests = 0;
  const { feed } = setup(() => ++requests === 2 ? pending.promise : page(0, 2, 2));
  feed.reset();
  await feed.more();
  const stale = feed.goToPage(1);
  assert.equal(await stale, false);
  const refresh = feed.reloadAfterDelete();
  const newer = feed.reloadAfterDelete();
  pending.resolve(page(100, 1, 1));
  assert.equal(await refresh, false);
  assert.equal(await newer, true);
  assert.deepEqual(feed.getState().items.map(item => item.scan_id), ['report-0']);
});

test('deletion refresh does not defeat the initial no-report/no-fetch view', async () => {
  const { feed, calls } = setup();
  feed.reset();
  assert.equal(await feed.reloadAfterDelete(), false);
  assert.equal(calls.length, 0);
  assert.equal(feed.getState().items.length, 0);
});

test('shrinking totals correct an out-of-range page once, with no unbounded retry loop', async () => {
  const { feed, calls } = setup(path => {
    const offset = Number(new URL(path, 'http://localhost').searchParams.get('offset'));
    if (calls.length === 1) return page(offset);
    return calls.length === 2 ? page(48, 0, 25) : page(24, 0, 1);
  });
  feed.reset();
  await feed.more();
  assert.equal(await feed.goToPage(3), false);
  assert.equal(calls.length, 3);
  assert.equal(feed.getState().phase, 'error');
  assert.match(feed.getState().error, /changed again/);
  assert.equal(feed.getState().page, 1);
  assert.equal(feed.getState().items.length, 1);
  assert.equal(await feed.more(), false);
});
