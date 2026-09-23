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
  progress.hidden = true;
  launchButton.disabled = false;
  launchButton.querySelector('span').textContent = 'Scan';
  cancelButton.hidden = true;
  activeScanId = null;
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
    scannerAvailable = status.scanner_available;
    activeNetwork = status.allowed_network;
    if (status.storage_status !== 'ok') {
      scannerAvailable = false;
      configText.textContent = 'The local results folder is not writable. Restart the app with normal user permissions.';
      return;
    }
    if (activeNetwork && scannerAvailable) {
      const concurrentScans = status.max_concurrent_scans || 2;
      const aiMessage = status.ai_enabled
        ? (status.ai_available ? 'Local AI explanations enabled.' : 'AI is enabled but the local model is unavailable; fixed guidance will be shown.')
        : 'AI explanations are off; enable them in Settings if you want local rewrites.';
      configText.textContent = `Ready to assess ${activeNetwork}. Light checks 12 TCP and 3 UDP services. Up to ${concurrentScans} scans can run at once. ${aiMessage}`;
    } else if (!scannerAvailable) {
      configText.textContent = 'Nmap is not installed or configured on this computer.';
    } else {
      configText.textContent = 'An active private network could not be detected. Configure APP_ALLOWED_NETWORK to continue.';
    }
  } catch {
    configText.textContent = 'The local scanner status could not be checked.';
  }
}

function updateProgress(scan) {
  const coverage = scan.coverage || {};
  const candidates = coverage.candidate_count || 0;
  const discovered = coverage.discovered_count || 0;
  const completed = coverage.service_completed_count || 0;
  const attempted = coverage.service_attempted_count || 0;
  let percent = 0;
  if (scan.phase === 'discovery') {
    phaseText.textContent = 'Discovering authorised hosts';
    detailText.textContent = candidates ? `Checking ${candidates} private addresses` : 'Checking the private scope';
  } else if (discovered > 0 || candidates > 0) {
    const serviceDenominator = discovered || candidates;
    percent = Math.min(96, Math.round((completed / serviceDenominator) * 100));
    phaseText.textContent = completed < serviceDenominator ? 'Inspecting selected TCP and UDP services' : 'Reviewing observed services';
    detailText.textContent = completed < serviceDenominator
      ? `Scanning discovered devices: ${completed} of ${serviceDenominator} complete`
      : `Analysing ${attempted} completed host${attempted === 1 ? '' : 's'}`;
  }
  percentText.textContent = `${percent}%`;
  progressBar.style.width = `${percent}%`;
  progressNote.textContent = `${coverage.discovered_count || 0} devices observed, ${scan.finding_count || 0} findings so far.`;
}

async function pollScan(scanId) {
  try {
    const scan = await request(`/api/live-scans/${scanId}`);
    updateProgress(scan);
    if (scan.state === 'queued' || scan.state === 'running') {
      window.setTimeout(() => pollScan(scanId), 1000);
      return;
    }
    cancelButton.hidden = true;
    activeScanId = null;
    if (scan.state === 'failed' && scan.errors?.length) {
      setError(scan.errors.map((item) => item.message).join(' '));
      return;
    }
    window.location.href = `/scans/${scanId}`;
  } catch (error) {
    setError(error.message);
  }
}

launchButton.addEventListener('click', async () => {
  errorPanel.hidden = true;
  if (!scannerAvailable) {
    setError('Nmap is not installed or configured. Install Nmap before running a real scan.');
    return;
  }
  const deep = selectedProfile === 'deep-tcp-v1';
  const deepHost = deepHostInput.value.trim();
  if (!activeNetwork) {
    setError('An active private network could not be detected. Configure APP_ALLOWED_NETWORK before starting a scan.');
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
    activeScanId = payload.scan_id;
    cancelButton.hidden = false;
    cancelButton.disabled = false;
    cancelButton.textContent = 'Cancel scan';
    await pollScan(payload.scan_id);
  } catch (error) {
    setError(error.message);
  }
});

loadStatus();
