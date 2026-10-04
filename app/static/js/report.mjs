const priorities = { high: 0, medium: 1, low: 2, informational: 3 };

export function ollamaStatusText(status) {
  if (status.ai_available) return `Ollama is ready (${status.ai_model || 'configured model'}).`;
  const model = status.ai_model || 'the configured model';
  const states = {
    missing_model: `Ollama is running, but ${model} is not installed. See AI settings for setup.`,
    unreachable: 'Ollama could not be reached. Start Ollama on this computer.',
    unresponsive: 'Ollama is taking longer to respond. It may be starting or busy; you can check again shortly.',
    error: 'Ollama responded, but its readiness could not be confirmed. Check AI settings and retry.',
  };
  return (states[status.ai_readiness?.state] || 'Ollama readiness could not be confirmed. See AI settings.')
    + ' Scan facts will be saved even if plain-language preparation is unavailable.';
}

export function prioritise(findings = [], devices = [], services = []) {
  const addresses = new Map(devices.map(d => [d.device_id, d.ip]));
  const features = new Map(services.map(s => [s.service_id, s]));
  const compare = (a, b) => String(a || '').localeCompare(String(b || ''), 'en', { numeric: true });
  // IDs contain the scan ID: tie-break using observed identity, not generated UUIDs.
  return [...findings].sort((a, b) => (priorities[a.severity] ?? 4) - (priorities[b.severity] ?? 4)
    || compare(a.rule_id, b.rule_id) || compare(addresses.get(a.device_id), addresses.get(b.device_id))
    || compare(features.get(a.service_id)?.protocol, features.get(b.service_id)?.protocol)
    || compare(features.get(a.service_id)?.port, features.get(b.service_id)?.port)
    || compare(a.title, b.title));
}

export function deviceCheckLabel(data) {
  const c = data.coverage;
  if (!c) return 'Coverage not recorded';
  const discover = data.target?.mode === 'discover';
  return `${c.service_completed_count || 0} of ${(discover ? c.discovered_count : c.candidate_count) || 0} ${discover ? 'discovered' : 'selected'}`;
}

export function completedCheckSummary(data) {
  const c = data.coverage || {};
  const total = data.target?.mode === 'discover' ? c.discovered_count : c.candidate_count;
  if (['queued', 'running'].includes(data.state)) return `In progress. ${coverageSummary(data)}`;
  if (data.state === 'completed' && total > 0 && c.service_completed_count === total && !c.service_failed_count) {
    return `All selected device checks finished (${total} device${total === 1 ? '' : 's'}). This is not a full security assessment.`;
  }
  return coverageSummary(data);
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
    tcpwrapped: 'Connection closed before its feature could be identified (tcpwrapped)',
  };
  const name = service.name === 'http' && service.tunnel === 'ssl' ? 'https' : service.name;
  const label = names[name] || name || 'Unidentified feature';
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
  const mdnsOnly = (c.targets || []).filter((target) => target.discovery_sources?.includes('mdns') && !target.discovery_sources.includes('nmap')).length;
  const scope = discover ? `${total} device${total === 1 ? '' : 's'} identified during discovery${mdnsOnly ? `, including ${mdnsOnly} seen only through mDNS announcements` : ''}.` : `${total} device address${total === 1 ? ' was' : 'es were'} selected.`;
  return `${scope} ${finished} device check${finished === 1 ? '' : 's'} finished.`
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

// A setup link only pre-fills the dashboard. It never grants scan authorisation.
export function readScanSetup(hash = '') {
  if (hash.length > 5000) return null;
  const params = new URLSearchParams(hash.replace(/^#/, ''));
  if (params.get('setup') !== '1') return null;
  const profile = params.get('profile') || 'light';
  if (!['light', 'deep-tcp-v1'].includes(profile)) return null;
  const hosts = params.get('hosts') ? params.get('hosts').split(',') : [];
  const valid = (ip) => /^(?:\d{1,3}\.){3}\d{1,3}$/.test(ip)
    && ip.split('.').every((part) => Number(part) <= 255 && String(Number(part)) === part);
  if (hosts.length > 254 || hosts.some((ip) => !valid(ip))
      || (profile === 'deep-tcp-v1' && hosts.length > 1)) return null;
  return { profile, hosts: [...new Set(hosts)] };
}

export function scanSetupLink(data, sameDevice = true) {
  const profile = data.policy?.profile === 'deep-tcp-v1' ? 'deep-tcp-v1' : 'light';
  const params = new URLSearchParams({ setup: '1', profile });
  if (sameDevice && (profile === 'deep-tcp-v1' || data.target?.mode === 'known_hosts')) {
    const hosts = data.target?.hosts || [];
    params.set('hosts', hosts.join(','));
  }
  const hash = `#${params}`;
  return readScanSetup(hash) ? `/${hash}` : `/#setup=1&profile=${profile}`;
}

export function aiExplanationNote(data) {
  const records = data.explanations || [];
  const allRecords = [...records, data.report_explanation].filter(Boolean);
  const outdated = allRecords.some((record) => record.prompt_version && record.prompt_version !== data.guidance_status?.ai_prompt_version);
  const rejected = [...records, data.report_explanation].filter(Boolean).reduce((total, record) => total + Object.keys(record.rejected_fields || {}).length, 0);
  const count = records.filter((record) => usableAiRecord(record, data)).length;
  if (data.phase === 'analysis') return 'Ollama is preparing your plain-language report.';
  if (outdated) return 'Older AI wording is hidden because it predates the current validation checks. Reviewed rule-based guidance is shown where needed; prepare this saved report again to update its AI wording.';
  if (rejected) return 'Some explanations are simplified; other parts use reviewed rule-based guidance because their AI wording could not be accepted. Retry remaining wording without scanning again.';
  if (data.analysis_status === 'failed') return 'The scan observations are saved, but the AI explanation did not finish. Retry report preparation; no new scan is needed.';
  const reviewed = (record) => record?.content && record.prompt_version === data.guidance_status?.ai_prompt_version
    && !Object.keys(record.rejected_fields || {}).length
    && (record.status === 'ready' || record.fallback_reason === 'not_simpler');
  if (data.analysis_status === 'ready' && reviewed(data.report_explanation)
      && (data.findings || []).every((finding) => records.some((record) => record.finding_id === finding.finding_id && reviewed(record)))) {
    const total = data.findings?.length || 0;
    return `Ollama reviewed the report overview and ${total} review item${total === 1 ? '' : 's'}. Accepted AI wording is shown; parts without an accepted alternative use reviewed guidance. Original wording remains available in details.`;
  }
  if (count) return `Local AI selected reviewed wording for ${count} finding${count === 1 ? '' : 's'}; remaining wording is rule-based.`;
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

export function analysisProgressText(data) {
  const p = data.analysis_progress;
  if (!p || !Number.isInteger(p.total) || p.total < 1) return 'Ollama is reading the saved results and choosing clear wording.';
  if (p.state === 'waiting') return 'Waiting for local AI to become free. Your scan observations are saved.';
  const complete = Math.max(0, Math.min(p.completed || 0, p.total));
  return `Prepared ${complete} of ${p.total} explanations.`
    + (p.active > 0 ? ` Working on ${p.active} remaining explanation${p.active === 1 ? '' : 's'} (attempt ${p.attempt} of 2).` : ' Saving the results of this step.');
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
    : `Recorded ${topic}.${check.truncated ? ' Technical output was shortened to the saved evidence limit.' : ''}`;
}
