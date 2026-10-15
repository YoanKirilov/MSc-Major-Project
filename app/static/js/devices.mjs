// Display-only device components. Nicknames and later lookups remain notes;
// announcements and previous observations never become completed scan checks.
import {
  IDENTIFY_DEVICE_LABEL, deviceLabel, featureLabel, namingCoverage,
  recordedDeviceRole, recordedTimeLabel, reviewItemTitle,
} from './presentation.mjs?v=20261014-dates';
import { prioritise } from './report.mjs?v=20261008-dates';

const nameSources = {
  nmap: 'Scan response', nmap_discovery: 'Discovery response',
  reverse_dns: 'Local name lookup', mdns: 'Device announcement',
  pihole_dhcp: 'Pi-hole address lease', pihole_network: 'Pi-hole history',
  upnp: 'Device description (UPnP)', netbios: 'Computer-name response (NetBIOS)',
  saved_report: 'Previous scan — not confirmed this time',
};
const detailLabels = {
  friendlyName: 'Reported device name', manufacturer: 'Reported manufacturer',
  modelName: 'Reported model', deviceType: 'Reported device type',
  'Reported md': 'Reported model', 'Reported ty': 'Reported model or product',
  'Reported fn': 'Advertised friendly name',
};
const observedStates = {
  advertised: 'Device announcement; unverified claim', inferred: 'Comparison or inference',
  unavailable: 'Could not check', not_checked: 'Not fully checked', observed: 'Observed',
};
const advertisedFeatures = {
  _http: 'a device web page', _https: 'a protected device web page',
  _ipp: 'printing', _ipps: 'protected printing', _printer: 'printing',
  _airplay: 'AirPlay media sharing', _raop: 'audio streaming',
  _googlecast: 'media casting', _hap: 'a smart-home accessory',
  _mqtt: 'smart-home messaging', _smb: 'file sharing', '_device-info': 'device information',
};
// In-memory presentation state only. Keep optional evidence open across nickname
// projections and filters without storing any changes in factual scan data.
const disclosureStates = new WeakMap();
const renderedExpansionStates = new WeakMap();
const descendants = node => Array.from(node.children || []).flatMap(child => [child, ...descendants(child)]);
function disclosurePath(node, group) {
  const parts = [];
  for (let current = node; current && current !== group; current = current.parentElement) {
    if (current.tagName === 'DETAILS') {
      const summary = Array.from(current.children || []).find(child => child.tagName === 'SUMMARY');
      parts.unshift(current.dataset.disclosureKey || summary?.textContent || 'details');
    }
  }
  return JSON.stringify(parts);
}
function focusIdentity(node, group) {
  if (node.tagName === 'SUMMARY') return `summary:${disclosurePath(node.parentElement, group)}`;
  const context = disclosurePath(node, group);
  if (node.dataset.deviceAction) return `${context}:${node.dataset.deviceAction}`;
  if (node.dataset.findingId) return `${context}:finding:${node.dataset.findingId}`;
  if (node.tagName === 'A') return `${context}:link:${node.href}`;
  return '';
}

export function deviceResultEntries(data) {
  const entries = [...(data.devices || [])];
  for (const target of data.coverage?.targets || []) {
    const selected = target.discovery_status === 'observed' || data.target?.mode === 'known_hosts';
    if ((['failed', 'timed_out', 'cancelled'].includes(target.service_status)
          || (selected && target.service_status !== 'completed'))
        && !entries.some(device => device.ip === target.ip)) entries.push({ ip: target.ip });
  }
  return entries;
}

export function deviceStatus(device, target) {
  const advertisedOnly = device.discovery_method === 'mdns_advertisement'
    || device.reachability === 'advertised';
  const serviceResponse = device.reachability_evidence?.some(item =>
    ['open_port_response', 'closed_port_response'].includes(item));
  if (target?.service_status === 'completed') {
    return advertisedOnly && !serviceResponse
      ? 'Selected checks finished; advertised device, service response not confirmed.'
      : 'Selected checks finished; not a safety verdict.';
  }
  if (target?.service_status) {
    return ({ pending: 'Waiting for device checks.', running: 'Device checks are running.',
      failed: 'Device checks could not finish.', timed_out: 'Device checks ran out of time.',
      cancelled: 'Device checks were cancelled.', skipped: 'Selected device checks were not performed.',
      not_scheduled: 'Device checks were not scheduled.' })[target.service_status]
      || 'Check completion was not confirmed.';
  }
  if (advertisedOnly && !serviceResponse) return 'Advertised by a device; service response not confirmed.';
  if (serviceResponse) return 'Responded to a service check; full check completion not recorded.';
  return 'Check completion not recorded.';
}

