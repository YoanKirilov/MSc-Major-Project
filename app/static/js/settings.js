import { request } from './api.js';

const form = document.querySelector('#settings-form');
const allowedNetwork = document.querySelector('#allowed-network');
const interfaceSelect = document.querySelector('#interface-select');
const retainRawXml = document.querySelector('#retain-raw-xml');
const mdnsEnabled = document.querySelector('#mdns-enabled');
const mdnsStatus = document.querySelector('#mdns-status');
const piholeEnabled = document.querySelector('#pihole-enabled');
const piholeStatus = document.querySelector('#pihole-status');
const aiStatus = document.querySelector('#ai-status');
let revision = null;

async function loadSettings() {
  try {
    const [settings, status] = await Promise.all([
      request('/api/settings'),
      request('/api/status'),
    ]);
    revision = settings.revision;
    allowedNetwork.value = settings.allowed_network || '';
    allowedNetwork.placeholder = status.allowed_network ? `Automatic: ${status.allowed_network}` : 'Enter your authorised network range';
    document.querySelector('#network-status').textContent = [status.detected_network ? `Active connection: ${status.detected_network}.` : '', status.network_warning || 'Confirm that you are authorised to scan this range.'].join(' ');
    interfaceSelect.replaceChildren();
    const automaticOption = document.createElement('option');
    automaticOption.value = '';
    automaticOption.textContent = 'Automatic';
    interfaceSelect.append(automaticOption);
    (status.interface_choices || []).forEach((name) => {
      const option = document.createElement('option');
      option.value = name;
      option.textContent = name;
      option.selected = name === settings.interface;
      interfaceSelect.append(option);
    });
    retainRawXml.checked = settings.retain_raw_xml;
    mdnsEnabled.checked = settings.mdns_enabled;
    mdnsEnabled.disabled = !status.mdns_available && !settings.mdns_enabled;
    mdnsStatus.textContent = status.mdns_available
      ? 'Optional local device announcements are available. They are unverified and may add up to eight device checks.'
      : settings.mdns_enabled
        ? 'Local device announcements are unavailable. Turn this option off before saving settings.'
        : 'Optional local device announcements are unavailable in this installation.';
    piholeEnabled.checked = settings.pihole_enabled;
    piholeEnabled.disabled = !status.pihole_configured && !settings.pihole_enabled;
    piholeStatus.textContent = status.pihole_configuration_error
      ? `Pi-hole setup needs attention: ${status.pihole_configuration_error}`
      : status.pihole_configured
        ? 'Pi-hole details are configured; this page does not check the connection. When enabled, names are requested during an authorised scan. Missing names are possible and do not mean a device is absent.'
        : 'Pi-hole is not configured. Set APP_PIHOLE_URL and APP_PIHOLE_PASSWORD_FILE (or APP_PIHOLE_PASSWORD) on the server, then restart the app. No Pi-hole connection is made by this page.';
    aiStatus.textContent = status.ai_available
      ? `Ollama is ready (${status.ai_model}). Scan facts and original guidance remain available.`
      : `Ollama is unavailable. Start Ollama and install ${status.ai_model} before scanning.`;
  } catch (error) {
    window.alert(error.message);
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (revision === null) {
    window.alert('Settings have not loaded yet.');
    return;
  }
  const payload = {
    expected_revision: revision,
    allowed_network: allowedNetwork.value.trim() || null,
    interface: interfaceSelect.value || null,
    retain_raw_xml: retainRawXml.checked,
    mdns_enabled: mdnsEnabled.checked,
    ai_enabled: true,
    pihole_enabled: piholeEnabled.checked,
  };

  try {
    await request('/api/settings', { method: 'PATCH', body: JSON.stringify(payload) });
    window.location.href = '/';
  } catch (error) {
    window.alert(error.message);
  }
});

loadSettings();
