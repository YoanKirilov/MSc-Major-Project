// Display-only helpers. Never turn annotations or optional observations into findings.
export const IDENTIFY_DEVICE_LABEL = 'Try identifying this address again';

export function recordedTimeLabel(value, unavailable = 'Time unavailable') {
  // Do not invent a local timezone for uncertain legacy/imported metadata.
  if (typeof value !== 'string') return unavailable;
  const parts = /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?:Z|[+-](\d{2}):?(\d{2}))$/i.exec(value);
  if (!parts) return unavailable;
  const [year, month, day, hour, minute, second] = parts.slice(1, 7).map(Number);
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  // Date() can silently roll February 30 or 24:00 into another day.
  if (year < 1 || month < 1 || month > 12 || day < 1 || day > days[month - 1]
      || hour > 23 || minute > 59 || second > 59
      || Number(parts[7] || 0) > 23 || Number(parts[8] || 0) > 59) return unavailable;
  const date = new Date(value);
  if (!Number.isFinite(date.getTime()) || date.getUTCFullYear() < 1 || date.getUTCFullYear() > 9999) return unavailable;
  return date.toLocaleString(undefined, { timeZoneName: 'short' });
}

export function recordedUtcDay(value) {
  return recordedTimeLabel(value, '') ? new Date(value).toISOString().slice(0, 10) : '';
}

export function localFeatureHelp(device, service, data) {
  if (!device || service?.state !== 'open' || !['tcp', 'udp'].includes(service.protocol)
      || service.detection_method !== 'probed' || !(service.nmap_confidence >= 7)) return null;
  if (service.protocol === 'udp' && !['domain', 'dns'].includes(service.name)) return null;
  const self = recordedDeviceRole(device, data) === 'Computer that ran this scan';
  const features = {
    msrpc: {
      meaning: 'This response is consistent with communication between Windows programs. It can support normal system features; it is not evidence that someone is remotely controlling the computer.',
      check: 'On a Windows computer you own, open Windows Security, then Firewall & network protection, to review the current protection. Do not switch off the firewall or stop core Windows services to remove this result.',
    },
    'netbios-ssn': {
      meaning: 'This response is consistent with an older Windows network-sharing feature. It does not show that a folder or printer is shared, or that anyone accessed your files.',
      check: 'On a Windows computer you own, search Settings for Advanced sharing settings and review File and printer sharing. Check whether you intentionally share files or a printer. Leave settings unchanged if you are unsure.',
    },
    'microsoft-ds': {
      meaning: 'This reply is consistent with file or printer sharing. It does not show which files are shared or who can access them.',
      check: 'On a Windows computer you own, review Advanced sharing settings and the Sharing tab of any folder you deliberately shared. Do not enable sharing to test this result or change permissions without understanding who needs access.',
    },
    'vmware-auth': {
      meaning: 'The scanner identified a name associated with virtual-machine software, which runs another computer inside this one. This is a clue, not confirmation of the installed product or its security.',
      check: 'If you own this computer, check your installed applications for VMware and ask whether the virtual machines are expected. Review the application documentation before changing any related service; do not stop it just because it answered a scan.',
    },
    rtsp: {
      meaning: 'This reply is consistent with a feature for sending video or sound. Cameras and media devices sometimes use it; this does not identify the device or show that anyone watched a stream.',
      check: 'Think about whether you use a camera, television or media app on this device. Check its manual or ask its owner whether streaming is expected. Leave settings unchanged if you are unsure.',
    },
    domain: {
      meaning: 'A name-lookup feature helps devices find websites by name. This reply does not reveal which websites anyone visited or whether the settings are correct.',
      check: 'If this is your router, ask its owner or the person who set up your Wi-Fi whether it provides name lookup. Do not switch this feature off just because it replied; it may be needed for normal internet use.',
    },
    tcpwrapped: {
      meaning: 'The device accepted a connection, then closed it before the scanner could identify the feature. This does not reveal which program replied or why it closed the connection.',
      check: 'Do not switch off protection or stop programs just to remove this result. On a Windows computer you own, you can review Windows Security for protection messages. Otherwise, ask the device owner or maker for help if you have a problem using it.',
    },
  };
  const help = features[service.name === 'dns' ? 'domain' : service.name];
  if (!help) return null;
  const windowsFeature = ['msrpc', 'netbios-ssn', 'microsoft-ds'].includes(service.name);
  return { ...help, limitation: self
    ? 'This is a check from the computer to itself. It does not establish whether another device or someone on the internet can connect.'
    : windowsFeature
      ? 'This scanner label does not confirm that the device runs Windows. Follow the Windows steps only for a Windows computer you own.'
      : 'The scanner label is a clue, not proof of the device identity, installed software or safety.' };
}

