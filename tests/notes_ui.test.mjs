import assert from 'node:assert/strict';
import test from 'node:test';
import { createNoteState, projectNotes, reviewProgress, confirmedTitleReceipt } from '../app/static/js/notes.mjs';

test('title save receipts require a strictly newer safe revision and the normalised requested value', () => {
  assert.equal(confirmedTitleReceipt({ revision: 3, title: 'Home' }, 2, '  Home  '), true);
  assert.equal(confirmedTitleReceipt({ revision: 3, title: '' }, 2, ' '), true);
  for (const receipt of [null, {}, { revision: 2, title: 'Home' },
    { revision: 1, title: 'Home' }, { revision: 3, title: 'Other title' },
    { revision: 3, title: null }, { revision: '3', title: 'Home' },
    { revision: Number.MAX_SAFE_INTEGER + 1, title: 'Home' }]) {
    assert.equal(confirmedTitleReceipt(receipt, 2, 'Home'), false);
  }
  assert.equal(confirmedTitleReceipt({ revision: 3, title: 'Home' }, null, 'Home'), false);
  assert.equal(confirmedTitleReceipt({ revision: 3, title: 'Home' }, 2, null), false);
});

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
    querySelectorAll: selector => selector === '.action-check select' ? controls
      : selector === '[data-note-panel]' ? panels : [] };
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

test('status filters hide complete task rows, not recommendations in the selected item', () => {
  const elements = new Map(['#report-user-title', '#editReportTitle', '#annotation-notice',
    '#checklist-filter', '#checklist-filter-count', '#checklist-empty'].map(id => [id, {}]));
  elements.get('#checklist-filter').value = 'checked';
  const task = { hidden: false };
  const detailRow = { dataset: {} };
  const taskRow = { dataset: {} };
  const controls = [
    { dataset: { findingId: 'one', actionId: 'a' }, closest: selector => selector === '.review-task' ? null : detailRow },
    { dataset: { findingId: 'one', actionId: 'a' }, closest: selector => selector === '.review-task' ? task : taskRow },
  ];
  const document = { querySelector: id => elements.get(id), querySelectorAll: selector => ({
    '.action-check select': controls, '#nextStepsList .review-task': [task],
  })[selector] || [] };
  projectNotes(document, { revision: 1, action_checks: [] });
  assert.equal(detailRow.hidden, false);
  assert.equal(taskRow.hidden, false);
  assert.equal(task.hidden, true);
  assert.match(elements.get('#checklist-filter-count').textContent, /0 of 1 review tasks available/);
  assert.match(elements.get('#checklist-filter-count').textContent, /Choose All statuses/);
  assert.doesNotMatch(elements.get('#checklist-filter-count').textContent, /Open a Review tasks heading/);
  assert.equal(elements.get('#checklist-empty').hidden, false);
  document.activeElement = controls[1];
  projectNotes(document, { revision: 1, action_checks: [] });
  assert.equal(task.hidden, false, 'a focused control must not disappear mid-edit');
  taskRow.dataset.editing = 'true';
  document.activeElement = null;
  projectNotes(document, { revision: 1, action_checks: [] });
  assert.equal(task.hidden, false, 'an in-flight save must remain visible');
});

test('no-action reports do not direct users to nonexistent task controls or imply safety', () => {
  const elements = new Map(['#report-user-title', '#editReportTitle', '#annotation-notice',
    '#checklist-filter', '#checklist-filter-count'].map(id => [id, {}]));
  elements.get('#checklist-filter').value = 'all';
  projectNotes({ querySelector: id => elements.get(id), querySelectorAll: () => [] },
    { revision: 1, action_checks: [] });
  assert.equal(elements.get('#checklist-filter-count').textContent,
    'No review tasks were recorded. This is not a safety verdict.');
});

