import { request } from './api.js?v=20261001-library-fixes';

const list = document.querySelector('#history-list');
const status = document.querySelector('#history-status');
const previous = document.querySelector('#history-previous');
const next = document.querySelector('#history-next');
let offset = 0;
let generation = 0;
const filters = document.querySelector('#history-filters');

async function loadHistory() {
  const current = ++generation;
  previous.disabled = true;
  next.disabled = true;
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
        item.textContent = 'A saved report could not be read. Its files have been preserved.';
      } else {
        const link = document.createElement('a');
        link.href = `/scans/${encodeURIComponent(report.scan_id)}`;
        const labels = { completed: 'Finished', partial: 'Some checks unfinished', failed: 'Scan failed',
          cancelled: 'Cancelled', running: 'In progress', queued: 'Waiting' };
        link.textContent = `${report.title ? report.title + ' — ' : ''}${report.profile === 'deep-tcp-v1' ? 'Deep' : report.profile === 'light' ? 'Light' : 'Scan'} — ${new Date(report.created_at).toLocaleString()} — ${labels[report.state] || report.state} — ${report.device_count} devices, ${report.finding_count} findings`;
        item.append(link);
      }
      list.append(item);
    }
    const filtered = ['q', 'profile', 'state', 'after', 'before'].some(key => params.has(key));
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
    status.textContent = error.message;
    previous.disabled = offset === 0;
  }
}
previous.addEventListener('click', () => { offset = Math.max(0, offset - 20); loadHistory(); });
next.addEventListener('click', () => { offset += 20; loadHistory(); });
filters.addEventListener('submit', event => { event.preventDefault(); offset = 0; loadHistory(); });
filters.addEventListener('reset', () => { offset = 0; window.setTimeout(loadHistory, 0); });
loadHistory();
