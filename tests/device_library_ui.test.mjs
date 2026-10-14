import test from 'node:test';
import assert from 'node:assert/strict';
import { createDeviceLibrary, validateDevicePage, validDeviceLabels } from '../app/static/js/device-library-model.mjs';

const key = index => `d-${index.toString(16).padStart(64, '0')}`;
const labels = (room = '', favourite = false, recognised = false) => ({ room, favourite, recognised });
const device = (index = 1, extra = {}) => ({
  device_key: key(index), display_name: `Recorded device ${index}`, last_ip: `192.168.56.${index}`,
  network: '192.168.56.0/24', first_observed: '2026-10-10T09:00:00Z',
  last_observed: '2026-10-14T09:00:00Z', report_count: 1, review_count: 2, unfinished_count: 0,
  reports: [{ scan_id: '00000000-0000-4000-8000-000000000001', device_id: 'recorded-device',
    created_at: '2026-10-14T09:00:00Z', state: 'completed' }],
  annotations: labels(), editable: true, ...extra,
});
const page = (items = [device()], extra = {}) => ({ items, total: items.length, offset: 0,
  limit: 24, revision: 1, warnings: [], ...extra });
function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
function setup(responder = () => page()) {
  const calls = [], updates = [];
  const library = createDeviceLibrary({ request: (path, options = {}) => {
    calls.push({ path, options }); return responder(path, options);
  }, onChange: update => updates.push(update) });
  return { library, calls, updates };
}

test('a complete bounded 24-device page loads once without scroll-driven paging', async () => {
  const app = setup(() => page(Array.from({ length: 24 }, (_, i) => device(i + 1)), { total: 50 }));
  assert.equal(await app.library.load(), true);
  assert.equal(app.library.getState().items.length, 24);
  assert.equal(app.calls.length, 1);
  const url = new URL(app.calls[0].path, 'http://localhost');
  assert.equal(url.searchParams.get('limit'), '24');
  assert.equal(url.searchParams.get('offset'), '0');
});

test('search and explicit numbered pages address the whole server collection', async () => {
  const app = setup(path => {
    const offset = Number(new URL(path, 'http://localhost').searchParams.get('offset'));
    return page([device(offset + 1)], { total: 70, offset });
  });
  await app.library.load('  Living room  ', 3);
  const url = new URL(app.calls[0].path, 'http://localhost');
  assert.equal(url.searchParams.get('search'), 'Living room');
  assert.equal(url.searchParams.get('offset'), '48');
  assert.equal(app.library.getState().offset, 48);
  assert.equal(await app.library.load('x'.repeat(121)), false);
  assert.equal(await app.library.load('', 0), false);
  assert.equal(app.calls.length, 1);
});

test('the latest submitted load wins over delayed earlier page responses', async () => {
  const earlier = deferred(), latest = deferred();
  const app = setup(path => path.includes('search=latest') ? latest.promise : earlier.promise);
  const oldLoad = app.library.load('earlier');
  const newLoad = app.library.load('latest');
  latest.resolve(page([device(2)]));
  assert.equal(await newLoad, true);
  earlier.resolve(page([device(1)]));
  assert.equal(await oldLoad, false);
  assert.equal(app.library.getState().search, 'latest');
  assert.equal(app.library.getState().items[0].device_key, key(2));
});

test('an unavailable page retains displayed evidence and unsaved household input', async () => {
  let fail = false;
  const app = setup(() => { if (fail) throw new Error('Synthetic outage'); return page(); });
  await app.library.load();
  app.library.change(key(1), labels('Kitchen', true));
  fail = true;
  assert.equal(await app.library.load('other'), false);
  assert.equal(app.library.getState().items[0].draft.room, 'Kitchen');
  assert.equal(app.library.getState().items[0].last_ip, '192.168.56.1');
  assert.equal(app.library.getState().draftCount, 1);
  assert.match(app.library.getState().error, /Synthetic outage/);
});

test('drafts survive page changes and explicit reload reveals latest labels without replacing the draft', async () => {
  let revision = 1;
  const app = setup(path => {
    const offset = Number(new URL(path, 'http://localhost').searchParams.get('offset'));
    return page([device(offset ? 25 : 1, { annotations: labels(revision === 1 ? '' : 'Saved elsewhere') })], { total: 25, offset, revision });
  });
  await app.library.load();
  app.library.change(key(1), labels('My draft', true, true));
  await app.library.load('', 2);
  assert.equal(app.library.getState().draftCount, 1);
  revision = 2;
  await app.library.load('', 1);
  assert.equal(app.library.getState().items[0].annotations.room, 'Saved elsewhere');
  assert.equal(app.library.getState().items[0].draft.room, 'My draft');
  assert.equal(app.library.getState().revision, 2);
});

