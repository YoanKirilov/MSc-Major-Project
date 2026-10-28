import { request } from './api.js?v=20261018-cve-deadline';
import { configurePicker, startSetupTools } from './setup-tools.mjs?v=20261014-reliability';
import { analysisProgressText, progressAnnouncement, readScanSetup, ollamaStatusText } from './report.mjs?v=20261014-reliability';
import { createStartState } from './start-state.mjs?v=20261021-organisation';

const launchButton = document.querySelector('#scanLaunchButton');
const configText = document.querySelector('#scan-config');
const progress = document.querySelector('#scanProgress');
const errorPanel = document.querySelector('#scanError');
const phaseText = document.querySelector('#progressPhase');
const percentText = document.querySelector('#progressPercent');
const detailText = document.querySelector('#progressDetail');
const progressBar = document.querySelector('#progressBar');
const progressTrack = document.querySelector('#progressTrack');
const progressNote = document.querySelector('#progressNote');
const cancelButton = document.querySelector('#scanCancelButton');
const modeButtons = [...document.querySelectorAll('.mode-button')];
const deepHostField = document.querySelector('#deepHostField');
const deepHostInput = document.querySelector('#deepHostInput');
const deepHostError = document.querySelector('#deepHostError');
const setupNote = document.querySelector('#scanSetupNote');
const clearTargetsButton = document.querySelector('#clearSavedTargetsButton');
const pageProfile = ({ '/light': 'light', '/deep': 'deep-tcp-v1' })[window.location.pathname] || null;
const pagePath = pageProfile ? window.location.pathname : '/';
const suppliedSetup = readScanSetup(window.location.hash);
const requestedSetup = suppliedSetup && (!pageProfile || suppliedSetup.profile === pageProfile) ? suppliedSetup : null;
const scanParams = new URLSearchParams(window.location.hash.slice(1));
const validScanId = (id) => /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id || '');
const linkedScanId = validScanId(scanParams.get('scan')) ? scanParams.get('scan') : null;
const newScanSetup = requestedSetup && scanParams.get('new') === '1';
const capacityNote = document.querySelector('#capacityNote');
let capacityFull = false;
let capacityCheckScheduled = false;
let aiReadinessChecks = 0;
let spokenProgressKey = '';

function showScanMessage(message) {
  // Repeated polls should not replace an unchanged live-region message.
  if (configText.textContent !== message) configText.textContent = message;
}

function clearTargetError() {
  deepHostInput.removeAttribute('aria-invalid');
  deepHostError.hidden = true;
  deepHostError.textContent = '';
}
deepHostInput.addEventListener('input', clearTargetError);
document.querySelector('#recentDeviceSelect').addEventListener('change', () => {
  if (!deepHostInput.disabled) clearTargetError();
});

function showCapacityWait() {
  capacityFull = true;
  capacityNote.hidden = false;
  capacityNote.textContent = 'All scan slots are in use. This page will become ready when a slot is free. No new scan has started; press Scan when it is ready.';
  showScanMessage('Waiting for a free scan slot. No new scan has started on this page.');
  launchButton.disabled = true;
  launchButton.querySelector('span').textContent = 'Waiting for a free slot';
  if (!capacityCheckScheduled) {
    capacityCheckScheduled = true;
    window.setTimeout(() => {
      capacityCheckScheduled = false;
      if (!activeScanId) return loadStatus();
    }, 3000);
  }
}

