import test from 'node:test';
import assert from 'node:assert/strict';
import { validReportId, canDeleteReport, deletionTarget, createReportSelection,
  validateDeletionReceipt, validateRestoreReceipt } from '../app/static/js/history-selection.mjs';

const id = number => '00000000-0000-4000-8000-' + String(number).padStart(12, '0');
const report = (number, changes = {}) => ({ scan_id: id(number), source: 'live',
  state: 'completed', deletable: true, revision: 3, expected_notes_revision: 2, ...changes });
const target = number => deletionTarget(report(number));
const invalidReceipt = /Removal outcome could not be verified.*Reload the reports/;
const invalidRestore = /Restore outcome could not be verified.*Reload the reports/;

test('report IDs must be canonical lower-case UUIDs, not paths or malformed input', () => {
  assert.equal(validReportId(id(1)), true);
  assert.equal(validReportId('abcdef01-2345-4678-9abc-def012345678'), true);
  for (const value of [null, undefined, 1, {}, '', '../report', id(1) + '/scan.json',
    id(1) + '\n', 'ABCDEF01-2345-4678-9ABC-DEF012345678', id(1).replaceAll('-', '')]) {
    assert.equal(validReportId(value), false);
  }
});

test('only explicitly deletable terminal live reports with both revision tokens qualify', () => {
  for (const state of ['completed', 'partial', 'failed', 'cancelled']) {
    assert.equal(canDeleteReport(report(1, { state })), true);
  }
  for (const state of ['queued', 'running', 'analysis', 'unknown', '', undefined]) {
    assert.equal(canDeleteReport(report(1, { state })), false);
  }
  for (const changes of [{ deletable: false }, { deletable: 'true' }, { deletable: undefined },
    { source: 'demo' }, { source: undefined }, { scan_id: '../report' }]) {
    assert.equal(canDeleteReport(report(1, changes)), false);
  }
  assert.equal(canDeleteReport(null), false);
  assert.equal(canDeleteReport(undefined), false);
});

test('both scan and notes revisions must be positive safe integers', () => {
  for (const field of ['revision', 'expected_notes_revision']) {
    for (const value of [undefined, null, 0, -1, 1.5, '3', Infinity, Number.MAX_SAFE_INTEGER + 1]) {
      assert.equal(canDeleteReport(report(1, { [field]: value })), false);
    }
    assert.equal(canDeleteReport(report(1, { [field]: Number.MAX_SAFE_INTEGER })), true);
  }
});

test('deletion targets contain only the ID and concurrency tokens and do not mutate reports', () => {
  const row = report(1, { title: 'Private title', target: { ip: '192.168.0.2' } });
  const selected = deletionTarget(row);
  assert.deepEqual(selected, { scan_id: id(1), expected_revision: 3, expected_notes_revision: 2 });
  selected.expected_revision = 99;
  assert.equal(row.revision, 3);
  assert.deepEqual(deletionTarget(row), { scan_id: id(1), expected_revision: 3,
    expected_notes_revision: 2 });
});

test('selection starts empty and ignores unavailable or ineligible report IDs', () => {
  const selection = createReportSelection();
  assert.deepEqual(selection.getState(), { count: 0, eligibleCount: 0, all: false, some: false });
  selection.sync([report(1), report(2, { state: 'running' }), report(3, { source: 'demo' })]);
  for (const number of [2, 3, 4]) selection.set(id(number), true);
  assert.deepEqual(selection.targets(), []);
  assert.deepEqual(selection.getState(), { count: 0, eligibleCount: 1, all: false, some: false });
});

test('individual selection tracks partial and all-selected states without duplicate targets', () => {
  const selection = createReportSelection();
  selection.sync([report(1), report(2)]);
  selection.set(id(1), true);
  selection.set(id(1), true);
  assert.deepEqual(selection.targets(), [target(1)]);
  assert.deepEqual(selection.getState(), { count: 1, eligibleCount: 2, all: false, some: true });
  selection.set(id(2), true);
  assert.deepEqual(selection.getState(), { count: 2, eligibleCount: 2, all: true, some: false });
  selection.set(id(1), false);
  assert.equal(selection.has(id(1)), false);
  assert.equal(selection.has(id(2)), true);
  assert.deepEqual(selection.getState(), { count: 1, eligibleCount: 2, all: false, some: true });
});

