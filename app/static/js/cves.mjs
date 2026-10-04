import { request } from './api.js?v=20261001-network-recovery';

// All links are constructed locally; neither database prose nor AI supplies URLs.
export function createCvePanel(document, scanId, service, saved, onSaved) {
  const element = (tag, value = '') => {
    const node = document.createElement(tag);
    node.textContent = value;
    return node;
  };
  const panel = element('section');
  panel.className = 'detail-block cve-references';
  panel.append(element('h4', 'CVE: published software problems'));
  panel.append(element('p', 'A CVE is a reference number for a publicly reported software problem. A port number alone cannot tell us which CVE applies.'));
  const browse = element('a', 'Browse the CVE database (NVD)');
  browse.href = 'https://nvd.nist.gov/vuln/search';
  browse.target = '_blank';
  browse.rel = 'noopener noreferrer';
  panel.append(browse);
  const output = element('div');
  output.setAttribute('aria-live', 'polite');
  // Use the same exact-version policy as the lookup endpoint; a product/OS CPE
  // alone is insufficient. Older backends fail closed until they are restarted.
  const eligible = service?.cve_lookup_available === true;
  const button = element('button', 'Check CVEs for this software');
  button.type = 'button';
  button.className = 'text-button';

  function show(record) {
    output.replaceChildren();
    output.append(element('p', record.message));
    if (record.query) {
      const identity = element('details');
      identity.append(element('summary', 'Software fingerprint used for this lookup'), element('p', record.query));
      if (record.resolved_query && record.resolved_query !== record.query) identity.append(element('p', `Dictionary candidate: ${record.resolved_query}. The original scan fingerprint is unchanged.`));
      if (record.resolution === 'unique_product_version_candidate') output.append(element('p', 'The dictionary uses a different vendor identifier for this product/version. These are research candidates, not a verified identity or proof your device is affected.'));
      output.append(identity);
    }
    if (record.checked_at) output.append(element('p', `Reference check: ${new Date(record.checked_at).toLocaleString()}. Saved checks are reused for 24 hours.`));
    if (record.results?.length) {
      output.append(element('p', `Showing ${record.results.length} of ${record.total} database records. These are possible matches, not confirmed vulnerabilities on your device.`));
      const list = element('ul');
      record.results.forEach(item => {
        if (!/^CVE-\d{4}-\d{4,19}$/.test(item.cve_id)) return;
        const row = element('li');
        const link = element('a', item.cve_id);
        link.href = `https://nvd.nist.gov/vuln/detail/${item.cve_id}`;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        const details = element('details');
        details.append(element('summary', 'Published technical description'), element('p', item.description));
        row.append(link, details);
        list.append(row);
      });
      output.append(list);
    }
    (record.explanation || []).forEach(line => output.append(element('p', line)));
    if (record.explanation?.length) output.append(element('p', record.ai_source === 'ollama'
      ? 'Local Ollama selected the reviewed explanation above. CVE links come from NVD.'
      : 'Reviewed guidance is shown; an AI explanation was unavailable for this lookup.'));
    button.textContent = 'Check CVEs again';
  }

  if (saved) show(saved);
  if (eligible) {
    panel.append(element('p', 'This online lookup sends the detected software fingerprint to NIST, without your device name, local address or scan report.'));
    panel.append(button);
    button.addEventListener('click', async () => {
      button.disabled = true;
      button.textContent = 'Checking published CVEs…';
      try {
        const payload = await request(`/api/live-scans/${encodeURIComponent(scanId)}/services/${encodeURIComponent(service.service_id)}/cves`, { method: 'POST', body: '{}', timeoutMs: 95000 });
        onSaved(payload);
        show(payload.lookup);
      } catch (error) {
        output.append(element('p', error.message));
        button.textContent = 'Retry CVE lookup';
      } finally { button.disabled = false; }
    });
  } else if (!saved) {
    output.append(element('p', 'This scan did not identify a precise software fingerprint and version. A new Deep scan may collect more detail; a matching CVE cannot be inferred from the port.'));
  }
  panel.append(output);
  panel.append(element('p', 'This product uses data from the NVD API but is not endorsed or certified by the NVD.'));
  return panel;
}
