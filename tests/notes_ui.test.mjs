import assert from 'node:assert/strict';
import test from 'node:test';
import { createNoteState, projectNotes, reviewProgress } from '../app/static/js/notes.mjs';

test('every full snapshot is projected once; delayed older responses cannot regress notes', () => {
  const projected = [];
  const state = createNoteState(snapshot => projected.push(snapshot));
  const fresh = { revision: 4, title: 'New', action_checks: [] };
  assert.equal(state.apply(fresh), true);
  assert.equal(state.apply({ revision: 3, title: 'Old' }), false);
  assert.equal(state.apply({ revision: 0 }), false);
  assert.equal(state.value, fresh);
  assert.deepEqual(projected, [fresh]);
  state.apply(null);
  assert.equal(state.value, null);
  assert.equal(state.apply({ revision: 3, title: 'Delayed response after outage' }), false);
  assert.equal(state.apply(fresh), true); // Reconnect after a failed read.
});

test('review progress counts unique saved actions, not duplicate controls or unrelated notes', () => {
  const action = { action_id: 'a' };
  const data = { findings: [{ finding_id: 'one', actions: [action, action] }, { finding_id: 'two', actions: [action] }] };
  const notes = { action_checks: [{ finding_id: 'one', action_id: 'a', status: 'checked' },
    { finding_id: 'deleted', action_id: 'a', status: 'need_help' }] };
  assert.deepEqual(reviewProgress(data, notes), { total: 2, checked: 1, need_help: 0, to_check: 1 });
  assert.equal(reviewProgress(data, null).checked, 0); // A fresh report never inherits checks.
});

test('snapshot updates title, duplicated checklist controls, name/CVE panels and recovery in place', () => {
  const elements = new Map(['#report-user-title', '#editReportTitle', '#annotation-notice', '#checklist-filter', '#checklist-progress'].map(id => [id, {}]));
  elements.get('#checklist-filter').value = 'checked';
  const controls = [1, 2].map(() => {
    const row = { dataset: {} };
    return { dataset: { findingId: 'one', actionId: 'a' }, closest: () => row };
  });
  const observed = [];
  const panels = [1, 2].map(() => ({ updateNotes: notes => observed.push(notes?.revision) }));
  const document = { querySelector: id => elements.get(id),
    querySelectorAll: selector => selector === '.action-check select' ? controls : panels };
  const data = { findings: [{ finding_id: 'one', actions: [{ action_id: 'a' }] }] };
  projectNotes(document, { revision: 4, title: 'Saved title', recovery_notice: 'Previous backup restored',
    action_checks: [{ finding_id: 'one', action_id: 'a', status: 'checked' }] }, { data });
  assert.equal(elements.get('#report-user-title').textContent, 'Saved title');
  assert.deepEqual(controls.map(c => c.value), ['checked', 'checked']);
  assert.deepEqual(observed, [4, 4]);
  assert.equal(elements.get('#annotation-notice').hidden, false);
  assert.match(elements.get('#checklist-progress').textContent, /1 of 1.*not a security score/);
  projectNotes(document, null, { data });
  assert.ok(controls.every(c => c.disabled));
});
