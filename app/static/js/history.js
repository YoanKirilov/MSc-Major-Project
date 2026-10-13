import { request } from './api.js?v=20261001-network-recovery';
import { recordedTimeLabel } from './presentation.mjs?v=20261008-dates';
import { createHistoryFeed } from './history-feed.mjs?v=20261013-one-at-a-time';

const list = document.querySelector('#history-list');
const status = document.querySelector('#history-status');
const more = document.querySelector('#history-load-more');
const moreHint = document.querySelector('#history-more-hint');
const sentinel = document.querySelector('#history-sentinel');
const stage = document.querySelector('#history-scroll-stage');
const empty = document.querySelector('#history-empty');
const filterError = document.querySelector('#history-filter-error');
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

function reportItem(report) {
  const item = document.createElement('li');
  if (report.storage_status !== 'ok') {
    item.className = 'status-message status-warning';
    item.textContent = 'A saved report could not be read. Its files have been preserved.';
    return item;
  }
  const link = document.createElement('a');
  link.href = `/scans/${encodeURIComponent(report.scan_id)}`;
  link.dataset.profile = ['light', 'deep-tcp-v1'].includes(report.profile) ? report.profile : 'unknown';
  const labels = { completed: 'Finished', partial: 'Some checks unfinished', failed: 'Scan failed',
    cancelled: 'Cancelled', running: 'In progress', queued: 'Waiting' };
  const profile = report.profile === 'deep-tcp-v1' ? 'Deep' : report.profile === 'light' ? 'Light' : 'Scan';
  const title = document.createElement('strong');
  title.textContent = report.title || `${profile} report`;
  const meta = document.createElement('span');
  meta.className = 'history-report-meta';
  meta.textContent = `${profile} · ${recordedTimeLabel(report.created_at, 'Date unavailable')} · ${labels[report.state] || report.state}`;
  const counts = document.createElement('span');
  counts.className = 'history-report-counts';
  counts.textContent = `${report.device_count} device${report.device_count === 1 ? '' : 's'} recorded · ${report.finding_count} review item${report.finding_count === 1 ? '' : 's'}`;
  link.append(title, meta, counts);
  item.append(link);
  return item;
}

function renderHistory(state) {
  stage.dataset.phase = state.phase;
  stage.dataset.hasMore = String(state.hasMore);
  const needsRefresh = state.changed && !state.hasMore && !state.busy && !state.error;
  if (state.render === 'replace') list.replaceChildren(...state.added.map(reportItem));
  else if (state.render === 'append') list.append(...state.added.map(reportItem));
  if (state.busy) list.setAttribute('aria-busy', 'true');
  else list.removeAttribute('aria-busy');
  empty.hidden = state.phase !== 'ready' || Boolean(state.total || Object.keys(state.filters).length || state.unreadableCount);
  if (state.phase === 'waiting') status.textContent = Object.keys(state.filters).length
    ? 'Filters are ready. Scroll down to see matching reports one at a time.'
    : 'Scroll down to reveal saved reports one at a time.';
  else if (state.busy) status.textContent = 'Loading the next report…';
  else if (state.error) status.textContent = `${state.error} ${state.items.length ? 'The reports already shown are still available.' : ''} Use Retry loading reports to try again.`;
  else if (state.items.length > state.total) status.textContent = `${state.items.length} previously loaded reports are shown. Use Search reports to refresh the changed list.`;
  else status.textContent = state.total ? `Showing ${state.items.length} of ${state.total} reports.`
    : Object.keys(state.filters).length ? 'No reports match your filters.'
      : state.unreadableCount ? 'No readable saved reports are available.' : 'No saved reports yet.';
  const warning = document.querySelector('#history-warnings');
  warning.textContent = state.warnings.join(' ');
  warning.hidden = !warning.textContent;
  more.disabled = state.busy || (!state.hasMore && !state.error && !needsRefresh);
  more.textContent = state.busy ? 'Loading report…' : state.error ? 'Retry loading reports'
    : state.phase === 'waiting' ? 'Scroll to reports' : state.hasMore ? 'Show next report'
      : needsRefresh ? 'Refresh reports' : 'All matching reports shown';
  more.hidden = state.phase === 'ready' && !state.items.length && !needsRefresh;
  moreHint.textContent = state.error ? 'Retry keeps the reports already on this page.'
    : state.phase === 'waiting' ? 'Reports appear as you scroll down. You can also use this button.'
      : state.hasMore ? 'Keep scrolling down to show one more report, or use the button.'
      : needsRefresh ? 'The list changed. Refresh it to check for missing or new reports.'
        : state.items.length ? 'You have reached the end of this list.' : '';
  moreHint.hidden = !moreHint.textContent;
}

