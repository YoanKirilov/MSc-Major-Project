// Display-only helpers. Never turn annotations or optional observations into findings.
export function featureLabel(service) {
  const names = { http: 'Device web page', https: 'Protected web connection',
    'http-proxy': 'Web-related connection', 'https-alt': 'Possible protected web connection',
    'microsoft-ds': 'File sharing', 'ms-wbt-server': 'Remote desktop', rtsp: 'Media streaming',
    domain: 'Network name lookup', dns: 'Network name lookup', ssh: 'Protected remote control',
    telnet: 'Older remote control (Telnet)', ftp: 'File transfer', mqtt: 'Smart-home messaging',
    snmp: 'Device monitoring', upnp: 'Device discovery', ssdp: 'Device discovery', ntp: 'Clock synchronisation' };
  const name = service.name === 'http' && service.tunnel === 'ssl' ? 'https' : service.name;
  return `${names[name] || 'Unidentified feature'}${service.detection_method === 'table' ? ' (type unconfirmed; inferred from its contact number)' : ''}`;
}

export function confidenceLabel(value) {
  return ({ high: 'Strong supporting evidence', medium: 'Some supporting evidence',
    low: 'Limited supporting evidence' })[value] || 'Evidence strength not recorded';
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
  return `Only after you recognise this device and have permission, type ${address} into your browser's address bar, not its search box. `
    + 'This is its starting page, not a confirmed settings or sign-in page. Do not enter passwords or personal details over HTTP, and do not bypass certificate warnings. If unsure, use the device manual or ask its owner.';
}

export function deviceLabel(device) {
  if (!device) return 'Observed device';
  if (device.user_nickname) return `${device.user_nickname} (your nickname)`;
  return `${device.hostname || 'Unnamed device'}${device.hostname_source === 'saved_report' ? ' (previously reported)' : ''}`;
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
