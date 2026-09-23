import { request } from './api.js';
import { prioritise, serviceLabel, coverageSummary, emptyFindingMessage, usableAiRecord, checkSummary, aiExplanationNote } from './report.mjs';

const severityConfig = {
  high: { label: 'High', color: '#ff626d' },
  medium: { label: 'Medium', color: '#ff9a52' },
  low: { label: 'Low', color: '#f6ca61' },
  informational: { label: 'Review', color: '#63a9ff' },
};
const scanId = window.location.pathname.split('/').pop();
const title = document.querySelector('#result-title');
const lead = document.querySelector('#result-lead');
const status = document.querySelector('#result-status');
const technicalStatus = document.querySelector('#result-technical');
const state = document.querySelector('#result-state');
const count = document.querySelector('#result-count');
const ring = document.querySelector('#result-ring');
const coverage = document.querySelector('#result-coverage');
const summary = document.querySelector('#resultsSummary');
const findingsList = document.querySelector('#findingsList');
const detailPanel = document.querySelector('#detailPanel');
const deviceTableBody = document.querySelector('#device-table-body');
const mdnsSection = document.querySelector('#mdns-section');
const mdnsList = document.querySelector('#mdns-list');
const runAgainButton = document.querySelector('#runAgainButton');
const simplifyButton = document.querySelector('#simplifyButton');
const refreshGuidanceButton = document.querySelector('#refreshGuidanceButton');
const guidanceNotice = document.querySelector('#guidance-notice');
const scanProblems = document.querySelector('#scan-problems');
const searchInput = document.querySelector('#searchInput');
const filterButtons = [...document.querySelectorAll('.filter-chip')];
const nextStepsList = document.querySelector('#nextStepsList');
let selectedFinding = null;
let currentData = null;
let activeFilter = 'all';
let searchTerm = '';

searchInput.addEventListener('input', () => {
  searchTerm = searchInput.value.trim().toLowerCase();
  if (currentData) renderFindings(currentData);
});

filterButtons.forEach((button) => button.addEventListener('click', () => {
  activeFilter = button.dataset.filter;
  filterButtons.forEach((item) => {
    const active = item === button;
    item.classList.toggle('active', active);
    item.setAttribute('aria-pressed', String(active));
  });
  if (currentData) renderFindings(currentData);
}));

runAgainButton.addEventListener('click', async () => {
  if (!currentData) return;
  runAgainButton.disabled = true;
  runAgainButton.textContent = 'Starting...';
  const profile = currentData.policy?.profile || 'light';
  const deep = profile === 'deep-tcp-v1';
  const hosts = deep ? (currentData.target?.hosts || currentData.devices.map((device) => device.ip)) : [];
  const body = {
    mode: deep ? 'known_hosts' : (currentData.target?.mode || 'discover'),
    profile,
    cidr: deep ? null : currentData.target?.cidr,
    hosts,
    authorised: true,
  };
  if (!window.confirm(`Run another ${deep ? 'Deep' : 'Light'} scan of ${deep ? hosts.join(', ') : body.cidr}? Only continue if you own or are authorised to assess this network.`)) {
    runAgainButton.disabled = false;
    runAgainButton.textContent = 'Run again';
    return;
  }
  try {
    const payload = await request('/api/live-scans', { method: 'POST', body: JSON.stringify(body) });
    window.location.href = `/scans/${payload.scan_id}`;
  } catch (error) {
    runAgainButton.disabled = false;
    runAgainButton.textContent = 'Run again';
    status.textContent = error.message;
  }
});

simplifyButton.addEventListener('click', async () => {
  if (!currentData) return;
  simplifyButton.disabled = true;
  try {
    const aiStatus = await request('/api/status');
    if (!aiStatus.ai_enabled) throw new Error('Enable local AI wording in Settings first.');
    if (!aiStatus.ai_available) throw new Error('The local Ollama model is unavailable. Check AI settings.');
    await request(`/api/live-scans/${scanId}/explanations`, { method: 'POST', body: '{}' });
    status.textContent = 'Local AI is checking optional wording. The saved scan facts are unchanged.';
    poll();
  } catch (error) {
    simplifyButton.disabled = false;
    status.textContent = error.message;
  }
});

refreshGuidanceButton.addEventListener('click', async () => {
  if (!currentData) return;
  refreshGuidanceButton.disabled = true;
  try {
    await request(`/api/live-scans/${scanId}/refresh-guidance`, {
      method: 'POST', body: JSON.stringify({ expected_revision: currentData.revision }),
    });
    await poll();
  } catch (error) {
    guidanceNotice.textContent = error.message;
    refreshGuidanceButton.disabled = false;
  }
});

