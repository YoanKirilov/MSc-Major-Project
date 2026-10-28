import { request, CVE_LOOKUP_TIMEOUT_MS } from './api.js?v=20261018-cve-deadline';
import { recordedTimeLabel } from './presentation.mjs?v=20261008-dates';

// CVE links are constructed locally. Maker links require validated structured
// NVD references; neither database prose nor AI can invent a destination.
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
  // Backend policy requires a confidently observed application, never a port/OS
  // guess. It labels version-specific and related-product research separately.
  const eligible = service?.cve_lookup_available === true;
  const button = element('button', 'Check CVEs for this software');
  button.type = 'button';
  button.className = 'secondary-button';
  button.dataset.deviceAction = 'cve-lookup';
  const reload = element('button', 'Reload saved CVE references');
  reload.type = 'button';
  reload.className = 'secondary-button';
  reload.hidden = true;
  const feedback = element('p');
  feedback.hidden = true;
  let unconfirmed = false;
  let pendingOperation = null;
  function availabilityText(record) {
    if (!record) return eligible
      ? 'Optional software research is available. Version matches and related-product references are kept separate. No online lookup has started.'
      : 'CVE matching is unavailable: a reliable software product was not recorded.';
    const count = (record.results || []).filter(item => /^CVE-\d{4}-\d{4,19}$/.test(item.cve_id)).length;
    const related = (record.related_results || []).filter(item => /^CVE-\d{4}-\d{4,19}$/.test(item.cve_id)).length;
    if (record.related_status === 'coverage_unknown') return 'The database did not provide enough detail to check this software. Related results remain unverified; no vulnerability was confirmed.';
    if (related) return `${record.query ? count + ' possible version matches' : 'Version not identified'}; ${related} related-product reference${related === 1 ? '' : 's'}. None confirms a vulnerability on this device.`;
    if (record.status === 'candidates' && count) return `${count} saved possible CVE match${count === 1 ? '' : 'es'}; not confirmed vulnerabilities on this device.`;
    return ({ no_matches: 'No matching CVE records were returned by the saved lookup; this is not proof of safety.',
      identity_unresolved: 'The saved lookup could not identify this software reliably; no match is confirmed.',
      insufficient_evidence: 'The saved lookup did not have enough software evidence to match CVEs.',
      unavailable: 'The saved CVE lookup was unavailable. Your scan evidence remains accessible.' })[record.status]
      || 'Saved CVE research is available; matches require checking the actual software and version.';
  }

  function references(records, parent) {
    const list = element('ul');
    records.forEach(item => {
      if (!/^CVE-\d{4}-\d{4,19}$/.test(item.cve_id)) return;
      const row = element('li');
      const link = element('a', item.cve_id);
      link.href = `https://nvd.nist.gov/vuln/detail/${item.cve_id}`;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      const details = element('details');
      details.dataset.disclosureKey = `description:${item.cve_id}`;
      details.append(element('summary', 'Published technical description'), element('p', item.description));
      row.append(link);
      const published = recordedTimeLabel(item.published_at, '');
      const modified = recordedTimeLabel(item.modified_at, '');
      if (published || modified) row.append(element('p', [published && `Published: ${published}`, modified && `Updated: ${modified}`].filter(Boolean).join(' · ')));
      row.append(details);
      for (const advisory of (item.advisories || []).slice(0, 3)) {
        try {
          const url = new URL(advisory.url);
          if (url.protocol !== 'https:' || url.username || url.password || url.hash || (url.port && url.port !== '443')
            || !/^[a-z0-9][a-z0-9.-]*\.[a-z][a-z0-9-]*$/i.test(url.hostname)
            || /\.(local|localhost|internal|lan|home\.arpa)$/i.test(url.hostname)) continue;
          const help = element('a', `Maker's advice — ${url.hostname} (NVD reference)`);
          help.href = url.href; help.target = '_blank'; help.rel = 'noopener noreferrer';
          row.append(element('p', 'Check the maker and affected versions before changing settings.'), help);
        } catch { /* Invalid saved or external URLs never become links. */ }
      }
      list.append(row);
    });
    parent.append(list);
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
    if (record.checked_at) output.append(element('p', `Reference check: ${recordedTimeLabel(record.checked_at)}. ${record.related_search_incomplete
      ? 'The search was incomplete. Checking again requests fresh references.'
      : 'Completed searches may be reused for up to 24 hours.'}`));
    if (record.results?.length) {
      output.append(element('h5', 'References for the recorded version'));
      output.append(element('p', `Showing ${record.results.length} of ${record.total} database records. These are possible matches, not confirmed vulnerabilities on your device.`));
      references(record.results, output);
    }
    if (record.related_query) {
      const related = element('section');
      related.className = 'cve-related-references';
      related.append(element('h5', 'Related software problems — version not verified'));
      related.append(element('p', 'These records concern the same software product, possibly other versions or settings. They are leads to compare with the maker’s advice, not matches confirmed for your device.'));
      if (record.related_selection === 'recent_first') related.append(element('p', `Recent published cases are shown first among the ${record.related_examined || 0} records checked. This can help even when the recorded version has no exact match.`));
      if (record.related_search_incomplete) related.append(element('p', 'Part of the product search could not finish. Available references are preserved; check again later for a fuller selection.'));
      if (record.related_results?.length) {
        related.append(element('p', `Showing ${record.related_results.length} additional reference${record.related_results.length === 1 ? '' : 's'} from a limited product search. Records already listed above are not repeated.`));
        references(record.related_results, related);
      } else related.append(element('p', record.related_status === 'unavailable'
        ? 'The related-product search could not finish. Any version references above remain available.'
        : 'No additional verified product references were retained from the limited search. This is not proof of safety.'));
      if (record.related_truncated) related.append(element('p', 'This is a limited selection, not a complete list of published problems.'));
      if (record.related_unverified) related.append(element('p', `${record.related_unverified} returned record${record.related_unverified === 1 ? '' : 's'} lacked usable product applicability. We could not check whether they relate to this software; they are not a no-problems result.`));
      output.append(related);
    }
    (record.explanation || []).forEach(line => output.append(element('p', line)));
    if (record.explanation?.length) output.append(element('p', record.ai_source === 'ollama'
      ? 'Local Ollama selected the reviewed explanation above. CVE links come from NVD.'
      : 'Reviewed guidance is shown. CVE links come from NVD.'));
    button.textContent = 'Check CVEs again';
  }

  availability.textContent = availabilityText(saved);
  if (saved) show(saved);
  function signatureOf(record) {
    if (!record) return '';
    const visible = { ...record };
    delete visible.operation_id; // A receipt is not new wording/evidence.
    delete visible.operation_receipts;
    return JSON.stringify(visible);
  }
  let shown = signatureOf(saved);
  function display(record) {
    const signature = signatureOf(record);
    if (signature !== shown) { show(record); shown = signature; }
    else {
      availability.textContent = availabilityText(record);
      button.textContent = 'Check CVEs again';
    }
  }
  panel.updateNotes = snapshot => {
    const record = snapshot?.cve_lookups?.find(item => item.service_id === service?.service_id);
    const signature = signatureOf(record);
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
    research.append(reload, feedback);
    reload.addEventListener('click', async () => {
      const hadFocus = document.activeElement === reload;
      reload.disabled = true;
      feedback.hidden = false;
      feedback.textContent = 'Reading saved references. This does not start another lookup or scan.';
      try {
        const snapshot = await request(`/api/live-scans/${encodeURIComponent(scanId)}/annotations`);
        const accepted = onSaved({ annotations: snapshot, revision: snapshot?.revision });
        const record = snapshot?.cve_lookups?.find(item => item.service_id === service.service_id);
        // A title/checklist edit can advance the overall revision while leaving
        // old CVEs unchanged. Only this attempt's saved receipt confirms it.
        // Without a receipt, remain uncertain rather than guessing from changed
        // text/dates. A successful direct POST can still confirm a cache hit.
        const matchesAttempt = record && pendingOperation && (record.operation_id === pendingOperation
          || (record.operation_receipts || []).slice(-8).some(item => item.operation_id === pendingOperation));
        if (accepted !== false && record && (!unconfirmed || matchesAttempt)) {
          display(record);
          unconfirmed = false;
          pendingOperation = null;
          button.disabled = false;
          reload.hidden = true;
          feedback.textContent = 'Saved references loaded. Their recorded date shows when they were checked; this did not perform a new lookup.';
        } else {
          availability.textContent = 'The latest lookup is still unconfirmed. Any earlier saved references remain available.';
          feedback.textContent = 'No newer saved references could be confirmed for this attempt. A saved record or an unrelated edit does not confirm that it finished. Try reading saved references again shortly, or reload the report before starting a new lookup.';
        }
      } catch (error) {
        availability.textContent = 'Saved CVE references could not be read. No new lookup or scan was started.';
        feedback.textContent = `${error.message} Saved references could not be read; no new lookup was started.`;
      } finally {
        reload.disabled = false;
        if (hadFocus && reload.hidden && [reload, document.body].includes(document.activeElement)) button.focus({ preventScroll: true });
      }
    });
    button.addEventListener('click', async () => {
      if (unconfirmed) return;
      pendingOperation = globalThis.crypto?.randomUUID?.() || null;
      const hadFocus = document.activeElement === button;
      button.disabled = true;
      button.textContent = 'Checking published CVEs…';
      availability.textContent = 'Checking published software problems. This does not run another device scan.';
      feedback.hidden = true;
      try {
        const payload = await request(`/api/live-scans/${encodeURIComponent(scanId)}/services/${encodeURIComponent(service.service_id)}/cves`, { method: 'POST', body: JSON.stringify(pendingOperation ? { operation_id: pendingOperation } : {}), timeoutMs: CVE_LOOKUP_TIMEOUT_MS });
        // A delayed lookup response may contain an older snapshot than another
        // completed edit. Its caller rejects it rather than regressing the UI.
        if (onSaved(payload) !== false) display(payload.lookup);
      } catch (error) {
        unconfirmed = !Number.isInteger(error.status) || error.status >= 500;
        feedback.hidden = false;
        feedback.textContent = error.message;
        reload.hidden = false;
        button.textContent = 'Check CVEs again';
        availability.textContent = unconfirmed
          ? 'The lookup result was not confirmed. It may still finish and save. Read saved references before starting another lookup; scan evidence is preserved.'
          : 'The lookup request was not completed. You can read saved references without starting another lookup; scan evidence is preserved.';
      } finally {
        button.disabled = unconfirmed;
        if (button.textContent === 'Checking published CVEs…') {
          button.textContent = shown ? 'Check CVEs again' : 'Check CVEs for this software';
          availability.textContent = availabilityText(shown ? JSON.parse(shown) : null);
        }
        if (hadFocus && document.activeElement === document.body) button.focus({ preventScroll: true });
      }
    });
  } else if (!saved) {
    output.append(element('p', 'This scan did not reliably identify the software product. A new Deep scan may collect more detail; a matching CVE cannot be inferred from the port.'));
  }
  research.append(output);
  research.append(element('p', 'This product uses data from the NVD API but is not endorsed or certified by the NVD.'));
  panel.append(availability, research);
  return panel;
}
