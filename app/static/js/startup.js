// Classic, external bootstrap: works before modules and under script-src 'self'.
(() => {
  if (document.documentElement.dataset.localApp !== 'backend') {
    // A static preview cannot run the Python scanner or read private reports.
    window.location.replace('http://127.0.0.1:8765/');
    return;
  }
  window.addEventListener('error', () => {
    const button = document.querySelector('#scanLaunchButton');
    const label = button?.querySelector('span');
    if (!label) {
      const title = document.querySelector('#result-title');
      const lead = document.querySelector('#result-lead');
      const retry = document.querySelector('#retryReportLoad');
      if (title?.textContent !== 'Loading your report' || !lead || !retry) return;
      title.textContent = 'The saved report could not load';
      lead.textContent = 'Reload this page to read the saved results. If this continues, restart the NetGuard backend after active scans finish. Your saved evidence remains on this computer; no scan was started.';
      retry.hidden = false; retry.disabled = false; retry.textContent = 'Reload page';
      retry.onclick = () => window.location.reload();
      return;
    }
    if (label.textContent !== 'Checking scanner...') return;
    const notice = document.querySelector('#scan-config');
    if (notice) notice.textContent = 'The dashboard could not finish loading. Reload the page (Ctrl+F5) to get the latest app files. If this continues, restart the NetGuard backend and reopen its session link. No scan was started by this page.';
    button.disabled = false;
    label.textContent = 'Reload page';
    button.onclick = () => window.location.reload();
  }, true);
})();
