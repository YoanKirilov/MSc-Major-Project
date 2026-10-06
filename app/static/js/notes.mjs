// Mutable report notes, not scan facts. Keep projection updates in place so
// adopting a full snapshot never destroys focus, filters or expanded evidence.
export function createNoteState(project) {
  let current = null;
  let newestRevision = 0;
  return {
    get value() { return current; },
    apply(snapshot) {
      if (snapshot && (!Number.isInteger(snapshot.revision) || snapshot.revision < 1)) return false;
      if (snapshot && snapshot.revision < newestRevision) return false;
      if (snapshot) newestRevision = snapshot.revision;
      current = snapshot;
      project(current);
      return true;
    },
    refresh() { project(current); },
  };
}

export function checkStatus(notes, findingId, actionId) {
  const saved = notes?.action_checks?.find(item => item.finding_id === findingId && item.action_id === actionId)?.status;
  return ['checked', 'need_help'].includes(saved) ? saved : 'to_check';
}

export function reviewProgress(data, notes) {
  const counts = { total: 0, checked: 0, need_help: 0, to_check: 0 };
  const seen = new Set();
  for (const finding of data?.findings || []) {
    for (const action of finding.actions || []) {
      const key = JSON.stringify([finding.finding_id, action.action_id]);
      if (seen.has(key)) continue;
      seen.add(key);
      counts.total++;
      counts[checkStatus(notes, finding.finding_id, action.action_id)]++;
    }
  }
  return counts;
}

export function projectNotes(document, notes, { disabled = false, data = null } = {}) {
  document.querySelector('#report-user-title').textContent = notes?.title || '';
  document.querySelector('#editReportTitle').disabled = !notes || disabled;
  const notice = document.querySelector('#annotation-notice');
  notice.textContent = notes ? notes.recovery_notice || ''
    : 'Saved titles, checklists and later name lookups are unavailable. The original scan results are still shown. Reload to try again.';
  notice.hidden = !notice.textContent;
  const filter = document.querySelector('#checklist-filter')?.value || 'all';
  document.querySelectorAll('.action-check select').forEach(control => {
    control.value = checkStatus(notes, control.dataset.findingId, control.dataset.actionId);
    control.disabled = !notes || disabled;
    const row = control.closest('.action-check');
    // Never hide a focused control as its status changes; the filter applies on
    // the user's next filter change or subsequent rendering, not mid-edit.
    row.hidden = filter !== 'all' && control.value !== filter && document.activeElement !== control && row.dataset.editing !== 'true';
  });
  document.querySelectorAll('[data-note-panel]').forEach(panel => panel.updateNotes?.(notes));
  const progress = document.querySelector('#checklist-progress');
  if (progress) {
    const counts = reviewProgress(data, notes);
    progress.textContent = notes
      ? `Your review progress: ${counts.checked} of ${counts.total} actions marked Checked; ${counts.need_help} need help; ${counts.to_check} still to check. This is your record, not a security score.`
      : 'Your review progress is unavailable; scan coverage is shown separately above.';
  }
}