test('select all selects only eligible reports on the current displayed page', () => {
  const selection = createReportSelection();
  selection.sync([report(1), report(2, { state: 'running' }), report(3)]);
  selection.all(true);
  assert.deepEqual(selection.targets(), [target(1), target(3)]);
  assert.deepEqual(selection.getState(), { count: 2, eligibleCount: 2, all: true, some: false });
  selection.all(false);
  assert.deepEqual(selection.targets(), []);
  assert.deepEqual(selection.getState(), { count: 0, eligibleCount: 2, all: false, some: false });
});

test('selection cannot expand past the page cap even if oversized input reaches the model', () => {
  const selection = createReportSelection();
  selection.sync(Array.from({ length: 30 }, (_, index) => report(index + 1)));
  selection.all(true);
  assert.equal(selection.targets().length, 24);
  assert.equal(selection.getState().eligibleCount, 24);
  assert.equal(selection.has(id(24)), true);
  assert.equal(selection.has(id(25)), false);
  selection.set(id(25), true);
  assert.equal(selection.targets().length, 24);
});

test('revealing an extra row retains current-page selection but does not silently select it', () => {
  const selection = createReportSelection();
  selection.sync([report(1)]);
  selection.all(true);
  selection.sync([report(1), report(2)]);
  assert.deepEqual(selection.targets(), [target(1)]);
  assert.deepEqual(selection.getState(), { count: 1, eligibleCount: 2, all: false, some: true });
});

test('switching pages or filtering clears selections that are no longer displayed', () => {
  const selection = createReportSelection();
  selection.sync([report(1), report(2)]);
  selection.all(true);
  selection.sync([report(25), report(26)]);
  assert.deepEqual(selection.targets(), []);
  assert.deepEqual(selection.getState(), { count: 0, eligibleCount: 2, all: false, some: false });
  selection.all(true);
  selection.sync([]);
  assert.deepEqual(selection.getState(), { count: 0, eligibleCount: 0, all: false, some: false });
});

test('scan-revision changes remove stale selection while preserving unchanged selected reports', () => {
  const selection = createReportSelection();
  selection.sync([report(1), report(2)]);
  selection.all(true);
  selection.sync([report(1, { revision: 4 }), report(2)]);
  assert.equal(selection.has(id(1)), false);
  assert.equal(selection.has(id(2)), true);
  assert.deepEqual(selection.targets(), [target(2)]);
  selection.set(id(1), true);
  assert.equal(selection.targets().find(item => item.scan_id === id(1)).expected_revision, 4);
});

test('notes-revision changes and newly active reports invalidate stale selection', () => {
  const selection = createReportSelection();
  selection.sync([report(1), report(2), report(3)]);
  selection.all(true);
  selection.sync([report(1, { expected_notes_revision: 3 }), report(2, { state: 'running' }), report(3)]);
  assert.deepEqual(selection.targets(), [target(3)]);
  assert.equal(selection.getState().eligibleCount, 2);
  selection.set(id(1), true);
  assert.equal(selection.targets().find(item => item.scan_id === id(1)).expected_notes_revision, 3);
});

test('returned targets are cloned so confirmation snapshots cannot mutate current selection', () => {
  const selection = createReportSelection();
  selection.sync([report(1)]);
  selection.set(id(1), true);
  const first = selection.targets();
  first[0].scan_id = id(99);
  first[0].expected_revision = 99;
  first.push(target(2));
  assert.deepEqual(selection.targets(), [target(1)]);
  selection.clear();
  assert.deepEqual(selection.targets(), []);
  assert.equal(selection.getState().eligibleCount, 1);
});

test('an exact receipt accepts mixed outcomes and does not imply every target was deleted', () => {
  const targets = [1, 2, 3, 4, 5].map(target);
  const receipt = { results: [
    { scan_id: id(1), status: 'deleted', trash_id: id(101) },
    { scan_id: id(2), status: 'missing' },
    { scan_id: id(3), status: 'changed' },
    { scan_id: id(4), status: 'active' },
    { scan_id: id(5), status: 'unavailable' },
  ] };
  assert.deepEqual(validateDeletionReceipt(receipt, targets), receipt.results);
});

test('receipt ordering is irrelevant but every requested ID must appear exactly once', () => {
  const targets = [target(1), target(2)];
  const results = [{ scan_id: id(2), status: 'missing' },
    { scan_id: id(1), status: 'deleted', trash_id: id(101) }];
  assert.deepEqual(validateDeletionReceipt({ results }, targets), results);
  for (const invalid of [[], [results[0]], [...results, { scan_id: id(3), status: 'missing' }],
    [results[0], results[0]], [results[0], { scan_id: id(3), status: 'missing' }]]) {
    assert.throws(() => validateDeletionReceipt({ results: invalid }, targets), invalidReceipt);
  }
});