function text(tag, value, className = '') {
  const element = document.createElement(tag);
  element.textContent = value;
  if (className) element.className = className;
  return element;
}

function formatServiceLabel(service, fallback = 'Selected service') {
  return serviceLabel(service, fallback);
}

function deviceCategory(device) {
  if (device.user_category) return device.user_category;
  const labels = {
    camera: 'camera', printer: 'printer', router: 'router',
    iot_other: 'smart-home device', computer: 'computer', unknown: 'unknown type',
  };
  const category = labels[device.profile?.category] || 'unknown type';
  return category === 'unknown type' ? 'Type not identified' : `Possible ${category}`;
}

function explanationFor(finding) {
  const record = (currentData?.explanations || []).find((item) => (
    item.finding_id === finding.finding_id
    && usableAiRecord(item, currentData)
  ));
  return {
    content: record?.content || finding.fixed_explanation,
    aiAssisted: Boolean(record),
    aiFields: record?.ai_fields?.length ? record.ai_fields : (record ? ['meaning', 'why_it_matters'] : []),
    title: record?.display_title || finding.title,
    limitations: record?.display_limitations || finding.limitations,
  };
}

function visibleFindings(findings) {
  return findings.filter((finding) => {
    if (activeFilter !== 'all' && finding.severity !== activeFilter) return false;
    if (!searchTerm) return true;
    const device = currentData.devices.find((item) => item.device_id === finding.device_id);
    const service = currentData.services.find((item) => item.service_id === finding.service_id);
    const explanation = explanationFor(finding).content;
    const searchable = [
      explanationFor(finding).title,
      explanation.meaning,
      explanationFor(finding).limitations.join(' '),
      device?.hostname,
      device?.ip,
      service?.name,
      service?.port,
    ].filter(Boolean).join(' ').toLowerCase();
    return searchable.includes(searchTerm);
  });
}

function renderFilterCounts(findings) {
  const severities = ['all', 'high', 'medium', 'low', 'informational'];
  severities.forEach((severity) => {
    const count = severity === 'all'
      ? findings.length
      : findings.filter((finding) => finding.severity === severity).length;
    document.querySelector(`#count-${severity}`).textContent = count;
  });
}

