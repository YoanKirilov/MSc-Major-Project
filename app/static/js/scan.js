import { request } from './api.js?v=20261001-network-recovery';
import { createTextEditor } from './editor.mjs?v=20261008-ui-ux';
import { renderFindingList, findingDeviceOptions, repeatedUnknownReplies } from './finding-list.mjs?v=20261012-followups';
import { createReadingState, openDisclosureKeys, restoreDisclosures, bindReportNavigation } from './report-view.mjs?v=20261012-followups';
import { renderDeviceSummaries as renderDeviceComponents, deviceResultEntries } from './devices.mjs?v=20261012-reading';
import { createCvePanel } from './cves.mjs?v=20261002-cve';
import { createNoteState, checkStatus, projectNotes } from './notes.mjs?v=20261012-followups';
import { createNicknameState, projectNicknames } from './nicknames.mjs?v=20261007-followup';
import { recordedTimeLabel, localFeatureHelp, scanComputerCoverage, actionDeviceLabel, recordedDeviceRole, matchesSearch, deviceSearchValues, deviceLabel, reviewItemTitle, confidenceLabel, actionGuidance, pendingWording, wordingLabels, savedCheckNote, webPageInstructions, firstActionPrecaution } from './presentation.mjs?v=20261012-reading';
import { partialScanTitle, prioritise, serviceLabel as formatServiceLabel, coverageSummary, deviceCheckLabel, completedCheckSummary, emptyFindingMessage, usableAiRecord, checkSummary, analysisProgressText, scanSetupLink, readScanSetup } from './report.mjs?v=20261007-clarity';

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
const priorityBreakdown = document.querySelector('#priority-breakdown');
const coverage = document.querySelector('#result-coverage');
const summary = document.querySelector('#resultsSummary');
const findingsList = document.querySelector('#findingsList');
const detailPanel = document.querySelector('#detailPanel');
const deviceTableBody = document.querySelector('#device-table-body');
const deviceSummaries = document.querySelector('#device-summaries');
const mdnsSection = document.querySelector('#mdns-section');
const mdnsList = document.querySelector('#mdns-list');
const runAgainButton = document.querySelector('#runAgainButton');
const runAgainDialog = document.querySelector('#runAgainDialog');
const sameDeviceButton = document.querySelector('#sameDeviceButton');
const anotherDeviceButton = document.querySelector('#anotherDeviceButton');
const cancelRunAgainButton = document.querySelector('#cancelRunAgainButton');
const runAgainDevice = document.querySelector('#runAgainDevice');
const simplifyButton = document.querySelector('#simplifyButton');
const refreshGuidanceButton = document.querySelector('#refreshGuidanceButton');
const guidanceNotice = document.querySelector('#guidance-notice');
const scanProblems = document.querySelector('#scan-problems');
const searchInput = document.querySelector('#searchInput');
const reviewDevice = document.querySelector('#reviewDevice');
let reviewDeviceSignature = '';
const filterButtons = [...document.querySelectorAll('.filter-chip')];
const nextStepsList = document.querySelector('#nextStepsList');
const reportContent = document.querySelector('#report-content');
const retryHostsButton = document.querySelector('#retryHostsButton');
const guidanceArchives = document.querySelector('#guidance-archives');
const reportFirstStep = document.querySelector('#report-first-step');
const reportChecks = document.querySelector('#report-checks');
let selectedFinding = null;
let currentData = null;
let activeFilter = 'all';
let searchTerm = '';
let checklistSaving = false;
let revealFilteredTasks = false;
const notes = createNoteState(snapshot => {
  projectNotes(document, snapshot, {
    disabled: checklistSaving || currentData?.phase !== 'finished', data: currentData,
    expandFiltered: revealFilteredTasks,
  });
  revealFilteredTasks = false;
});
const expandedDevices = new Map();
const expandedSteps = new Map();
const editor = createTextEditor(document);
const deviceSearchInput = document.querySelector('#deviceSearchInput');
let deviceSearchTerm = '';
let deviceLimit = 24;
let detailSignature = '';
let tasksSignature = '';
let nicknamePollScheduled = false;
const nicknameState = createNicknameState();
let nicknameSaving = false;
const retryReportLoad = document.querySelector('#retryReportLoad');
retryReportLoad.addEventListener('click', () => { retryReportLoad.disabled = true; poll(); });
const readingState = createReadingState(() => window.sessionStorage, scanId);
const savedReading = readingState.load();
const textAlignment = document.querySelector('#textAlignment');
textAlignment.value = savedReading?.alignment || 'justify';
document.body.dataset.textAlignment = textAlignment.value;
textAlignment.addEventListener('change', () => {
  document.body.dataset.textAlignment = textAlignment.value === 'left' ? 'left' : 'justify';
  rememberReading();
});
document.addEventListener?.('click', event => {
  if (!event.target?.closest?.('[data-glossary-link]')) return;
  event.preventDefault();
  const glossary = document.querySelector('#report-glossary');
  glossary.open = true;
  glossary.scrollIntoView({ block: 'start', behavior: 'instant' });
  glossary.querySelector('summary').focus({ preventScroll: true });
});
let readingRestored = false;
let restoringReading = Boolean(savedReading);
if (savedReading) {
  selectedFinding = savedReading.selected;
  activeFilter = savedReading.filter;
  searchInput.value = savedReading.search;
  searchTerm = savedReading.search.trim().toLowerCase();
  deviceSearchInput.value = savedReading.devices;
  deviceSearchTerm = savedReading.devices.trim().toLowerCase();
  deviceLimit = savedReading.limit;
  document.querySelector('#deviceSort').value = savedReading.sort;
  document.querySelector('#checklist-filter').value = savedReading.tasks;
  filterButtons.forEach(button => {
    const active = button.dataset.filter === activeFilter;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
}
bindReportNavigation(document, window);
if (window.history && 'scrollRestoration' in window.history) window.history.scrollRestoration = 'manual';

function rememberReading() {
  if (restoringReading || currentData?.phase !== 'finished') return;
  readingState.save({ version: 1, selected: selectedFinding,
    search: searchInput.value, devices: deviceSearchInput.value, filter: activeFilter,
    tasks: document.querySelector('#checklist-filter').value,
    sort: document.querySelector('#deviceSort').value, limit: deviceLimit,
    alignment: document.body.dataset.textAlignment,
    reviewDevice: reviewDevice.value,
    open: openDisclosureKeys(document), y: window.scrollY || 0 });
}
for (const event of ['input', 'change', 'click', 'toggle']) {
  document.addEventListener?.(event, () => window.setTimeout(rememberReading, 0), true);
}
window.addEventListener?.('pagehide', rememberReading);
let readingScrollTimer;
window.addEventListener?.('scroll', () => {
  window.clearTimeout(readingScrollTimer);
  readingScrollTimer = window.setTimeout(rememberReading, 150);
}, { passive: true });

function restoreReading() {
  if (readingRestored) return;
  readingRestored = true;
  const apply = () => {
    if (savedReading) {
      restoreDisclosures(document, savedReading.open);
      deviceSummaries.querySelectorAll('.device-summary-group').forEach(group => {
        expandedDevices.set(group.dataset.deviceIp, group.querySelector('.device-summary').open);
      });
      nextStepsList.querySelectorAll('.next-step-checklist').forEach(detail => {
        expandedSteps.set(detail.dataset.findingId, detail.open);
      });
      notes.refresh();
    }
    const scroll = () => {
      const anchors = ['first-action', 'devices-title', 'findings-title', 'next-title', 'changes-title'];
      const anchor = window.location.hash?.slice(1);
      const navigation = window.performance?.getEntriesByType('navigation')[0]?.type;
      const returning = savedReading && ['reload', 'back_forward'].includes(navigation);
      if (!returning && anchors.includes(anchor)) document.querySelector(`#${anchor}`)?.scrollIntoView({ block: 'start' });
      else if (savedReading) window.scrollTo({ top: savedReading.y, behavior: 'instant' });
      restoringReading = false;
      reportContent.inert = false;
      reportContent.dataset.readingReady = 'true';
    };
    if (window.requestAnimationFrame) window.requestAnimationFrame(scroll);
    else scroll();
  };
  // Native disclosure layout and the sticky-nav offset must settle before scrolling.
  if (window.requestAnimationFrame) window.requestAnimationFrame(apply);
  else apply();
}

function refreshNicknameProjection() {
  if (!currentData || currentData.phase !== 'finished' || !Array.isArray(currentData.devices)) return;
  const focused = document.activeElement;
  const identity = focused?.dataset;
  const inNextSteps = Boolean(focused?.closest?.('.next-step-checklist'));
  projectNicknames(currentData, nicknameState);
  renderFindings(currentData);
  renderDevices(currentData);
  renderNextSteps(currentData);
  renderBeginnerGuide(currentData);
  notes.refresh();
  if (document.activeElement === document.body && identity) {
    const controls = identity.nicknameDevice ? document.querySelectorAll('[data-nickname-device]')
      : identity.findingId ? document.querySelectorAll(inNextSteps ? '#nextStepsList .action-check select' : '#detailPanel .action-check select') : [];
    const replacement = [...controls].find(control => identity.nicknameDevice
      ? control.dataset.nicknameDevice === identity.nicknameDevice
      : control.dataset.findingId === identity.findingId && control.dataset.actionId === identity.actionId);
    if (!replacement?.disabled) replacement?.focus({ preventScroll: true });
  }
}

function adoptNicknameSnapshot(update) {
  const previous = nicknameState.value;
  if (!nicknameState.apply(update)) return false;
  const notice = nicknameState.value.recovery_notice;
  if (notice && notice !== previous?.recovery_notice) status.textContent += ` ${notice}`;
  if (currentData) delete currentData.nickname_error;
  refreshNicknameProjection();
  return true;
}

function actionChecklist(finding, action) {
  const container = text('div', '', 'action-check');
  const device = currentData?.devices.find(item => item.device_id === finding.device_id);
  const service = currentData?.services.find(item => item.service_id === finding.service_id);
  const label = document.createElement('label');
  const explanation = explanationFor(finding);
  const actionIndex = finding.actions.findIndex(item => item.action_id === action.action_id);
  const step = explanation.content.recommended_steps?.[actionIndex] || action.text;
  label.append(text('span', 'Your review status'), text('span', ` for ${actionDeviceLabel(device, currentData)}${service ? `, ${formatServiceLabel(service)}` : ''}: ${step}`, 'sr-only'));
  const select = document.createElement('select');
  select.dataset.findingId = finding.finding_id;
  select.dataset.actionId = action.action_id;
  const feedback = text('p', '', 'action-check-note');
  feedback.setAttribute('role', 'status');
  feedback.hidden = true;
  for (const [value, name] of [['to_check', 'To check'], ['checked', 'Checked'], ['need_help', 'Need help']]) {
    const option = text('option', name);
    option.value = value;
    select.append(option);
  }
  select.value = checkStatus(notes.value, finding.finding_id, action.action_id);
  select.disabled = !notes.value || checklistSaving || currentData?.phase !== 'finished';
  select.addEventListener('change', async () => {
    if (!notes.value || checklistSaving) return;
    const hadFocus = document.activeElement === select;
    container.dataset.editing = 'true';
    checklistSaving = true;
    document.querySelectorAll('.action-check select').forEach(control => { control.disabled = true; });
    const notice = document.querySelector('#checklist-notice');
    notice.textContent = 'Saving your checklist…';
    feedback.hidden = false;
    feedback.textContent = notice.textContent;
    try {
      notes.apply(await request(`/api/live-scans/${scanId}/action-checks`, {
        method: 'PUT', body: JSON.stringify({ finding_id: finding.finding_id, action_id: action.action_id,
          status: select.value, expected_revision: notes.value.revision }),
      }));
      notice.textContent = 'Checklist saved. This records your review; the scan results have not changed.';
    } catch (error) {
      try { notes.apply(await request(`/api/live-scans/${scanId}/annotations`)); }
      catch { notes.apply(null); }
      notice.textContent = `Your checklist change was not saved. ${error.message}${notes.value ? ' Latest notes loaded; review the saved status before trying again.' : ' Reload to reconnect to saved notes.'}`;
    } finally {
      checklistSaving = false;
      notes.refresh();
      feedback.textContent = notice.textContent;
      if (hadFocus && document.activeElement === document.body && !select.disabled) select.focus({ preventScroll: true });
      delete container.dataset.editing;
    }
  });
  label.append(select);
  container.append(label, feedback);
  return container;
}

document.querySelector('#editReportTitle').addEventListener('click', event => {
  if (!notes.value || checklistSaving) return;
  let expectedRevision = notes.value.revision;
  editor.open({
    title: 'Name this saved report', label: 'Your report title', maxLength: 100,
    value: notes.value.title || '', trigger: event.currentTarget,
    resolveTrigger: () => document.querySelector('#editReportTitle'),
    hint: 'Use up to 100 characters. Leave empty to remove your title. Scan observations are unchanged.',
    onSave: async value => {
      try {
        notes.apply(await request(`/api/live-scans/${scanId}/title`, {
          method: 'PUT', body: JSON.stringify({ title: value, expected_revision: expectedRevision }),
        }));
        updateDocumentTitle();
      } catch (error) {
        try { notes.apply(await request(`/api/live-scans/${scanId}/annotations`)); } catch { notes.apply(null); }
        if (notes.value) expectedRevision = notes.value.revision;
        throw new Error(`Your title was not saved. ${error.message} ${notes.value ? 'Latest saved title: ' + (notes.value.title || '(no title)') + '. Review your draft before saving again.' : 'Reconnect before trying again.'}`);
      }
    },
  });
});

document.querySelector('#checklist-filter').addEventListener('change', () => {
  revealFilteredTasks = true;
  notes.refresh();
});
document.querySelector('#expandReviewTasks').addEventListener('click', () => {
  document.querySelectorAll('.next-step-checklist').forEach(item => {
    if (!item.closest('li')?.hidden) item.open = true;
  });
});
document.querySelector('#collapseReviewTasks').addEventListener('click', () => {
  document.querySelectorAll('.next-step-checklist').forEach(item => {
    if (item.closest('li')?.hidden) return;
    item.open = false;
    expandedSteps.set(item.dataset.findingId, false);
  });
});
deviceSearchInput.addEventListener('input', () => {
  deviceSearchTerm = deviceSearchInput.value.trim().toLowerCase();
  deviceLimit = 24;
  if (currentData) renderDevices(currentData);
});
document.querySelector('#clearDeviceSearch').addEventListener('click', () => {
  deviceSearchInput.value = '';
  deviceSearchTerm = '';
  deviceLimit = 24;
  if (currentData) renderDevices(currentData);
  deviceSearchInput.focus({ preventScroll: true });
});
document.querySelector('#deviceSort').addEventListener('change', () => {
  deviceLimit = 24;
  if (currentData) renderDevices(currentData);
});
document.querySelector('#showMoreDevices').addEventListener('click', () => {
  deviceLimit += 24;
  if (currentData) renderDevices(currentData);
});
const compactResults = window.matchMedia('(max-width: 880px)');
compactResults.addEventListener('change', () => { if (currentData) renderFindings(currentData); });

function updateDocumentTitle() {
  const profile = currentData?.policy?.profile === 'deep-tcp-v1' ? 'Deep' : 'Light';
  document.title = `${notes.value?.title || profile + ' scan report'} — ${recordedTimeLabel(currentData?.created_at, 'Date unavailable')} — NetGuard AI`;
}

function scheduleNicknameRefresh() {
  if (nicknamePollScheduled) return;
  nicknamePollScheduled = true;
  window.setTimeout(async () => {
    nicknamePollScheduled = false;
    if (currentData?.phase === 'finished' && !document.hidden && !nicknameSaving) {
      try {
        const update = await request(`/api/live-scans/${scanId}/nicknames${nicknameState.available ? `?revision=${nicknameState.value.revision}` : ''}`);
        // Unchanged replies still carry recovery notices, but need no destructive redraw.
        if (update.changed || (update.recovery_notice || '') !== (nicknameState.value?.recovery_notice || '')) adoptNicknameSnapshot(update);
      } catch { /* Preserve the readable report and retry on the next visible poll. */ }
    }
    scheduleNicknameRefresh();
  }, 8000);
}

retryHostsButton.addEventListener('click', async () => {
  if (!currentData) return;
  retryHostsButton.disabled = true;
  try {
    const result = await request(`/api/live-scans/${scanId}/retry-hosts`, {
      method: 'POST', body: JSON.stringify({ expected_revision: currentData.revision }),
    });
    window.location.href = `/scans/${result.scan_id}`;
  } catch (error) {
    status.textContent = error.message;
    retryHostsButton.disabled = false;
  }
});

searchInput.addEventListener('input', () => {
  searchTerm = searchInput.value.trim().toLowerCase();
  if (currentData) renderFindings(currentData);
});
reviewDevice.addEventListener('change', () => {
  if (currentData) renderFindings(currentData);
});
document.querySelector('#clearSearchButton').addEventListener('click', () => {
  searchInput.value = '';
  searchTerm = '';
  if (currentData) renderFindings(currentData);
  searchInput.focus({ preventScroll: true });
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

runAgainButton.addEventListener('click', () => {
  if (!currentData) return;
  if (currentData.policy?.profile !== 'deep-tcp-v1') {
    window.location.href = scanSetupLink(currentData);
    return;
  }
  const setup = readScanSetup(scanSetupLink(currentData).slice(1));
  const host = setup?.hosts[0];
  sameDeviceButton.disabled = !host;
  runAgainDevice.textContent = host
    ? `Previous address: ${host}. Addresses can change; confirm the device before scanning.`
    : 'The previous device address is unavailable. Choose another device to continue.';
  runAgainDialog.showModal();
});
sameDeviceButton.addEventListener('click', () => {
  if (currentData && !sameDeviceButton.disabled) window.location.href = scanSetupLink(currentData);
});
anotherDeviceButton.addEventListener('click', () => {
  if (currentData) window.location.href = scanSetupLink(currentData, false);
});
cancelRunAgainButton.addEventListener('click', () => runAgainDialog.close());

simplifyButton.addEventListener('click', async () => {
  if (!currentData) return;
  simplifyButton.disabled = true;
  try {
    const aiStatus = await request('/api/status');
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

function deviceCategory(device) {
  if (device.user_category) return device.user_category;
  const labels = {
    camera: 'camera', printer: 'printer', router: 'router',
    iot_other: 'smart-home device', computer: 'computer', media: 'television or media device', unknown: 'unknown type',
  };
  const category = labels[device.profile?.category] || 'unknown type';
  return category === 'unknown type' ? 'Type not identified' : `Possible ${category}`;
}

function explanationFor(finding) {
  const record = (currentData?.explanations || []).find((item) => (
    item.finding_id === finding.finding_id
    && usableAiRecord(item, currentData)
  ));
  const plain = currentData?.plain_guidance?.[finding.finding_id];
  const aiFields = record?.ai_fields?.length ? record.ai_fields : (record ? ['meaning', 'why_it_matters'] : []);
  const content = { ...(plain?.content || finding.fixed_explanation) };
  for (const field of ['meaning', 'why_it_matters', 'recommended_steps', 'how_to_check']) {
    if (aiFields.includes(field) && record?.content?.[field] !== undefined) content[field] = record.content[field];
  }
  return {
    content,
    editorial: Boolean(plain),
    aiAssisted: Boolean(record),
    aiFields,
    title: (aiFields.includes('title') && record?.display_title) || plain?.title || finding.title,
    limitations: (aiFields.includes('limitations') && record?.display_limitations) || plain?.limitations || finding.limitations,
    rejectedFields: record?.rejected_fields || {},
  };
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
  detailPanel.dataset.findingId = finding?.finding_id || '';
  const device = currentData?.devices.find(item => item.device_id === finding?.device_id);
  const service = currentData?.services.find(item => item.service_id === finding?.service_id);
  const explanation = finding ? explanationFor(finding) : null;
  const signature = JSON.stringify([finding, deviceLabel(device || {}), service, explanation, currentData?.guidance_history]);
  if (signature === detailSignature) { notes.refresh(); return; }
  detailSignature = signature;
  detailPanel.replaceChildren();
  if (!finding) {
    detailPanel.append(text('strong', 'No review item selected'), text('p', 'Select a review item to inspect what was observed and the suggested checks.'));
    return;
  }
  const config = severityConfig[finding.severity] || severityConfig.informational;
  const top = text('div', '', 'detail-topline');
  top.append(text('span', finding.severity === 'informational' ? 'Review item' : config.label + ' priority', 'severity-badge'),
    text('span', confidenceLabel(finding.confidence) + ' — not a safety rating', 'confidence'));
  detailPanel.style.setProperty('--severity-color', config.color);
  const deviceDescription = device ? deviceLabel(device) + ' · ' + device.ip : 'Observed device';
  detailPanel.append(top, text('h3', reviewItemTitle(finding, service, explanation.title)),
    text('p', deviceDescription + ' · ' + formatServiceLabel(service), 'detail-location'));
  const block = (heading, value, className = 'detail-block') => {
    const section = text('div', '', className);
    section.append(text('h4', heading), text('p', value));
    return section;
  };
  detailPanel.append(block('What we found', explanation.content.meaning));
  const featureHelp = localFeatureHelp(device, service, currentData);
  if (featureHelp) {
    const purpose = block(service.name === 'tcpwrapped' ? 'Why its purpose is unknown' : 'What this feature may do', featureHelp.meaning);
    purpose.append(text('p', featureHelp.limitation, 'context-note'));
    detailPanel.append(purpose);
  }
  detailPanel.append(block('What this means for you', explanation.content.why_it_matters));
  if (explanation.limitations.length) {
    detailPanel.append(block('What we could not confirm', explanation.limitations.join(' ')));
  }
  const actions = text('div', '', 'detail-block recommendation');
  actions.append(text('h4', 'What to do next'));
  const list = document.createElement('ol');
  list.className = 'remediation-list';
  finding.actions.forEach((action, index) => {
    const step = explanation.editorial || explanation.aiFields.includes('recommended_steps')
      ? explanation.content.recommended_steps[index] || action.text : action.text;
    const check = explanation.editorial || explanation.aiFields.includes('how_to_check')
      ? explanation.content.how_to_check[index] || action.verification : action.verification;
    const item = document.createElement('li');
    item.append(text('span', actionGuidance(step, check)), actionChecklist(finding, action));
    if (step !== action.text || check !== action.verification) {
      const original = document.createElement('details');
      original.append(text('summary', 'Original rule-based step'), text('p', action.text + ' ' + action.verification));
      item.append(original);
    }
    list.append(item);
  });
  if (list.childElementCount) { actions.append(list); detailPanel.append(actions); }
  const pageHelp = webPageInstructions(device, service);
  const savedCheck = savedCheckNote(device, service);
  if (featureHelp?.check || pageHelp || savedCheck) {
    const practical = text('div', '', 'detail-block practical-help');
    practical.append(text('h4', 'Where to look and what to check'));
    if (featureHelp?.check) practical.append(text('p', featureHelp.check));
    if (pageHelp) practical.append(text('p', pageHelp));
    if (savedCheck) practical.append(text('p', savedCheck));
    detailPanel.append(practical);
  }
  const help = document.createElement('details');
  help.className = 'detail-block supporting-details';
  help.append(text('summary', 'Sources, explanation provenance and technical evidence'));
  help.append(text('p', explanation.aiAssisted
    ? 'Local AI contributed validated wording. Unaccepted fields keep reviewed rule-based guidance.'
    : 'This wording uses reviewed rule-based guidance from the saved observations.', 'explanation-source'));
  if (Object.keys(explanation.rejectedFields).length) {
    help.append(block('Wording checks', 'AI wording was not accepted for: ' + wordingLabels(explanation.rejectedFields) + '. Reviewed rule-based guidance is used instead.'));
    const diagnostics = document.createElement('details');
    diagnostics.append(text('summary', 'Technical wording checks'), text('p', JSON.stringify(explanation.rejectedFields)));
    help.append(diagnostics);
  }
  const previous = currentData.guidance_history?.[0]?.findings?.find(item => item.finding_id === finding.finding_id);
  if (previous) {
    const saved = document.createElement('details');
    saved.append(text('summary', 'Guidance saved before the first refresh'),
      text('p', previous.title), text('p', previous.fixed_explanation.meaning), text('p', previous.fixed_explanation.why_it_matters));
    previous.limitations.forEach(line => saved.append(text('p', line)));
    previous.actions.forEach(action => saved.append(text('p', action.text + ' ' + action.verification)));
    help.append(saved);
  }
  if (explanation.aiAssisted || explanation.editorial) {
    const original = document.createElement('details');
    original.append(text('summary', 'Original rule-based explanation'), text('p', finding.title),
      text('p', finding.fixed_explanation.meaning), text('p', finding.fixed_explanation.why_it_matters));
    finding.limitations.forEach(item => original.append(text('p', item)));
    help.append(original);
  }
  const evidence = document.createElement('details');
  evidence.append(text('summary', 'Technical evidence'));
  finding.evidence.forEach(item => evidence.append(text('p', item.field + ': ' + item.value)));
  help.append(evidence);
  if (service?.script_results?.length) {
    const checks = document.createElement('details');
    checks.append(text('summary', 'Technical service checks'));
    service.script_results.forEach(item => checks.append(text('p', item.script_id + ': ' + item.output)));
    help.append(checks);
  }
  const referenceList = document.createElement('ul');
  (finding.references || []).forEach(reference => {
    try {
      const url = new URL(reference.url);
      if (url.protocol !== 'https:') return;
      const item = document.createElement('li');
      const link = document.createElement('a');
      link.href = url.href;
      link.textContent = reference.title || 'Read more';
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      item.append(link); referenceList.append(item);
    } catch { /* Ignore unsafe or malformed source links. */ }
  });
  if (referenceList.childElementCount) help.append(text('h4', 'Learn more'), referenceList);
  detailPanel.append(help, cvePanel(service));
  notes.refresh();
}

function cvePanel(service) {
  return createCvePanel(document, scanId, service,
    notes.value?.cve_lookups?.find(item => item.service_id === service?.service_id),
    payload => payload.annotations ? notes.apply(payload.annotations) : true);
}

function renderFindings(data, { reveal = false, trigger = null } = {}) {
  currentData = data;
  const currentFindings = prioritise(data.findings, data.devices, data.services);
  const options = findingDeviceOptions(currentFindings, data.devices, deviceLabel);
  const optionSignature = JSON.stringify(options);
  if (reviewDeviceSignature !== optionSignature) {
    const selected = reviewDeviceSignature ? reviewDevice.value : savedReading?.reviewDevice || 'all';
    const all = text('option', `All devices (${currentFindings.length} items)`);
    all.value = 'all';
    reviewDevice.replaceChildren(all, ...options.map(item => {
      const option = text('option', `${item.label} (${item.count} item${item.count === 1 ? '' : 's'})`);
      option.value = item.id;
      return option;
    }));
    reviewDevice.value = options.some(item => item.id === selected) ? selected : 'all';
    reviewDevice.disabled = options.length === 0;
    reviewDeviceSignature = optionSignature;
  }
  const searchMatches = currentFindings.filter(finding => (reviewDevice.value === 'all' || finding.device_id === reviewDevice.value) && findingMatchesSearch(finding, data));
  renderFilterCounts(searchMatches);
  const visible = searchMatches.filter(finding => activeFilter === 'all' || finding.severity === activeFilter);
  summary.textContent = currentFindings.length
    ? `Showing ${visible.length} of ${currentFindings.length} review items${reviewDevice.value === 'all' ? '' : ' for the selected device'}${searchTerm ? ' matching your search' : ''}${activeFilter !== 'all' ? ', ' + severityConfig[activeFilter].label + ' only' : ''}.`
    : emptyFindingMessage(data);
  const repeated = repeatedUnknownReplies(visible, data.services);
  const repeatedNote = document.querySelector('#repeated-replies-note');
  repeatedNote.hidden = repeated === 0;
  repeatedNote.textContent = repeated ? `${repeated} items below record connection replies whose features could not be identified. Each numbered connection is listed separately; these are not confirmed software problems. The cause of the early closes is unknown. Do not disable protection just to clear these items.` : '';
  if (!visible.length) {
    if (detailPanel.parentElement !== findingsList.parentElement) findingsList.parentElement.append(detailPanel);
    findingsList.replaceChildren(text('div', currentFindings.length
      ? 'No review items match these filters. Clear the search or choose All to see more.'
      : emptyFindingMessage(data), 'empty-state'));
    showDetail(null);
    return;
  }
  const selected = visible.find(finding => finding.finding_id === selectedFinding) || visible[0];
  selectedFinding = selected.finding_id;
  renderFindingList({
    document, container: findingsList, layout: findingsList.parentElement, panel: detailPanel,
    findings: visible, selectedId: selectedFinding, compact: compactResults.matches,
    describe: finding => {
      const config = severityConfig[finding.severity] || severityConfig.informational;
      const device = data.devices.find(item => item.device_id === finding.device_id);
      const service = data.services.find(item => item.service_id === finding.service_id);
      const explanation = explanationFor(finding);
      return { priority: config.label, color: config.color,
        device: device ? `${deviceLabel(device)} · ${device.ip}` : 'Observed device',
        title: reviewItemTitle(finding, service, explanation.title),
        feature: formatServiceLabel(service) };
    },
    onSelect: (id, button) => { selectedFinding = id; renderFindings(currentData, { reveal: true, trigger: button }); },
  });
  showDetail(selected);
  if (reveal) {
    const selectedButton = [...findingsList.querySelectorAll('.finding-card')].find(button => button.dataset.findingId === selectedFinding);
    (compactResults.matches ? selectedButton : detailPanel)?.scrollIntoView({ block: 'start', behavior: 'instant' });
    if (trigger?.isConnected) trigger.focus({ preventScroll: true });
    document.querySelector('#report-interaction-status').textContent = `Showing ${reviewItemTitle(selected, data.services.find(item => item.service_id === selected.service_id), explanationFor(selected).title)} for ${deviceLabel(data.devices.find(item => item.device_id === selected.device_id) || {})}.`;
  }
}

function findingMatchesSearch(finding, data) {
  if (!searchTerm) return true;
  const device = data.devices.find(item => item.device_id === finding.device_id);
  const service = data.services.find(item => item.service_id === finding.service_id);
  const explanation = explanationFor(finding);
  return matchesSearch(searchTerm, [explanation.title, explanation.content.meaning,
    ...explanation.limitations, ...deviceSearchValues(device || {}, service ? [service] : [])], device?.ip);
}

function openReviewItem(findingId, trigger) {
  activeFilter = 'all';
  searchTerm = '';
  searchInput.value = '';
  reviewDevice.value = 'all';
  filterButtons.forEach(button => {
    const active = button.dataset.filter === 'all';
    button.classList.toggle('active', active); button.setAttribute('aria-pressed', String(active));
  });
  selectedFinding = findingId;
  renderFindings(currentData, { reveal: true });
  detailPanel.focus({ preventScroll: true });
}

function renderNextSteps(data) {
  const signature = JSON.stringify([data.findings, data.devices.map(device => [device.device_id, device.hostname, device.user_nickname]), data.services.map(service => [service.service_id, service.name, service.port]), data.explanations, data.plain_guidance, currentOverview(data), data.plain_overview, data.state, data.phase, data.coverage, data.analysis_status, data.guidance_status]);
  if (signature === tasksSignature) { notes.refresh(); return; }
  tasksSignature = signature;
  nextStepsList.replaceChildren();
  const ordered = prioritise(data.findings, data.devices, data.services);
  let index = 0;
  for (const finding of ordered) {
    if (!finding.actions?.length) continue;
    const device = data.devices.find(item => item.device_id === finding.device_id);
    const service = data.services.find(item => item.service_id === finding.service_id);
    const explanation = explanationFor(finding);
    const group = document.createElement('li');
    const copy = document.createElement('div');
    group.append(text('span', String(++index)), copy);
    copy.append(text('strong', reviewItemTitle(finding, service, explanation.title)), text('p', `${actionDeviceLabel(device, data)} · ${formatServiceLabel(service)}`, 'review-task-context'));
    const checklist = document.createElement('details');
    checklist.className = 'next-step-checklist';
    checklist.dataset.findingId = finding.finding_id;
    checklist.open = expandedSteps.get(finding.finding_id) ?? false;
    checklist.addEventListener('toggle', () => expandedSteps.set(finding.finding_id, checklist.open));
    checklist.append(text('summary', `Record your review (${finding.actions.length} task${finding.actions.length === 1 ? '' : 's'})`));
    finding.actions.forEach((action, actionIndex) => {
      const task = text('div', '', 'review-task');
      const step = explanation.content.recommended_steps?.[actionIndex] || action.text;
      const check = explanation.content.how_to_check?.[actionIndex] || action.verification;
      task.dataset.findingId = finding.finding_id;
      task.dataset.actionId = action.action_id;
      task.append(text('p', actionGuidance(step, check)), actionChecklist(finding, action));
      checklist.append(task);
    });
    const open = text('button', 'Read the related review item', 'text-button');
    open.type = 'button';
    open.addEventListener('click', () => openReviewItem(finding.finding_id, open));
    copy.append(checklist, open);
    nextStepsList.append(group);
  }
  if (!index) {
    nextStepsList.append(text('li', emptyFindingMessage(data), 'empty-state'));
    const overview = currentOverview(data) || data.plain_overview;
    (overview?.content.recommended_steps || []).forEach(step => nextStepsList.append(text('li', step)));
  }
  notes.refresh();
}

function currentOverview(data) {
  const record = data.report_explanation;
  if (!['ready', 'failed'].includes(data.analysis_status) || !record || !usableAiRecord(record, data)) return null;
  const plain = data.plain_overview;
  const content = { ...(plain?.content || record.content) };
  const fields = record.ai_fields || [];
  for (const field of ['meaning', 'why_it_matters', 'recommended_steps', 'how_to_check']) {
    if (fields.includes(field) && record.content[field] !== undefined) content[field] = record.content[field];
  }
  return { ...record, content, limitations: fields.includes('limitations') ? record.display_limitations : plain?.limitations || record.display_limitations };
}

function renderBeginnerGuide(data) {
  const selfCheck = document.querySelector('#self-check-notice');
  selfCheck.hidden = !data.devices.some(device => recordedDeviceRole(device, data) === 'Computer that ran this scan');
  selfCheck.textContent = 'This report includes this computer. A program answering here does not prove that other devices or the internet can reach it; firewall access was not confirmed.';
  const overview = currentOverview(data) || data.plain_overview;
  const unfinished = (data.coverage?.service_failed_count || 0) > 0 || ['partial', 'failed', 'cancelled'].includes(data.state);
  const first = prioritise(data.findings, data.devices, data.services)[0];
  const firstDevice = data.devices.find(item => item.device_id === first?.device_id);
  const firstService = data.services.find(item => item.service_id === first?.service_id);
  reportFirstStep.textContent = first
    ? 'Start with ' + actionDeviceLabel(data.devices.find(item => item.device_id === first.device_id), data) + '. Confirm you recognise it before changing settings. ' + (explanationFor(first).content.recommended_steps?.[0] || first.actions?.[0]?.text || 'Open its review item below.')
    : overview?.content.recommended_steps?.join(' ') || (unfinished
      ? 'Retry the unfinished checks when those devices are available. Missing results cannot tell you whether a device is safe.'
      : 'Check which devices and features were observed. No listed review items does not prove everything is safe.');
  const precaution = document.querySelector('#first-action-precaution');
  precaution.textContent = firstActionPrecaution(firstDevice, firstService);
  precaution.hidden = !precaution.textContent;
  const open = document.querySelector('#openFirstFinding');
  open.hidden = !first;
  open.onclick = () => { if (first) openReviewItem(first.finding_id, open); };
  const identify = document.querySelector('#identifyFirstDevice');
  identify.hidden = !first?.device_id;
  identify.onclick = () => {
    const device = data.devices.find(item => item.device_id === first?.device_id);
    if (!device) return;
    deviceSearchInput.value = device.ip;
    deviceSearchTerm = device.ip;
    deviceLimit = 24;
    expandedDevices.set(device.ip, true);
    renderDevices(currentData);
    // Recognition is an explicit request to reveal this device, unlike a
    // background nickname refresh that must preserve collapsed disclosures.
    const group = [...deviceSummaries.querySelectorAll('.device-summary-group')]
      .find(item => item.dataset.deviceIp === device.ip);
    const card = group?.querySelector('.device-summary');
    if (card) card.open = true;
    expandedDevices.set(device.ip, true);
    const button = nicknameTrigger(device);
    const target = button || document.querySelector('#device-summaries summary');
    target?.scrollIntoView({ block: 'center', behavior: 'instant' });
    target?.focus({ preventScroll: true });
  };
  reportChecks.textContent = completedCheckSummary(data);
  const computerCoverage = document.querySelector('#scan-computer-coverage');
  computerCoverage.textContent = scanComputerCoverage(data);
  computerCoverage.hidden = !computerCoverage.textContent;
}

function deviceMatchesSearch(device, data) {
  const services = data.services.filter(item => item.device_id === device.device_id);
  return matchesSearch(deviceSearchTerm, deviceSearchValues(device, services), device.ip);
}

function renderComparisons(data) {
  const earlier = data.earlier_observations;
  document.querySelector('#earlier-devices-note').textContent = earlier?.reason
    || 'This saved report has no earlier-device comparison. Run a new Light network scan to record one; no conclusion about missing devices is available.';
  const earlierList = document.querySelector('#earlier-devices-list');
  earlierList.replaceChildren();
  if (earlier?.status === 'available') {
    for (const item of earlier.items || []) {
      if (!matchesSearch(deviceSearchTerm, [item.reported_name, item.last_ip, item.name_source], item.last_ip)) continue;
      earlierList.append(text('li', `${item.reported_name || 'No unambiguous name recorded'} (reported earlier). Last recorded address: ${item.last_ip}. Source: ${item.name_source || 'not recorded'}; observed ${recordedTimeLabel(item.observed_at)}.`));
    }
    if (!earlierList.childElementCount) earlierList.append(text('li', deviceSearchTerm
      ? 'No earlier observations match this search.' : 'No unmatched earlier observations in the comparison available. This does not prove every device is present.'));
    if (earlier.omitted_count) earlierList.append(text('li', `${earlier.omitted_count} additional earlier observations are not displayed because this view is limited to 50.`));
    const source = text('a', 'Open the earlier source report');
    if (/^[0-9a-f-]{36}$/i.test(earlier.source_scan_id || '')) {
      source.href = `/scans/${earlier.source_scan_id}`;
      const item = document.createElement('li'); item.append(source); earlierList.append(item);
    }
  }
  let comparable = 0;
  let unavailable = 0;
  for (const device of data.devices.filter(item => deviceMatchesSearch(item, data))) {
    const details = (device.details || []).filter(item => item.kind === 'history');
    if (details.some(item => item.label === 'Service comparison' && item.status === 'inferred')) comparable++;
    else unavailable++;
  }
  document.querySelector('#comparison-summary').textContent = comparable || unavailable
    ? `For the matching devices: ${comparable} service comparison${comparable === 1 ? ' is' : 's are'} available; ${unavailable} could not be compared reliably. Open each device's About this device details for recorded differences.`
    : 'No saved comparison is available for these device results. A first scan or unmatched device can have no comparison; this does not mean nothing changed.';
}

function renderDeviceSummaries(data) {
  const rank = device => Math.min(4, ...data.findings.filter(item => item.device_id === device.device_id)
    .map(item => ({high:0, medium:1, low:2, informational:3})[item.severity] ?? 4));
  const mode = document.querySelector('#deviceSort').value;
  const projected = renderDeviceComponents({
    document, container: deviceSummaries, data, expandedDevices, matchesDevice: deviceMatchesSearch,
    explanationFor, createCvePanel: cvePanel, notesSnapshot: notes.value,
    nicknameAvailable: nicknameState.available, nicknameSaving, deviceLimit,
    sortDevices: (a, b) => (mode === 'priority' ? rank(a) - rank(b) : 0)
      || String(mode === 'name' ? deviceLabel(a) : a.ip).localeCompare(String(mode === 'name' ? deviceLabel(b) : b.ip), 'en', { numeric: true }),
    onEditNickname: editNickname, onRefreshName: refreshDeviceName, onViewFinding: openReviewItem,
  });
  document.querySelector('#naming-coverage').textContent = projected.namingText;
  document.querySelector('#device-search-count').textContent = projected.countText;
  const more = document.querySelector('#showMoreDevices');
  more.hidden = projected.visibleCount >= projected.matching.length;
  more.textContent = `Show more devices (${Math.max(0, projected.matching.length - projected.visibleCount)} remaining)`;
  document.querySelector('#devices-title').textContent = data.policy?.profile === 'deep-tcp-v1' && projected.entries.length === 1 ? 'This device' : 'Your devices';
}

function nicknameTrigger(device) {
  return [...document.querySelectorAll('[data-nickname-device]')].find(button => button.dataset.nicknameDevice === device.device_id);
}

function nicknameFeedback(device, message) {
  const group = [...deviceSummaries.querySelectorAll('.device-summary-group')].find(item => item.dataset.deviceId === device.device_id);
  if (!group) return;
  let feedback = group.querySelector('[data-nickname-status]');
  if (!feedback) {
    feedback = text('p', '', 'status-message'); feedback.dataset.nicknameStatus = 'true'; feedback.setAttribute('role', 'status');
    group.querySelector('.device-name-tools').append(feedback);
  }
  feedback.textContent = message;
}

function editNickname(device, trigger) {
  if (!nicknameState.available || nicknameSaving) return;
  let expectedRevision = nicknameState.value.revision;
  editor.open({
    title: 'Your nickname for this device', label: 'Your nickname', maxLength: 80,
    value: device.user_nickname || '', trigger, resolveTrigger: () => nicknameTrigger(device),
    resolveFallback: () => deviceSearchInput,
    hint: `Address: ${device.ip}. Use up to 80 characters; leave empty to remove. This is your label, not a detected or verified name. Reuse across scans requires a recent, unambiguous adapter match.`,
    onSave: async nickname => {
      if (!nicknameState.available) throw new Error('Reconnect to the saved names before editing. Your draft has not been saved.');
      nicknameSaving = true;
      document.querySelectorAll('[data-nickname-device]').forEach(button => { button.disabled = true; });
      let committed = false;
      try {
        const receipt = await request(`/api/live-scans/${scanId}/devices/${device.device_id}/nickname`, {
          method: 'PUT', body: JSON.stringify({ nickname, expected_revision: expectedRevision }),
        });
        committed = true;
        if (!nicknameState.confirmRevision(receipt.nickname_revision)) throw new Error('The saved nickname version could not be confirmed.');
        render(await request(`/api/live-scans/${scanId}`));
        nicknameFeedback(device, 'Your nickname was saved. Reported names and scan evidence are unchanged.');
        status.textContent += ' Your nickname was saved; detected names and scan results are unchanged.';
      } catch (error) {
        let loaded = false;
        try { loaded = adoptNicknameSnapshot(await request(`/api/live-scans/${scanId}/nicknames`)); }
        catch { nicknameState.unavailable(); refreshNicknameProjection(); }
        if (nicknameState.available) expectedRevision = nicknameState.value.revision;
        const result = committed ? 'Your nickname was saved, but its latest display could not be loaded.'
          : error.status === 409 ? 'Your nickname change was not saved.' : 'The nickname save could not be confirmed.';
        const message = `${result} ${error.message}${loaded ? ' Latest nicknames loaded; review them before trying again.' : ' Reload to reconnect before editing.'}`;
        status.textContent = message;
        nicknameFeedback(device, message);
        throw new Error(message);
      } finally {
        nicknameSaving = false;
        document.querySelectorAll('[data-nickname-device]').forEach(button => { button.disabled = !nicknameState.available; });
      }
    },
  });
}

async function refreshDeviceName(device, trigger, localStatus) {
  if (!window.confirm(`Look up names for ${device.ip} on your authorised network? This address may now belong to a different device. Only DNS and enabled local announcements are checked; no port scan starts.`)) return;
  const hadFocus = document.activeElement === trigger;
  trigger.disabled = true; localStatus.hidden = false;
  localStatus.textContent = 'Looking for a name. The original report will not change.';
  try {
    notes.apply(await request(`/api/live-scans/${scanId}/devices/${device.device_id}/refresh-name`, {
      method: 'POST', body: JSON.stringify({ authorised: true }),
    }));
  } catch (error) { localStatus.textContent = `Name lookup could not finish. ${error.message}`; }
  finally {
    trigger.disabled = false;
    if (hadFocus && document.activeElement === document.body && trigger.isConnected) trigger.focus({ preventScroll: true });
  }
}

function renderDevices(data) {
  renderDeviceSummaries(data);
  renderComparisons(data);
  deviceTableBody.replaceChildren();
  if (!data.devices.length) {
    const emptyRow = document.createElement('tr');
    const emptyCell = text('td', 'No devices responded to the selected discovery or service checks.', 'device-table-empty');
    emptyCell.colSpan = 7;
    emptyRow.append(emptyCell);
    deviceTableBody.append(emptyRow);
    return;
  }
  data.devices.filter(device => deviceMatchesSearch(device, data)).forEach((device) => {
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
      deviceLabel(device),
      device.ip,
      deviceCategory(device),
      device.reachability_evidence?.some((item) => ['open_port_response', 'closed_port_response'].includes(item))
        ? 'Responded to a service check'
        : device.reachability_evidence?.includes('nmap_discovery_response') ? 'Responded to discovery'
          : device.discovery_method === 'mdns_advertisement' || device.reachability === 'advertised'
            ? 'Advertised by mDNS; service response not confirmed' : 'Not confirmed',
      services.map((item) => formatServiceLabel(item)).join(', ') || 'None found in selected checks',
    ].forEach((value) => row.append(text('td', value)));
    row.append(checkCell, text('td', String(deviceFindings.length)));
    if (device.user_nickname) row.children[0].append(text('p', `Reported name: ${device.hostname || 'none'}. Your nickname does not verify identity.`));
    if (device.hostname_source || device.vendor) {
      const sources = { nmap: 'scan response', reverse_dns: 'local name lookup', mdns: 'device announcement',
        pihole_dhcp: 'Pi-hole address lease', pihole_network: 'Pi-hole history', nmap_discovery: 'Nmap discovery',
          upnp: 'device description (UPnP)', netbios: 'computer-name response (NetBIOS)',
          saved_report: 'previous scan — not confirmed this time' };
      const nameDetails = document.createElement('details');
      nameDetails.append(text('summary', 'About this name'));
      nameDetails.append(text('p', `Source: ${sources[device.hostname_source] || 'scan'}. ${device.hostname_observed_at ? `Recorded: ${device.hostname_observed_at}.` : ''}`));
      if (device.hostname_source === 'saved_report') nameDetails.append(text('p', 'A recent scan recorded this name for the same network-adapter address. It was not confirmed in this scan; adapter addresses can change or be copied.'));
      nameDetails.append(text('p', device.hostname_conflict ? 'Sources reported different names; the alternatives are listed below.' : `Name confidence: ${device.hostname_confidence || 'low'}. Reported names do not verify a device identity.`));
      if (device.vendor) nameDetails.append(text('p', `Network adapter manufacturer: ${device.vendor}. This does not identify the device model.`));
      (device.name_candidates || []).forEach((item) => nameDetails.append(text('p', `${item.name} — ${sources[item.source] || item.source}, ${item.observed_at}`)));
      row.children[0].append(nameDetails);
    }
    if (device.details?.length) {
      const extra = document.createElement('details');
      extra.append(text('summary', 'More about this device'));
      extra.append(text('p', 'These details help you recognise the device. Advertised names and features are claims, not verified identity or security checks.'));
      const labels = { friendlyName: 'Reported device name', manufacturer: 'Reported manufacturer',
        modelName: 'Reported model', deviceType: 'Reported device type',
          'Reported md': 'Reported model', 'Reported ty': 'Reported model or product',
          'Reported fn': 'Advertised friendly name' };
      const statuses = { advertised: 'Device announcement', inferred: 'Comparison or inference',
        unavailable: 'Could not check', not_checked: 'Not fully checked', observed: 'Observed' };
      device.details.forEach((item) => {
        extra.append(text('p', `${labels[item.label] || item.label}: ${item.value}`));
        extra.append(text('small', `${statuses[item.status] || 'Reported'} · ${item.source} · ${item.observed_at}`));
      });
      row.children[0].append(extra);
    }
    if (device.profile?.hints?.length) {
      const basis = document.createElement('details');
      basis.append(text('summary', 'Why this possible type?'));
      basis.append(text('p', device.profile.conflict ? 'Clues disagree; no device type is assigned.' : 'This is a suggestion from reported clues, not verified identity.'));
      device.profile.hints.forEach((hint) => basis.append(text('p', `${hint.source}: ${hint.token}`)));
      row.children[2].append(basis);
    }
    deviceTableBody.append(row);
  });
}

function renderAdvertisements(data) {
  const deviceAddresses = new Set(deviceResultEntries(data).map(device => device.ip));
  const observations = (data.observations || []).filter(item => item.source === 'mdns' && !deviceAddresses.has(item.ip));
  mdnsSection.hidden = observations.length === 0;
  mdnsList.replaceChildren();
  observations.forEach(item => {
    const features = { _http: 'a device web page', _https: 'an encrypted device web page',
      _ipp: 'printing', _ipps: 'encrypted printing', _printer: 'printing', _airplay: 'AirPlay media sharing',
      _raop: 'audio streaming', _googlecast: 'media casting', _hap: 'a smart-home accessory',
      _mqtt: 'smart-home messaging', _smb: 'file sharing', '_device-info': 'device information' };
    const feature = features[item.service_type.split('.')[0]] || 'a device feature';
    mdnsList.append(text('li', (item.advertised_name || 'Name not identified') + ' (' + item.ip + ') advertised ' + feature + (item.port ? ' on port ' + item.port : '') + '. No matching checked device result was recorded; this advertisement does not verify an open service.'));
  });
}

function render(data) {
  retryReportLoad.hidden = true;
  retryReportLoad.disabled = false;
  const profileName = data.policy?.profile === 'deep-tcp-v1' ? 'Deep' : 'Light';
  document.querySelector('#report-meta').textContent = `${profileName} scan · ${recordedTimeLabel(data.created_at, 'Date unavailable')}`;
  if (data.nickname_error) nicknameState.unavailable();
  else if (data.user_nicknames) nicknameState.apply({ revision: data.nickname_revision,
    changed: true, names: data.user_nicknames, recovery_notice: data.nickname_recovery_notice });
  projectNicknames(data, nicknameState);
  const openServices = (data.services || []).filter((service) => service.state === 'open').length;
  const stateLabels = {
    queued: 'Waiting to start', running: 'Scanning', completed: 'Completed',
    partial: 'Some checks could not finish', failed: 'Could not complete', cancelled: 'Cancelled',
  };
  const preparing = ['queued', 'running'].includes(data.state) || data.phase === 'analysis';
  const analysisFailed = data.analysis_status === 'failed';
  reportContent.hidden = preparing;
  reportContent.inert = preparing || !readingRestored;
  reportContent.setAttribute('aria-busy', String(preparing));
  document.querySelector('#first-action').hidden = preparing;
  runAgainButton.disabled = preparing;
  retryHostsButton.hidden = preparing || !(data.coverage?.targets || []).some((target) => ['failed', 'timed_out', 'cancelled', 'pending', 'running'].includes(target.service_status) && (data.target?.mode === 'known_hosts' || target.discovery_status === 'observed'));
  retryHostsButton.disabled = preparing;
  if (preparing) {
    currentData = data;
    title.textContent = data.phase === 'analysis' ? 'Making your results easier to understand.'
      : data.phase === 'enrichment' ? 'Gathering device details.' : 'Checking your devices.';
    lead.textContent = data.phase === 'analysis' ? analysisProgressText(data) : 'Your report will appear after the scan and AI explanation finish.';
    status.textContent = coverageSummary(data);
    state.textContent = 'In progress';
    simplifyButton.hidden = true;
    refreshGuidanceButton.hidden = true;
    return;
  }
  title.textContent = data.state === 'completed' ? 'Your local scan is ready.' : `${stateLabels[data.state] || 'Scan status unknown'}.`;
  if (data.state === 'partial') {
    title.textContent = partialScanTitle(data);
  }
  lead.textContent = `Saved results for ${data.devices.length} device${data.devices.length === 1 ? '' : 's'}. Found ${openServices} service${openServices === 1 ? '' : 's'} accepting requests. A service is a device feature that other devices can contact.`;
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
  priorityBreakdown.textContent = ['high', 'medium', 'low', 'informational'].map((level) => `${data.findings.filter((item) => item.severity === level).length} ${level === 'informational' ? 'review only (no risk assigned)' : level + ' priority'}`).join(' · ');
  coverage.textContent = coverageSummary(data);
  updateDocumentTitle();
  const displayed = currentOverview(data) || data.plain_overview;
  if (displayed?.content.meaning) lead.textContent = displayed.content.meaning;
  const overviewHelp = document.querySelector('#overview-help');
  overviewHelp.replaceChildren();
  if (displayed) {
    if (displayed.content.why_it_matters) overviewHelp.append(text('h3', 'About this overview'), text('p', displayed.content.why_it_matters));
    (displayed.limitations || displayed.display_limitations || []).forEach(line => overviewHelp.append(text('p', line)));
    const steps = displayed.content.recommended_steps || [];
    if (steps.length) {
      overviewHelp.append(text('h4', 'Report-wide guidance'));
      const list = document.createElement('ul');
      steps.forEach((step, index) => list.append(text('li', actionGuidance(step, displayed.content.how_to_check?.[index] || ''))));
      overviewHelp.append(list);
    }
  }
  const aiNotice = document.querySelector('#ai-report-notice');
  aiNotice.hidden = !analysisFailed;
  aiNotice.textContent = pendingWording(data)
    ? 'Some wording still uses reviewed rule-based guidance. Retry the remaining AI wording without scanning again.'
    : 'AI simplification is unavailable. Your saved facts and reviewed rule-based guidance remain accessible; you can retry without scanning again.';
  const overviewRecord = currentOverview(data);
  const aiRecords = (data.explanations || []).filter(record => record.source === 'ai' && usableAiRecord(record, data));
  document.querySelector('#ai-report-source').textContent = overviewRecord || aiRecords.length
    ? 'Local AI contributed validated wording. Unaccepted fields retain reviewed rule-based guidance; the recorded evidence and priorities have not changed.'
    : 'The report uses reviewed rule-based guidance. No new AI conclusion is being claimed.';
  const records = [overviewRecord, ...aiRecords].filter(Boolean);
  const models = [...new Set(records.map(record => record.model).filter(Boolean))];
  const versions = [...new Set(records.map(record => record.prompt_version).filter(Boolean))];
  document.querySelector('#ai-report-model').textContent = models.length
    ? 'Recorded model: ' + models.join(', ') + (versions.length ? '. Prompt version: ' + versions.join(', ') + '.' : '.')
    : 'No validated model output is recorded for the displayed wording.';
  if (data.nickname_error) status.textContent += ' ' + data.nickname_error;
  if (data.nickname_recovery_notice) status.textContent += ' ' + data.nickname_recovery_notice;
  scanProblems.replaceChildren();
  const hasSelfCheck = data.devices.some(device => recordedDeviceRole(device, data) === 'Computer that ran this scan');
  const problems = [...(data.errors || []).filter(item => !item.target_ip), ...(data.warnings || []).filter(item =>
    !(item.code === 'AI_PREFLIGHT_UNAVAILABLE' && data.analysis_status === 'ready')
    && !(item.code === 'SELF_SCAN_LOCAL_ROUTING' && hasSelfCheck))];
  (data.coverage?.targets || []).filter((target) => ['failed', 'timed_out', 'cancelled'].includes(target.service_status)).forEach((target) => {
    const reasons = { host_scan_timeout: 'timed out', host_result_invalid: 'returned an incomplete or invalid result',
      host_unreachable: 'could not reach the device for checking (it may be asleep, disconnected or not responding; the cause is unknown)',
      host_output_limit: 'returned more output than the scanner can retain', host_scan_failed: 'ended with a scanner error',
      host_privilege_required: 'could not start because Nmap lacks the required permissions',
      host_driver_unavailable: 'could not start because Nmap could not use the packet-capture driver or adapter',
      network_interrupted: 'stopped by the network safety check; confirm the current connection before retrying',
      result_size_limit: 'could not be saved within the report size limit', scan_failed: 'stopped because the scan encountered an error',
      scan_time_limit: 'did not finish within the scan time budget',
      storage_busy: 'stopped because report storage was busy',
      host_scan_cancelled: 'was cancelled', process_restarted: 'was interrupted when the app stopped' };
    const reason = reasons[target.reason_code] || 'did not finish';
    problems.push({ message: `The device check for ${target.ip} ${reason} after ${target.attempts ?? 0} attempt(s). Its remaining checks were not assessed.` });
  });
  scanProblems.hidden = !problems.length;
  if (problems.length) {
    const incomplete = ['partial', 'failed', 'cancelled'].includes(data.state);
    scanProblems.append(text('strong', incomplete ? 'Scan notes and unfinished checks' : 'Scan notes'));
    const list = document.createElement('ul');
    problems.forEach((problem) => list.append(text('li', problem.message || 'A check did not complete.')));
    scanProblems.append(list);
  }
  const outdatedAi = (data.explanations || []).some((record) => record.source === 'ai' && record.prompt_version !== data.guidance_status?.ai_prompt_version);
  guidanceArchives.replaceChildren();
  (data.guidance_archives || []).forEach((name) => {
    if (!/^guidance-[0-9a-f-]{36}\.json$/.test(name)) return;
    const link = document.createElement('a');
    link.href = `/api/live-scans/${scanId}/guidance/${name}`;
    link.textContent = 'Archived guidance (JSON)';
    guidanceArchives.append(link, text('span', ' '));
  });
  refreshGuidanceButton.hidden = !data.guidance_status?.refresh_available;
  refreshGuidanceButton.disabled = data.phase !== 'finished' || ['queued', 'running'].includes(data.state);
  guidanceNotice.textContent = data.guidance_status?.refresh_available
    ? 'This saved report has older guidance. Refresh it using the saved observations; previous guidance is kept and no network scan is run.'
    : data.guidance_status?.outdated_findings
      ? 'Some older guidance cannot be refreshed from the saved evidence. Run a new scan to reassess those findings.'
      : data.guidance_updated_at ? 'Guidance was refreshed from saved observations. The original scan date and evidence are unchanged.' : '';
  if (outdatedAi) guidanceNotice.textContent += ' Older AI wording is hidden because it predates the current validation checks. You can request local AI wording again.';
  document.querySelector('#finding-metric').textContent = data.findings.length;
  document.querySelector('#device-metric').textContent = deviceCheckLabel(data);
  document.querySelector('#service-metric').textContent = openServices;
  renderFindings(data);
  renderDevices(data);
  renderAdvertisements(data);
  renderNextSteps(data);
  renderBeginnerGuide(data);
  simplifyButton.hidden = !['completed', 'partial', 'failed', 'cancelled'].includes(data.state)
    || (data.analysis_status === 'ready' && !pendingWording(data) && !outdatedAi && currentOverview(data));
  simplifyButton.disabled = preparing;
  simplifyButton.textContent = pendingWording(data) ? 'Retry remaining wording' : analysisFailed ? 'Retry report preparation' : 'Prepare this saved report with Ollama';
  restoreReading();
}

async function poll() {
  try {
    const progress = await request(`/api/live-scans/${scanId}/progress`);
    if (['queued', 'running'].includes(progress.state) || progress.phase === 'analysis') {
      render(progress);
      window.setTimeout(poll, 1000);
      return;
    }
    const data = await request(`/api/live-scans/${scanId}`);
    try {
      notes.apply(await request(`/api/live-scans/${scanId}/annotations`));
    } catch {
      notes.apply(null);
    }
    render(data);
    notes.refresh();
    scheduleNicknameRefresh();
    if (data.state === 'queued' || data.state === 'running' || data.phase === 'analysis') {
      window.setTimeout(poll, 1000);
    }
  } catch (error) {
    if (currentData?.phase === 'finished') {
      status.textContent = `This saved report is still shown, but the latest information could not be loaded. ${error.message}`;
    } else {
      title.textContent = 'Scan results unavailable';
      lead.textContent = error.message;
      reportContent.hidden = true;
    }
    reportContent.setAttribute('aria-busy', 'false');
    retryReportLoad.hidden = false;
    retryReportLoad.disabled = false;
  }
}

poll();
