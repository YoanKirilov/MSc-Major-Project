import { request } from './api.js';

const form = document.querySelector('#scan-form');
const historyContainer = document.querySelector('#history-container');
const errors = document.querySelector('#scan-errors');
const networkText = document.querySelector('#configured-network');
const scannerStatus = document.querySelector('#scanner-status');
const aiStatus = document.querySelector('#ai-status');

async function loadStatus() {
  try {
    const status = await request('/api/status');
    networkText.textContent = status?.interface_choices?.[0] || 'Not yet configured';
    scannerStatus.textContent = status.scanner_available ? 'Available' : 'Unavailable';
    aiStatus.textContent = status.ai_configured ? 'On' : 'Off';
  } catch (error) {
    console.error(error);
  }
}

async function loadHistory() {
  try {
    const data = await request('/api/scans?source=live&limit=20&offset=0');
    historyContainer.innerHTML = data.items.length
      ? data.items.map((item) => `<div class="card"><p>${item.scan_id}</p><p>State: ${item.state}</p></div>`).join('')
      : '<p>No saved scans yet.</p>';
  } catch (error) {
    historyContainer.innerHTML = `<p>Unable to load history.</p>`;
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const mode = form.querySelector('input[name="mode"]:checked').value;
  const cidr = document.querySelector('#cidr-input').value;
  const hostList = document.querySelector('#host-list').value;
  const approved = document.querySelector('#auth-check').checked;

  if (!approved) {
    errors.textContent = 'You must confirm permission before starting a scan.';
    return;
  }

  const payload = {
    mode,
    cidr: mode === 'discover' ? cidr : null,
    hosts: mode === 'known_hosts' ? hostList.split(/\s+/).filter(Boolean) : [],
    authorised: true,
  };

  try {
    const response = await request('/api/scans', { method: 'POST', body: JSON.stringify(payload) });
    window.location.href = `/scans/${response.scan_id}`;
  } catch (error) {
    errors.textContent = error.message;
  }
});

document.querySelector('#demo-button').addEventListener('click', async () => {
  try {
    const response = await request('/api/demo-scans', { method: 'POST', body: JSON.stringify({ scenario: 'mixed-network-v1' }) });
    window.location.href = `/scans/${response.scan_id}`;
  } catch (error) {
    errors.textContent = error.message;
  }
});

loadStatus();
loadHistory();
