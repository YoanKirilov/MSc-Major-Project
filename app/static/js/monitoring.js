import { request } from './api.js?v=20261001-network-recovery';
import { recordedTimeLabel } from './presentation.mjs?v=20261014-dates';
import { createMonitoringModel, intervalLabel, boundedPrivateScope } from './monitoring-model.mjs?v=20261014-periodic';

const get = name => document.querySelector(`#monitor-${name}`);
const interval = get('interval');
const authorised = get('authorised');
const summary = get('summary');
const error = get('error');
summary.tabIndex = error.tabIndex = -1;
authorised.setAttribute('aria-describedby', 'monitor-scope monitor-error');
let eventSignature = '';
const reasons = { restarted: 'The app restarted; fresh permission is required.',
  network_changed: 'The connection changed; checks stopped and fresh permission is required.',
  network_unavailable: 'The authorised network is unavailable; checks stopped.',
  storage_unavailable: 'Saved configuration is unavailable; checks stopped.',
  submission_failed: 'A periodic check could not be submitted; checks stopped.' };
const outcomes = { queued: 'Queued', completed: 'Finished', partial: 'Some checks unfinished',
  failed: 'Failed', cancelled: 'Cancelled', unavailable: 'Result unavailable' };

function renderEvents(events) {
  const signature = JSON.stringify(events);
  if (signature === eventSignature) return;
  eventSignature = signature;
  const list = get('events');
  list.replaceChildren();
  if (!events.length) {
    const row = document.createElement('li');
    row.textContent = 'No recent local periodic-check events are recorded.';
    list.append(row);
    return;
  }
  for (const event of events) {
    const row = document.createElement('li');
    const label = document.createElement('p');
    label.textContent = `${recordedTimeLabel(event.occurred_at)} · ${event.message}`;
    row.append(label);
    if (event.counts) {
      const counts = document.createElement('p');
      const labels = { device_count: 'Recorded devices', finding_count: 'Review items',
        completed_count: 'Finished device checks', unfinished_count: 'Unfinished checks',
        comparable_device_count: 'Comparable devices', changed_device_count: 'Devices with different recorded observations' };
      counts.textContent = Object.entries(labels).filter(([key]) => event.counts[key] !== undefined)
        .map(([key, label]) => `${label}: ${event.counts[key]}`).join(' · ');
      if (counts.textContent) row.append(counts);
    }
    if (event.scan_id) {
      const link = document.createElement('a');
      link.href = `/scans/${encodeURIComponent(event.scan_id)}`;
      link.textContent = 'Open this saved check';
      row.append(link);
    }
    list.append(row);
  }
}
function render(state) {
  const saved = state.status;
  const locked = state.loading || state.saving;
  get('form').setAttribute('aria-busy', String(locked));
  interval.disabled = locked || !saved || saved.revision === null;
  if (![...interval.options].some(option => Number(option.value) === state.draftInterval)) {
    const option = document.createElement('option');
    option.value = String(state.draftInterval);
    option.textContent = `${intervalLabel(state.draftInterval)} (saved)`;
    interval.append(option);
  }
  interval.value = String(state.draftInterval);
  authorised.checked = state.authorised;
  authorised.disabled = !state.canAuthorise;
  get('start').disabled = !state.canEnable;
  get('start').textContent = state.saving ? 'Saving periodic-check setting…'
    : saved?.enabled ? 'Update periodic checks' : 'Enable periodic checks';
  get('stop').disabled = !state.canStop;
  get('reload').disabled = locked;
  error.textContent = state.error;
  error.hidden = !state.error;
  const scope = saved?.current_scope;
  get('scope').textContent = scope
    ? `Network at the last status reload: ${scope}. Confirm this range before enabling repeated checks. ${saved.scope && saved.scope !== scope ? `Previously authorised range: ${saved.scope}. ` : ''}Reload this status after changing your connection or network settings.`
    : 'No effective private network is available for periodic checks. Reload status after the connection is ready.';
  if (state.saving) summary.textContent = 'Saving the periodic-check setting… No request is repeated automatically.';
  else if (state.loading) summary.textContent = 'Loading periodic-check status… Permission must be checked again after this reload.';
  else if (saved) {
    const parts = [saved.enabled
      ? `Periodic checks are enabled for ${saved.scope || 'the recorded authorised network'}, every ${intervalLabel(saved.interval_minutes)}.`
      : 'Periodic checks are off.'];
    if (saved.pause_reason) parts.push(reasons[saved.pause_reason] || 'Checks stopped; review the connection and authorise again if appropriate.');
    if (saved.configuration_error) parts.push(`Periodic checks are unavailable: ${saved.configuration_error}`);
    else if (!saved.available || !boundedPrivateScope(scope)) parts.push('A bounded private network and available local scanner are required to enable checks.');
    if (saved.enabled && saved.next_check_at) parts.push(`Next scheduled check: ${recordedTimeLabel(saved.next_check_at)}. Actual start may wait for a scanner slot.`);
    if (saved.last_outcome) parts.push(`Last recorded outcome: ${outcomes[saved.last_outcome]}.`);
    if (state.intervalDirty) parts.push(`Your unsaved interval choice is ${intervalLabel(state.draftInterval)}; the saved setting above has not changed.`);
    if (state.notice) parts.push(state.notice);
    summary.replaceChildren(document.createTextNode(parts.join(' ')));
    if (saved.last_scan_id) {
      const link = document.createElement('a');
      link.href = `/scans/${encodeURIComponent(saved.last_scan_id)}`;
      link.textContent = ' Open last saved check';
      summary.append(link);
    }
  } else summary.textContent = 'Periodic-check status is unavailable. Reload it before changing settings; no check was enabled by this page.';
  if (saved) renderEvents(saved.events);
  if (state.action === 'saved') summary.focus({ preventScroll: true });
  if (state.action === 'save-error') error.focus({ preventScroll: true });
}
const monitoring = createMonitoringModel({ request, onChange: render });
interval.addEventListener('change', () => monitoring.chooseInterval(interval.value));
authorised.addEventListener('change', () => monitoring.authorise(authorised.checked));
get('form').addEventListener('submit', event => { event.preventDefault(); void monitoring.enable(); });
get('stop').addEventListener('click', () => void monitoring.stop());
get('reload').addEventListener('click', async () => {
  const loaded = await monitoring.load();
  (loaded ? summary : error).focus({ preventScroll: true });
});
for (const id of ['scope-mode', 'allowed-network', 'interface-select']) {
  document.getElementById(id)?.addEventListener('change', () => monitoring.invalidateScope());
  if (id === 'allowed-network') document.getElementById(id)?.addEventListener('input', () => monitoring.invalidateScope());
}
document.getElementById('settings-form')?.addEventListener('submit', () => monitoring.invalidateScope());
void monitoring.load();