test('background projections do not undo the user closing a filtered task disclosure', () => {
  const elements = new Map(['#report-user-title', '#editReportTitle', '#annotation-notice',
    '#checklist-filter'].map(id => [id, {}]));
  elements.get('#checklist-filter').value = 'to_check';
  const disclosure = { open: false };
  const row = { hidden: false };
  const group = { querySelectorAll: () => [row], querySelector: () => disclosure };
  const document = { querySelector: id => elements.get(id), querySelectorAll: selector => ({
    '#nextStepsList .review-task': [row], '#nextStepsList > li': [group],
  })[selector] || [] };
  projectNotes(document, { revision: 1 }, { expandFiltered: true });
  assert.equal(disclosure.open, true);
  disclosure.open = false;
  projectNotes(document, { revision: 2 }, { expandFiltered: false });
  assert.equal(disclosure.open, false);
  assert.equal(group.hidden, false);
});

test('an uncertain checklist draft survives projection and keeps a filtered row available without claiming it saved', () => {
  const elements = new Map(['#report-user-title', '#editReportTitle', '#annotation-notice',
    '#checklist-filter'].map(id => [id, {}]));
  elements.get('#checklist-filter').value = 'to_check';
  const retry = {};
  const row = { dataset: {}, querySelector: () => retry };
  const task = {};
  const control = { dataset: { findingId: 'one', actionId: 'a' },
    closest: selector => selector === '.review-task' ? task : row };
  const drafts = new Map([[JSON.stringify(['one', 'a']), { status: 'checked', message: 'Save not confirmed. Choice kept as a draft.' }]]);
  const document = { querySelector: id => elements.get(id), querySelectorAll: selector =>
    selector === '.action-check select' ? [control] : [] };
  projectNotes(document, { revision: 1, action_checks: [] }, { drafts });
  assert.equal(control.value, 'checked');
  assert.equal(task.hidden, false);
  assert.equal(retry.hidden, false);
  assert.equal(retry.disabled, false);
  projectNotes(document, null, { drafts });
  assert.equal(control.value, 'checked');
  assert.equal(control.disabled, true);
  assert.equal(retry.disabled, true);
});

test('collapsed checklists expose saved status without rebuilding controls and empty filters retain truthful counts', () => {
  const elements = new Map(['#report-user-title', '#editReportTitle', '#annotation-notice',
    '#checklist-filter', '#checklist-filter-count'].map(id => [id, {}]));
  elements.get('#checklist-filter').value = 'all';
  const summary = {};
  const rows = ['a', 'b'].map(actionId => ({ hidden: false, dataset: { actionId } }));
  const disclosure = { open: false, dataset: { findingId: 'one' }, querySelector: () => summary };
  const group = { querySelectorAll: () => rows, querySelector: () => disclosure };
  const document = { querySelector: id => elements.get(id), querySelectorAll: selector => ({
    '#nextStepsList .review-task': rows, '#nextStepsList > li': [group],
  })[selector] || [] };
  const notes = { revision: 1, action_checks: [{ finding_id: 'one', action_id: 'a', status: 'checked' },
    { finding_id: 'one', action_id: 'b', status: 'need_help' }] };
  projectNotes(document, notes, { expandFiltered: false });
  assert.equal(summary.textContent, 'Review tasks (2) · 1 Checked · 1 need help');
  assert.equal(disclosure.open, false);
  assert.match(elements.get('#checklist-filter-count').textContent, /tasks available.*Open a Review tasks heading/);
  elements.get('#checklist-filter').value = 'to_check';
  rows.forEach(row => { row.hidden = true; });
  projectNotes(document, notes, { expandFiltered: false });
  assert.equal(summary.textContent, 'Review tasks (2) · 1 Checked · 1 need help · 0 available in this filter');
  assert.equal(group.hidden, true);
  rows.forEach(row => { row.hidden = false; });
  elements.get('#checklist-filter').value = 'all';
  projectNotes(document, null, { expandFiltered: false });
  assert.match(summary.textContent, /saved status unavailable/);
  assert.doesNotMatch(summary.textContent, /to check|Checked|need help/);
});
