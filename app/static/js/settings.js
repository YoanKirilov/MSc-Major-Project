import { request } from './api.js';

const form = document.querySelector('#settings-form');
const allowedNetwork = document.querySelector('#allowed-network');
const interfaceSelect = document.querySelector('#interface-select');
const retainRawXml = document.querySelector('#retain-raw-xml');
const mdnsEnabled = document.querySelector('#mdns-enabled');
const mdnsStatus = document.querySelector('#mdns-status');
const aiEnabled = document.querySelector('#ai-enabled');
const aiStatus = document.querySelector('#ai-status');
let revision = null;

async function loadSettings() {
  try {
    const [settings, status] = await Promise.all([
      request('/api/settings'),
      request('/api/status'),
    ]);
    revision = settings.revision;
    allowedNetwork.value = settings.allowed_network || status.allowed_network || '';
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
    aiEnabled.checked = settings.ai_enabled;
    aiStatus.textContent = status.ai_available
      ? 'The local AI model is ready. It may simplify wording, while scan evidence and the original rule-based actions stay unchanged.'
      : 'The local AI model is not available. The report will use rule-based guidance even if AI explanations are enabled.';
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
    ai_enabled: aiEnabled.checked,
  };

  try {
    await request('/api/settings', { method: 'PATCH', body: JSON.stringify(payload) });
    window.location.href = '/';
  } catch (error) {
    window.alert(error.message);
  }
});

loadSettings();