let scannerAvailable = false;
let selectedProfile = pageProfile || requestedSetup?.profile || 'light';
let savedLightHosts = selectedProfile === 'light' ? (requestedSetup?.hosts || []) : [];
let activeNetwork = null;
let scopeSource = null;
let activeScanId = null;
let statusReady = false;
let statusError = null;
let networkWarning = null;
let storageReady = false;
let pollFailures = 0;
let pollEpoch = 0;
let pageSuspended = false;
window.addEventListener?.('pagehide', () => { pageSuspended = true; pollEpoch += 1; });
window.addEventListener?.('pageshow', event => {
  pageSuspended = false;
  if (event.persisted && activeScanId) pollScan(activeScanId);
});
const pendingScanKey = `network-assessor-pending-scan${pageProfile ? `:${pageProfile}` : ''}`;
const pendingStartKey = `${pendingScanKey}:start`;
const startRecover = document.querySelector('#scanStartRecover');
const startReset = document.querySelector('#scanStartReset');
let initialStart = validScanId(scanParams.get('start')) ? scanParams.get('start') : null;
try {
  if (!initialStart && !newScanSetup) {
    const saved = window.sessionStorage.getItem(pendingStartKey);
    if (validScanId(saved)) initialStart = saved;
  }
  if (newScanSetup && !initialStart) window.sessionStorage.removeItem(pendingStartKey);
} catch { /* A pinned URL also preserves uncertain start recovery. */ }
const starts = createStartState(initialStart);
const ownsStart = starts.owns;

function rememberStart(id) {
  if (starts.select(id)) startRecover.disabled = false;
  try {
    if (id) window.sessionStorage.setItem(pendingStartKey, id);
    else window.sessionStorage.removeItem(pendingStartKey);
  } catch { /* Never store permission or automatically resubmit from this key. */ }
  if (id) window.history.replaceState(null, '', `${pagePath}#start=${id}`);
  else if (window.location.hash.startsWith('#start=')) window.history.replaceState(null, '', pagePath);
  startRecover.hidden = startReset.hidden = !id;
  if (id) {
    deepHostInput.disabled = true;
    modeButtons.forEach(button => { button.disabled = true; });
    document.querySelector('#recentDeviceSelect').disabled = true;
    document.querySelector('#refreshDeviceChoices').disabled = true;
  }
}

function showStartUncertain(message) {
  errorPanel.hidden = !message;
  errorPanel.textContent = message || '';
  launchButton.disabled = true;
  launchButton.querySelector('span').textContent = 'Confirming original start';
  progress.hidden = false;
  cancelButton.hidden = true;
  phaseText.textContent = 'Confirming whether your scan started';
  detailText.textContent = 'Reading the original attempt; no replacement scan is submitted.';
  progressTrack.removeAttribute('aria-valuenow');
  progressTrack.setAttribute('aria-valuetext', 'Scan start not yet confirmed. No replacement submitted.');
  percentText.textContent = 'Waiting';
  startRecover.hidden = startReset.hidden = false;
  showScanMessage('The original start is not yet confirmed. Checking it does not start another scan.');
}

async function recoverStart() {
  const read = starts.beginRead();
  if (!read) return;
  const { operation, generation } = read;
  startRecover.disabled = true;
  let again = true;
  try {
    const receipt = await request(`/api/scan-starts/${operation}`);
    if (!ownsStart(operation, generation)) return;
    if (receipt.request) document.querySelector('#progressTarget').textContent =
      `Original ${receipt.request.profile === 'deep-tcp-v1' ? 'Deep' : 'Light'} scan: ${receipt.request.cidr || receipt.request.hosts?.join(', ') || receipt.request.confirmed_scope}. These settings belong to the original attempt.`;
    if (receipt.state === 'accepted' && validScanId(receipt.scan_id)) {
      rememberStart(null);
      errorPanel.hidden = true;
      await resumeScan(receipt.scan_id);
      return;
    }
    if (receipt.state === 'rejected') {
      rememberStart(null);
      setError('The original scan was not started. Check your settings before choosing Scan again.');
      return;
    }
    showStartUncertain(receipt.state === 'preparing' ? ''
      : 'The earlier start cannot finish or its report is unavailable. Read Saved reports before choosing a new scan.');
    again = receipt.state === 'preparing';
  } catch (error) {
    again = ![401, 403].includes(error.status);
    if (ownsStart(operation, generation)) showStartUncertain(error.status === 404
      ? 'The app has not recorded this start yet. Keep checking the original attempt before choosing another scan.'
      : error.status === 401 ? 'Your local app session has expired. Reopen the session link in the backend terminal, then return to this original start. No replacement scan was submitted.'
      : error.message);
  } finally {
    if (starts.finishRead(read)) startRecover.disabled = false;
    if (again && starts.shouldPoll(read)) {
      window.setTimeout(() => { if (ownsStart(operation, generation)) recoverStart(); }, 3000);
    }
  }
}
startRecover.addEventListener('click', () => { starts.resetReads(); return recoverStart(); });
startReset.addEventListener('click', () => {
  if (!window.confirm('The original scan may still exist. Check running scans and Saved reports first. Return to setup for a separate new scan?')) return;
  rememberStart(null);
  setError('Back at setup. No new scan was submitted. The earlier scan, if accepted, remains available in running scans or Saved reports.');
});
launchButton.disabled = true;
launchButton.querySelector('span').textContent = 'Checking scanner...';

