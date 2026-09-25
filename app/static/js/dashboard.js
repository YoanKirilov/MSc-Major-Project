import { request } from './api.js';

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

let scannerAvailable = false;
let selectedProfile = 'light';
let activeNetwork = null;
let activeScanId = null;
let statusReady = false;
let statusError = null;
let storageReady = false;
let pollFailures = 0;
const pendingScanKey = 'network-assessor-pending-scan';
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
  rememberScan(id);
  launchButton.disabled = true;
  launchButton.querySelector('span').textContent = 'Scan in progress';
  progress.hidden = false;
  cancelButton.hidden = false;
  cancelButton.disabled = false;
  cancelButton.textContent = 'Cancel scan';
  await pollScan(id);
}

modeButtons.forEach((button) => button.addEventListener('click', () => {
  selectedProfile = button.dataset.profile;
  modeButtons.forEach((item) => {
    const active = item === button;
    item.classList.toggle('active', active);
    item.setAttribute('aria-pressed', String(active));
  });
  const deep = selectedProfile === 'deep-tcp-v1';
  deepHostField.hidden = !deep;
  deepHostInput.hidden = !deep;
}));

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
  try {
    const status = await request('/api/status');
    statusReady = true;
    statusError = null;
    scannerAvailable = status.scanner_available;
    activeNetwork = status.allowed_network;
    storageReady = status.storage_status === 'ok';
    const pending = savedScanId() || status.active_scan_id || status.active_scan_ids?.[0];
    if (pending) {
      configText.textContent = 'Reconnecting to your saved scan. Refreshing does not start a new scan.';
      await resumeScan(pending);
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
        ? 'Ready to scan your authorised local network. Ollama will explain the results before your report opens.'
        : 'Start Ollama and install the configured model to prepare your scan results. See Settings for details.';
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
      launchButton.disabled = false;
      launchButton.querySelector('span').textContent = statusReady ? 'Scan' : 'Retry connection';
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
    percent = 95;
    phaseText.textContent = 'Making your results easier to understand.';
    detailText.textContent = 'Ollama is reading the saved results and choosing clear wording.';
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
  if (!statusReady) {
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
  launchButton.disabled = true;
  launchButton.querySelector('span').textContent = 'Starting...';
  progress.hidden = false;
  phaseText.textContent = 'Preparing local scan';
  detailText.textContent = 'Validating authorised scope';
  try {
    const payload = await request('/api/live-scans', {
      method: 'POST',
      body: JSON.stringify({
        mode: deep ? 'known_hosts' : 'discover',
        profile: selectedProfile,
        hosts: deep ? [deepHost] : [],
        authorised: true,
      }),
    });
    await resumeScan(payload.scan_id);
  } catch (error) {
    setError(error.message);
  }
});

loadStatus();
