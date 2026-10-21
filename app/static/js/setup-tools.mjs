import { request } from './api.js?v=20261018-cve-deadline';
import { recordedTimeLabel } from './presentation.mjs?v=20261014-dates';

let pickerLoaded = false;
let pickerBusy = false;
let pickerItems = [];
let pickerNotice = '';
let pickerWarnings = '';

function showPickerContext() {
  const select = document.querySelector('#recentDeviceSelect');
  const target = document.querySelector('#deepHostInput').value.trim();
  const item = pickerItems.find(candidate => candidate.ip === target);
  select.value = item ? target : '';
  const note = document.querySelector('#recentDeviceNote');
  let notice = pickerNotice;
  if (target && !item) {
    notice += ' Your entered address is not in this list. It has been kept in the address field; check it before scanning.';
  }
  if (pickerWarnings) notice += ` ${pickerWarnings}`;
  if (note.textContent !== notice) note.textContent = notice;
  const details = document.querySelector('#recentDeviceDetails');
  if (!details) return;
  details.hidden = !target;
  const time = item ? recordedTimeLabel(item.observed_at, '') : '';
  const context = item
    ? `${item.last_check || 'Check status not recorded'}. ${time ? `Saved ${time}.` : 'The recording time is unavailable.'} This is saved information, not a check of whether the device is connected now.`
    : target
      ? 'You are using an entered address. No saved device check from this list is selected.'
      : 'Choose a device to see its last saved check, or enter an address below.';
  if (details.textContent !== context) details.textContent = context;
}

export async function configurePicker(deep, refresh = false) {
  const panel = document.querySelector('#recentDevicePanel');
  panel.hidden = !deep;
  if (!deep || pickerBusy) return;
  if (pickerLoaded && !refresh) {
    showPickerContext();
    return;
  }
  pickerBusy = true;
  panel.setAttribute('aria-busy', 'true');
  const select = document.querySelector('#recentDeviceSelect');
  try {
    const data = await request('/api/recent-devices');
    if (!Array.isArray(data?.items) || data.items.some(item => !item || typeof item.ip !== 'string')) {
      throw new Error('The saved device list could not be read.');
    }
    pickerItems = data.items;
    select.replaceChildren();
    const manual = document.createElement('option');
    manual.value = ''; manual.textContent = 'Choose a recent device, or enter an address below';
    select.append(manual);
    for (const item of pickerItems) {
      const option = document.createElement('option');
      option.value = item.ip;
      option.textContent = `${item.name || 'Unnamed device'} — ${item.ip}`;
      select.append(option);
    }
    pickerNotice = pickerItems.length
      ? 'From Light reports saved in the last seven days for this network. Addresses may have changed; confirm the device is yours. Choosing a device does not start a scan.'
      : 'No recent Light results for this network. You can enter an authorised device address manually.';
    pickerWarnings = data.warnings?.length ? data.warnings.join(' ') : '';
    pickerLoaded = true;
    // Read the target now: typing while the list loads must not be overwritten.
    showPickerContext();
  } catch (error) {
    pickerNotice = `Recent devices unavailable. ${error.message} You can still enter an address manually.`;
    showPickerContext();
  } finally {
    pickerBusy = false;
    panel.setAttribute('aria-busy', 'false');
  }
}