function rememberScan(id) {
  if (activeScanId !== id) pollEpoch += 1;
  activeScanId = id;
  try {
    if (id) window.sessionStorage.setItem(pendingScanKey, id);
    else window.sessionStorage.removeItem(pendingScanKey);
  } catch { /* The backend still tracks running jobs if browser storage is blocked. */ }
}

function savedScanId() {
  try {
    const id = window.sessionStorage.getItem(pendingScanKey);
    return /^[0-9a-f-]{36}$/i.test(id || '') ? id : null;
  } catch { return null; }
}

async function resumeScan(id) {
  rememberScan(id);
  clearTargetError();
  showScanMessage('Reconnecting to this scan. Progress is below; refreshing does not start another scan.');
  launchButton.disabled = true;
  deepHostInput.disabled = true;
  modeButtons.forEach(button => { button.disabled = true; });
  document.querySelector('#recentDeviceSelect').disabled = true;
  document.querySelector('#refreshDeviceChoices').disabled = true;
  let metadata;
  try {
    metadata = await request(`/api/scans/${id}`);
    if (pageProfile && metadata.policy?.profile !== pageProfile) {
      // An explicitly pasted link to another profile belongs on the general dashboard.
      rememberScan(null);
      window.location.replace(`/#scan=${id}`);
      return;
    }
  } catch {
    // Progress can remain readable even if the full metadata is temporarily unavailable.
    // Never interpret a metadata read failure as permission to launch another scan.
  }
  if (['light', 'deep-tcp-v1'].includes(metadata?.policy?.profile)) {
    selectedProfile = metadata.policy.profile;
  }
  const hosts = metadata?.target?.hosts;
  if (selectedProfile === 'deep-tcp-v1') deepHostInput.value = hosts?.[0] || '';
  if (['light', 'deep-tcp-v1'].includes(metadata?.policy?.profile)) showSetup();
  document.querySelector('#progressTarget').textContent = metadata?.target
    ? `${selectedProfile === 'deep-tcp-v1' ? 'Deep' : 'Light'} scan: ${metadata.target.cidr || hosts?.join(', ') || 'saved target'}. This target is fixed for this scan.`
    : 'Reconnecting to the saved target. Refreshing does not change or restart this scan.';
  // A URL pins this tab to its job even if session storage is blocked or copied.
  window.history.replaceState(null, '', `${pagePath}#scan=${id}`);
  setupNote.hidden = true;
  clearTargetsButton.hidden = true;
  launchButton.disabled = true;
  launchButton.querySelector('span').textContent = 'Scan in progress';
  progress.hidden = false;
  cancelButton.hidden = false;
  cancelButton.disabled = false;
  cancelButton.textContent = 'Cancel scan';
  const main = document.querySelector('.scan-home-main');
  main.classList.toggle('is-running', true);
  // Keep progress below setup and preserve the reader's position, including on refresh.
  await pollScan(id);
}