test('save carries only household annotations and the global revision; recorded facts remain unchanged', async () => {
  const app = setup((path, options) => options.method === 'PUT'
    ? { device_key: key(1), annotations: labels('Kitchen', true, true), revision: 2, editable: true } : page());
  await app.library.load();
  app.library.change(key(1), labels(' Kitchen ', true, true));
  assert.equal(await app.library.save(key(1)), true);
  assert.deepEqual(JSON.parse(app.calls[1].options.body), {
    expected_revision: 1, room: 'Kitchen', favourite: true, recognised: true,
  });
  assert.equal(app.calls[1].path, `/api/devices/${key(1)}`);
  assert.equal(app.library.getState().items[0].last_ip, '192.168.56.1');
  assert.equal(app.library.getState().items[0].annotations.room, 'Kitchen');
  assert.equal(app.library.getState().draftCount, 0);
});

test('a conflict retains the draft and requires explicit reload before any further write', async () => {
  let revision = 1, writes = 0;
  const app = setup((path, options) => {
    if (options.method === 'PUT') { writes += 1; throw Object.assign(new Error('Saved labels changed'), { status: 409 }); }
    return page([device()], { revision });
  });
  await app.library.load();
  app.library.change(key(1), labels('Study'));
  assert.equal(await app.library.save(key(1)), false);
  assert.equal(app.library.getState().items[0].draft.room, 'Study');
  assert.equal(app.library.getState().needsReload, true);
  assert.equal(await app.library.save(key(1)), false);
  assert.equal(writes, 1);
  revision = 2;
  await app.library.load();
  assert.equal(app.library.getState().needsReload, false);
  assert.equal(app.library.getState().items[0].draft.room, 'Study');
});

test('uncertain save outcomes never replay writes, and explicit reload reconciles acknowledged labels', async () => {
  let written = false, writes = 0;
  const app = setup((path, options) => {
    if (options.method === 'PUT') { writes += 1; written = true; throw new Error('Response lost'); }
    return page([device(1, { annotations: labels(written ? 'Study' : '') })], { revision: written ? 2 : 1 });
  });
  await app.library.load(); app.library.change(key(1), labels('Study'));
  await app.library.save(key(1));
  assert.equal(await app.library.save(key(1)), false);
  assert.equal(writes, 1);
  await app.library.load();
  assert.equal(app.library.getState().draftCount, 0);
  assert.equal(writes, 1);
});

test('writes are serialized across devices against one global revision', async () => {
  const pending = deferred();
  const app = setup((path, options) => options.method === 'PUT' ? pending.promise : page([device(1), device(2)]));
  await app.library.load();
  app.library.change(key(1), labels('One')); app.library.change(key(2), labels('Two'));
  const firstSave = app.library.save(key(1));
  assert.equal(await app.library.save(key(2)), false);
  assert.equal(await app.library.load(), false);
  pending.resolve({ device_key: key(1), annotations: labels('One'), revision: 2, editable: true });
  assert.equal(await firstSave, true);
  assert.equal(app.calls.filter(call => call.options.method === 'PUT').length, 1);
  assert.equal(app.library.getState().items[1].draft.room, 'Two');
});

test('malformed save receipts preserve the draft and block another write pending reload', async () => {
  const app = setup((path, options) => options.method === 'PUT'
    ? { device_key: key(2), annotations: labels('Unexpected'), revision: 2, editable: true } : page());
  await app.library.load(); app.library.change(key(1), labels('Kitchen'));
  assert.equal(await app.library.save(key(1)), false);
  assert.equal(app.library.getState().items[0].annotations.room, '');
  assert.equal(app.library.getState().items[0].draft.room, 'Kitchen');
  assert.equal(app.library.getState().needsReload, true);
});

test('unreadable household metadata leaves observations readable but all label writes unavailable', async () => {
  const app = setup(() => page([device(1, { editable: false })], { revision: null, warnings: ['Household labels unavailable'] }));
  assert.equal(await app.library.load(), true);
  assert.equal(app.library.change(key(1), labels('Kitchen')), false);
  assert.equal(await app.library.save(key(1)), false);
  assert.equal(app.calls.length, 1);
});

test('ledger-only records retain their qualification and a report reference without a fabricated device identity', async () => {
  const note = 'Selected address only; a response was not established.';
  const item = device(1, { identity_note: note });
  item.reports[0].device_id = null;
  const app = setup(() => page([item]));
  assert.equal(await app.library.load(), true);
  assert.equal(app.library.getState().items[0].identity_note, note);
  assert.equal(app.library.getState().items[0].reports[0].device_id, null);
});

