import { request } from './api.js?v=20261001-network-recovery';
import { recordedTimeLabel } from './presentation.mjs?v=20261008-dates';

// All links are constructed locally; neither database prose nor AI supplies URLs.
export function createCvePanel(document, scanId, service, saved, onSaved) {
  const element = (tag, value = '') => {
    const node = document.createElement(tag);
    node.textContent = value;
    return node;
  };
  const panel = element('section');
  panel.className = 'detail-block cve-references';
  panel.dataset.notePanel = 'cve';
  panel.append(element('h4', 'Published software problems (CVE)'));
  const availability = element('p');
  availability.className = 'cve-status status-message';
  availability.setAttribute('role', 'status');
  const research = element('details');
  research.className = 'cve-research';
  research.dataset.disclosureKey = `cve:${service?.service_id || 'unidentified-service'}`;
  research.append(element('summary', 'About CVE research and saved references'));
  research.append(element('p', 'A CVE is a reference number for a publicly reported software problem. A port number alone cannot tell us which CVE applies. Possible database matches are not confirmed vulnerabilities on this device.'));
  const browse = element('a', 'Browse the CVE database (NVD)');
  browse.href = 'https://nvd.nist.gov/vuln/search';
  browse.target = '_blank';
  browse.rel = 'noopener noreferrer';
  research.append(browse);
  const output = element('div');
  // Use the same exact-version policy as the lookup endpoint; a product/OS CPE
  // alone is insufficient. Older backends fail closed until they are restarted.
  const eligible = service?.cve_lookup_available === true;
  const button = element('button', 'Check CVEs for this software');
  button.type = 'button';
  button.className = 'secondary-button';
  button.dataset.deviceAction = 'cve-lookup';
  function availabilityText(record) {
    if (!record) return eligible
      ? 'Optional research is available for the recorded software version. No online lookup has started.'
      : 'CVE matching is unavailable: a precise software fingerprint and version were not recorded.';
    const count = (record.results || []).filter(item => /^CVE-\d{4}-\d{4,19}$/.test(item.cve_id)).length;
    if (record.status === 'candidates' && count) return `${count} saved possible CVE match${count === 1 ? '' : 'es'}; not confirmed vulnerabilities on this device.`;
    return ({ no_matches: 'No matching CVE records were returned by the saved lookup; this is not proof of safety.',
      identity_unresolved: 'The saved lookup could not identify this software reliably; no match is confirmed.',
      insufficient_evidence: 'The saved lookup did not have enough software evidence to match CVEs.',
      unavailable: 'The saved CVE lookup was unavailable. Your scan evidence remains accessible.' })[record.status]
      || 'Saved CVE research is available; matches require checking the actual software and version.';
  }

  function show(record) {
    availability.textContent = availabilityText(record);
    output.replaceChildren();
    output.append(element('p', record.message));
    if (record.query) {
      const identity = element('details');
      identity.dataset.disclosureKey = 'software-fingerprint';
      identity.append(element('summary', 'Software fingerprint used for this lookup'), element('p', record.query));
      if (record.resolved_query && record.resolved_query !== record.query) identity.append(element('p', `Dictionary candidate: ${record.resolved_query}. The original scan fingerprint is unchanged.`));
      if (record.resolution === 'unique_product_version_candidate') output.append(element('p', 'The dictionary uses a different vendor identifier for this product/version. These are research candidates, not a verified identity or proof your device is affected.'));
      output.append(identity);
    }
    if (record.checked_at) output.append(element('p', `Reference check: ${recordedTimeLabel(record.checked_at)}. Saved checks are reused for 24 hours.`));
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
        details.dataset.disclosureKey = `description:${item.cve_id}`;
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

  availability.textContent = availabilityText(saved);
  if (saved) show(saved);
  let shown = saved ? JSON.stringify(saved) : '';
  panel.updateNotes = snapshot => {
    const record = snapshot?.cve_lookups?.find(item => item.service_id === service?.service_id);
    const signature = record ? JSON.stringify(record) : '';
    if (signature === shown) return;
    shown = signature;
    if (record) show(record);
    else {
      output.replaceChildren();
      button.textContent = 'Check CVEs for this software';
      availability.textContent = availabilityText(null);
    }
  };
  if (eligible) {
    research.append(element('p', 'Only pressing the lookup button sends the detected software fingerprint to NIST, without your device name, local address or scan report. Opening this section does not start a lookup.'));
    research.append(button);
    button.addEventListener('click', async () => {
      const hadFocus = document.activeElement === button;
      button.disabled = true;
      button.textContent = 'Checking published CVEs…';
      availability.textContent = 'Checking published software problems. This does not run another device scan.';
      try {
        const payload = await request(`/api/live-scans/${encodeURIComponent(scanId)}/services/${encodeURIComponent(service.service_id)}/cves`, { method: 'POST', body: '{}', timeoutMs: 95000 });
        // A delayed lookup response may contain an older snapshot than another
        // completed edit. Its caller rejects it rather than regressing the UI.
        if (onSaved(payload) !== false) { show(payload.lookup); shown = JSON.stringify(payload.lookup); }
      } catch (error) {
        output.append(element('p', error.message));
        button.textContent = 'Retry CVE lookup';
        availability.textContent = 'The CVE lookup could not finish. Saved references and scan evidence are unchanged.';
      } finally {
        button.disabled = false;
        if (button.textContent === 'Checking published CVEs…') {
          button.textContent = shown ? 'Check CVEs again' : 'Check CVEs for this software';
          availability.textContent = availabilityText(shown ? JSON.parse(shown) : null);
        }
        if (hadFocus && document.activeElement === document.body) button.focus({ preventScroll: true });
      }
    });
  } else if (!saved) {
    output.append(element('p', 'This scan did not identify a precise software fingerprint and version. A new Deep scan may collect more detail; a matching CVE cannot be inferred from the port.'));
  }
  research.append(output);
  research.append(element('p', 'This product uses data from the NVD API but is not endorsed or certified by the NVD.'));
  panel.append(availability, research);
  return panel;
}
