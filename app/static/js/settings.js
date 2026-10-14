import { request } from './api.js?v=20261001-network-recovery';
import { ollamaStatusText } from './report.mjs?v=20261001-network-recovery';

const form = document.querySelector('#settings-form');
const allowedNetwork = document.querySelector('#allowed-network');
const scopeMode = document.querySelector('#scope-mode');
const interfaceSelect = document.querySelector('#interface-select');
const retainRawXml = document.querySelector('#retain-raw-xml');
const mdnsEnabled = document.querySelector('#mdns-enabled');
const mdnsStatus = document.querySelector('#mdns-status');
const aiStatus = document.querySelector('#ai-status');
const saveButton = document.querySelector('#save-settings');
const pageStatus = document.querySelector('#settings-status');
const errorSummary = document.querySelector('#settings-errors');
const errorMessage = document.querySelector('#settings-error-message');
const errorList = document.querySelector('#settings-error-list');
const reloadButton = document.querySelector('#reload-settings');
const fieldErrors = { 'allowed-network': 'allowed-network-error', 'interface-select': 'interface-error',
  'mdns-enabled': 'mdns-error' };
let revision = null;
let generation = 0;
let saving = false;
let baseline = '';
let dirty = false;
function scannerValues() {
  return { allowed_network: scopeMode.value === 'automatic' ? null : allowedNetwork.value.trim() || null,
    interface: interfaceSelect.value || null, retain_raw_xml: retainRawXml.checked,
    mdns_enabled: mdnsEnabled.checked, ai_enabled: true };
}
function trackChanges() {
  dirty = Boolean(baseline) && baseline !== JSON.stringify(scannerValues());
  document.querySelector('#discard-settings').hidden = !dirty;
  if (!saving && baseline) pageStatus.textContent = dirty
    ? 'Unsaved network or scanner changes. Save settings to apply them, or discard your changes.'
    : 'No unsaved network or scanner changes.';
}
form.addEventListener('input', trackChanges);
form.addEventListener('change', trackChanges);
window.addEventListener('beforeunload', event => {
  if (dirty || saving) { event.preventDefault(); event.returnValue = ''; }
});

function clearErrors() {
  errorSummary.hidden = true;
  errorList.replaceChildren();
  reloadButton.hidden = true;
  for (const [id, errorId] of Object.entries(fieldErrors)) {
    document.querySelector(`#${id}`).removeAttribute('aria-invalid');
    const output = document.querySelector(`#${errorId}`);
    output.textContent = '';
    output.hidden = true;
  }
}

function showError(message, { field, reload = false, loading = false } = {}) {
  clearErrors();
  errorSummary.querySelector('h2').textContent = loading ? 'Settings could not be loaded' : 'Settings could not be saved';
  errorMessage.textContent = message;
  reloadButton.hidden = !reload;
  if (field && fieldErrors[field]) {
    const input = document.querySelector(`#${field}`);
    const output = document.querySelector(`#${fieldErrors[field]}`);
    input.setAttribute('aria-invalid', 'true');
    output.textContent = message;
    output.hidden = false;
    const item = document.createElement('li');
    const link = document.createElement('a');
    link.href = `#${field}`;
    link.textContent = input.labels?.[0]?.textContent.trim() || 'Check this setting';
    link.addEventListener('click', (event) => {
      event.preventDefault();
      const disclosure = input.closest('details');
      if (disclosure) disclosure.open = true;
      input.focus();
    });
    item.append(link);
    errorList.append(item);
  }
  errorSummary.hidden = false;
  errorSummary.focus();
}

function networkError(value) {
  const match = value.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\/(\d{1,2})$/);
  if (!match) return 'Enter a private IPv4 network in CIDR format, such as an address followed by /24.';
  const octets = match.slice(1, 5).map(Number);
  const prefix = Number(match[5]);
  if (octets.some((part, index) => part > 255 || String(part) !== match[index + 1]) || prefix < 24 || prefix > 32) {
    return 'Use a valid IPv4 network with a /24 or smaller scope (a prefix from /24 to /32).';
  }
  const privateAddress = octets[0] === 10 || (octets[0] === 172 && octets[1] >= 16 && octets[1] <= 31)
    || (octets[0] === 192 && octets[1] === 168);
  if (!privateAddress) return 'Use a private network range that you are authorised to scan.';
  const numericAddress = octets.reduce((total, part) => total * 256 + part, 0);
  if (numericAddress % (2 ** (32 - prefix))) return 'Enter the network address for this range, not a device address.';
  return null;
}

function showScopeMode() {
  const automatic = scopeMode.value === 'automatic';
  allowedNetwork.disabled = automatic;
  allowedNetwork.required = !automatic;
  document.querySelector('#manual-network-field').hidden = automatic;
  clearErrors();
}
scopeMode.addEventListener('change', showScopeMode);
document.querySelector('#check-ai').addEventListener('click', async (event) => {
  event.target.disabled = true;
  try { aiStatus.textContent = ollamaStatusText(await request('/api/status')); }
  catch (error) { aiStatus.textContent = `Ollama readiness could not be checked. ${error.message}`; }
  finally { event.target.disabled = false; }
});

