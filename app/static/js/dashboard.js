import { request } from './api.js?v=20261001-network-recovery';
import { configurePicker, startSetupTools } from './setup-tools.mjs?v=20261001-network-recovery';
import { analysisProgressText, readScanSetup, ollamaStatusText } from './report.mjs?v=20261001-network-recovery';

const launchButton = document.querySelector('#scanLaunchButton');
const configText = document.querySelector('#scan-config');
const progress = document.querySelector('#scanProgress');
const errorPanel = document.querySelector('#scanError');
const phaseText = document.querySelector('#progressPhase');
const percentText = document.querySelector('#progressPercent');
const detailText = document.querySelector('#progressDetail');
const progressBar = document.querySelector('#progressBar');
const progressNote = document.querySelector('#progressNote');
const cancelButton = document.querySelector('#scanCancelButton');
const modeButtons = [...document.querySelectorAll('.mode-button')];
const deepHostField = document.querySelector('#deepHostField');
const deepHostInput = document.querySelector('#deepHostInput');
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

function showCapacityWait() {
  capacityFull = true;
  capacityNote.hidden = false;
  capacityNote.textContent = 'All scan slots are in use. This page will become ready when a slot is free. No new scan has started; press Scan when it is ready.';
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
let scopeConfirmationSupported = false;
let activeScanId = null;
let statusReady = false;
let statusError = null;
let networkWarning = null;
let storageReady = false;
let pollFailures = 0;
const pendingScanKey = `network-assessor-pending-scan${pageProfile ? `:${pageProfile}` : ''}`;
launchButton.disabled = true;
launchButton.querySelector('span').textContent = 'Checking scanner...';

function rememberScan(id) {
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
  if (pageProfile) {
    const metadata = await request(`/api/scans/${id}`);
    if (metadata.policy?.profile !== pageProfile) {
      // An explicitly pasted link to another profile belongs on the general dashboard.
      rememberScan(null);
      window.location.replace(`/#scan=${id}`);
      return;
    }
  }
  rememberScan(id);
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
  await pollScan(id);
}

function showSetup() {
  modeButtons.forEach((item) => {
    const active = item.dataset.profile === selectedProfile;
    item.classList.toggle('active', active);
    item.setAttribute('aria-pressed', String(active));
  });
  const deep = selectedProfile === 'deep-tcp-v1';
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
  selectedProfile = button.dataset.profile;
  savedLightHosts = [];
  showSetup();
}));
clearTargetsButton.addEventListener('click', () => { savedLightHosts = []; showSetup(); });

function setError(message) {
  errorPanel.hidden = false;
  errorPanel.textContent = message;
  progress.hidden = !activeScanId;
  launchButton.disabled = Boolean(activeScanId);
  launchButton.querySelector('span').textContent = 'Scan';
  cancelButton.hidden = true;
}

cancelButton.addEventListener('click', async () => {
  if (!activeScanId) return;
  cancelButton.disabled = true;
  cancelButton.textContent = 'Cancelling...';
  try {
    await request(`/api/live-scans/${activeScanId}`, { method: 'DELETE' });
  } catch (error) {
    setError(error.message);
  }
});

async function loadStatus() {
  capacityFull = false;
  capacityNote.hidden = true;
  try {
    const status = await request('/api/status');
    statusReady = true;
    statusError = null;
    scannerAvailable = status.scanner_available;
    activeNetwork = status.allowed_network;
    scopeSource = status.scope_source;
    scopeConfirmationSupported = status.scope_confirmation_supported === true;
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
        ? 'Ready to scan your authorised local network. Ollama will explain the results before your report opens.'
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
    statusReady = false;
    statusError = error.message;
    configText.textContent = `Scanner status could not be checked. ${error.message}`;
  } finally {
    if (!activeScanId) {
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
  percentText.textContent = `${percent}%`;
  progressBar.style.width = `${percent}%`;
  progressNote.textContent = scan.phase === 'analysis'
    ? 'Scan observations have been saved. This final step can take a few minutes.'
    : `${scan.device_count ?? scan.devices?.length ?? 0} device results saved, ${scan.finding_count ?? scan.findings?.length ?? 0} items to review so far.`;
  if (scan.started_at) {
    const elapsed = Math.max(0, Math.floor((Date.now() - Date.parse(scan.started_at)) / 60000));
    if (Number.isFinite(elapsed)) progressNote.textContent += ` Elapsed: ${elapsed} minute${elapsed === 1 ? '' : 's'}. Device response times vary.`;
  }
}

async function pollScan(scanId) {
  try {
    const scan = await request(`/api/live-scans/${scanId}/progress`);
    pollFailures = 0;
    errorPanel.hidden = true;
    updateProgress(scan);
    if (scan.state === 'queued' || scan.state === 'running' || scan.phase === 'analysis') {
      window.setTimeout(() => pollScan(scanId), 1000);
      return;
    }
    cancelButton.hidden = true;
    rememberScan(null);
    window.location.href = `/scans/${scanId}`;
  } catch (error) {
    if (error.status === 404) {
      rememberScan(null);
      setError('This saved scan could not be found. Open Saved reports to check your scan history.');
    } else if (error.status === 401 || error.status === 403) {
      setError(error.message);
    } else {
      // Losing the browser connection must not forget or restart the backend job.
      errorPanel.hidden = false;
      errorPanel.textContent = `Connection interrupted. Reconnecting to the same scan; do not start another. ${error.message}`;
      window.setTimeout(() => pollScan(scanId), Math.min(1000 * 2 ** Math.min(pollFailures++, 4), 15000));
    }
  }
}

launchButton.addEventListener('click', async () => {
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
    setError('Enter one authorised device IP for a Deep scan.');
    return;
  }
  if (scopeSource === 'automatic' && !window.confirm(`Scan the detected network ${activeNetwork}? Continue only if you own this network or have permission to scan it.`)) return;
  launchButton.disabled = true;
  launchButton.querySelector('span').textContent = 'Starting...';
  progress.hidden = false;
  phaseText.textContent = 'Preparing local scan';
  detailText.textContent = 'Validating authorised scope';
  try {
    const payload = await request('/api/live-scans', {
      method: 'POST',
      body: JSON.stringify({
        mode: deep || savedLightHosts.length ? 'known_hosts' : 'discover',
        profile: selectedProfile,
        hosts: deep ? [deepHost] : savedLightHosts,
        authorised: true,
        ...(scopeConfirmationSupported ? { confirmed_scope: activeNetwork } : {}),
      }),
    });
    await resumeScan(payload.scan_id);
  } catch (error) {
    if (error.status === 429) {
      // Another tab may have taken the last slot since status was read.
      progress.hidden = true;
      cancelButton.hidden = true;
      showCapacityWait();
      return;
    }
    setError(error.message);
  }
});

startSetupTools();
loadStatus();