export function nameQualification(device) {
  if (!device.device_id) return 'No usable device result; identity not recorded.';
  const qualifications = [];
  if (device.user_nickname) qualifications.push('Your nickname; not a verified identity');
  else if (!device.hostname) qualifications.push('Name not identified; this does not mean an intruder');
  else if (device.hostname_source === 'saved_report') qualifications.push('Previously reported name; not confirmed this time');
  else qualifications.push(`Reported name${device.hostname_source ? ` · ${nameSources[device.hostname_source] || device.hostname_source}` : ' · source not recorded'}`);
  if (device.hostname_conflict) qualifications.push('Name sources disagree');
  return qualifications.join('. ');
}

function possibleCategory(device, data) {
  if (data && recordedDeviceRole(device, data) === 'Computer that ran this scan') return 'This computer (scan source)';
  if (device.profile?.conflict) return 'Clues disagree; device type not identified';
  const label = { camera: 'camera', printer: 'printer', router: 'network gateway',
    iot_other: 'smart-home device', computer: 'computer', media: 'media device' }[device.profile?.category];
  return label ? `Possible ${label}; based on reported clues, not verified identity` : 'Type not identified';
}

// The parent owns API requests, selection, revision fences and persistent state.
// Every callback is user initiated; rendering or expanding never starts a lookup.
export function renderDeviceSummaries({ document, container, data, expandedDevices = new Map(),
  matchesDevice = () => true, explanationFor = finding => ({ title: finding.title }),
  createCvePanel, notesSnapshot, nicknameAvailable = false, nicknameSaving = false,
  onEditNickname, onRefreshName, onViewFinding, sortDevices, deviceLimit = 24 }) {
  const savedStates = disclosureStates.get(container) || new Map();
  disclosureStates.set(container, savedStates);
  const renderedExpansions = renderedExpansionStates.get(container) || new Map();
  renderedExpansionStates.set(container, renderedExpansions);
  const stateKey = ip => JSON.stringify([data.scan_id || '', ip]);
  let focusedControl = null;
  for (const group of Array.from(container.children || [])) {
    if (!group.dataset?.deviceIp) continue;
    const states = new Map();
    for (const node of descendants(group)) {
      if (node.tagName === 'DETAILS') states.set(disclosurePath(node, group), node.open);
      if (node === document.activeElement) focusedControl = {
        ip: group.dataset.deviceIp, key: focusIdentity(node, group),
      };
    }
    savedStates.set(stateKey(group.dataset.deviceIp), states);
  }
  const text = (tag, value = '', className = '') => {
    const node = document.createElement(tag);
    node.textContent = value;
    if (className) node.className = className;
    return node;
  };
  const fact = (list, label, value) => {
    const row = text('div');
    row.append(text('dt', label), text('dd', value));
    list.append(row);
  };
  const disclosure = (label, className = 'device-supporting-details', key = label) => {
    const node = text('details', '', className);
    node.dataset.disclosureKey = key;
    node.append(text('summary', label));
    return node;
  };
  const entries = deviceResultEntries(data);
  const matching = entries.filter(device => matchesDevice(device, data));
  if (sortDevices) matching.sort((a, b) => sortDevices(a, b, data));
  const visible = Number.isFinite(deviceLimit) ? matching.slice(0, Math.max(1, Math.floor(deviceLimit))) : matching;
  container.replaceChildren();
  for (const [index, device] of visible.entries()) {
    const target = data.coverage?.targets?.find(item => item.ip === device.ip);
    const findings = (data.findings || []).filter(item => device.device_id && item.device_id === device.device_id);
    const services = (data.services || []).filter(item => device.device_id && item.device_id === device.device_id && item.state === 'open');
    const group = text('article', '', 'device-summary-group');
    group.dataset.deviceId = device.device_id || '';
    group.dataset.deviceIp = device.ip;
    const card = text('details', '', 'device-summary');
    card.dataset.disclosureKey = 'device';
    card.open = expandedDevices.get(device.ip) ?? false;
    card.addEventListener('toggle', () => expandedDevices.set(device.ip, card.open));
    const heading = text('summary', '', 'device-summary-heading');
    heading.id = `device-summary-${index}`;
    heading.append(text('span', deviceLabel(device), 'device-summary-name'));
    heading.append(text('span', `Network address: ${device.ip}`, 'device-summary-address'));
    heading.append(text('span', nameQualification(device), 'device-summary-source'));
    heading.append(text('span', possibleCategory(device, data), 'device-summary-type'));
    const role = recordedDeviceRole(device, data);
    if (role) heading.append(text('span', role, 'device-summary-source'));
    heading.append(text('span', deviceStatus(device, target), 'device-summary-status'));
    const incomplete = !device.device_id || (target && target.service_status !== 'completed');
    heading.append(text('span', incomplete && !services.length && !findings.length
      ? 'Features not assessed; no usable check result'
      : `${services.length} observed feature${services.length === 1 ? '' : 's'} · ${findings.length} review item${findings.length === 1 ? '' : 's'}${incomplete ? ' · remaining checks not assessed' : ''}`, 'device-summary-preview'));
    card.append(heading);
    const body = text('div', '', 'device-summary-body');
    const statusFacts = text('dl', '', 'device-facts');
    fact(statusFacts, 'Check result', deviceStatus(device, target));
    if (target?.reason_code) fact(statusFacts, 'Recorded reason', target.reason_code.replaceAll('_', ' '));
    if (target?.attempts) fact(statusFacts, 'Attempts', String(target.attempts));
    body.append(statusFacts);
    if (target && target.service_status !== 'completed') {
      body.append(text('p', 'Missing checks do not mean the device is safe. If you own this device, check that it is switched on and connected before retrying its unfinished checks.'));
    }
    body.append(text('h3', 'Features that answered'));
    body.append(text('p', services.length
      ? 'These features accepted a connection during the scan. A port is a numbered connection point for a feature. This does not show that anyone used them or that they have a vulnerability.'
      : incomplete ? 'Features were not assessed. Missing results do not mean that this device has no features or that it is safe.'
        : 'No open features were recorded in the selected checks. This is not proof that the device is safe.'));
    const words = text('a', 'Explain features, ports and other unfamiliar words', 'feature-word-help');
    words.href = '#report-glossary';
    words.dataset.glossaryLink = '';
    body.append(words);
    const featureEvidence = disclosure('Supporting feature details', 'device-supporting-details feature-technical', 'features');
    featureEvidence.append(text('p', 'Technical notes for the features listed above. A scanner label is a clue, not proof of the installed software or its safety.'));
    const hostChecks = device.host_script_results || [];
    const selectedSmbChecks = (data.policy?.selected_scripts || []).filter(name => ['smb-protocols', 'smb2-security-mode'].includes(name));
    if (hostChecks.length || selectedSmbChecks.length) {
      const help = { 'smb-protocols': 'File-sharing versions the device reported supporting',
        'smb2-security-mode': 'Protection for file-sharing messages in the version checked',
        'smb-os-discovery': 'Additional computer information reported through file sharing' };
      const checks = text('section', '', 'feature-evidence');
      checks.append(text('h4', 'Recorded device checks'));
      checks.append(text('p', 'These are recorded replies, not a safety certificate. A missing reply does not mean a check passed. File-sharing message protection applies to the negotiated version, not every possible connection.'));
      for (const check of hostChecks.slice(0, 32)) {
        checks.append(text('h5', help[check.script_id] || `Additional check: ${check.script_id}`));
        checks.append(text('p', `${check.output}${check.truncated ? ' (Recorded output was shortened; a complete result was not established.)' : ''}`));
      }
      for (const name of selectedSmbChecks.filter(name => !hostChecks.some(check => check.script_id === name)
        && !services.some(service => service.script_results?.some(check => check.script_id === name)))) {
        checks.append(text('p', `${help[name]}: no usable reply was recorded. The check may not have applied or returned a result; no pass is assumed.`));
      }
      if (hostChecks.length > 32) checks.append(text('p', `${hostChecks.length - 32} additional replies are retained in the saved technical evidence.`));
      featureEvidence.append(checks);
    }
    if (services.length) {
      const features = text('ul', '', 'device-features');
      services.forEach(service => {
        const row = text('li', '', 'device-feature');
        row.append(text('strong', featureLabel(service)));
        row.append(text('span', `${String(service.protocol || 'tcp').toUpperCase()} port ${service.port}`, 'device-feature-context'));
        const evidence = text('section', '', 'feature-evidence');
        evidence.append(text('h4', `${featureLabel(service)} · ${String(service.protocol || 'tcp').toUpperCase()} port ${service.port}`));
        evidence.append(text('p', `Scanner name: ${service.name || 'Not identified'}. ${service.detection_method === 'table'
          ? 'The name was inferred from the port; the application was not identified.'
          : service.detection_method === 'probed' ? 'The scanner identified this name from a response; it is not verified product identity.'
            : 'Identification method not recorded.'}`));
        if (service.product || service.version) evidence.append(text('p', `Reported software: ${[service.product, service.version].filter(Boolean).join(' ')}. Software fingerprints can be incomplete or misleading.`));
        for (const check of service.script_results || []) {
          evidence.append(text('p', `${check.script_id}: ${check.output}${check.truncated ? ' (Recorded output was shortened.)' : ''}`));
        }
        featureEvidence.append(evidence);
        features.append(row);
      });
      body.append(features);
    }
    body.append(text('h3', 'Review items for this device'));
    if (findings.length) {
      const list = text('ul', '', 'device-review-links');
      for (const finding of prioritise(findings, data.devices || [], data.services || [])) {
        const row = text('li');
        const service = (data.services || []).find(item => item.service_id === finding.service_id);
        const title = reviewItemTitle(finding, service, explanationFor(finding)?.title);
        const label = finding.severity === 'informational' ? title : `${finding.severity || 'Review'}: ${title}`;
        const trigger = text(onViewFinding ? 'button' : 'span', label, onViewFinding ? 'secondary-button' : '');
        if (onViewFinding) {
          trigger.type = 'button';
          trigger.dataset.findingId = finding.finding_id;
          trigger.addEventListener('click', () => onViewFinding(finding.finding_id, trigger));
        }
        row.append(trigger);
        list.append(row);
      }
      body.append(list);
    } else body.append(text('p', incomplete
      ? 'Review items could not be assessed from the missing checks.'
      : 'No review items were recorded. This is not proof of safety.'));

    const about = disclosure('About this device');
    const identity = text('dl', '', 'device-facts');
    fact(identity, 'Network address', device.ip);
    fact(identity, 'Reported name', device.hostname || 'Not identified');
    if (device.user_nickname) fact(identity, 'Your nickname', `${device.user_nickname} — your label, not detected identity`);
    fact(identity, 'Name source', nameSources[device.hostname_source] || device.hostname_source || 'Not recorded');
    fact(identity, 'Name evidence', device.hostname_conflict
      ? 'Sources disagree; no name verifies identity' : `${device.hostname_confidence || 'Not recorded'} confidence; reported names do not verify identity`);
    if (device.hostname_observed_at) fact(identity, 'Name recorded', recordedTimeLabel(device.hostname_observed_at));
    fact(identity, 'Possible type', possibleCategory(device, data));
    if (device.vendor) fact(identity, 'Network adapter manufacturer', `${device.vendor} — does not identify the device model`);
    about.append(identity);
    if (device.hostname_source === 'saved_report') about.append(text('p', 'An earlier scan reported this name for the same network-adapter address. It was not confirmed this time. Adapter addresses can change or be copied.'));
    if (device.hostname_conflict) about.append(text('p', 'Different sources reported different names. Do not choose one as a verified identity; compare with the device itself or your router.'));
    if (device.name_candidates?.length) {
      const alternatives = disclosure('Reported names and their sources');
      for (const candidate of device.name_candidates) {
        alternatives.append(text('p', `${candidate.name} — ${nameSources[candidate.source] || candidate.source || 'Source not recorded'}; ${recordedTimeLabel(candidate.observed_at)}. Unverified name claim.`));
      }
      about.append(alternatives);
    }
    if (device.profile?.hints?.length) {
      const basis = disclosure('Why this possible type?');
      basis.append(text('p', device.profile.conflict ? 'Clues disagree; no device type is assigned.' : 'These reported clues suggest a category, not verified identity.'));
      for (const hint of device.profile.hints) basis.append(text('p', `${hint.source}: ${hint.token}`));
      about.append(basis);
    }
    const details = (device.details || []).filter(item => item.kind !== 'history');
    if (details.length) {
      const observed = disclosure('Reported model and additional observations');
      observed.append(text('p', 'These clues help you recognise a device. Advertised descriptions are claims, not verified identity or passing security checks.'));
      for (const item of details) {
        observed.append(text('p', `${detailLabels[item.label] || item.label}: ${item.value}`));
        observed.append(text('small', `${observedStates[item.status] || 'Reported'} · ${item.source} · ${recordedTimeLabel(item.observed_at)}`));
      }
      about.append(observed);
    }
    const history = (device.details || []).filter(item => item.kind === 'history');
    if (history.length) {
      const comparison = disclosure('Comparison with earlier observations', 'device-observations');
      comparison.append(text('p', 'This compares saved observations, not proof that the same physical device or its security has changed.'));
      for (const item of history) {
        comparison.append(text('p', `${item.label}: ${item.value}`));
        comparison.append(text('small', `${observedStates[item.status] || 'Reported'} · ${item.source} · ${recordedTimeLabel(item.observed_at)}`));
      }
      about.append(comparison);
    }
    const advertisements = (data.observations || []).filter(item => item.source === 'mdns' && item.ip === device.ip);
    if (advertisements.length) {
      const announcements = disclosure(`Device announcements (${advertisements.length})`, 'device-observations', 'announcements');
      announcements.append(text('p', 'These announcements used this address when recorded. They do not verify the device identity or an open feature.'));
      for (const item of advertisements) {
        const feature = advertisedFeatures[String(item.service_type || '').split('.')[0]] || 'a device feature';
        announcements.append(text('p', `${item.advertised_name || 'No name reported'} advertised ${feature}${item.port ? ` on port ${item.port}` : ''}.`));
        announcements.append(text('small', `Device announcement (mDNS) · ${recordedTimeLabel(item.observed_at)} · unverified claim`));
      }
      about.append(announcements);
    }
    const information = text('div', '', 'device-info-disclosures');
    information.append(about);
    if (services.length || hostChecks.length || selectedSmbChecks.length) information.append(featureEvidence);
    body.append(information);
    const eligibleServices = services.filter(service => service.cve_lookup_available
      || notesSnapshot?.cve_lookups?.some(item => item.service_id === service.service_id));
    if (eligibleServices.length && createCvePanel) {
      const references = disclosure('Published software problems (CVE research)');
      references.append(text('p', 'Optional online research. Possible matches are not confirmed vulnerabilities on this device.'));
      for (const service of eligibleServices) {
        references.append(text('h4', `${featureLabel(service)} · port ${service.port}`), createCvePanel(service));
      }
      body.append(references);
    }
    card.append(body);
    const tools = text('footer', '', 'device-name-tools');
    const actions = text('div', '', 'device-action-buttons');
    if (device.device_id) {
      if (onEditNickname || (data.phase === 'finished' && onRefreshName)) tools.append(actions);
      if (onEditNickname) {
        const edit = text('button', device.user_nickname ? 'Edit or remove your nickname' : 'Add your own nickname', 'secondary-button');
        edit.type = 'button';
        edit.dataset.nicknameDevice = device.device_id;
        edit.dataset.deviceAction = 'edit-nickname';
        edit.setAttribute('aria-describedby', heading.id);
        edit.disabled = !nicknameAvailable || nicknameSaving;
        edit.addEventListener('click', () => onEditNickname(device, edit));
        actions.append(edit);
      }
      if (data.phase === 'finished' && onRefreshName) {
        const refresh = text('button', IDENTIFY_DEVICE_LABEL, 'secondary-button');
        refresh.type = 'button';
        refresh.dataset.deviceAction = 'refresh-name';
        refresh.setAttribute('aria-describedby', heading.id);
        const lookupStatus = text('p', '', 'status-message identification-status');
        lookupStatus.setAttribute('role', 'status');
        lookupStatus.hidden = true;
        refresh.addEventListener('click', () => onRefreshName(device, refresh, lookupStatus));
        actions.append(refresh);
        tools.append(lookupStatus);
        const laterDetails = text('div');
        laterDetails.dataset.notePanel = 'name';
        let shown = '';
        laterDetails.updateNotes = snapshot => {
          const later = snapshot?.name_refreshes?.find(item => item.device_id === device.device_id);
          const signature = later ? JSON.stringify(later) : '';
          if (signature === shown) return;
          shown = signature;
          const open = laterDetails.querySelector?.('details')?.open || false;
          laterDetails.replaceChildren();
          if (!later) { lookupStatus.hidden = true; lookupStatus.textContent = ''; return; }
          lookupStatus.hidden = false;
          lookupStatus.textContent = later.names?.length
            ? `The last lookup returned ${later.names.length} reported name${later.names.length === 1 ? '' : 's'}: ${later.names.map(item => item.name).join(', ')}. Unverified claims; the saved device name has not changed.`
            : 'No new name found in the last lookup. The saved name has not changed; this does not mean the device is absent or safe.';
          const extra = disclosure(`Later identification lookup — ${recordedTimeLabel(later.checked_at)}`,
            'device-supporting-details', 'later-identification');
          extra.open = open;
          for (const name of later.names || []) extra.append(text('p', `${name.name} — ${nameSources[name.source] || name.source}; ${recordedTimeLabel(name.observed_at)}. Unverified name claim.`));
          for (const note of later.notes || []) extra.append(text('p', note));
          laterDetails.append(extra);
        };
        laterDetails.updateNotes(notesSnapshot);
        tools.append(laterDetails);
      }
    } else tools.append(text('p', 'A nickname can be saved after this address returns a usable device result.'));
    group.append(card, tools);
    container.append(group);
    const previous = savedStates.get(stateKey(device.ip));
    // An explicit parent action (for example "Find this device") may request
    // a different outer state. Honour that intent without discarding the inner
    // disclosure state. Otherwise actual DOM state beats a queued stale toggle.
    const desiredExpansion = expandedDevices.get(device.ip);
    const explicitExpansion = renderedExpansions.has(stateKey(device.ip))
      && desiredExpansion !== undefined
      && desiredExpansion !== renderedExpansions.get(stateKey(device.ip));
    if (previous) {
      for (const node of descendants(group)) {
        if (node.tagName !== 'DETAILS') continue;
        const key = disclosurePath(node, group);
        if (node === card && explicitExpansion) continue;
        if (previous.has(key)) node.open = previous.get(key);
      }
    }
    expandedDevices.set(device.ip, card.open);
    renderedExpansions.set(stateKey(device.ip), card.open);
    if (focusedControl?.ip === device.ip && focusedControl.key) {
      const replacement = descendants(group).find(node => focusIdentity(node, group) === focusedControl.key);
      if (replacement && !replacement.disabled) replacement.focus?.({ preventScroll: true });
    }
  }
  if (!matching.length) container.append(text('p', entries.length
    ? 'No device results match this search. Clear the search to see all recorded devices.'
    : 'No device results were recorded. This does not prove that no devices are connected.'));
  const failed = visible.filter(device => !device.device_id).length;
  return {
    entries, matching, visibleCount: visible.length,
    namingText: `Naming information covers the ${data.devices?.length || 0} device${data.devices?.length === 1 ? '' : 's'} with usable saved results; addresses without a usable result are excluded. ${namingCoverage(data.devices || [])}`,
    countText: `Showing ${visible.length} of ${matching.length} matching device results (${entries.length} recorded in total)${failed ? `, including ${failed} shown address${failed === 1 ? '' : 'es'} without a usable device result` : ''}. Devices without review items are included.`,
  };
}