test('invalid keys, duplicate records, unsafe report links and unbounded responses fail closed', () => {
  for (const response of [
    page([device(1, { device_key: '../../other' })]),
    page([device(1), device(1)]),
    page([device(1, { reports: [{ scan_id: 'javascript:alert(1)', device_id: 'x', created_at: '', state: 'completed' }] })]),
    page(Array.from({ length: 25 }, (_, i) => device(i + 1))),
    page([device()], { revision: null }),
    page([device()], { total: -1 }),
  ]) assert.throws(() => validateDevicePage(response), /could not be read/);
  assert.equal(validDeviceLabels(labels('x'.repeat(81))), false);
  assert.equal(validDeviceLabels(labels('Two\nlines')), false);
  assert.equal(validDeviceLabels(labels('Kitchen', 'true')), false);
});

test('a vanished last page is corrected once within the current filtered collection', async () => {
  const app = setup(path => {
    const offset = Number(new URL(path, 'http://localhost').searchParams.get('offset'));
    return page(offset ? [] : [device()], { total: 1, offset });
  });
  assert.equal(await app.library.load('Kitchen', 3), true);
  assert.equal(app.calls.length, 2);
  assert.equal(app.library.getState().offset, 0);
  assert.equal(app.library.getState().search, 'Kitchen');
});

test('discard changes household draft state only and never calls a write endpoint', async () => {
  const app = setup(); await app.library.load();
  app.library.change(key(1), labels('Temporary')); app.library.discard(key(1));
  assert.equal(app.library.getState().draftCount, 0);
  assert.equal(app.library.getState().items[0].draft.room, '');
  assert.equal(app.calls.length, 1);
});

test('invalid room input remains a draft through reload but cannot reach a write endpoint', async () => {
  const app = setup(); await app.library.load();
  const invalid = 'Study\u200b';
  assert.equal(app.library.change(key(1), labels(invalid)), true);
  assert.equal(await app.library.save(key(1)), false);
  await app.library.load();
  assert.equal(app.library.getState().items[0].draft.room, invalid);
  assert.equal(app.library.getState().draftCount, 1);
  assert.equal(app.calls.filter(call => call.options.method === 'PUT').length, 0);
});

test('views are applied server-side and retained through paging and reload', async () => {
  const app = setup(path => {
    const params = new URL(path, 'http://localhost').searchParams;
    return page([device()], { total: 50, offset: Number(params.get('offset')), view: params.get('view') || 'all' });
  });
  await app.library.load('Study', 2, 'favourites');
  await app.library.load();
  assert.equal(app.calls.length, 2);
  for (const call of app.calls) {
    const params = new URL(call.path, 'http://localhost').searchParams;
    assert.equal(params.get('view'), 'favourites');
    assert.equal(params.get('offset'), '24');
    assert.equal(params.get('search'), 'Study');
  }
  assert.equal(app.library.getState().view, 'favourites');
  assert.equal(await app.library.load('', 1, '__proto__'), false);
  assert.equal(app.calls.length, 2);
});

test('an old backend cannot silently ignore a requested view; observations and drafts survive', async () => {
  const app = setup(); await app.library.load();
  app.library.change(key(1), labels('Study'));
  assert.equal(await app.library.load('', 1, 'not-recognised'), false);
  assert.equal(app.library.getState().view, 'all');
  assert.equal(app.library.getState().items[0].draft.room, 'Study');
  assert.match(app.library.getState().error, /restart the backend/);
});

test('missing inventory API gives useful restart guidance without any scan or write', async () => {
  const app = setup(() => { throw Object.assign(new Error('Not Found'), { status: 404 }); });
  assert.equal(await app.library.load(), false);
  assert.match(app.library.getState().error, /Let active scans finish/);
  assert.equal(app.calls.length, 1);
  assert.equal(app.calls[0].options.method, undefined);
});

test('unchanged revisions and contradictory label receipts cannot erase a draft', async () => {
  for (const receipt of [
    { annotations: labels('Study'), revision: 1 },
    { annotations: labels('Wrong room'), revision: 2 },
    { annotations: labels('Study', true), revision: 2 },
  ]) {
    const app = setup((path, options) => options.method === 'PUT'
      ? { device_key: key(1), editable: true, ...receipt } : page());
    await app.library.load(); app.library.change(key(1), labels('Study'));
    assert.equal(await app.library.save(key(1)), false);
    assert.equal(app.library.getState().items[0].annotations.room, '');
    assert.equal(app.library.getState().items[0].draft.room, 'Study');
    assert.equal(app.library.getState().needsReload, true);
    assert.equal(await app.library.save(key(1)), false);
    assert.equal(app.calls.length, 2);
  }
});
