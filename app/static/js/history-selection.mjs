const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
export const validReportId = value => typeof value === 'string' && uuid.test(value);
export function canDeleteReport(report) {
  return report?.deletable === true && report.source === 'live' && validReportId(report.scan_id)
    && ['completed', 'partial', 'failed', 'cancelled'].includes(report.state)
    && Number.isSafeInteger(report.revision) && report.revision > 0
    && Number.isSafeInteger(report.expected_notes_revision) && report.expected_notes_revision > 0;
}
export function deletionTarget(report) {
  return { scan_id: report.scan_id, expected_revision: report.revision,
    expected_notes_revision: report.expected_notes_revision };
}
export function createReportSelection() {
  let rows = new Map();
  const selected = new Map();
  return {
    sync(items) {
      rows = new Map(items.slice(0, 24).filter(canDeleteReport).map(item => [item.scan_id, item]));
      for (const [id, token] of selected) {
        const current = rows.get(id);
        if (!current || current.revision !== token.expected_revision
          || current.expected_notes_revision !== token.expected_notes_revision) selected.delete(id);
      }
    },
    set(id, checked) {
      if (!checked) selected.delete(id);
      else if (rows.has(id)) selected.set(id, deletionTarget(rows.get(id)));
    },
    all(checked) {
      selected.clear();
      if (checked) for (const item of rows.values()) selected.set(item.scan_id, deletionTarget(item));
    },
    clear() { selected.clear(); },
    targets() { return Array.from(selected.values(), item => ({ ...item })); },
    has(id) { return selected.has(id); },
    getState() { return { count: selected.size, eligibleCount: rows.size,
      all: rows.size > 0 && selected.size === rows.size,
      some: selected.size > 0 && selected.size < rows.size }; },
  };
}
export function validateDeletionReceipt(receipt, targets) {
  const expected = new Set(targets.map(item => item.scan_id));
  if (!Array.isArray(receipt?.results) || receipt.results.length !== expected.size) throw new Error('Removal outcome could not be verified. Reload the reports before trying again.');
  const seen = new Set();
  for (const item of receipt.results) {
    if (!expected.has(item?.scan_id) || seen.has(item.scan_id)
      || !['deleted', 'missing', 'changed', 'active', 'unavailable'].includes(item.status)
      || (item.status === 'deleted' && !validReportId(item.trash_id))) throw new Error('Removal outcome could not be verified. Reload the reports before trying again.');
    seen.add(item.scan_id);
  }
  return receipt.results;
}

export function validateRestoreReceipt(receipt, trashIds) {
  const failure = () => new Error('Restore outcome could not be verified. Reload the reports before trying again.');
  if (!Array.isArray(trashIds) || trashIds.some(id => !validReportId(id))) throw failure();
  const expected = new Set(trashIds);
  if (expected.size !== trashIds.length || !Array.isArray(receipt?.results)
    || receipt.results.length !== expected.size) throw failure();
  const seen = new Set();
  for (const item of receipt.results) {
    if (!expected.has(item?.trash_id) || seen.has(item.trash_id)
      || !['restored', 'missing', 'changed', 'unavailable'].includes(item.status)
      || (item.status === 'restored' && !validReportId(item.scan_id))) throw failure();
    seen.add(item.trash_id);
  }
  return receipt.results;
}
