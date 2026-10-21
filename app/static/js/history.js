import { request } from './api.js?v=20261018-cve-deadline';
import { startRecoveryBrowser } from './recovery.mjs?v=20261014-recovery';
import { historyContext, reportIdentity, reportDateLabel } from './history-context.mjs?v=20261014-context';
import { createHistoryFeed } from './history-feed.mjs?v=20261014-paged-viewport';
import { reportViewport } from './history-viewport.mjs?v=20261014-paged-viewport';
import { canDeleteReport, createReportSelection, deletionTarget,
  validateDeletionReceipt, validateRestoreReceipt } from './history-selection.mjs?v=20261013-management';

const element = id => document.querySelector(`#history-${id}`);
const list = element('list');
const status = element('status');
const stage = element('scroll-stage');
const filters = element('filters');
const dialog = element('delete-dialog');
const selection = createReportSelection();
let operationBusy = false;
let pendingDelete = [];
let lastUndo = [];
let dialogTrigger = null;
let pagerKey = '';
let context;
try { context = historyContext(window.sessionStorage); }
catch { context = historyContext(null); }
const resumed = context.read();
let recovery;
const viewport = reportViewport({ window, list });

document.querySelector('#storageUsageButton').addEventListener('click', async event => {
  const output = document.querySelector('#storageUsage');
  event.currentTarget.disabled = true;
  output.textContent = 'Measuring saved data...';
  try {
    const usage = await request('/api/storage-usage');
    if (!Number.isFinite(usage?.bytes) || usage.bytes < 0 || !Number.isSafeInteger(usage.files) || usage.files < 0) throw new Error('The saved-data size response could not be read. No files were changed.');
    if (![usage.active_bytes, usage.recovery_bytes, usage.recovery_limit_bytes].every(value => Number.isFinite(value) && value >= 0)) {
      output.textContent = `${(usage.bytes / 1048576).toFixed(1)} MiB in ${usage.files} files (older active-data measurement). Recovery copies are not included. Restart the NetGuard backend task for separate active/recovery totals. No files were removed.`;
      return;
    }
    const copies = Number.isSafeInteger(usage.recovery_reports) && Number.isSafeInteger(usage.recovery_limit_reports)
      ? ` ${usage.recovery_reports} of ${usage.recovery_limit_reports} recovery-copy slots used.` : '';
    output.textContent = `${(usage.active_bytes / 1048576).toFixed(1)} MiB active saved data; ${(usage.recovery_bytes / 1048576).toFixed(1)} MiB recovery copies (capacity ${(usage.recovery_limit_bytes / 1048576).toFixed(0)} MiB).${copies} ${usage.files} files in total. ${usage.warning || 'No files were removed.'}`;
  } catch (error) { output.textContent = error.message; }
  finally { document.querySelector('#storageUsageButton').disabled = false; }
});

function reportName(report) {
  const profile = report.profile === 'deep-tcp-v1' ? 'Deep' : report.profile === 'light' ? 'Light' : 'Scan';
  return report.title || `${profile} report`;
}

function reportItem(report) {
  const item = document.createElement('li');
  item.className = 'history-report';
  item.dataset.reportId = report.scan_id;
  if (report.storage_status !== 'ok') {
    item.classList.add('status-message', 'status-warning');
    item.tabIndex = -1;
    item.textContent = 'A saved report could not be read. Its files have been preserved.';
    return item;
  }
  const name = reportName(report);
  const choice = document.createElement('label');
  choice.className = 'history-report-select';
  const checkbox = document.createElement('input');
  checkbox.type = 'checkbox';
  checkbox.dataset.reportSelect = report.scan_id;
  checkbox.setAttribute('aria-label', `Select report ${reportIdentity(report)}`);
  checkbox.disabled = !canDeleteReport(report);
  checkbox.addEventListener('change', () => {
    if (operationBusy) return;
    selection.set(report.scan_id, checkbox.checked);
    syncManagement();
  });
  choice.append(checkbox);
  const link = document.createElement('a');
  link.href = `/scans/${encodeURIComponent(report.scan_id)}`;
  link.dataset.profile = ['light', 'deep-tcp-v1'].includes(report.profile) ? report.profile : 'unknown';
  const labels = { completed: 'Finished', partial: 'Some checks unfinished', failed: 'Scan failed',
    cancelled: 'Cancelled', running: 'In progress', queued: 'Waiting' };
  const profile = report.profile === 'deep-tcp-v1' ? 'Deep' : report.profile === 'light' ? 'Light' : 'Scan';
  const title = document.createElement('strong');
  title.textContent = name;
  const meta = document.createElement('span');
  meta.className = 'history-report-meta';
  meta.textContent = `${profile} · ${reportDateLabel(report)} · ${labels[report.state] || report.state}`;
  const counts = document.createElement('span');
  counts.className = 'history-report-counts';
  counts.textContent = `${report.device_count} device${report.device_count === 1 ? '' : 's'} recorded · ${report.finding_count} review item${report.finding_count === 1 ? '' : 's'}`;
  link.append(title, meta, counts);
  const remove = document.createElement('button');
  remove.type = 'button';
  remove.className = 'danger-button history-report-delete';
  remove.dataset.reportDelete = report.scan_id;
  remove.textContent = 'Delete';
  remove.setAttribute('aria-label', `Delete report ${reportIdentity(report)}`);
  remove.disabled = !canDeleteReport(report);
  if (!canDeleteReport(report)) remove.title = 'Only readable, finished live reports can be deleted.';
  remove.addEventListener('click', () => openDelete([report], remove));
  item.append(choice, link, remove);
  return item;
}

