import { request } from './api.js?v=20261001-network-recovery';
import { recordedTimeLabel } from './presentation.mjs?v=20261008-dates';

const list = document.querySelector('#history-list');
const status = document.querySelector('#history-status');
const previous = document.querySelector('#history-previous');
const next = document.querySelector('#history-next');
const empty = document.querySelector('#history-empty');
const filterError = document.querySelector('#history-filter-error');
let offset = 0;
let generation = 0;
const filters = document.querySelector('#history-filters');
document.querySelector('#storageUsageButton').addEventListener('click', async (event) => {
  const output = document.querySelector('#storageUsage');
  event.currentTarget.disabled = true;
  output.textContent = 'Measuring saved data…';
  try {
    const usage = await request('/api/storage-usage');
    output.textContent = `${(usage.bytes / 1048576).toFixed(1)} MiB in ${usage.files} saved files. ${usage.warning || 'No files were removed.'}`;
  } catch (error) { output.textContent = error.message; }
  finally { document.querySelector('#storageUsageButton').disabled = false; }
});

async function loadHistory() {
  const current = ++generation;
  previous.disabled = true;
  next.disabled = true;
  status.textContent = 'Loading matching reports…';
  list.setAttribute('aria-busy', 'true');
  empty.hidden = true;
  try {
    const params = new URLSearchParams({ offset, limit: 20 });
    for (const [field, id] of [['q', 'query'], ['profile', 'profile'], ['state', 'state'], ['after', 'after'], ['before', 'before']]) {
      const value = document.querySelector(`#history-${id}`).value.trim();
      if (value) params.set(field, value);
    }
    const page = await request(`/api/reports?${params}`);
    if (current !== generation) return;
    list.replaceChildren();
    for (const report of page.items) {
      const item = document.createElement('li');
      if (report.storage_status !== 'ok') {
        item.className = 'status-message status-warning';
        item.textContent = 'A saved report could not be read. Its files have been preserved.';
      } else {
        const link = document.createElement('a');
        link.href = `/scans/${encodeURIComponent(report.scan_id)}`;
        const labels = { completed: 'Finished', partial: 'Some checks unfinished', failed: 'Scan failed',
          cancelled: 'Cancelled', running: 'In progress', queued: 'Waiting' };
        const title = document.createElement('strong');
        title.textContent = report.title || `${report.profile === 'deep-tcp-v1' ? 'Deep' : report.profile === 'light' ? 'Light' : 'Scan'} report`;
        const meta = document.createElement('span');
        meta.className = 'history-report-meta';
        meta.textContent = `${report.profile === 'deep-tcp-v1' ? 'Deep' : report.profile === 'light' ? 'Light' : 'Scan'} · ${recordedTimeLabel(report.created_at, 'Date unavailable')} · ${labels[report.state] || report.state}`;
        const counts = document.createElement('span');
        counts.className = 'history-report-counts';
        counts.textContent = `${report.device_count} device${report.device_count === 1 ? '' : 's'} recorded · ${report.finding_count} review item${report.finding_count === 1 ? '' : 's'}`;
        link.append(title, meta, counts);
        item.append(link);
      }
      list.append(item);
    }
    const filtered = ['q', 'profile', 'state', 'after', 'before'].some(key => params.has(key));
    empty.hidden = Boolean(page.total || filtered || page.unreadable_count);
    status.textContent = page.total ? `Showing ${offset + 1}–${offset + page.items.length} of ${page.total} reports.`
      : filtered ? 'No reports match your filters.'
        : page.unreadable_count ? 'No readable saved reports are available.' : 'No saved reports yet.';
    const warning = document.querySelector('#history-warnings');
    warning.textContent = page.warnings?.join(' ') || '';
    warning.hidden = !warning.textContent;
    previous.disabled = offset === 0;
    next.disabled = offset + page.items.length >= page.total;
  } catch (error) {
    if (current !== generation) return;
    status.textContent = `${error.message} Previous results, if any, are still shown; try Search reports again.`;
    previous.disabled = offset === 0;
  } finally {
    if (current === generation) list.removeAttribute('aria-busy');
  }
}
previous.addEventListener('click', () => { offset = Math.max(0, offset - 20); loadHistory(); });
next.addEventListener('click', () => { offset += 20; loadHistory(); });
function clearFilterError() {
  filterError.hidden = true;
  document.querySelector('#history-before').removeAttribute('aria-invalid');
  document.querySelector('#history-before-error').hidden = true;
}
filters.addEventListener('submit', event => {
  event.preventDefault();
  clearFilterError();
  const after = document.querySelector('#history-after').value;
  const before = document.querySelector('#history-before').value;
  if (after && before && after > before) {
    const message = 'The To date must be on or after the From date.';
    document.querySelector('#history-filter-error-message').textContent = message;
    const error = document.querySelector('#history-before-error');
    error.textContent = message;
    error.hidden = false;
    document.querySelector('#history-before').setAttribute('aria-invalid', 'true');
    filterError.hidden = false;
    filterError.focus();
    return;
  }
  offset = 0;
  loadHistory();
});
filters.addEventListener('reset', () => { clearFilterError(); offset = 0; window.setTimeout(loadHistory, 0); });
loadHistory();