function showSetup() {
  modeButtons.forEach((item) => {
    const active = item.dataset.profile === selectedProfile;
    item.classList.toggle('active', active);
    item.setAttribute('aria-pressed', String(active));
  });
  const deep = selectedProfile === 'deep-tcp-v1';
  if (!deep) clearTargetError();
  deepHostField.hidden = !deep;
  deepHostInput.hidden = !deep;
  configurePicker(deep);
  clearTargetsButton.hidden = deep || !savedLightHosts.length;
  setupNote.hidden = !requestedSetup && !savedLightHosts.length;
  setupNote.textContent = !deep && savedLightHosts.length
    ? `Light scan of the previous device addresses: ${savedLightHosts.join(', ')}. Confirm these devices are still yours before pressing Scan.`
    : deep ? 'Confirm or enter one authorised device address, then press Scan. No scan has started.'
      : 'Ready to set up another Light scan. Press Scan when you are ready; your previous report stays saved.';
}
deepHostInput.value = selectedProfile === 'deep-tcp-v1' ? (requestedSetup?.hosts[0] || '') : '';
showSetup();
modeButtons.forEach((button) => button.addEventListener('click', () => {
  if (activeScanId || starts.operation) return;
  selectedProfile = button.dataset.profile;
  savedLightHosts = [];
  showSetup();
}));
clearTargetsButton.addEventListener('click', () => { if (!activeScanId) { savedLightHosts = []; showSetup(); } });

function setError(message) {
  if (starts.operation) { showStartUncertain(message); return; }
  errorPanel.hidden = false;
  errorPanel.textContent = message;
  progress.hidden = !activeScanId;
  launchButton.disabled = Boolean(activeScanId);
  launchButton.querySelector('span').textContent = activeScanId ? 'Scan in progress' : 'Scan';
  cancelButton.hidden = !activeScanId;
  if (activeScanId) {
    cancelButton.disabled = false;
    cancelButton.textContent = 'Cancel scan';
    showScanMessage('This scan is still selected. Check the message below; do not start another scan to reconnect.');
  } else {
    showScanMessage('Check the message below before trying again.');
  }
  if (!activeScanId) {
    deepHostInput.disabled = false;
    modeButtons.forEach(button => { button.disabled = false; });
    document.querySelector('#recentDeviceSelect').disabled = false;
    document.querySelector('#refreshDeviceChoices').disabled = false;
    const main = document.querySelector('.scan-home-main');
    main.classList.toggle('is-running', false);
    showSetup();
  }
}

cancelButton.addEventListener('click', async () => {
  if (!activeScanId) return;
  cancelButton.disabled = true;
  cancelButton.textContent = 'Cancelling...';
  try {
    await request(`/api/live-scans/${activeScanId}`, { method: 'DELETE' });
    cancelButton.textContent = 'Cancellation requested';
    showScanMessage('Cancellation requested. Waiting for this scan to stop; saved results will remain available.');
  } catch (error) {
    setError(error.message);
  }
});

async function loadStatus() {
  capacityFull = false;
  capacityNote.hidden = true;
  // Recovery reads do not depend on Nmap/AI/status readiness and never submit work.
  if (starts.operation) {
    rememberStart(starts.operation);
    showStartUncertain('');
    await recoverStart();
    return;
  }
  const generation = starts.generation;
  const currentStatus = () => generation === starts.generation && !starts.operation && !activeScanId;
  try {
    const status = await request('/api/status');
    if (!currentStatus()) return;
    statusReady = true;
    statusError = null;
    scannerAvailable = status.scanner_available;
    activeNetwork = status.allowed_network;
    scopeSource = status.scope_source;
    networkWarning = status.network_warning || null;
    storageReady = status.storage_status === 'ok';
    const activeIds = (status.active_scan_ids || (status.active_scan_id ? [status.active_scan_id] : []))
      .filter(validScanId);
    // Only an explicit new-tab setup bypasses recovery. Never arbitrarily pick the
    // first of multiple jobs, and never resume another tab's job from a copied key.
    const pending = linkedScanId || (newScanSetup ? null : pageProfile
      ? (requestedSetup ? null : savedScanId()) : requestedSetup
      ? (activeIds.length === 1 ? activeIds[0] : null)
      : savedScanId() || (activeIds.length === 1 ? activeIds[0] : null));
    if (pending) {
      configText.textContent = 'Reconnecting to your saved scan. Refreshing does not start a new scan.';
      await resumeScan(pending);
      return;
    }
    if (status.ui_contract_version !== 1) {
      throw new Error('The page and backend versions do not match. Let active scans finish, restart the NetGuard backend, then reopen its session link and reload this page. No new scan has started.');
    }
    if (requestedSetup) rememberScan(null);
    if (status.scan_capacity_available === false
        || (status.scan_capacity_available === undefined && status.active_scan_count >= status.max_concurrent_scans)) {
      showCapacityWait();
      return;
    }
    if (status.network_warning) {
      configText.textContent = status.network_warning;
      return;
    }
    if (status.storage_status !== 'ok') {
      configText.textContent = 'The local results folder is not writable. Restart the app with normal user permissions.';
      return;
    }
    if (activeNetwork && scannerAvailable) {
      configText.textContent = status.ai_available
        ? 'Ready to scan your authorised local network. We will make the results easier to understand before your report opens.'
        : ollamaStatusText(status);
      if (!status.ai_available && status.ai_readiness?.state === 'unresponsive' && aiReadinessChecks < 3) {
        aiReadinessChecks += 1;
        window.setTimeout(() => { if (!activeScanId) return loadStatus(); }, 30000);
      }
    } else if (!scannerAvailable) {
      configText.textContent = 'Nmap is not installed or configured on this computer.';
    } else {
      configText.textContent = 'Your home network could not be detected. Open Settings to choose the authorised network.';
    }
  } catch (error) {
    if (!currentStatus()) return;
    statusReady = false;
    statusError = error.message;
    configText.textContent = `Scanner status could not be checked. ${error.message}`;
  } finally {
    if (currentStatus()) {
      launchButton.disabled = capacityFull;
      launchButton.querySelector('span').textContent = capacityFull ? 'Waiting for a free slot' : !statusReady ? 'Retry connection' : networkWarning ? 'Check network again' : 'Scan';
    }
  }
}