export function scanComputerCoverage(data) {
  const address = data.policy?.network_context?.address;
  if (data.phase !== 'finished' || data.target?.mode !== 'discover' || !address) return '';
  const target = data.coverage?.targets?.find(item => item.ip === address);
  if (!target) return ''; // A subnet scan may intentionally exclude this address.
  if (target.service_status === 'completed') return 'The computer running NetGuard was included in these selected checks. This was a self-check: it does not show whether another device can connect.';
  if (target.discovery_status === 'observed') return 'The computer running NetGuard was found, but its selected device checks did not finish. Its remaining features were not checked.';
  return 'The computer running NetGuard was not discovered in this Light scan and was not included in its device checks. This is not a safety verdict. You can set up a separate Deep scan of this computer; it will not start automatically.';
}
export function recordedDeviceRole(device, data) {
  const context = data.policy?.network_context;
  if (!context || !device?.ip) return '';
  if (context.address === device.ip) return 'Computer that ran this scan';
  const gateways = context.connection?.Gateways;
  return Array.isArray(gateways) && gateways.includes(device.ip)
    ? 'Network gateway — used to reach other networks when this scan started. This recorded role does not confirm the device name.' : '';
}

export function matchesSearch(query, values, deviceAddress) {
  const normalise = value => String(value || '').normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase();
  const exact = String(query || '').trim();
  const parts = exact.split('.');
  if (parts.length === 4 && parts.every(part => /^(0|[1-9][0-9]{0,2})$/.test(part) && Number(part) <= 255)) {
    // A complete address names one device, never a prefix or an older address
    // mentioned in its notes. Other queries retain normal partial/text search.
    return deviceAddress !== undefined ? deviceAddress === exact : values.some(value => value === exact);
  }
  const haystack = normalise(values.filter(Boolean).join(' '));
  return normalise(query).split(/\s+/).filter(Boolean).every(word => haystack.includes(word));
}

export function actionDeviceLabel(device, data) {
  const label = device ? `${deviceLabel(device)} (${device.ip})` : 'Observed device';
  const role = recordedDeviceRole(device, data);
  return role ? `${label} — ${role.startsWith('Network gateway') ? 'Network gateway (recorded route, not a verified device name)' : role}` : label;
}

export function deviceSearchValues(device, services = []) {
  return [device.user_nickname, device.hostname, device.ip, device.mac, device.vendor,
    device.profile?.category, ...(device.name_candidates || []).map(item => item.name),
    ...(device.details || []).map(item => item.value),
    ...services.flatMap(service => [service.name, service.port, service.product, featureLabel(service)])];
}

export function featureLabel(service) {
  const names = { http: 'Device web page', https: 'Protected web connection',
    'http-proxy': 'Web-related connection', 'https-alt': 'Possible protected web connection',
    'microsoft-ds': 'File sharing', 'ms-wbt-server': 'Remote desktop', rtsp: 'Media streaming',
    msrpc: 'Windows communication between programs', 'netbios-ssn': 'Older Windows sharing connection',
    domain: 'Network name lookup', dns: 'Network name lookup', ssh: 'Protected remote control',
    telnet: 'Older remote control (Telnet)', ftp: 'File transfer', mqtt: 'Smart-home messaging',
    snmp: 'Device monitoring', upnp: 'Device discovery', ssdp: 'Device discovery', ntp: 'Clock synchronisation',
    tcpwrapped: 'Connection closed before its feature could be identified' };
  names['vmware-auth'] = 'Virtual computer software (VMware)';
  const name = service.name === 'http' && service.tunnel === 'ssl' ? 'https' : service.name;
  return `${names[name] || 'Unidentified feature'}${service.detection_method === 'table' ? ' (type unconfirmed; inferred from its port)' : ''}`;
}

export function confidenceLabel(value) {
  return ({ high: 'Strong supporting evidence', medium: 'Some supporting evidence',
    low: 'Limited supporting evidence' })[value] || 'Evidence strength not recorded';
}

// One display label for every route to a review item. Never change saved titles.
export function reviewItemTitle(finding, service, title = finding?.title) {
  const label = finding?.severity === 'informational' && service
    ? service.name === 'tcpwrapped' ? 'Feature not identified' : featureLabel(service)
    : (title || 'Review this item').replace(/ \((HTTP|FTP|Telnet|MQTT)\)$/, '');
  return service?.port ? `${label} · port ${service.port}` : label;
}

