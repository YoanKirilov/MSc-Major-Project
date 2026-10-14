import test from 'node:test';
import assert from 'node:assert/strict';
import { boundedPrivateScope, createMonitoringModel, intervalLabel, validateMonitoringStatus } from '../app/static/js/monitoring-model.mjs';

const uuid = '00000000-0000-4000-8000-000000000001';
const status = (extra = {}) => ({ revision: 1, enabled: false, scope: null,
  current_scope: '192.168.56.0/24', interval_minutes: 60, next_check_at: null,
  last_scan_id: null, last_outcome: null, events: [], pause_reason: null,
  configuration_error: null, available: true,
  ...(extra.enabled ? {scope:'192.168.56.0/24',next_check_at:'2026-10-14T11:00:00Z'} : {}), ...extra });
function deferred() {
  let resolve;
  const promise = new Promise(yes => { resolve = yes; });
  return { promise, resolve };
}
function setup(responder = () => status()) {
  const calls = [], changes = [];
  const model = createMonitoringModel({ request: (path, options = {}) => {
    calls.push({ path, options }); return responder(path, options);
  }, onChange: value => changes.push(value) });
  return { model, calls, changes };
}

test('loading and selecting an interval never authorise or start periodic checks', async () => {
  const app = setup(); await app.model.load();
  app.model.chooseInterval(30);
  assert.equal(app.model.getState().canEnable, false);
  assert.equal(await app.model.enable(), false);
  assert.equal(app.calls.length, 1);
  assert.equal(app.calls[0].path, '/api/monitoring');
  assert.equal(app.calls[0].options.method, undefined);
});

test('enable writes only explicit current scope permission, interval and revision', async () => {
  const app = setup((path, options) => options.method === 'PUT'
    ? status({ enabled: true, scope: '192.168.56.0/24', interval_minutes: 360, revision: 2 })
    : status());
  await app.model.load(); app.model.chooseInterval(360); app.model.authorise(true);
  assert.equal(await app.model.enable(), true);
  assert.deepEqual(JSON.parse(app.calls[1].options.body), {
    expected_revision: 1, enabled: true, authorised: true,
    confirmed_scope: '192.168.56.0/24', interval_minutes: 360,
  });
  assert.equal(app.model.getState().authorised, false);
  assert.equal(app.model.getState().canStop, true);
  assert.equal(app.model.getState().canEnable, false);
});

test('reload clears permission immediately and preserves an unsaved interval separately from saved settings', async () => {
  const response = deferred(); let reload = false;
  const app = setup(() => reload ? response.promise : status());
  await app.model.load(); app.model.chooseInterval(360); app.model.authorise(true);
  reload = true;
  const pending = app.model.load();
  assert.equal(app.model.getState().authorised, false);
  assert.equal(app.model.getState().canEnable, false);
  response.resolve(status({ interval_minutes: 30, revision: 2 }));
  assert.equal(await pending, true);
  assert.equal(app.model.getState().draftInterval, 360);
  assert.equal(app.model.getState().status.interval_minutes, 30);
  assert.equal(app.model.getState().intervalDirty, true);
});

test('stop remains available without a permission checkbox and does not apply an interval draft', async () => {
  const app = setup((path, options) => options.method === 'PUT' ? status({ revision: 2 })
    : status({ enabled: true, scope: '192.168.56.0/24', available: false,
      configuration_error: 'Scanner unavailable' }));
  await app.model.load(); app.model.chooseInterval(360);
  assert.equal(app.model.getState().authorised, false);
  assert.equal(app.model.getState().canStop, true);
  assert.equal(await app.model.stop(), true);
  assert.deepEqual(JSON.parse(app.calls[1].options.body), {
    expected_revision: 1, enabled: false, authorised: false,
    confirmed_scope: '192.168.56.0/24', interval_minutes: 60,
  });
  assert.equal(app.model.getState().draftInterval, 360);
  assert.equal(app.model.getState().intervalDirty, true);
});

test('network settings edits clear permission and block enable until reload, without blocking a known stop', async () => {
  const app = setup(() => status({ enabled: true, scope: '192.168.56.0/24' }));
  await app.model.load(); app.model.authorise(true); app.model.invalidateScope();
  assert.equal(app.model.getState().authorised, false);
  assert.equal(app.model.authorise(true), false);
  assert.equal(app.model.getState().canStop, true);
  await app.model.load();
  assert.equal(app.model.authorise(true), true);
});

test('scope-change and restart statuses stay off until fresh explicit authorisation', async () => {
  let response = status();
  const app = setup(() => response);
  await app.model.load(); app.model.authorise(true);
  response = status({ current_scope: '10.2.3.0/24', scope: '192.168.56.0/24',
    pause_reason: 'network_changed', revision: 2 });
  await app.model.load();
  assert.equal(app.model.getState().authorised, false);
  assert.equal(app.model.getState().canEnable, false);
  app.model.authorise(true);
  assert.equal(app.model.getState().confirmedScope, '10.2.3.0/24');
  response = status({ pause_reason: 'restarted', revision: 3 });
  await app.model.load();
  assert.equal(app.model.getState().canEnable, false);
  assert.equal(app.calls.some(call => call.options.method === 'PUT'), false);
});

test('unavailable or unbounded public scopes cannot be authorised, while unreadable revision blocks writes', async () => {
  for (const response of [status({ available: false }), status({ current_scope: '8.8.8.0/24' }),
    status({ current_scope: '10.0.0.0/8' }), status({ revision: null }), status({ current_scope: null })]) {
    const app = setup(() => response); await app.model.load();
    assert.equal(app.model.authorise(true), false);
    assert.equal(await app.model.enable(), false);
    assert.equal(app.calls.length, 1);
  }
});

