import { deviceLabel, featureLabel, recordedTimeLabel } from './presentation.mjs?v=20261014-dates';
import { deviceResultEntries } from './devices.mjs?v=20261014-reliability';

export function serviceGroups(data) {
  const groups = new Map();
  for (const service of data.services || []) {
    if (service.state !== 'open') continue;
    const device = data.devices?.find(item => item.device_id === service.device_id);
    if (!device) continue;
    const label = featureLabel(service);
    if (!groups.has(label)) groups.set(label, []);
    groups.get(label).push({ service, device });
  }
  return [...groups].sort(([a], [b]) => a.localeCompare(b));
}

export function comparisonEntries(data) {
  return (data.devices || []).map(device => {
    const value = device.comparison;
    if (value) return { device, ...value };
    const older = device.details?.find(item => item.kind === 'history' && item.label === 'Service comparison');
    return { device, status: 'not_compared', reason: older
      ? `This older report has text-only comparison information: ${older.value}`
      : 'We could not compare this device with an earlier completed check. This does not mean nothing changed.' };
  });
}

export function renderReportInsights({ document, data, onShowDevice }) {
  const text = (tag, value) => { const node = document.createElement(tag); node.textContent = value; return node; };
  const comparisons = comparisonEntries(data);
  const available = comparisons.filter(item => item.status === 'available');
  const added = available.reduce((sum, item) => sum + (item.added_count ?? item.added?.length ?? 0), 0);
  const missing = available.reduce((sum, item) => sum + (item.not_observed_count ?? item.not_observed?.length ?? 0), 0);
  document.querySelector('#changes-overview').textContent = available.length
    ? `We compared ${available.length} device${available.length === 1 ? '' : 's'} with earlier finished checks. ${added} feature${added === 1 ? '' : 's'} accepted requests this time but ${added === 1 ? 'was' : 'were'} not recorded doing so earlier. ${missing} previously available feature${missing === 1 ? ' was' : 's were'} not recorded accepting requests this time. ${comparisons.length - available.length} device${comparisons.length - available.length === 1 ? '' : 's'} could not be compared.`
    : 'A comparison with earlier completed checks is not available. The reasons are below. This does not mean nothing changed.';
  const list = document.querySelector('#changes-list');
  list.replaceChildren();
  for (const item of comparisons.slice(0, 254)) {
    const row = text('li', '');
    row.append(text('strong', deviceLabel(item.device)));
    if (item.source_created_at) row.append(text('p', `Earlier check: ${recordedTimeLabel(item.source_created_at)}. This check: ${recordedTimeLabel(item.current_created_at)}.`));
    if (item.status === 'available') {
      const describe = values => values.map(value => `${value.protocol.toUpperCase()} ${value.port}`).join(', ') || 'none';
      row.append(text('p', `Accepted requests this time, not recorded doing so earlier: ${describe(item.added || [])}. Accepted requests earlier, not recorded doing so this time: ${describe(item.not_observed || [])}.`));
      if (item.added_count > (item.added?.length || 0) || item.not_observed_count > (item.not_observed?.length || 0)) row.append(text('p', 'Up to 200 examples per change type are listed; summary totals include all recorded differences.'));
    }
    row.append(text('p', item.reason || 'Comparison limits were not recorded.'));
    if (/^[0-9a-f-]{36}$/i.test(item.source_scan_id || '')) {
      const link = text('a', 'Open the earlier report'); link.href = `/scans/${item.source_scan_id}`; row.append(link);
    }
    list.append(row);
  }
  if (comparisons.length > 254) list.append(text('li', `${comparisons.length - 254} more device comparisons are not shown here. This summary lists up to 254.`));
  if (!comparisons.length) list.append(text('li', 'No saved device results are available to compare.'));
  const features = document.querySelector('#feature-inventory-list');
  features.replaceChildren();
  for (const [label, entries] of serviceGroups(data)) {
    const group = text('li', '');
    const count = new Set(entries.map(item => item.device.device_id)).size;
    group.append(text('h3', `${label} · ${count} device${count === 1 ? '' : 's'}`));
    const rows = document.createElement('ul');
    for (const {service, device} of entries.slice(0, 200)) {
      const row = text('li', `${deviceLabel(device)} · ${service.protocol?.toUpperCase() || 'Protocol not recorded'} ${service.port}. `);
      if (service.product || service.version) row.append(text('span', `Reported software: ${[service.product, service.version].filter(Boolean).join(' ')}. `));
      const button = text('button', 'View this device'); button.type = 'button'; button.className = 'text-button';
      button.addEventListener('click', () => onShowDevice(device.ip)); row.append(button); rows.append(row);
    }
    if (entries.length > 200) rows.append(text('li', `${entries.length - 200} additional responses in this group are recorded in the technical device details; this summary lists up to 200.`));
    group.append(rows); features.append(group);
  }
  if (!features.childElementCount) features.append(text('li', 'No features were recorded accepting requests. Not every possible feature was checked. This does not prove the devices are safe.'));
  return { deviceCount: deviceResultEntries(data).length };
}
