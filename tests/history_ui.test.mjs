import test from 'node:test';
import assert from 'node:assert/strict';
import { createHistoryFeed } from '../app/static/js/history-feed.mjs';

const report = index => ({ scan_id: `report-${index}`, storage_status: 'ok', title: `Report ${index}` });
const page = (start, count = 1, total = 3, extra = {}) => ({ items: Array.from({ length: count }, (_, i) => report(start + i)), total, ...extra });
function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
function setup(request) {
  const calls = [], updates = [];
  const feed = createHistoryFeed({ request: path => { calls.push(path); return request(path); }, onChange: state => updates.push(state) });
  return { feed, calls, updates };
}

test('opening history prepares an empty list without fetching any report', async () => {
  const { feed, calls, updates } = setup(async () => page(0));
  feed.reset();
  assert.equal(calls.length, 0);
  assert.equal(feed.getState().items.length, 0);
  assert.equal(feed.getState().phase, 'waiting');
  assert.equal(feed.getState().total, null);
  assert.equal(updates.at(-1).render, 'replace');
  await new Promise(resolve => setTimeout(resolve, 20));
  assert.equal(calls.length, 0);
});

test('each explicit demand appends exactly one report and never chains another request', async () => {
  const { feed, updates, calls } = setup(async path => {
    const offset = Number(new URL(path, 'http://localhost').searchParams.get('offset'));
    return page(offset);
  });
  feed.reset();
  for (const expectedCount of [1, 2, 3]) {
    await feed.more();
    assert.equal(feed.getState().items.length, expectedCount);
    assert.equal(updates.at(-1).render, 'append');
    assert.equal(updates.at(-1).added.length, 1);
    assert.equal(calls.length, expectedCount);
    assert.match(calls.at(-1), /limit=1$/);
  }
  assert.equal(feed.getState().hasMore, false);
  assert.equal(await feed.more(), false);
  assert.equal(calls.length, 3);
});

test('append failures keep the revealed report and retry the same offset', async () => {
  let fail = true;
  const { feed, calls } = setup(async path => {
    if (path.includes('offset=1')) {
      if (fail) throw new Error('Temporary local failure');
      return page(1);
    }
    return page(0);
  });
  feed.reset();
  await feed.more();
  assert.equal(await feed.more(), false);
  assert.equal(feed.getState().items.length, 1);
  assert.equal(feed.getState().offset, 1);
  assert.equal(feed.getState().retryMode, 'append');
  assert.equal(await feed.more(), false);
  fail = false;
  await feed.retry();
  assert.equal(calls[1], calls[2]);
  assert.equal(feed.getState().items.length, 2);
  assert.equal(feed.getState().error, '');
});

test('submitted filters are copied and later one-report requests use the snapshot', async () => {
  const input = { q: ' Kitchen TV ', state: 'completed', ignored: 'never send' };
  const { feed, calls } = setup(async path => page(Number(new URL(path, 'http://localhost').searchParams.get('offset'))));
  feed.reset(input);
  input.q = 'Unsubmitted change';
  assert.equal(calls.length, 0);
  await feed.more();
  await feed.more();
  for (const path of calls) {
    const params = new URL(path, 'http://localhost').searchParams;
    assert.equal(params.get('q'), 'Kitchen TV');
    assert.equal(params.get('state'), 'completed');
    assert.equal(params.has('ignored'), false);
    assert.equal(params.get('limit'), '1');
  }
});

test('a filter reset immediately clears visible reports and waits for fresh demand', async () => {
  const { feed, calls } = setup(async () => page(0));
  feed.reset();
  await feed.more();
  feed.reset({ q: 'new' });
  assert.equal(feed.getState().items.length, 0);
  assert.equal(feed.getState().phase, 'waiting');
  assert.equal(feed.getState().offset, 0);
  assert.equal(calls.length, 1);
  await new Promise(resolve => setTimeout(resolve, 20));
  assert.equal(calls.length, 1);
});

test('a filter reset ignores a late old request and cannot repopulate the empty list', async () => {
  const pending = deferred();
  const { feed } = setup(async path => path.includes('q=new') ? page(90, 1, 1) : pending.promise);
  feed.reset();
  const append = feed.more();
  feed.reset({ q: 'new' });
  pending.resolve(page(0));
  assert.equal(await append, false);
  assert.equal(feed.getState().items.length, 0);
  assert.equal(feed.getState().phase, 'waiting');
  await feed.more();
  assert.deepEqual(feed.getState().items.map(item => item.scan_id), ['report-90']);
});

test('a late failed request cannot replace a newer filter state or result', async () => {
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
});

test('a failed first reveal is explicit to retry and does not restart automatically', async () => {
  let fail = true;
  const { feed, calls } = setup(async () => {
    if (fail) throw new Error('Cannot load saved report');
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

test('overlapping demands are bounded to one in-flight request', async () => {
  const pending = deferred();
  const { feed, calls } = setup(() => pending.promise);
  feed.reset();
  const first = feed.more();
  assert.equal(await feed.more(), false);
  assert.equal(calls.length, 1);
  pending.resolve(page(0));
  await first;
});

test('changing history is deduplicated and raw offsets stay monotonic', async () => {
  const { feed, calls } = setup(async path => path.includes('offset=1') ? page(0, 1, 4) : page(0));
  feed.reset();
  await feed.more();
  await feed.more();
  assert.equal(feed.getState().items.length, 1);
  assert.equal(feed.getState().offset, 2);
  assert.equal(feed.getState().changed, true);
  assert.match(feed.getState().warnings.join(' '), /changed while you were browsing/);
  assert.match(calls[1], /offset=1/);
});

test('an unexpectedly empty page cannot trigger an automatic retry loop', async () => {
  const { feed } = setup(async path => path.includes('offset=1') ? page(1, 0) : page(0));
  feed.reset();
  await feed.more();
  await feed.more();
  assert.equal(feed.getState().items.length, 1);
  assert.equal(feed.getState().hasMore, false);
  assert.equal(feed.getState().changed, true);
});

test('empty unreadable history is evaluated only after deliberate demand', async () => {
  const { feed, calls } = setup(async () => page(0, 0, 0, { unreadable_count: 2, warnings: ['Files preserved.'] }));
  feed.reset({ profile: 'light' });
  assert.equal(feed.getState().unreadableCount, 0);
  assert.equal(calls.length, 0);
  await feed.more();
  assert.equal(feed.getState().total, 0);
  assert.equal(feed.getState().unreadableCount, 2);
  assert.deepEqual(feed.getState().warnings, ['Files preserved.']);
});

test('invalid and multi-report responses are rejected without altering revealed data', async () => {
  for (const response of [{ items: [{}], total: 1 }, page(0, 2)]) {
    const { feed } = setup(async () => response);
    feed.reset();
    assert.equal(await feed.more(), false);
    assert.equal(feed.getState().items.length, 0);
    assert.equal(feed.getState().phase, 'error');
    assert.match(feed.getState().error, /could not be read/);
  }
});

test('history cannot be configured to reveal more than one report at a time', () => {
  for (const limit of [0, 2, 8, 51, 1.5]) assert.throws(() => createHistoryFeed({ request() {}, onChange() {}, limit }), TypeError);
});