function updateProgress(scan) {
  const coverage = scan.coverage || {};
  const candidates = coverage.candidate_count || 0;
  const discovered = coverage.discovered_count || 0;
  const completed = coverage.service_completed_count || 0;
  const attempted = coverage.service_attempted_count || 0;
  const deep = (scan.policy?.profile || selectedProfile) === 'deep-tcp-v1';
  if (!cancelButton.disabled) {
    showScanMessage(scan.phase === 'queued'
      ? 'Your scan is waiting to start. Progress is below; refreshing does not start another scan.'
      : scan.phase === 'analysis'
      ? 'Your scan results are saved. We are making the explanations easier to understand; progress is below.'
      : 'Your scan is in progress. Progress is below; refreshing does not start another scan.');
  }
  const phases = ['discovery', 'service_scan', 'enrichment', 'analysis'];
  const activeStage = phases.indexOf(scan.phase);
  ['Discovery', 'Checks', 'Details', 'Analysis'].forEach((stage, index) => {
    const element = document.querySelector(`#scanStage${stage}`);
    const label = [deep ? 'Confirm device' : 'Find devices', 'Check features', 'Gather details', 'Explain results'][index];
    element.dataset.state = activeStage === index ? 'current' : activeStage > index ? 'previous' : 'waiting';
    if (activeStage === index) element.setAttribute('aria-current', 'step');
    else element.removeAttribute('aria-current');
    element.textContent = `${activeStage === index ? 'Current: ' : activeStage > index ? 'Earlier: ' : ''}${label}`;
  });
  let percent = 0;
  if (scan.phase === 'analysis') {
    const p = scan.analysis_progress;
    percent = p?.total > 0 ? Math.min(99, 92 + Math.floor((p.completed / p.total) * 7)) : 92;
    phaseText.textContent = 'Making your results easier to understand.';
    detailText.textContent = analysisProgressText(scan);
  } else if (scan.phase === 'enrichment') {
    percent = 92;
    phaseText.textContent = 'Gathering device details';
    detailText.textContent = 'Looking for names and other clues to help you recognise your devices.';
  } else if (scan.phase === 'queued') {
    phaseText.textContent = 'Waiting for a scanner slot';
    detailText.textContent = 'Your request is saved. Device checks have not started yet.';
  } else if (scan.phase === 'discovery') {
    phaseText.textContent = 'Looking for devices';
    detailText.textContent = candidates ? `Checking ${candidates} private addresses` : 'Checking the private scope';
  } else if (discovered > 0 || candidates > 0) {
    const serviceDenominator = discovered || candidates;
    percent = Math.min(90, Math.round(((completed + (coverage.service_failed_count || 0)) / serviceDenominator) * 90));
    const retrying = coverage.targets?.some((target) => target.service_status === 'running' && target.attempts > 1);
    phaseText.textContent = retrying ? 'Trying a device check again' : 'Checking device connections';
    detailText.textContent = completed < serviceDenominator
      ? `Scanning discovered devices: ${completed} of ${serviceDenominator} complete`
      : `Analysing ${attempted} completed host${attempted === 1 ? '' : 's'}`;
  }
  const checkingOne = deep && scan.phase === 'service_scan';
  const indeterminate = checkingOne || ['queued', 'discovery'].includes(scan.phase);
  percent = Math.max(0, Math.min(99, Number.isFinite(percent) ? percent : 0));
  const speech = progressAnnouncement(scan, deep);
  if (speech.key !== spokenProgressKey) {
    spokenProgressKey = speech.key;
    document.querySelector('#scan-progress-status').textContent = speech.message;
  }
  percentText.textContent = indeterminate ? (scan.phase === 'queued' ? 'Waiting' : 'Running') : `${percent}%`;
  percentText.dataset.activity = indeterminate ? 'true' : 'false';
  progressBar.classList.toggle('is-active', indeterminate);
  progressBar.style.width = `${percent}%`;
  if (checkingOne) detailText.textContent = 'Checking this device’s features. Results will be saved when the check returns.';
  if (indeterminate) progressTrack.removeAttribute('aria-valuenow');
  else progressTrack.setAttribute('aria-valuenow', String(percent));
  progressTrack.setAttribute('aria-valuetext', indeterminate
    ? `${phaseText.textContent}. Time remaining is unknown.`
    : `${percent}% overall stage progress. Time remaining is unknown.`);
  progressNote.textContent = scan.phase === 'analysis'
    ? 'Scan observations have been saved. This final step can take a few minutes.'
    : `${scan.device_count ?? scan.devices?.length ?? 0} device results saved, ${scan.finding_count ?? scan.findings?.length ?? 0} items to review so far.`;
  if (scan.started_at) {
    const elapsed = Math.max(0, Math.floor((Date.now() - Date.parse(scan.started_at)) / 60000));
    if (Number.isFinite(elapsed)) progressNote.textContent += ` Elapsed: ${elapsed} minute${elapsed === 1 ? '' : 's'}. Device response times vary.`;
  }
  if (scan.runtime?.backend_checked_at) {
    progressNote.textContent += ' App connection confirmed.';
    const running = scan.runtime.scanner_checks_running || 0;
    if (running) {
      progressNote.textContent += ` ${running} check${running === 1 ? ' is' : 's are'} running. Waiting for results; the time remaining is unknown.`;
    } else if (scan.runtime.job_active && ['discovery', 'service_scan'].includes(scan.phase)) {
      progressNote.textContent += ' The scan is waiting or preparing its next check.';
    }
    const eventAt = Date.parse(scan.runtime.last_scanner_event_at);
    const event = scan.runtime.last_scanner_event;
    if (Number.isFinite(eventAt) && ['started', 'returned'].includes(event) && ['discovery', 'service_scan'].includes(scan.phase)) {
      const seconds = Math.max(0, Math.floor((Date.now() - eventAt) / 1000));
      const minutes = Math.floor(seconds / 60);
      const age = minutes ? `${minutes} minute${minutes === 1 ? '' : 's'} ago` : 'less than a minute ago';
      progressNote.textContent += ` ${event === 'started' ? 'The most recent check started' : 'A check ended'} ${age}. This does not confirm that a device answered.`;
    }
  }
}

