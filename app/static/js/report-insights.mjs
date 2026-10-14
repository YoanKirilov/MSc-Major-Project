import { deviceLabel, featureLabel, recordedTimeLabel } from './presentation.mjs?v=20261014-dates';
import { deviceResultEntries } from './devices.mjs?v=20261014-reliability';

export function shortcutMatches(device, data, mode = 'all') {
  const target = data.coverage?.targets?.find(item => item.ip === device.ip);
  if (mode === 'unnamed') return !device.user_nickname && !device.hostname;
  if (mode === 'unfinished') return target?.service_status !== 'completed';
  if (mode === 'review') return Boolean(device.device_id && data.findings?.some(item => item.device_id === device.device_id));
  return true;
}

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
      : 'No structured comparison was saved. This does not establish that nothing changed.' };
  });
}

export function renderReportInsights({ document, data, onShowDevice }) {
  const text = (tag, value) => { const node = document.createElement(tag); node.textContent = value; return node; };
  const comparisons = comparisonEntries(data);
  const available = comparisons.filter(item => item.status === 'available');
  const added = available.reduce((sum, item) => sum + (item.added_count ?? item.added?.length ?? 0), 0);
  const missing = available.reduce((sum, item) => sum + (item.not_observed_count ?? item.not_observed?.length ?? 0), 0);
  document.querySelector('#changes-overview').textContent = available.length
    ? `${available.length} device comparisons available: ${added} newly observed answering features; ${missing} previously answering features not observed open this time. ${comparisons.length - available.length} devices could not be compared.`
    : 'A reliable structured comparison is not available for these saved results. See the reasons below; this is not a claim that nothing changed.';
  const list = document.querySelector('#changes-list');
  list.replaceChildren();
  for (const item of comparisons.slice(0, 254)) {
    const row = text('li', '');
    row.append(text('strong', deviceLabel(item.device)));
    if (item.source_created_at) row.append(text('p', `Earlier check: ${recordedTimeLabel(item.source_created_at)}. This check: ${recordedTimeLabel(item.current_created_at)}.`));
    if (item.status === 'available') {
      const describe = values => values.map(value => `${value.protocol.toUpperCase()} ${value.port}`).join(', ') || 'none';
      row.append(text('p', `Newly observed open: ${describe(item.added || [])}. Previously open, not observed open now: ${describe(item.not_observed || [])}.`));
      if (item.added_count > (item.added?.length || 0) || item.not_observed_count > (item.not_observed?.length || 0)) row.append(text('p', 'Up to 200 examples per change type are listed; summary totals include all recorded differences.'));
    }
    row.append(text('p', item.reason || 'Comparison limits were not recorded.'));
    if (/^[0-9a-f-]{36}$/i.test(item.source_scan_id || '')) {
      const link = text('a', 'Open the earlier report'); link.href = `/scans/${item.source_scan_id}`; row.append(link);
    }
    list.append(row);
  }
  if (comparisons.length > 254) list.append(text('li', `${comparisons.length - 254} additional device comparisons are not displayed in this bounded summary.`));
  if (!comparisons.length) list.append(text('li', 'No usable device observations to compare.'));
  const features = document.querySelector('#feature-inventory-list');
  features.replaceChildren();
  for (const [label, entries] of serviceGroups(data)) {
    const group = text('li', '');
    group.append(text('h3', `${label} · ${new Set(entries.map(item => item.device.device_id)).size} devices`));
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
  if (!features.childElementCount) features.append(text('li', 'No answering features were recorded. This does not mean every possible feature was checked or that the devices are safe.'));
  return { deviceCount: deviceResultEntries(data).length };
}
