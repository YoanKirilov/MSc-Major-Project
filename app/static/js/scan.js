const summary = document.querySelector('#scan-summary');
const pathParts = window.location.pathname.split('/');
const scanId = pathParts[pathParts.length - 1];

async function loadScan() {
  try {
    const response = await fetch(`/api/scans/${scanId}`);
    if (!response.ok) {
      throw new Error('Unable to load scan');
    }
    const data = await response.json();
    summary.innerHTML = `<h3>Scan ${data.scan_id}</h3><p>State: ${data.state}</p><p>Phase: ${data.phase}</p><p>Source: ${data.source}</p>`;
  } catch (error) {
    summary.textContent = error.message;
  }
}

loadScan();