async function pollScan(scanId, epoch = pollEpoch) {
  const current = () => !pageSuspended && epoch === pollEpoch && activeScanId === scanId;
  if (!current()) return;
  try {
    const scan = await request(`/api/live-scans/${scanId}/progress`);
    if (!current()) return;
    pollFailures = 0;
    errorPanel.hidden = true;
    updateProgress(scan);
    if (scan.state === 'queued' || scan.state === 'running' || scan.phase === 'analysis') {
      window.setTimeout(() => pollScan(scanId, epoch), 1000);
      return;
    }
    cancelButton.hidden = true;
    rememberScan(null);
    window.location.href = `/scans/${scanId}`;
  } catch (error) {
    if (!current() || error.code === 'page_inactive') return;
    if (error.status === 404) {
      rememberScan(null);
      setError('This saved scan could not be found. Open Saved reports to check your scan history.');
    } else if (error.status === 401 || error.status === 403) {
      setError(error.message);
    } else {
      // Losing the browser connection must not forget or restart the backend job.
      errorPanel.hidden = false;
      showScanMessage('Connection interrupted. Reconnecting to the same selected scan without restarting it.');
      errorPanel.textContent = `Connection interrupted. Reconnecting to the same scan; do not start another. ${error.message}`;
      window.setTimeout(() => pollScan(scanId, epoch), Math.min(1000 * 2 ** Math.min(pollFailures++, 4), 15000));
    }
  }
}

