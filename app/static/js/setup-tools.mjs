import { request } from './api.js?v=20261001-library-fixes';

let pickerLoaded = false;
let pickerBusy = false;
export async function configurePicker(deep, refresh = false) {
  const panel = document.querySelector('#recentDevicePanel');
  panel.hidden = !deep;
  if (!deep || pickerBusy || (pickerLoaded && !refresh)) return;
  pickerBusy = true;
  const select = document.querySelector('#recentDeviceSelect');
  const note = document.querySelector('#recentDeviceNote');
  try {
    const data = await request('/api/recent-devices');
    // Read after the request: a user may have edited the target while it was loading.
    const target = document.querySelector('#deepHostInput').value.trim();
    select.replaceChildren();
    const manual = document.createElement('option');
    manual.value = ''; manual.textContent = 'Choose a recent device, or enter an address below';
    select.append(manual);
    for (const item of data.items) {
      const option = document.createElement('option');
      option.value = item.ip;
      option.textContent = `${item.name} — ${item.ip} — ${item.last_check || 'Check status not recorded'} — saved ${new Date(item.observed_at).toLocaleString()}`;
      select.append(option);
    }
    note.textContent = data.items.length
      ? 'From Light reports in the last seven days in this configured network. Addresses may have changed; confirm the device is yours. Selecting does not start a scan.'
      : 'No recent Light observations in this configured network. You can enter an authorised device address manually.';
    pickerLoaded = true;
    select.value = data.items.some(item => item.ip === target) ? target : '';
    if (target && !select.value) {
      note.textContent += ' Your entered address is not in this list. It has been kept in the address field; check it before scanning.';
    }
    if (data.warnings?.length) note.textContent += ` ${data.warnings.join(' ')}`;
  } catch (error) { note.textContent = `Recent devices unavailable. ${error.message} You can still enter an address manually.`; }
  finally { pickerBusy = false; }
}

export function startSetupTools() {
  document.querySelector('#deepHostInput').addEventListener('input', event => {
    const select = document.querySelector('#recentDeviceSelect');
    const target = event.target.value.trim();
    select.value = Array.from(select.options).some(option => option.value === target) ? target : '';
  });
  document.querySelector('#recentDeviceSelect').addEventListener('change', event => {
    document.querySelector('#deepHostInput').value = event.target.value;
  });
  document.querySelector('#refreshDeviceChoices').addEventListener('click', () => configurePicker(true, true));
  async function refreshRunning() {
    if (document.hidden) { window.setTimeout(refreshRunning, 4000); return; }
    const panel = document.querySelector('#runningScans');
    try {
      const data = await request('/api/running-scans');
      document.querySelector('#runningScansNote').textContent = '';
      // Avoid replacing focused cancel/link controls on every unchanged poll.
      const snapshot = JSON.stringify(data.items);
      if (panel.dataset.snapshot !== snapshot) {
        panel.dataset.snapshot = snapshot;
        panel.replaceChildren();
        panel.hidden = !data.items.length;
        for (const item of data.items) {
          const row = document.createElement('article');
          const label = item.profile === 'deep-tcp-v1' ? 'Deep' : item.profile === 'light' ? 'Light' : 'Saved';
          const target = item.target?.cidr || item.target?.hosts?.join(', ') || 'Target unavailable';
          const phase = ({ queued: 'Waiting to start', discovery: 'Looking for devices',
            service_scan: 'Checking device connections (checks may wait for a scanner slot)',
            enrichment: 'Gathering device details', analysis: item.analysis_progress?.state === 'waiting'
              ? 'Waiting for local AI' : 'Making results easier to understand', finished: 'Finished',
            unavailable: 'Saved progress temporarily unavailable' })[item.phase] || item.phase;
          const text = document.createElement('p');
          text.textContent = `${label}: ${target}. ${phase}. ${item.completed ?? 0} of ${item.total ?? 0} device checks finished. Started ${item.started_at ? new Date(item.started_at).toLocaleString() : 'time unavailable'}.`;
          const link = document.createElement('a');
          link.href = `/#scan=${encodeURIComponent(item.scan_id)}`;
          link.target = '_blank'; link.rel = 'noopener'; link.textContent = `Open ${label} progress`;
          const report = document.createElement('a');
          report.href = `/scans/${encodeURIComponent(item.scan_id)}`;
          report.target = '_blank'; report.rel = 'noopener'; report.textContent = 'Open saved report';
          const cancel = document.createElement('button');
          cancel.type = 'button'; cancel.className = 'text-button'; cancel.textContent = `Cancel ${label} scan`;
          cancel.addEventListener('click', async () => {
            if (!window.confirm(`Cancel only this ${label} scan of ${target}? Saved observations will remain.`)) return;
            cancel.disabled = true;
            try {
              await request(`/api/live-scans/${item.scan_id}`, { method: 'DELETE' });
              cancel.textContent = 'Cancellation requested';
            } catch (error) { text.textContent = error.message; cancel.disabled = false; }
          });
          row.append(text, link, document.createTextNode(' · '), report, cancel);
          panel.append(row);
        }
      }
    } catch (error) { document.querySelector('#runningScansNote').textContent = `Running overview unavailable. ${error.message}`; }
    window.setTimeout(refreshRunning, 4000);
  }
  refreshRunning();
}