async function loadSettings() {
  const current = ++generation;
  saveButton.disabled = true;
  clearErrors();
  pageStatus.textContent = 'Loading your saved settings…';
  try {
    const responses = await Promise.allSettled([
      request('/api/settings'),
      request('/api/status'),
    ]);
    if (current !== generation) return;
    if (responses[0].status !== 'fulfilled') throw responses[0].reason;
    const settings = responses[0].value;
    const status = responses[1].status === 'fulfilled' ? responses[1].value : {};
    revision = settings.revision;
    allowedNetwork.value = settings.allowed_network || '';
    scopeMode.value = settings.allowed_network ? 'manual' : 'automatic';
    showScopeMode();
    allowedNetwork.placeholder = '';
    const source = { manual: 'Saved manual range', server: 'Range fixed by the backend configuration', automatic: 'Automatically detected range' }[status.scope_source] || 'Effective range';
    document.querySelector('#network-status').textContent = responses[1].status === 'fulfilled'
      ? [status.detected_network ? `Active connection: ${status.detected_network}.` : '', `${source}: ${status.allowed_network || 'unavailable'}.`, status.network_warning || 'Confirm that you are authorised to scan this range.'].join(' ')
      : 'The current connection could not be checked. Your saved settings are shown; confirm the effective range before scanning.';
    interfaceSelect.replaceChildren();
    const automaticOption = document.createElement('option');
    automaticOption.value = '';
    automaticOption.textContent = 'Automatic';
    interfaceSelect.append(automaticOption);
    const choices = status.interface_choices || (settings.interface ? [settings.interface] : []);
    choices.forEach((name) => {
      const option = document.createElement('option');
      option.value = name;
      option.textContent = name;
      option.selected = name === settings.interface;
      interfaceSelect.append(option);
    });
    retainRawXml.checked = settings.retain_raw_xml;
    mdnsEnabled.checked = settings.mdns_enabled;
    mdnsEnabled.disabled = responses[1].status === 'fulfilled' && !status.mdns_available && !settings.mdns_enabled;
    mdnsStatus.textContent = responses[1].status !== 'fulfilled'
      ? 'Device-announcement availability could not be checked. Your saved choice is unchanged.'
      : status.mdns_available
      ? 'Optional local device announcements are available. They are unverified and may add up to eight device checks.'
      : settings.mdns_enabled
        ? 'Local device announcements are unavailable. Turn this option off before saving settings.'
        : 'Optional local device announcements are unavailable in this installation.';
    aiStatus.textContent = responses[1].status === 'fulfilled' ? ollamaStatusText(status) : 'Ollama availability could not be checked. Use Check Ollama again to retry.';
    saveButton.disabled = false;
    baseline = JSON.stringify(scannerValues());
    dirty = false;
    document.querySelector('#discard-settings').hidden = true;
    pageStatus.textContent = responses[1].status === 'fulfilled' ? 'Settings loaded. Network and scanner changes apply when saved.' : 'Settings loaded, but scanner availability could not be checked.';
  } catch (error) {
    if (current !== generation) return;
    revision = null;
    pageStatus.textContent = 'Settings are unavailable. No changes have been saved.';
    showError(error.message, { reload: true, loading: true });
  }
}

function discardAndLoad() {
  if ((dirty || saving) && !window.confirm('Discard unsaved network and scanner changes? Display preferences are kept.')) return;
  if (!saving) void loadSettings();
}
reloadButton.addEventListener('click', discardAndLoad);
document.querySelector('#discard-settings').addEventListener('click', discardAndLoad);

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (saving) return;
  clearErrors();
  if (revision === null) {
    showError('Settings have not loaded yet. Reload the saved settings before making changes.', { reload: true, loading: true });
    return;
  }
  if (scopeMode.value === 'manual') {
    const message = networkError(allowedNetwork.value.trim());
    if (message) { showError(message, { field: 'allowed-network' }); return; }
  }
  const submitted = scannerValues();
  const payload = { expected_revision: revision, ...submitted };

  saving = true;
  saveButton.disabled = true;
  reloadButton.disabled = true;
  form.setAttribute('aria-busy', 'true');
  pageStatus.textContent = 'Saving your settings…';
  try {
    const saved = await request('/api/settings', { method: 'PATCH', body: JSON.stringify(payload) });
    if (!Number.isSafeInteger(saved?.revision) || saved.revision <= payload.expected_revision) throw new Error('The save response could not be confirmed. Reload saved settings before trying again; your input is kept.');
    revision = saved.revision;
    baseline = JSON.stringify(submitted);
    trackChanges();
    pageStatus.textContent = dirty ? 'Settings saved, but you made further changes while saving. Save again to apply those changes.'
      : 'Network and scanner settings saved. You can now return Home to set up a scan.';
    const networkStatus = document.querySelector('#network-status');
    networkStatus.textContent = 'Settings saved. Checking the current effective network again…';
    void request('/api/status').then(status => {
      networkStatus.textContent = `${status.scope_source === 'server' ? 'Range fixed by backend configuration' : 'Current effective range'}: ${status.allowed_network || 'unavailable'}. ${status.network_warning || 'Confirm permission for this range before scanning.'}`;
    }).catch(() => { networkStatus.textContent = 'Settings saved, but the effective network could not be checked again. Return Home to check the current range before scanning.'; });
  } catch (error) {
    pageStatus.textContent = 'Your changes have not been saved. The input you entered is still here.';
    const message = error.message.toLowerCase();
    const field = /network range|allowed.network|ipv4|cidr/.test(message) ? 'allowed-network'
      : /interface|adapter/.test(message) ? 'interface-select'
        : /mdns/.test(message) ? 'mdns-enabled' : null;
    showError(error.status === 409 ? `${error.message}. Your input is unchanged. Reload saved settings to use the latest version; reloading replaces unsaved changes.` : error.message,
      { field, reload: error.status === 409 });
  } finally {
    saving = false;
    saveButton.disabled = revision === null;
    reloadButton.disabled = false;
    form.removeAttribute('aria-busy');
  }
});

loadSettings();