test('conflicts and uncertain writes preserve the interval and require explicit reload without replay', async () => {
  for (const error of [Object.assign(new Error('Version changed'), { status: 409 }), new Error('Response lost')]) {
    let revision = 1;
    const app = setup((path, options) => { if (options.method === 'PUT') throw error; return status({ revision }); });
    await app.model.load(); app.model.chooseInterval(360); app.model.authorise(true);
    assert.equal(await app.model.enable(), false);
    assert.equal(app.model.getState().draftInterval, 360);
    assert.equal(app.model.getState().needsReload, true);
    assert.equal(app.model.authorise(true), false);
    assert.equal(await app.model.enable(), false);
    assert.equal(app.calls.filter(call => call.options.method === 'PUT').length, 1);
    revision = 2; await app.model.load();
    assert.equal(app.model.getState().needsReload, false);
    assert.equal(app.model.getState().authorised, false);
    assert.equal(app.model.getState().draftInterval, 360);
  }
});

test('duplicate submissions and reloads are disabled while the one write is in flight', async () => {
  const pending = deferred();
  const app = setup((path, options) => options.method === 'PUT' ? pending.promise : status());
  await app.model.load(); app.model.authorise(true);
  const enabled = app.model.enable();
  assert.equal(await app.model.enable(), false);
  assert.equal(await app.model.stop(), false);
  assert.equal(await app.model.load(), false);
  pending.resolve(status({ revision: 2, enabled: true, scope: '192.168.56.0/24' }));
  assert.equal(await enabled, true);
  assert.equal(app.calls.length, 2);
});

test('a failed read preserves known configuration, clears enable permission and still allows a revision-checked stop', async () => {
  let fail = false;
  const app = setup(() => { if (fail) throw new Error('Read outage'); return status({ enabled: true, scope: '192.168.56.0/24' }); });
  await app.model.load(); app.model.authorise(true); fail = true;
  assert.equal(await app.model.load(), false);
  assert.equal(app.model.getState().status.enabled, true);
  assert.equal(app.model.getState().authorised, false);
  assert.equal(app.model.getState().canAuthorise, false);
  assert.equal(app.model.getState().canStop, true);
});

test('delayed earlier status responses cannot overwrite the most recent reload', async () => {
  const first = deferred(), second = deferred(); let count = 0;
  const app = setup(() => ++count === 1 ? first.promise : second.promise);
  const oldLoad = app.model.load(), newLoad = app.model.load();
  second.resolve(status({ revision: 2, current_scope: '10.2.3.0/24' }));
  assert.equal(await newLoad, true);
  first.resolve(status());
  assert.equal(await oldLoad, false);
  assert.equal(app.model.getState().status.revision, 2);
});

test('malformed receipts never imply a successful enable and require a status reload', async () => {
  const app = setup((path, options) => options.method === 'PUT' ? status({ revision: null, enabled: true }) : status());
  await app.model.load(); app.model.authorise(true);
  assert.equal(await app.model.enable(), false);
  assert.equal(app.model.getState().status.enabled, false);
  assert.equal(app.model.getState().needsReload, true);
});

test('unchanged revision or opposite enabled state cannot confirm a submitted change', async () => {
  for (const response of [status({enabled:true,revision:1}), status({enabled:false,revision:2})]) {
    const app = setup((_path, options) => options.method === 'PUT' ? response : status());
    await app.model.load(); app.model.authorise(true);
    assert.equal(await app.model.enable(), false);
    assert.equal(app.model.getState().needsReload, true);
    assert.equal(app.model.getState().status.enabled, false);
  }
});

test('an enabled status must retain its approved scope and next date', () => {
  for (const response of [status({enabled:true,scope:null}), status({enabled:true,next_check_at:null}),status({enabled:false,next_check_at:'2026-10-14T11:00:00Z'})]) {
    assert.throws(() => validateMonitoringStatus(response), /could not be read/);
  }
});

test('status validation bounds events and rejects unsafe saved-report identifiers', () => {
  const event = { event_id: uuid, occurred_at: '2026-10-14T09:00:00Z', kind: 'finished',
    message: '<script>untrusted text</script>', scan_id: uuid, outcome: 'partial',
    counts: { device_count: 2, unfinished_count: 1 } };
  assert.equal(validateMonitoringStatus(status({ events: [event] })).events.length, 1);
  for (const response of [status({ events: Array.from({ length: 101 }, () => event) }),
    status({ last_scan_id: 'javascript:alert(1)' }), status({ interval_minutes: 1 }),
    status({ events: [{ ...event, scan_id: '../not-a-report' }] }),
    status({ events: [{ ...event, counts: { device_count: -1 } }] })]) {
    assert.throws(() => validateMonitoringStatus(response), /could not be read/);
  }
});

test('saved non-preset intervals remain explicit and scope confirmation accepts only bounded canonical private networks', async () => {
  const app = setup(() => status({ interval_minutes: 90 })); await app.model.load();
  assert.equal(app.model.getState().draftInterval, 90);
  assert.equal(intervalLabel(90), '90 minutes');
  for (const scope of ['192.168.56.0/24', '10.2.3.128/25', '172.16.0.4/32']) assert.equal(boundedPrivateScope(scope), true);
  for (const scope of ['192.168.056.0/24', '192.168.56.1/24', '172.32.0.0/24', '0.0.0.0/0', '10.0.0.0/8']) assert.equal(boundedPrivateScope(scope), false);
});
