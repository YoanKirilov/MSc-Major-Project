const priorities = { high: 0, medium: 1, low: 2, informational: 3 };

export function prioritise(findings = []) {
  return [...findings].sort((a, b) => (priorities[a.severity] ?? 4) - (priorities[b.severity] ?? 4));
}

export function serviceLabel(service, fallback = 'Selected service') {
  if (!service) return fallback;
  const names = {
    telnet: 'Older remote control (Telnet)', ftp: 'File transfer (FTP)',
    http: 'Device web page (HTTP)', https: 'Encrypted web connection (HTTPS)',
    'ms-wbt-server': 'Remote desktop', 'microsoft-ds': 'File sharing (SMB)',
    mqtt: 'Smart-home messaging (MQTT)', ssh: 'Encrypted remote connection (SSH)',
    domain: 'Network name lookup (DNS)', dns: 'Network name lookup (DNS)',
    snmp: 'Device monitoring (SNMP)', rtsp: 'Media streaming (RTSP)',
    upnp: 'Device discovery (UPnP)', ssdp: 'Device discovery (SSDP)',
    ntp: 'Clock synchronisation (NTP)',
  };
  const name = service.name === 'http' && service.tunnel === 'ssl' ? 'https' : service.name;
  const label = names[name] || name || 'Unidentified connection';
  const inferred = service.detection_method === 'table' ? ' (name inferred from port)' : '';
  return `${label}${inferred} — ${String(service.protocol || 'tcp').toUpperCase()} port ${service.port}`;
}

export function coverageSummary(data) {
  const c = data.coverage || {};
  const discover = data.target?.mode === 'discover';
  const total = (discover ? c.discovered_count : c.candidate_count) || 0;
  const finished = c.service_completed_count || 0;
  const active = ['queued', 'running'].includes(data.state);
  const remaining = Math.max(0, total - finished);
  if (!total && !active) {
    return discover
      ? 'No devices answered discovery. Device security could not be assessed.'
      : 'No device checks finished. Device security could not be assessed.';
  }
  const scope = discover ? `${total} devices answered discovery.` : `${total} device addresses were requested.`;
  return `${scope} ${finished} device checks finished.`
    + (remaining ? ` ${remaining} ${active ? 'still pending' : 'did not finish'}.` : '');
}

export function emptyFindingMessage(data) {
  if (['queued', 'running'].includes(data.state)) return 'Checks are still running. Findings are not final.';
  if (data.state !== 'completed') {
    return 'Scan incomplete. No findings were recorded from the checks that finished. This does not establish that the devices are secure.';
  }
  if (!data.coverage?.service_completed_count) return 'No devices were assessed. Their security could not be checked.';
  return 'No issues were flagged by the selected checks. Other services and security settings were not fully assessed.';
}

export function usableAiRecord(record, data) {
  return record.status === 'ready' && record.source === 'ai' && record.content
    && record.prompt_version === data.guidance_status?.ai_prompt_version;
}

export function aiExplanationNote(data) {
  const records = data.explanations || [];
  const count = records.filter((record) => usableAiRecord(record, data)).length;
  if (data.phase === 'analysis') return 'Local AI is choosing optional reviewed wording. Rule-based guidance is already available.';
  if (count) return `Local AI selected reviewed wording for ${count} finding${count === 1 ? '' : 's'}; remaining wording is rule-based.`;
  if (records.some((record) => record.source === 'ai' && record.prompt_version !== data.guidance_status?.ai_prompt_version)) {
    return 'Older AI wording is hidden because it predates the current validation checks. Rule-based guidance is shown.';
  }
  if (records.some((record) => record.fallback_reason === 'provider_timeout')) return 'The local AI timed out. Rule-based guidance is shown.';
  if (records.some((record) => ['provider_unavailable', 'provider_not_configured'].includes(record.fallback_reason))) {
    return 'Local AI was unavailable. Rule-based guidance is shown.';
  }
  if (records.some((record) => ['ai_limit_reached', 'ai_request_limit'].includes(record.fallback_reason))) {
    return 'The AI request limit was reached. Rule-based guidance is shown.';
  }
  return records.length
    ? 'No reviewed alternative wording was accepted. Rule-based guidance is shown.'
    : 'AI has not been used for this report. Rule-based guidance is shown.';
}

export function checkSummary(check) {
  const topics = {
    'http-title': 'web page title', 'http-headers': 'web response details',
    'http-methods': 'web request methods', 'ssl-cert': 'certificate details',
    'ssh-hostkey': 'remote connection identity key', 'rdp-enum-encryption': 'remote desktop connection settings',
    'smb-os-discovery': 'file-sharing device information', 'dns-recursion': 'DNS forwarding behaviour',
    'snmp-info': 'device monitoring information', 'upnp-info': 'device discovery information',
    'ntp-info': 'clock service information', nbstat: 'local device names',
  };
  const topic = topics[check.script_id] || check.script_id;
  return /\b(error|failed|timed out)\b/i.test(check.output)
    ? `Could not reliably check ${topic}; see the technical result.`
    : `Recorded ${topic}.`;
}