function showDetail(finding) {
  detailPanel.replaceChildren();
  if (!finding) {
    detailPanel.append(text('strong', 'No finding selected'), text('p', 'Select a finding to inspect its evidence and fixed guidance.'));
    return;
  }
  const config = severityConfig[finding.severity] || severityConfig.informational;
  const top = text('div', '', 'detail-topline');
  top.append(text('span', finding.severity === 'informational' ? 'Review item' : `${config.label} priority`, 'severity-badge'), text('span', `${finding.confidence} confidence in assessment`, 'confidence'));
  detailPanel.style.setProperty('--severity-color', config.color);
  const device = currentData.devices.find((item) => item.device_id === finding.device_id);
  const service = currentData.services.find((item) => item.service_id === finding.service_id);
  const deviceLabel = device ? `${device.hostname || 'Unknown device'} · ${device.ip}` : 'Observed device';
  const serviceLabel = formatServiceLabel(service);
  const explanation = explanationFor(finding);
  detailPanel.append(top, text('h3', explanation.title), text('p', `${deviceLabel} · ${serviceLabel}`, 'detail-location'));
  detailPanel.append(text(
    'p',
    explanation.aiAssisted
      ? 'Local AI selected reviewed plain-language wording. Original guidance is available below.'
      : 'Rule-based guidance from the recorded observations. This is not proof of a security weakness.',
    `explanation-source${explanation.aiAssisted ? ' is-ai' : ''}`,
  ));
  const block = (heading, value, className = 'detail-block') => {
    const section = text('div', '', className);
    section.append(text('h4', heading), text('p', value));
    return section;
  };
  detailPanel.append(block('What was observed', explanation.content.meaning), block('Why it matters', explanation.content.why_it_matters));
  detailPanel.append(block('What this does not prove', explanation.limitations.join(' ')));
  const previous = currentData.guidance_history?.[0]?.findings?.find((item) => item.finding_id === finding.finding_id);
  if (previous) {
    const saved = document.createElement('details');
    saved.className = 'detail-block';
    saved.append(text('summary', 'Guidance saved before the first refresh'));
    saved.append(text('p', previous.title), text('p', previous.fixed_explanation.meaning), text('p', previous.fixed_explanation.why_it_matters));
    previous.limitations.forEach((line) => saved.append(text('p', line)));
    previous.actions.forEach((action) => saved.append(text('p', `${action.text} ${action.verification}`)));
    detailPanel.append(saved);
  }
  if (explanation.aiAssisted) {
    const original = document.createElement('details');
    original.className = 'detail-block';
    original.append(text('summary', 'Original rule-based explanation'));
    original.append(text('p', finding.title));
    original.append(text('p', finding.fixed_explanation.meaning));
    original.append(text('p', finding.fixed_explanation.why_it_matters));
    finding.limitations.forEach((item) => original.append(text('p', item)));
    detailPanel.append(original);
  }
  const evidence = document.createElement('details');
  evidence.className = 'detail-block';
  evidence.append(text('summary', 'Technical evidence'));
  finding.evidence.forEach((item) => evidence.append(text('p', `${item.field}: ${item.value}`)));
  detailPanel.append(evidence);
  if (service?.script_results?.length) {
    const safeChecks = document.createElement('details');
    safeChecks.className = 'detail-block';
    safeChecks.append(text('summary', 'Technical service checks'));
    service.script_results.forEach((item) => safeChecks.append(text('p', `${item.script_id}: ${item.output}`)));
    detailPanel.append(safeChecks);
  }
  const actions = text('div', '', 'detail-block recommendation');
  actions.append(text('h4', 'Recommended steps'));
  const list = document.createElement('ol');
  list.className = 'remediation-list';
  finding.actions.forEach((action, index) => {
    const step = explanation.aiFields.includes('recommended_steps')
      ? explanation.content.recommended_steps[index] || action.text
      : action.text;
    const check = explanation.aiFields.includes('how_to_check')
      ? explanation.content.how_to_check[index] || action.verification
      : action.verification;
    const item = document.createElement('li');
    item.append(text('span', `${step} ${check}`));
    if (step !== action.text || check !== action.verification) {
      const original = document.createElement('details');
      original.append(text('summary', 'Original rule-based step'));
      original.append(text('p', `${action.text} ${action.verification}`));
      item.append(original);
    }
    list.append(item);
  });
  actions.append(list);
  detailPanel.append(actions);
  const references = text('div', '', 'detail-block');
  const referenceList = document.createElement('ul');
  (finding.references || []).forEach((reference) => {
    try {
      const url = new URL(reference.url);
      if (url.protocol !== 'https:') return;
      const item = document.createElement('li');
      const link = document.createElement('a');
      link.href = url.href;
      link.textContent = reference.title || 'Read more';
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      item.append(link);
      referenceList.append(item);
    } catch {
      // Invalid references are ignored instead of becoming clickable links.
    }
  });
  if (referenceList.childElementCount) {
    references.append(text('h4', 'Learn more'), referenceList);
    detailPanel.append(references);
  }
}

function renderFindings(data) {
  currentData = data;
  const currentFindings = prioritise(data.findings);
  const visible = visibleFindings(currentFindings);
  findingsList.replaceChildren();
  const explanationNote = ` ${aiExplanationNote(data)}`;
  summary.textContent = currentFindings.length
    ? ((visible.length === currentFindings.length
      ? `Showing all ${currentFindings.length} findings.${explanationNote}`
      : `Showing ${visible.length} of ${currentFindings.length} findings from this scan.${explanationNote}`))
    : emptyFindingMessage(data);
  if (!visible.length) {
    findingsList.append(text('div', currentFindings.length
      ? 'No findings match the selected filter or search.'
      : emptyFindingMessage(data), 'empty-state'));
    showDetail(null);
    return;
  }
  const selected = visible.find((finding) => finding.finding_id === selectedFinding) || visible[0];
  selectedFinding = selected.finding_id;
  visible.forEach((finding) => {
    const config = severityConfig[finding.severity] || severityConfig.informational;
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `finding-card${selectedFinding === finding.finding_id ? ' selected' : ''}`;
    button.setAttribute('aria-pressed', String(selectedFinding === finding.finding_id));
    button.style.setProperty('--severity-color', config.color);
    const bar = text('span', '', 'severity-bar');
    const main = text('span', '', 'finding-main');
    const meta = text('span', '', 'finding-meta');
    const device = data.devices.find((item) => item.device_id === finding.device_id);
    const service = data.services.find((item) => item.service_id === finding.service_id);
    const deviceLabel = device ? `${device.hostname || 'Unknown device'} · ${device.ip}` : 'Observed device';
    const serviceLabel = formatServiceLabel(service);
    const explanation = explanationFor(finding);
    meta.append(text('span', config.label, 'severity-badge'), text('span', deviceLabel, 'device-name'));
    main.append(meta, text('h3', explanation.title), text('p', `${serviceLabel} · ${explanation.content.meaning}`));
    button.append(bar, main, text('span', '›', 'chevron'));
    button.addEventListener('click', () => { selectedFinding = finding.finding_id; renderFindings(data); showDetail(finding); });
    findingsList.append(button);
  });
  showDetail(selected);
}