export function startSetupTools() {
  document.querySelector('#deepHostInput').addEventListener('input', showPickerContext);
  document.querySelector('#recentDeviceSelect').addEventListener('change', event => {
    if (document.querySelector('#deepHostInput').disabled) return;
    document.querySelector('#deepHostInput').value = event.target.value;
    showPickerContext();
  });
  document.querySelector('#refreshDeviceChoices').addEventListener('click', () => configurePicker(true, true));
  const rows = new Map();
  async function refreshRunning() {
    if (document.hidden) { window.setTimeout(refreshRunning, 4000); return; }
    const panel = document.querySelector('#runningScans');
    try {
      const data = await request('/api/running-scans');
      const overviewNote = document.querySelector('#runningScansNote');
      if (overviewNote.textContent.startsWith('Running overview unavailable.')) overviewNote.textContent = '';
      if (!Array.isArray(data?.items)) throw new Error('The running overview could not be read.');
      panel.dataset.snapshot = JSON.stringify(data.items);
      const currentIds = new Set(data.items.map(item => item.scan_id));
      let removedFocus = false;
      for (const [id, entry] of rows) {
        if (!currentIds.has(id)) {
          removedFocus ||= entry.row.contains(document.activeElement);
          entry.row.remove();
          rows.delete(id);
        }
      }
      panel.hidden = !data.items.length;
      for (const item of data.items) {
        const label = item.profile === 'deep-tcp-v1' ? 'Deep' : item.profile === 'light' ? 'Light' : 'Saved';
        const target = item.target?.cidr || item.target?.hosts?.join(', ') || 'Target unavailable';
        const phase = ({ queued: 'Waiting to start', discovery: 'Looking for devices',
          service_scan: 'Checking device connections (checks may wait for a scanner slot)',
          enrichment: 'Gathering device details', analysis: item.analysis_progress?.state === 'waiting'
            ? 'Waiting for local AI' : 'Making results easier to understand', finished: 'Finished',
          unavailable: 'Saved progress temporarily unavailable' })[item.phase] || item.phase;
        const description = `${label}: ${target}. ${phase}. ${item.completed ?? 0} of ${item.total ?? 0} device checks finished. Started ${recordedTimeLabel(item.started_at)}.`;
        const existing = rows.get(item.scan_id);
        if (existing) {
          if (existing.text.textContent !== description) existing.text.textContent = description;
          continue; // Stable nodes retain focus and a pending cancellation across polls.
        }
        const row = document.createElement('article');
        row.dataset.scanId = item.scan_id;
        const text = document.createElement('p');
        text.textContent = description;
        const link = document.createElement('a');
        link.href = `/#scan=${encodeURIComponent(item.scan_id)}`;
        link.target = '_blank'; link.rel = 'noopener'; link.textContent = `Open ${label} progress`;
        const report = document.createElement('a');
        report.href = `/scans/${encodeURIComponent(item.scan_id)}`;
        report.target = '_blank'; report.rel = 'noopener'; report.textContent = 'Open saved report';
        const cancel = document.createElement('button');
        cancel.type = 'button'; cancel.className = 'text-button'; cancel.textContent = `Cancel ${label} scan`;
        const failure = document.createElement('p');
        failure.hidden = true; failure.className = 'status-message status-warning'; failure.setAttribute('role', 'alert');
        cancel.addEventListener('click', async () => {
          if (!window.confirm(`Cancel only this ${label} scan of ${target}? Saved observations will remain.`)) return;
          cancel.disabled = true;
          failure.hidden = true;
          try {
            await request(`/api/live-scans/${item.scan_id}`, { method: 'DELETE' });
            cancel.textContent = 'Cancellation requested';
          } catch (error) { failure.textContent = `${error.message} Cancellation was not confirmed; you can try again. Saved observations are kept.`; failure.hidden = false; cancel.disabled = false; }
        });
        const actions = document.createElement('div');
        actions.className = 'running-scan-actions';
        actions.setAttribute('role', 'group');
        actions.setAttribute('aria-label', `Actions for ${label} scan of ${target}`);
        actions.append(link, report, cancel);
        row.append(text, actions, failure);
        rows.set(item.scan_id, { row, text });
        panel.append(row);
      }
      if (removedFocus) {
        const note = document.querySelector('#runningScansNote');
        note.textContent = 'That scan is no longer running. Its saved observations can be opened from Saved reports.';
        note.tabIndex = -1;
        note.focus({ preventScroll: true });
      }
    } catch (error) { document.querySelector('#runningScansNote').textContent = `Running overview unavailable. ${error.message}`; }
    window.setTimeout(refreshRunning, 4000);
  }
  refreshRunning();
}