function pageNumbers(current, total) {
  return [...new Set([1, total, current - 1, current, current + 1])]
    .filter(page => page >= 1 && page <= total).sort((a, b) => a - b);
}

function renderPagination(state) {
  const key = `${state.page}:${state.pageCount}`;
  for (const id of ['pagination', 'pagination-bottom']) {
    const nav = element(id);
    nav.hidden = state.pageCount <= 1;
    if (key !== pagerKey) {
      const controls = [];
      const button = (page, label, ariaLabel) => {
        const control = document.createElement('button');
        control.type = 'button';
        control.className = 'secondary-button';
        control.dataset.page = String(page);
        control.textContent = label;
        control.setAttribute('aria-label', ariaLabel);
        if (page === state.page && /^\d+$/.test(label)) control.setAttribute('aria-current', 'page');
        control.addEventListener('click', async () => {
          if (operationBusy || dialog.open || feed.getState().busy) return;
          if (page === feed.getState().page && feed.getState().phase === 'ready') return;
          selection.clear();
          if (await feed.goToPage(page)) {
            element('results-title').focus({ preventScroll: true });
            element('results-title').scrollIntoView({ block: 'start', behavior: 'instant' });
          }
          syncManagement();
        });
        controls.push(control);
      };
      if (state.page > 1) button(state.page - 1, 'Previous', 'Previous page');
      let previous = 0;
      for (const page of pageNumbers(state.page, state.pageCount)) {
        if (previous && page > previous + 1) {
          const gap = document.createElement('span');
          gap.className = 'history-page-gap';
          gap.textContent = '...';
          gap.setAttribute('aria-hidden', 'true');
          controls.push(gap);
        }
        button(page, String(page), `Page ${page}`);
        previous = page;
      }
      if (state.page < state.pageCount) button(state.page + 1, 'Next', 'Next page');
      nav.replaceChildren(...controls);
    }
    nav.querySelectorAll('button').forEach(button => { button.disabled = state.busy || operationBusy; });
  }
  pagerKey = key;
}

function syncManagement() {
  recovery?.sync();
  const state = feed.getState();
  if (state.busy || operationBusy) list.setAttribute('aria-busy', 'true');
  else list.removeAttribute('aria-busy');
  const selected = selection.getState();
  const all = element('select-all');
  all.checked = selected.all;
  all.indeterminate = selected.some;
  all.disabled = operationBusy || state.busy || selected.eligibleCount === 0;
  element('delete-selected').disabled = operationBusy || state.busy || selected.count === 0;
  element('delete-selected').textContent = selected.count ? `Delete selected (${selected.count})` : 'Delete selected';
  element('selection-status').textContent = selected.count ? `${selected.count} report${selected.count === 1 ? '' : 's'} selected.` : 'No reports selected.';
  const rows = new Map(state.items.map(report => [report.scan_id, report]));
  list.querySelectorAll('[data-report-select]').forEach(input => {
    input.checked = selection.has(input.dataset.reportSelect);
    input.disabled = operationBusy || state.busy || !canDeleteReport(rows.get(input.dataset.reportSelect));
  });
  list.querySelectorAll('[data-report-delete]').forEach(button => {
    button.disabled = operationBusy || state.busy || !canDeleteReport(rows.get(button.dataset.reportDelete));
  });
  filters.querySelectorAll('input, select, button').forEach(control => { control.disabled = operationBusy; });
  element('delete-confirm').disabled = operationBusy || pendingDelete.length === 0;
  element('delete-cancel').disabled = operationBusy;
  element('delete-confirm').textContent = operationBusy ? 'Deleting...' : 'Delete reports';
  element('undo-delete').hidden = lastUndo.length === 0;
  element('undo-delete').disabled = operationBusy || state.busy;
  element('retry').disabled = operationBusy || state.busy;
  element('refresh').disabled = operationBusy || state.busy;
  renderPagination(state);
}