function renderNextSteps(data) {
  nextStepsList.replaceChildren();
  const steps = prioritise(data.findings).flatMap((finding) => (finding.actions || []).slice(0, 1).map((action) => ({ finding, action }))).slice(0, 3);
  if (!steps.length) {
    nextStepsList.append(text('li', emptyFindingMessage(data), 'empty-state'));
    return;
  }
  steps.forEach(({ finding, action }, index) => {
    const item = document.createElement('li');
    const copy = document.createElement('div');
    const explanation = explanationFor(finding);
    const actionIndex = finding.actions.findIndex((candidate) => candidate.action_id === action.action_id);
    const step = explanation.aiFields.includes('recommended_steps')
      ? explanation.content.recommended_steps[actionIndex] || action.text
      : action.text;
    const check = explanation.aiFields.includes('how_to_check')
      ? explanation.content.how_to_check[actionIndex] || action.verification
      : action.verification;
    const guidance = [step, check].filter(Boolean).join(' ');
    item.append(text('span', String(index + 1)), copy);
    const device = data.devices.find((item) => item.device_id === finding.device_id);
    copy.append(text('strong', explanation.title), text('p', device ? `${device.hostname || 'Device'} · ${device.ip}` : 'Observed device'), text('p', guidance));
    nextStepsList.append(item);
  });
}

function renderDevices(data) {
  deviceTableBody.replaceChildren();
  if (!data.devices.length) {
    const emptyRow = document.createElement('tr');
    const emptyCell = text('td', 'No devices responded to the selected discovery or service checks.', 'device-table-empty');
    emptyCell.colSpan = 7;
    emptyRow.append(emptyCell);
    deviceTableBody.append(emptyRow);
    return;
  }
  data.devices.forEach((device) => {
    const services = data.services.filter((item) => item.device_id === device.device_id && item.state === 'open');
    const deviceFindings = data.findings.filter((finding) => finding.device_id === device.device_id);
    const checks = [
      ...(device.host_script_results || []),
      ...services.flatMap((service) => (service.script_results || []).map((check) => ({
        ...check, location: formatServiceLabel(service),
      }))),
    ];
    const checkCell = text('td', 'No additional details were returned; this does not mean checks passed.');
    if (checks.length) {
      checkCell.textContent = '';
      const details = document.createElement('details');
      details.append(text('summary', `${checks.length} additional check results — view details`));
      details.append(text('p', 'These are observations, not a count of passed security tests.'));
      checks.forEach((check) => {
        details.append(text('p', `${check.location ? `${check.location}: ` : ''}${checkSummary(check)}`));
        const technical = document.createElement('details');
        technical.append(text('summary', 'Technical result'), text('p', `${check.script_id}: ${check.output}`));
        details.append(technical);
      });
      checkCell.append(details);
    }
    const row = document.createElement('tr');
    [
      device.hostname || 'Unknown device',
      device.ip,
      deviceCategory(device),
      device.reachability === 'observed' ? 'Responded' : 'Not confirmed',
      services.map((item) => formatServiceLabel(item)).join(', ') || 'None found in selected checks',
    ].forEach((value) => row.append(text('td', value)));
    row.append(checkCell, text('td', String(deviceFindings.length)));
    deviceTableBody.append(row);
  });
}

function renderAdvertisements(data) {
  const observations = (data.observations || []).filter((item) => item.source === 'mdns');
  mdnsSection.hidden = observations.length === 0;
  mdnsList.replaceChildren();
  observations.forEach((item) => {
    mdnsList.append(text('li', `${item.advertised_name || 'Unnamed device'} (${item.ip}) advertised ${item.service_type}. This has not been verified as an open service.`));
  });
}