export function firstActionPrecaution(device, service) {
  if (!webPageInstructions(device, service)) return '';
  return 'Before opening a device page, make sure it is yours or you have permission. Do not enter passwords or personal details on an HTTP page, and do not ignore certificate warnings.';
}

export function actionGuidance(step, check) {
  // Remove only this reviewed duplicate; keep all precautions and original text in details.
  const repeated = 'Look for https:// at the start of the address. ';
  const verification = (step || '').includes('https://') && (check || '').startsWith(repeated)
    ? check.slice(repeated.length) : check;
  return [step, verification].filter(Boolean).join(' ');
}

export function webPageInstructions(device, service) {
  if (!device || !service || service.state !== 'open' || service.protocol !== 'tcp'
      || service.detection_method !== 'probed' || !['http', 'https', 'http-proxy'].includes(service.name)) return '';
  const parts = String(device.ip).split('.');
  if (parts.length !== 4 || !parts.every((part) => /^(0|[1-9][0-9]{0,2})$/.test(part) && Number(part) <= 255)
      || !Number.isInteger(service.port) || service.port < 1 || service.port > 65535) return '';
  const scheme = service.name === 'https' || service.tunnel === 'ssl' ? 'https' : 'http';
  const address = `${scheme}://${device.ip}:${service.port}/`;
  return `First, make sure you recognise this device and have permission to open it. Then type ${address} into your browser's address bar, not its search box. `
    + 'This is its starting page, not a confirmed settings or sign-in page. Do not enter passwords or personal details over HTTP. Do not bypass certificate warnings. If unsure, use the device manual or ask its owner.';
}

export function deviceLabel(device) {
  if (!device) return 'Observed device';
  if (device.user_nickname) return `${device.user_nickname} (your nickname)`;
  return `${device.hostname || 'Unnamed device'}${device.hostname_source === 'saved_report' ? ' (previously reported)' : ''}`;
}

export function namingCoverage(devices = []) {
  const own = devices.filter(device => device.user_nickname).length;
  const previous = devices.filter(device => device.hostname && device.hostname_source === 'saved_report').length;
  const current = devices.filter(device => device.hostname && device.hostname_source && device.hostname_source !== 'saved_report').length;
  const unrecorded = devices.filter(device => device.hostname && !device.hostname_source).length;
  const unnamed = devices.filter(device => !device.hostname).length;
  return `${current} device${current === 1 ? '' : 's'} with names reported in this scan; ${previous} with earlier saved names; ${unnamed} without a detected name.`
    + (unrecorded ? ` The source of ${unrecorded} saved name${unrecorded === 1 ? ' is' : 's is'} missing. We do not know when or how ${unrecorded === 1 ? 'it was' : 'they were'} found.` : '')
    + (own ? ` Your nicknames label ${own} device${own === 1 ? '' : 's'} separately.` : '')
    + ` Names are clues, not verified identities. A missing name does not mean an intruder. To try finding a name, wake the device. Then choose “${IDENTIFY_DEVICE_LABEL}”; no name is guaranteed.`;
}

export function pendingWording(data) {
  return [...(data.explanations || []), data.report_explanation].filter(Boolean)
    .some((record) => Object.keys(record.rejected_fields || {}).length);
}

export function wordingLabels(fields) {
  const labels = { title: 'heading', meaning: 'what was found', why_it_matters: 'what it means for you',
    limitations: 'what we could not confirm', recommended_steps: 'suggested actions', how_to_check: 'how to check the result' };
  return [...new Set(Object.keys(fields).map((field) => labels[field.split('[')[0]] || 'explanation'))].join(', ');
}

export function savedCheckNote(device, service) {
  if (!device || !service) return '';
  const check = (device.details || []).find((item) => item.kind === 'web'
    && item.source === 'Bounded HTTP check' && item.label === `Web connection (port ${service.port})`);
  if (!check) return '';
  let result = '';
  if (check.status === 'unavailable' || check.status === 'not_checked') {
    result = 'The extra check could not confirm whether this web page switches to HTTPS, a protected web connection.';
  } else if (check.status === 'observed') {
    if (check.value.startsWith('Redirected to HTTPS on this device;')) {
      result = 'The starting page switched to a protected HTTPS connection, and its certificate passed the address check.';
    } else if (check.value.startsWith('The root page answered over HTTP (status ') || check.value.startsWith('Redirected to another HTTP address on this device;')) {
      result = 'The starting page did not switch to a protected HTTPS connection during this check.';
    }
  }
  return result ? `${result} This describes only the starting page at scan time, not every page or the whole device. (Saved check, not an AI conclusion.)` : '';
}