function renderHistory(state) {
  if (state.phase === 'ready' || state.phase === 'waiting') context.save(state.filters, state.page);
  stage.dataset.phase = state.phase;
  if (state.render === 'replace') list.replaceChildren(...state.added.map(reportItem));
  if (state.render === 'replace') viewport.update();
  selection.sync(state.items);
  if (state.busy || operationBusy) list.setAttribute('aria-busy', 'true');
  else list.removeAttribute('aria-busy');
  element('empty').hidden = state.phase !== 'ready' || Boolean(state.total || Object.keys(state.filters).length || state.unreadableCount);
  if (state.phase === 'waiting') status.textContent = 'Preparing your saved reports...';
  else if (state.busy) status.textContent = 'Loading this page of reports...';
  else if (state.error) status.textContent = `${state.error} ${state.items.length ? 'The reports already shown are still available.' : ''} Use Retry loading reports to try again.`;
  else status.textContent = state.total ? `Page ${state.page} of ${state.pageCount}: ${state.items.length} reports on this page. ${state.total} matching reports in total.`
    : Object.keys(state.filters).length ? 'No reports match your filters.'
      : state.unreadableCount ? 'No readable saved reports are available.' : 'No saved reports yet.';
  const filterValues = { light: 'Light', 'deep-tcp-v1': 'Deep', completed: 'Finished', partial: 'Some checks unfinished', failed: 'Failed', cancelled: 'Cancelled', running: 'In progress', queued: 'Waiting' };
  element('applied-filters').textContent = Object.entries(state.filters).map(([name, value]) => `${({q: 'Search', profile: 'Type', state: 'Completion', after: 'From (UTC)', before: 'To (UTC)'})[name]}: ${['profile', 'state'].includes(name) ? filterValues[value] || value : value}`).join(' · ');
  if (state.phase === 'ready') document.title = state.pageCount > 1 ? `Saved reports · Page ${state.page} of ${state.pageCount} · NetGuard AI` : 'Saved reports · NetGuard AI';
  const warning = element('warnings');
  warning.textContent = state.warnings.join(' ');
  warning.hidden = !warning.textContent;
  element('retry').hidden = !state.error;
  element('refresh').hidden = !state.changed;
  element('page-hint').textContent = state.phase === 'ready' && state.items.length
    ? state.pageCount > 1 ? 'This page contains all of its reports. Choose another page to see more.' : 'All matching reports are on this page.'
    : 'Each page contains up to 24 reports. Scrolling does not load another page.';
  syncManagement();
}

const feed = createHistoryFeed({ request, onChange: renderHistory });

element('retry').addEventListener('click', () => { if (!operationBusy) { void feed.retry(); } });
element('refresh').addEventListener('click', () => {
  if (operationBusy) return;
  selection.clear();
  feed.reset(feed.getState().filters, feed.getState().page);
  void feed.load();
});

function openDelete(reports, trigger) {
  if (operationBusy || feed.getState().busy || dialog.open) return;
  const eligible = reports.filter(canDeleteReport);
  if (!eligible.length || eligible.length > 24) return;
  pendingDelete = eligible.map(deletionTarget);
  dialogTrigger = trigger;
  element('delete-title').textContent = `Delete ${eligible.length} report${eligible.length === 1 ? '' : 's'}?`;
  element('delete-list').replaceChildren(...eligible.map(report => {
    const entry = document.createElement('li');
    entry.textContent = reportIdentity(report);
    return entry;
  }));
  element('delete-error').hidden = true;
  syncManagement();
  dialog.showModal();
  element('delete-cancel').focus();
}
function closeDelete(restoreFocus = true) {
  dialog.close();
  pendingDelete = [];
  syncManagement();
  if (restoreFocus) {
    const target = dialogTrigger?.isConnected && !dialogTrigger.disabled ? dialogTrigger : element('results-title');
    target.focus({ preventScroll: true });
  }
}
dialog.addEventListener('cancel', event => {
  event.preventDefault();
  if (!operationBusy) closeDelete();
});
element('delete-cancel').addEventListener('click', () => { if (!operationBusy) closeDelete(); });
element('select-all').addEventListener('change', event => {
  if (operationBusy) return;
  selection.all(event.currentTarget.checked);
  syncManagement();
});
element('delete-selected').addEventListener('click', event => {
  openDelete(feed.getState().items.filter(report => selection.has(report.scan_id)), event.currentTarget);
});