const feed = createHistoryFeed({ request, onChange: renderHistory });
// One wheel burst, touch contact or non-repeating scroll key is one gesture.
// Consume it before awaiting the request: momentum and responses cannot auto-fill.
let lastScrollY = window.scrollY;
let gesture = null;
let lastWheelAt = 0;
let touchY = null;
let touchGestureStarted = false;
function beginGesture(source) { gesture = { source, used: false, expires: Date.now() + 1500 }; }
function clearGesture() { gesture = null; lastWheelAt = 0; lastScrollY = window.scrollY; }
async function revealOne(focusAdded = false, retry = false) {
  const previousCount = list.children.length;
  const loaded = await (retry ? feed.retry() : feed.more());
  if (loaded && focusAdded) {
    const firstAdded = list.children[previousCount]?.querySelector('a');
    if (firstAdded) firstAdded.focus();
    else status.focus();
  }
}
function revealForGesture(actualDownwardScroll = false) {
  const state = feed.getState();
  if (!gesture || gesture.used || Date.now() > gesture.expires) return;
  if (state.phase === 'waiting' && !actualDownwardScroll) return;
  if (sentinel.getBoundingClientRect().top > window.innerHeight + 80) return;
  gesture.used = true;
  if (state.hasMore && !state.busy) revealOne(gesture.source === 'button');
}
window.addEventListener('wheel', event => {
  if (event.deltaY <= 0 || event.ctrlKey) { gesture = null; return; }
  const now = Date.now();
  if (gesture?.source !== 'wheel' || now - lastWheelAt > 300) beginGesture('wheel');
  lastWheelAt = now;
  gesture.expires = now + 1500;
  revealForGesture();
}, { passive: true });
window.addEventListener('touchstart', event => {
  touchY = event.touches[0]?.clientY ?? null;
  touchGestureStarted = false;
  gesture = null;
}, { passive: true });
window.addEventListener('touchmove', event => {
  const nextY = event.touches[0]?.clientY;
  if (touchY !== null && nextY < touchY) {
    if (!touchGestureStarted) { beginGesture('touch'); touchGestureStarted = true; }
    if (gesture?.source === 'touch') {
      gesture.expires = Date.now() + 1500;
      revealForGesture();
    }
  }
  touchY = nextY ?? null;
}, { passive: true });
window.addEventListener('keydown', event => {
  if (event.target?.matches('input, textarea, select, [contenteditable="true"]')) return;
  if (event.repeat) return;
  if (['ArrowDown', 'PageDown', 'End'].includes(event.key)
    || (event.key === ' ' && !event.shiftKey && !event.target?.matches('button'))) {
    beginGesture('key');
    revealForGesture();
  }
});
window.addEventListener('scroll', () => {
  const currentY = window.scrollY;
  const scrollingDown = currentY > lastScrollY;
  lastScrollY = currentY;
  if (scrollingDown) revealForGesture(true);
}, { passive: true });

more.addEventListener('click', () => {
  const state = feed.getState();
  clearGesture();
  if (state.changed && !state.hasMore && !state.error) {
    feed.reset(state.filters);
    return;
  }
  if (state.phase === 'waiting') {
    beginGesture('button');
    const top = Math.max(window.scrollY + 80, stage.getBoundingClientRect().top + window.scrollY + 24);
    window.scrollTo({ top, behavior: 'instant' });
    return;
  }
  revealOne(true, Boolean(state.error));
});

function selectedFilters() {
  return Object.fromEntries([['q', 'query'], ['profile', 'profile'], ['state', 'state'], ['after', 'after'], ['before', 'before']]
    .map(([field, id]) => [field, document.querySelector(`#history-${id}`).value.trim()]));
}
function clearFilterError() {
  filterError.hidden = true;
  document.querySelector('#history-before').removeAttribute('aria-invalid');
  document.querySelector('#history-before-error').hidden = true;
}
filters.addEventListener('submit', event => {
  event.preventDefault();
  clearFilterError();
  const selection = selectedFilters();
  if (selection.after && selection.before && selection.after > selection.before) {
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
  clearGesture();
  feed.reset(selection);
});
filters.addEventListener('reset', () => {
  clearFilterError();
  clearGesture();
  window.setTimeout(() => feed.reset(selectedFilters()), 0);
});
feed.reset();
