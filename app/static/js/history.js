import { request } from './api.js';

const list = document.querySelector('#history-list');
const status = document.querySelector('#history-status');
const previous = document.querySelector('#history-previous');
const next = document.querySelector('#history-next');
let offset = 0;

async function loadHistory() {
  previous.disabled = true;
  next.disabled = true;
  try {
    const page = await request(`/api/scans?source=live&offset=${offset}&limit=20`);
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
        link.textContent = `${new Date(report.created_at).toLocaleString()} — ${labels[report.state] || report.state} — ${report.device_count} devices, ${report.finding_count} findings`;
        item.append(link);
      }
      list.append(item);
    }
    status.textContent = page.total ? `Showing ${offset + 1}–${offset + page.items.length} of ${page.total} reports.` : 'No saved reports yet.';
    previous.disabled = offset === 0;
    next.disabled = offset + page.items.length >= page.total;
  } catch (error) {
    status.textContent = error.message;
  }
}
previous.addEventListener('click', () => { offset = Math.max(0, offset - 20); loadHistory(); });
next.addEventListener('click', () => { offset += 20; loadHistory(); });
loadHistory();
