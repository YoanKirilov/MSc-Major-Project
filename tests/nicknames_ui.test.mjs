import assert from 'node:assert/strict';
import test from 'node:test';
import { createNicknameState, projectNicknames } from '../app/static/js/nicknames.mjs';

const snapshot = (revision, name = 'Room computer') => ({ revision, changed: true, names: name ? { device: name } : {} });

test('older polls and full-report snapshots never replace newer names or notices', () => {
  const state = createNicknameState();
  assert.ok(state.apply(snapshot(1)));
  assert.ok(state.apply(snapshot(3, 'Newest label')));
  assert.equal(state.apply({ ...snapshot(2, 'Delayed label'), recovery_notice: 'Older notice' }), false);
  assert.equal(state.value.revision, 3);
  const data = { nickname_revision: 2, user_nicknames: { device: 'Old full report' }, devices: [{ device_id: 'device', hostname: 'Observed name' }] };
  assert.equal(state.apply({ revision: data.nickname_revision, changed: true, names: data.user_nicknames }), false);
  projectNicknames(data, state);
  assert.equal(data.nickname_revision, 3);
  assert.equal(data.devices[0].user_nickname, 'Newest label');
  assert.equal(data.devices[0].hostname, 'Observed name');
  assert.equal(state.value.recovery_notice, '');
});

test('committed edit revision fences delayed reads before a new snapshot arrives', () => {
  const state = createNicknameState();
  state.apply(snapshot(1));
  assert.ok(state.confirmRevision(3));
  assert.equal(state.available, false);
  assert.equal(state.apply(snapshot(2, 'Delayed')), false);
  assert.ok(state.apply(snapshot(3, 'Saved edit')));
  assert.equal(state.available, true);
  state.confirmRevision(2);
  assert.equal(state.value.revision, 3);
  assert.equal(state.apply(snapshot(2)), false);
});

test('invalid snapshots cannot partially mutate names, availability or notices', () => {
  const state = createNicknameState();
  state.apply(snapshot(3));
  for (const invalid of [null, {}, { ...snapshot(4), revision: '4' }, { ...snapshot(4), names: [] },
    { ...snapshot(4), changed: 'true' }, { ...snapshot(4), names: { device: 'x'.repeat(81) } },
    { ...snapshot(4), names: { device: 'bad\nname' } }, { ...snapshot(4), recovery_notice: {} },
    { ...snapshot(4), recovery_notice: 'x'.repeat(301) }, { revision: 4, changed: false }, snapshot(3, 'Same revision, different content')]) {
    assert.equal(state.apply(invalid), false);
    assert.equal(state.value.revision, 3);
  }
  assert.equal(state.confirmRevision(NaN), false);
});

test('unavailability retains the revision guard and full recovery/removal remains explicit', () => {
  const state = createNicknameState();
  state.apply(snapshot(3));
  state.unavailable();
  assert.equal(state.apply({ revision: 3, changed: false }), false);
  assert.equal(state.apply(snapshot(2)), false);
  assert.ok(state.apply({ ...snapshot(4, ''), recovery_notice: 'Recovered; latest edits may be missing.' }));
  assert.equal(state.available, true);
  assert.deepEqual(state.value.names, {});
  assert.ok(state.apply({ revision: 4, changed: false }));
  assert.match(state.value.recovery_notice, /latest edits/);
});

test('compact AI progress is not a full report and must not receive nickname projection', () => {
  const state = createNicknameState();
  state.apply(snapshot(3));
  const progress = { phase: 'analysis', state: 'running', device_count: 1, coverage: {} };
  const before = JSON.stringify(progress);
  assert.equal(projectNicknames(progress, state), progress);
  assert.equal(JSON.stringify(progress), before);
});