function feedback(message) { element('feedback').textContent = message; }
element('delete-confirm').addEventListener('click', async () => {
  if (operationBusy || !dialog.open || !pendingDelete.length) return;
  const targets = pendingDelete.map(target => ({ ...target }));
  operationBusy = true;
  element('delete-error').hidden = true;
  syncManagement();
  let results;
  try {
    const receipt = await request('/api/reports/delete', {
      method: 'POST', body: JSON.stringify({ reports: targets }), timeoutMs: 60000,
    });
    results = validateDeletionReceipt(receipt, targets);
  } catch (error) {
    // Do not retry a destructive request automatically: its outcome may be unknown.
    element('delete-error').textContent = `${error.message} If the connection was lost, reload the list to check what was removed before trying again.`;
    element('delete-error').hidden = false;
    operationBusy = false;
    syncManagement();
    return;
  }
  const removed = results.filter(item => item.status === 'deleted');
  const absent = results.filter(item => item.status === 'missing');
  const refused = results.filter(item => !['deleted', 'missing'].includes(item.status));
  for (const item of [...removed, ...absent]) selection.set(item.scan_id, false);
  if (removed.length) lastUndo = removed.map(item => item.trash_id);
  feedback(`${removed.length} report${removed.length === 1 ? '' : 's'} deleted from the list. ${removed.length ? 'A recovery copy is kept; use Undo last deletion to restore it. ' : ''}${absent.length ? `${absent.length} had already been removed. ` : ''}${refused.length ? `${refused.length} could not be deleted. ${[...new Set(refused.map(item => item.message).filter(message => typeof message === 'string'))].join(' ')}` : ''}`);
  closeDelete(false);
  await feed.reloadAfterDelete();
  operationBusy = false;
  syncManagement();
  element('feedback').focus({ preventScroll: true });
});
element('undo-delete').addEventListener('click', async () => {
  if (operationBusy || feed.getState().busy || !lastUndo.length) return;
  const ids = [...lastUndo];
  operationBusy = true;
  syncManagement();
  try {
    const receipt = await request('/api/reports/restore', {
      method: 'POST', body: JSON.stringify({ trash_ids: ids }), timeoutMs: 60000,
    });
    const results = validateRestoreReceipt(receipt, ids);
    const restored = results.filter(item => item.status === 'restored');
    lastUndo = results.filter(item => !['restored', 'missing'].includes(item.status)).map(item => item.trash_id);
    feedback(`${restored.length} report${restored.length === 1 ? '' : 's'} restored. ${lastUndo.length ? 'Some reports could not be restored. Existing or changed reports were not overwritten.' : ''}`);
    await feed.reloadAfterDelete();
  } catch (error) { feedback(error.message); }
  finally { operationBusy = false; syncManagement(); element('feedback').focus({ preventScroll: true }); }
});

function selectedFilters() {
  return Object.fromEntries([['q', 'query'], ['profile', 'profile'], ['state', 'state'], ['after', 'after'], ['before', 'before']]
    .map(([field, id]) => [field, element(id).value.trim()]));
}
function clearFilterError() {
  element('filter-error').hidden = true;
  element('before').removeAttribute('aria-invalid');
  element('before-error').hidden = true;
}
filters.addEventListener('submit', event => {
  event.preventDefault();
  if (operationBusy) return;
  clearFilterError();
  const chosen = selectedFilters();
  if (chosen.after && chosen.before && chosen.after > chosen.before) {
    const message = 'The To date must be on or after the From date.';
    element('filter-error-message').textContent = message;
    element('before-error').textContent = message;
    element('before-error').hidden = false;
    element('before').setAttribute('aria-invalid', 'true');
    element('filter-error').hidden = false;
    element('filter-error').focus();
    return;
  }
  selection.clear();
  feed.reset(chosen);
  void feed.load();
});
filters.addEventListener('reset', event => {
  if (operationBusy) { event.preventDefault(); return; }
  clearFilterError();
  selection.clear();
  window.setTimeout(() => { feed.reset(selectedFilters()); void feed.load(); }, 0);
});
if (resumed) {
  for (const [name, id] of [['q', 'query'], ['profile', 'profile'], ['state', 'state'], ['after', 'after'], ['before', 'before']]) element(id).value = resumed.filters[name] || '';
}
feed.reset(resumed?.filters, resumed?.page);
void feed.load();
recovery = startRecoveryBrowser({ document, request, isBusy: () => operationBusy || feed.getState().busy,
  setBusy: value => { operationBusy = value; syncManagement(); },
  onRestored: () => feed.reloadAfterDelete() });
void request('/api/report-capabilities').then(value => {
  if (value.management_version !== 2) throw new Error('The running backend needs updating.');
}).catch(error => {
  element('backend-status').textContent = error.status === 404 || error.message.includes('needs updating')
    ? 'Restart the NetGuard backend task to load the current report-management and recovery features. Saved evidence is unchanged.'
    : `Report-management availability could not be checked. ${error.message} Saved evidence is unchanged.`;
  element('backend-status').hidden = false;
});
