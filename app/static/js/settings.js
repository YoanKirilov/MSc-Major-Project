const form = document.querySelector('#settings-form');

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    expected_revision: 1,
    allowed_network: document.querySelector('#allowed-network').value,
    interface: document.querySelector('#interface-select').value,
    retain_raw_xml: document.querySelector('#retain-raw-xml').checked,
    ai_enabled: document.querySelector('#ai-enabled').checked,
  };

  try {
    const response = await fetch('/api/settings', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const body = await response.json();
    if (!response.ok) {
      throw new Error(body.error?.message || 'Unable to save settings');
    }
    window.location.href = '/';
  } catch (error) {
    window.alert(error.message);
  }
});