test('invalid receipt shape and unrecognised outcomes cannot be reported as success', () => {
  const targets = [target(1)];
  for (const receipt of [null, undefined, {}, { results: null }, { results: {} },
    { results: [null] }, { results: [{}] }, { results: [{ scan_id: id(1), status: 'success' }] },
    { results: [{ scan_id: id(1), status: 'DELETED', trash_id: id(101) }] }]) {
    assert.throws(() => validateDeletionReceipt(receipt, targets), invalidReceipt);
  }
});

test('a deleted outcome requires a valid recovery trash ID rather than an unverified promise', () => {
  const targets = [target(1)];
  for (const trash_id of [undefined, null, '', '../trash', 1, id(101) + '/scan.json']) {
    assert.throws(() => validateDeletionReceipt({ results: [
      { scan_id: id(1), status: 'deleted', trash_id },
    ] }, targets), invalidReceipt);
  }
  assert.doesNotThrow(() => validateDeletionReceipt({ results: [
    { scan_id: id(1), status: 'deleted', trash_id: id(101) },
  ] }, targets));
});

test('an empty target list accepts only an exact empty receipt', () => {
  assert.deepEqual(validateDeletionReceipt({ results: [] }, []), []);
  assert.throws(() => validateDeletionReceipt({ results: [
    { scan_id: id(1), status: 'missing' },
  ] }, []), invalidReceipt);
});

test('restore receipts accept exact mixed outcomes without assuming every copy was restored', () => {
  const trashIds = [101, 102, 103, 104].map(id);
  const results = [
    { trash_id: id(101), status: 'restored', scan_id: id(1) },
    { trash_id: id(102), status: 'missing' },
    { trash_id: id(103), status: 'changed', scan_id: id(3) },
    { trash_id: id(104), status: 'unavailable' },
  ];
  assert.deepEqual(validateRestoreReceipt({ results }, trashIds), results);
});

test('restore receipts may be reordered but must contain each recovery ID exactly once', () => {
  const trashIds = [id(101), id(102)];
  const results = [{ trash_id: id(102), status: 'missing' },
    { trash_id: id(101), status: 'restored', scan_id: id(1) }];
  assert.deepEqual(validateRestoreReceipt({ results }, trashIds), results);
  for (const invalid of [[], [results[0]], [results[0], results[0]],
    [results[0], { trash_id: id(103), status: 'missing' }],
    [...results, { trash_id: id(103), status: 'unavailable' }]]) {
    assert.throws(() => validateRestoreReceipt({ results: invalid }, trashIds), invalidRestore);
  }
});

test('restored outcomes require canonical report UUIDs before they can be treated as success', () => {
  for (const scan_id of [undefined, null, '', 1, '../report', id(1) + '/scan.json',
    'ABCDEF01-2345-4678-9ABC-DEF012345678']) {
    assert.throws(() => validateRestoreReceipt({ results: [
      { trash_id: id(101), status: 'restored', scan_id },
    ] }, [id(101)]), invalidRestore);
  }
  assert.doesNotThrow(() => validateRestoreReceipt({ results: [
    { trash_id: id(101), status: 'restored', scan_id: id(1) },
  ] }, [id(101)]));
});

test('malformed restore receipts and unknown outcomes never count as confirmed restoration', () => {
  for (const receipt of [null, undefined, {}, { results: null }, { results: {} },
    { results: [null] }, { results: [{}] },
    { results: [{ trash_id: id(101), status: 'deleted', scan_id: id(1) }] },
    { results: [{ trash_id: id(101), status: 'success', scan_id: id(1) }] },
    { results: [{ trash_id: id(101), status: 'RESTORED', scan_id: id(1) }] }]) {
    assert.throws(() => validateRestoreReceipt(receipt, [id(101)]), invalidRestore);
  }
});

test('restore validation rejects duplicate or malformed requested recovery IDs', () => {
  const receipt = { results: [{ trash_id: id(101), status: 'restored', scan_id: id(1) }] };
  for (const trashIds of [undefined, null, {}, id(101), [id(101), id(101)], ['../trash'],
    [null], [1], [id(101), '../trash']]) {
    assert.throws(() => validateRestoreReceipt(receipt, trashIds), invalidRestore);
  }
});

test('empty restore requests accept only exact empty receipts', () => {
  assert.deepEqual(validateRestoreReceipt({ results: [] }, []), []);
  assert.throws(() => validateRestoreReceipt({ results: [
    { trash_id: id(101), status: 'missing' },
  ] }, []), invalidRestore);
});