launchButton.addEventListener('click', async () => {
  if (starts.operation) return;
  errorPanel.hidden = true;
  if (activeScanId) return;
  if (capacityFull) return;
  if (!statusReady || networkWarning) {
    launchButton.disabled = true;
    await loadStatus();
    if (!statusReady) setError(statusError || 'The scanner status is not available yet. Try again.');
    return;
  }
  if (!storageReady) {
    setError('The local results folder is not writable. Check Settings before scanning.');
    return;
  }
  if (!scannerAvailable) {
    setError('Nmap is not installed or configured. Install Nmap before running a real scan.');
    return;
  }
  const deep = selectedProfile === 'deep-tcp-v1';
  const deepHost = deepHostInput.value.trim();
  if (!activeNetwork) {
    setError('Your home network could not be detected. Open Settings to choose the authorised network.');
    return;
  }
  if (deep && !deepHost) {
    const message = 'Enter the address of one device you own or have permission to check.';
    setError(message);
    deepHostError.textContent = message;
    deepHostError.hidden = false;
    deepHostInput.setAttribute('aria-invalid', 'true');
    deepHostInput.focus();
    return;
  }
  clearTargetError();
  if (scopeSource === 'automatic' && !window.confirm(`Scan the detected network ${activeNetwork}? Continue only if you own this network or have permission to scan it.`)) return;
  launchButton.disabled = true;
  launchButton.querySelector('span').textContent = 'Starting...';
  showScanMessage('Starting your scan. Progress will appear below; wait for confirmation before trying again.');
  progressTrack.removeAttribute('aria-valuenow');
  progressTrack.setAttribute('aria-valuetext', 'Preparing the scan. Time remaining is unknown.');
  progress.hidden = false;
  phaseText.textContent = 'Preparing local scan';
  detailText.textContent = 'Validating authorised scope';
  let operation = null;
  let generation;
  try {
    operation = globalThis.crypto?.randomUUID?.();
    if (!operation) throw new Error('This browser cannot safely identify a scan start. Use an updated browser on the local app address. No scan was submitted.');
    rememberStart(operation);
    generation = starts.generation;
    const payload = await request('/api/live-scans', {
      method: 'POST',
      body: JSON.stringify({
        operation_id: operation,
        mode: deep || savedLightHosts.length ? 'known_hosts' : 'discover',
        profile: selectedProfile,
        hosts: deep ? [deepHost] : savedLightHosts,
        authorised: true,
        confirmed_scope: activeNetwork,
      }),
    });
    // Reset/new-start and GET recovery may have superseded this HTTP caller.
    if (!ownsStart(operation, generation)) return;
    if (!validScanId(payload.scan_id)) throw new Error('The app reply did not identify the scan. Checking the original start; no replacement is submitted.');
    rememberStart(null);
    await resumeScan(payload.scan_id);
  } catch (error) {
    if (operation && !ownsStart(operation, generation)) return;
    if (error.status === 429) {
      rememberStart(null);
      // Another tab may have taken the last slot since status was read.
      progress.hidden = true;
      cancelButton.hidden = true;
      showCapacityWait();
      return;
    }
    if ([400, 401, 403, 409, 422].includes(error.status)) rememberStart(null);
    setError(error.message);
    if (starts.operation) await recoverStart();
  }
});

startSetupTools();
loadStatus();