function render(data) {
  const openServices = data.services.filter((service) => service.state === 'open').length;
  const stateLabels = {
    queued: 'Waiting to start', running: 'Scanning', completed: 'Completed',
    partial: 'Partly completed', failed: 'Could not complete', cancelled: 'Cancelled',
  };
  title.textContent = data.state === 'completed' ? 'Your local scan is ready.' : `${stateLabels[data.state] || 'Scan status unknown'}.`;
  lead.textContent = `Recorded ${data.devices.length} device result${data.devices.length === 1 ? '' : 's'} and ${openServices} open connection${openServices === 1 ? '' : 's'} among the selected checks.`;
  const fallbackTcpPorts = [21, 22, 23, 80, 443, 445, 554, 1883, 3389, 5900, 8080, 8443];
  const tcpPorts = data.policy?.tcp_ports || data.policy?.ports || fallbackTcpPorts;
  const udpPorts = data.policy?.udp_ports || [];
  const deep = data.policy?.profile === 'deep-tcp-v1';
  const profileLabel = deep
    ? `All TCP ports + ${udpPorts.length} selected UDP checks + safe service checks`
    : `${tcpPorts.length} TCP + ${udpPorts.length} UDP selected checks`;
  const ports = deep
    ? `UDP: ${udpPorts.join(', ')}`
    : `TCP: ${tcpPorts.join(', ')} · UDP: ${udpPorts.join(', ')}`;
  technicalStatus.textContent = data.target?.cidr
    ? `Scope: ${data.target.cidr} \u00b7 ${profileLabel}: ${ports}`
    : `Known-host scan \u00b7 Discovery was not performed \u00b7 ${profileLabel}: ${ports}`;
  status.textContent = data.target?.cidr
    ? 'Checked only the authorised local network range. Devices that did not respond may still exist.'
    : 'Checked only the device addresses you supplied; other devices were not discovered.';
  state.textContent = stateLabels[data.state] || data.state;
  count.textContent = data.findings.length;
  ring.style.setProperty('--score', Math.min(100, data.findings.length * 12));
  coverage.textContent = coverageSummary(data);
  scanProblems.replaceChildren();
  const problems = [...(data.errors || []), ...(data.warnings || [])];
  (data.coverage?.targets || []).filter((target) => ['failed', 'timed_out', 'cancelled'].includes(target.service_status)).forEach((target) => {
    const reason = target.service_status === 'timed_out' ? 'took too long and stopped' : 'did not finish';
    problems.push({ message: `The device check for ${target.ip} ${reason}. Its remaining checks were not assessed.` });
  });
  scanProblems.hidden = !problems.length;
  if (problems.length) {
    scanProblems.append(text('strong', 'What could not be completed'));
    const list = document.createElement('ul');
    problems.forEach((problem) => list.append(text('li', problem.message || 'A check did not complete.')));
    scanProblems.append(list);
  }
  const outdatedAi = (data.explanations || []).some((record) => record.source === 'ai' && record.prompt_version !== data.guidance_status?.ai_prompt_version);
  refreshGuidanceButton.hidden = !data.guidance_status?.refresh_available;
  refreshGuidanceButton.disabled = data.phase !== 'finished' || ['queued', 'running'].includes(data.state);
  guidanceNotice.textContent = data.guidance_status?.refresh_available
    ? 'This saved report has older guidance. Refresh it using the saved observations; previous guidance is kept and no network scan is run.'
    : data.guidance_status?.outdated_findings
      ? 'Some older guidance cannot be refreshed from the saved evidence. Run a new scan to reassess those findings.'
      : data.guidance_updated_at ? 'Guidance was refreshed from saved observations. The original scan date and evidence are unchanged.' : '';
  if (outdatedAi) guidanceNotice.textContent += ' Older AI wording is hidden because it predates the current validation checks. You can request local AI wording again.';
  document.querySelector('#finding-metric').textContent = data.findings.length;
  document.querySelector('#device-metric').textContent = data.devices.length;
  document.querySelector('#service-metric').textContent = openServices;
  renderFilterCounts(data.findings);
  renderFindings(data);
  renderDevices(data);
  renderAdvertisements(data);
  renderNextSteps(data);
  simplifyButton.hidden = !['completed', 'partial'].includes(data.state) || !data.findings.length;
  simplifyButton.disabled = data.phase === 'analysis' || data.ai_requests_used >= 12;
  simplifyButton.textContent = data.ai_requests_used >= 12
    ? 'AI request limit reached'
    : data.ai_requests_used ? 'Try local AI wording again' : 'Simplify this saved report';
}

async function poll() {
  try {
    const data = await request(`/api/live-scans/${scanId}`);
    render(data);
    if (data.state === 'queued' || data.state === 'running' || data.phase === 'analysis') {
      window.setTimeout(poll, 1000);
    }
  } catch (error) {
    title.textContent = 'Scan results unavailable';
    lead.textContent = error.message;
  }
}

poll();
