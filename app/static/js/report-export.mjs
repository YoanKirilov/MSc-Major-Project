// Sharing uses only the server's explicit projection, never the live report DOM.

const statusLabels = { to_check: 'To check', checked: 'Checked by you', need_help: 'Need help', unavailable: 'Review status unavailable' };

export function sharePath(scanId, { includeIdentifiers = false, includeNotes = false } = {}) {
  const options = new URLSearchParams({ include_identifiers: String(includeIdentifiers === true), include_notes: String(includeNotes === true) });
  return `/api/live-scans/${encodeURIComponent(scanId)}/share?${options}`;
}

export function csvCell(value) {
  let text = value == null ? '' : String(value);
  // Quoting CSV is insufficient: spreadsheet programs still execute formulas.
  if (/^[\s\u0000-\u001f\u007f]*[=+@-]/u.test(text) || /^[\t\r\n]/u.test(text)) text = `'${text}`;
  return `"${text.replaceAll('"', '""')}"`;
}

function portText(values = []) {
  return values.length ? values.map(value => value === 'all-tcp' ? 'All TCP ports (1–65535)' : value).join(', ') : 'Port selection not recorded';
}

function provenanceText(value = {}) {
  if (value.source === 'ai_assisted') {
    return `Local AI contributed accepted wording${value.model ? ` (${value.model})` : ''}. Other fields use reviewed guidance.`;
  }
  return 'Reviewed rule-based guidance.' + (value.older_ai_wording_hidden ? ' Older AI wording is hidden.' : '');
}

export function reportCsv(report) {
  const rows = [['Section', 'Device', 'Item', 'Field', 'Value']];
  const add = (section, device, item, field, value) => rows.push([section, device, item, field, value]);
  for (const key of ['title', 'created_at', 'started_at', 'finished_at', 'generated_at', 'profile_label', 'state', 'scan_outcome', 'review_status_note']) {
    add('Report', '', '', key, report[key]);
  }
  add('Privacy', '', '', 'Device identifiers included', report.privacy?.include_identifiers === true);
  add('Privacy', '', '', 'Report notes included', report.privacy?.include_notes === true);
  add('Privacy', '', '', 'Sharing notice', report.privacy?.notice);
  add('Coverage', '', '', 'Address selection', report.scope?.mode);
  add('Coverage', '', '', 'TCP ports', portText(report.scope?.tcp_ports));
  add('Coverage', '', '', 'UDP ports', portText(report.scope?.udp_ports));
  for (const [key, value] of Object.entries(report.coverage || {})) {
    if (key !== 'targets') add('Coverage', '', '', key, value);
  }
  for (const target of report.coverage?.targets || []) {
    for (const key of ['discovery_status', 'service_status', 'reason_code', 'ip']) {
      if (Object.hasOwn(target, key)) add('Target check', target.label, '', key, target[key]);
    }
  }
  const content = (section, device, item, value = {}) => {
    for (const key of ['meaning', 'why_it_matters']) add(section, device, item, key, value[key]);
    for (const key of ['recommended_steps', 'how_to_check']) {
      (value[key] || []).forEach((line, index) => add(section, device, item, `${key} ${index + 1}`, line));
    }
  };
  content('Overview', '', '', report.overview?.content);
  (report.overview?.limitations || []).forEach(line => add('Overview', '', '', 'Limitation', line));
  add('Overview', '', '', 'Wording source', provenanceText(report.overview?.provenance));
  for (const device of report.devices || []) {
    add('Device', device.label, '', 'Observed at', device.observed_at);
    add('Device', device.label, '', 'Reachability', device.reachability);
    for (const [key, value] of Object.entries(device.identifiers || {})) add('Device', device.label, '', key, value);
    for (const feature of device.features || []) {
      for (const [key, value] of Object.entries(feature)) add('Feature', device.label, feature.label, key, value);
    }
  }
  for (const finding of report.findings || []) {
    for (const key of ['title', 'feature_label', 'severity', 'confidence', 'observed_at']) {
      add('Review item', finding.device_label, finding.label, key, finding[key]);
    }
    content('Final guidance', finding.device_label, finding.label, finding.content);
    (finding.limitations || []).forEach(line => add('Final guidance', finding.device_label, finding.label, 'Limitation', line));
    add('Original guidance', finding.device_label, finding.label, 'Title', finding.fixed_title);
    content('Original guidance', finding.device_label, finding.label, finding.fixed_explanation);
    (finding.fixed_limitations || []).forEach(line => add('Original guidance', finding.device_label, finding.label, 'Limitation', line));
    for (const [key, value] of Object.entries(finding.provenance || {})) {
      add('Wording source', finding.device_label, finding.label, key, Array.isArray(value) ? value.join(', ') : value);
    }
    for (const task of finding.actions || []) {
      for (const key of ['step', 'verification', 'review_updated_at']) add('Review task', finding.device_label, `${finding.label}: ${task.label}`, key, task[key]);
      add('Review task', finding.device_label, `${finding.label}: ${task.label}`, 'Your review status', statusLabels[task.review_status] || 'Review status unavailable');
    }
  }
  for (const [section, items] of [['Warning', report.warnings], ['Unfinished check', report.errors]]) {
    for (const item of items || []) add(section, '', '', item.code, item.message);
  }
  for (const [key, value] of Object.entries(report.versions || {})) add('Recorded version', '', '', key, value);
  if (report.notes) {
    add('Included notes', '', '', 'Report title', report.notes.title);
    for (const item of report.notes.identification_notes || []) {
      add('Included notes', item.device_label, '', 'Identification checked at', item.checked_at);
      for (const line of item.notes || []) add('Included notes', item.device_label, '', 'Identification note', line);
    }
  }
  if (report.annotations_available === false) add('Warning', '', '', 'Notes unavailable', 'Saved review statuses and notes could not be read. No status is assumed.');
  return '\ufeff' + rows.map(row => row.map(csvCell).join(',')).join('\r\n') + '\r\n';
}

export function reportFilename(report, extension = 'csv') {
  const date = /^\d{4}-\d{2}-\d{2}/.exec(report.created_at || '')?.[0] || 'undated';
  return `netguard-report-${date}.${extension === 'csv' ? 'csv' : 'txt'}`;
}

function node(document, tag, text, className) {
  const value = document.createElement(tag);
  if (text != null) value.textContent = String(text);
  if (className) value.className = className;
  return value;
}

function paragraphs(document, parent, lines = []) {
  for (const line of lines) parent.append(node(document, 'p', line));
}

function contentNodes(document, parent, content = {}) {
  paragraphs(document, parent, [content.meaning, content.why_it_matters].filter(Boolean));
  for (const [label, key] of [['Suggested checks', 'recommended_steps'], ['How to check', 'how_to_check']]) {
    if (!content[key]?.length) continue;
    parent.append(node(document, 'h4', label));
    const list = node(document, 'ol');
    for (const line of content[key]) list.append(node(document, 'li', line));
    parent.append(list);
  }
}

function table(document, headings, rows) {
  const element = node(document, 'table');
  const head = node(document, 'thead');
  const headingRow = node(document, 'tr');
  for (const label of headings) {
    const cell = node(document, 'th', label);
    cell.setAttribute('scope', 'col');
    headingRow.append(cell);
  }
  head.append(headingRow);
  const body = node(document, 'tbody');
  for (const values of rows) {
    const row = node(document, 'tr');
    for (const value of values) row.append(node(document, 'td', value));
    body.append(row);
  }
  element.append(head, body);
  return element;
}

export function renderShareReport(document, report) {
  const article = node(document, 'article', null, 'report-export-preview');
  const header = node(document, 'header');
  header.append(node(document, 'h2', report.title), node(document, 'p', `${report.profile_label} scan · ${report.state}`));
  header.append(node(document, 'p', `Recorded: ${report.created_at || 'Date unavailable'}. Finished: ${report.finished_at || 'Finish date unavailable'}.`));
  header.append(node(document, 'p', `Preview prepared: ${report.generated_at || 'Date unavailable'}. Recorded dates use their saved timezone.`));
  article.append(header, node(document, 'p', report.privacy?.notice, 'report-export-privacy-note'));
  article.append(node(document, 'p', `Included: device identifiers ${report.privacy?.include_identifiers ? 'yes' : 'no'}; report notes ${report.privacy?.include_notes ? 'yes' : 'no'}.`));
  const coverage = node(document, 'section');
  coverage.append(node(document, 'h3', 'What this scan checked'));
  const c = report.coverage || {};
  paragraphs(document, coverage, [
    `${c.service_completed_count || 0} device checks finished; ${c.unfinished_device_count || 0} did not finish.`,
    `Address candidates: ${c.candidate_count || 0}; observed during discovery: ${c.discovered_count || 0}; device checks attempted: ${c.service_attempted_count || 0}; failed: ${c.service_failed_count || 0}; skipped: ${c.service_skipped_count || 0}.`,
    `TCP: ${portText(report.scope?.tcp_ports)}. UDP: ${portText(report.scope?.udp_ports)}.`,
    `Discovery completed: ${c.discovery_complete ? 'yes' : 'no or not recorded'}. Service stage completed: ${c.service_stage_complete ? 'yes' : 'no or not recorded'}.`,
  ]);
  coverage.append(node(document, 'p', report.scope?.mode === 'discovered'
    ? 'The table lists devices observed during discovery, including unfinished checks.'
    : 'The table lists explicitly selected device addresses, including unfinished checks.'));
  if (c.unlisted_target_count) coverage.append(node(document, 'p', `${c.unlisted_target_count} other candidate address${c.unlisted_target_count === 1 ? ' is' : 'es are'} not listed: ${c.unlisted_not_observed_count || 0} not observed during discovery; ${c.unlisted_skipped_count || 0} skipped; ${c.unlisted_not_scheduled_count || 0} not scheduled. These counts can overlap. No security conclusion is available for an address that was not checked.`));
  if (c.targets?.length) coverage.append(table(document, ['Device or selected target', 'Check status', 'Recorded reason'], c.targets.map(target => [target.label, target.service_status, target.reason_code || '—'])));
  article.append(coverage);
  const overview = node(document, 'section');
  overview.append(node(document, 'h3', 'Your results explained'));
  contentNodes(document, overview, report.overview?.content);
  paragraphs(document, overview, report.overview?.limitations);
  overview.append(node(document, 'p', provenanceText(report.overview?.provenance)));
  article.append(overview);
  const deviceSection = node(document, 'section');
  deviceSection.append(node(document, 'h3', 'Recorded devices and features'));
  if (!report.devices?.length) deviceSection.append(node(document, 'p', 'No device observations were saved. Device security could not be assessed.'));
  for (const device of report.devices || []) {
    const item = node(document, 'section');
    item.append(node(document, 'h4', device.label));
    const identity = Object.entries(device.identifiers || {}).filter(([, value]) => value).map(([key, value]) => `${key}: ${value}`).join(' · ');
    if (identity) item.append(node(document, 'p', identity));
    item.append(node(document, 'p', `Observed: ${device.observed_at || 'Date unavailable'}; response evidence: ${device.reachability}.`));
    if (device.features?.length) item.append(table(document, ['Feature', 'Reported feature name', 'Connection', 'Recorded state', 'Name source'], device.features.map(feature => [feature.label, feature.name, `${String(feature.protocol).toUpperCase()} port ${feature.port}`, feature.state, feature.detection_method === 'table' ? 'Inferred from port' : feature.detection_method])));
    else item.append(node(document, 'p', 'No service observations were saved for this device.'));
    deviceSection.append(item);
  }
  article.append(deviceSection);
  const reviews = node(document, 'section');
  reviews.append(node(document, 'h3', 'Review items and your checklist'), node(document, 'p', report.review_status_note));
  if (!report.findings?.length) reviews.append(node(document, 'p', 'No review items were recorded from the selected checks. This does not establish that the devices are secure.'));
  if (report.annotations_available === false) reviews.append(node(document, 'p', 'Saved review statuses and notes could not be read. No review status is assumed.'));
  for (const finding of report.findings || []) {
    const item = node(document, 'section', null, 'report-export-finding');
    item.append(node(document, 'h4', `${finding.label}: ${finding.title}`));
    item.append(node(document, 'p', `${finding.device_label} · ${finding.feature_label} · Original observed priority: ${finding.severity} · Confidence: ${finding.confidence}`));
    if (finding.actions?.length) paragraphs(document, item, [finding.content?.meaning, finding.content?.why_it_matters].filter(Boolean));
    else contentNodes(document, item, finding.content);
    paragraphs(document, item, finding.limitations);
    item.append(node(document, 'p', provenanceText(finding.provenance)));
    if (finding.provenance?.ai_fields?.length) item.append(node(document, 'p', `AI wording used for: ${finding.provenance.ai_fields.join(', ')}. Prompt version: ${finding.provenance.prompt_version || 'not recorded'}.`));
    for (const action of finding.actions || []) {
      item.append(node(document, 'p', `${action.label}: ${action.step}`));
      item.append(node(document, 'p', `Check: ${action.verification}. Your review status: ${statusLabels[action.review_status] || 'Review status unavailable'}${action.review_updated_at ? ` (${action.review_updated_at})` : ''}.`));
    }
    reviews.append(item);
  }
  article.append(reviews);
  if (report.errors?.length || report.warnings?.length) {
    const limits = node(document, 'section');
    limits.append(node(document, 'h3', 'Unfinished checks and notices'));
    for (const item of [...(report.errors || []), ...(report.warnings || [])]) limits.append(node(document, 'p', `${item.code || 'Notice'}: ${item.message}`));
    article.append(limits);
  }
  if (report.notes) {
    const notes = node(document, 'section');
    notes.append(node(document, 'h3', 'Included report notes'));
    if (report.notes.title) notes.append(node(document, 'p', report.notes.title));
    for (const item of report.notes.identification_notes || []) {
      notes.append(node(document, 'p', `${item.device_label}: identification checked ${item.checked_at}.`));
      paragraphs(document, notes, item.notes);
    }
    article.append(notes);
  }
  article.append(node(document, 'footer', `Recorded versions: ${Object.entries(report.versions || {}).map(([key, value]) => `${key}: ${value || 'not recorded'}`).join(' · ')}. NetGuard AI.`));
  return article;
}

export function bindReportExport({ button, scanId, request, getData = () => null, document = globalThis.document, window = globalThis.window }) {
  if (!button || !document) return { update() {}, destroy() {} };
  let dialog = null, preview = null, version = 0;
  const update = (data = getData()) => {
    button.disabled = !data || data.source !== 'live' || data.phase !== 'finished' || ['queued', 'running'].includes(data.state);
  };
  update();
  const onOpen = () => {
    if (button.disabled) return;
    if (dialog?.open) return;
    dialog?.remove();
    preview = null;
    dialog = node(document, 'dialog', null, 'report-export-dialog');
    dialog.id = 'report-export-dialog';
    dialog.setAttribute('aria-labelledby', 'report-export-title');
    const controls = node(document, 'div', null, 'report-export-controls');
    const title = node(document, 'h2', 'Print or share this report');
    title.id = 'report-export-title';
    controls.append(title, node(document, 'p', 'Choose what to include, review the preview, then print to paper or PDF or download CSV.'));
    const options = node(document, 'fieldset');
    options.append(node(document, 'legend', 'Information to include'));
    const checkbox = (label) => {
      const wrapper = node(document, 'label');
      const input = node(document, 'input');
      input.type = 'checkbox';
      input.checked = false;
      wrapper.append(input, node(document, 'span', label));
      options.append(wrapper);
      return input;
    };
    const identifiers = checkbox('Include device names and network addresses');
    const notes = checkbox('Include the report title and identification notes');
    const status = node(document, 'p', 'Preparing your private preview…');
    status.setAttribute('role', 'status');
    const print = node(document, 'button', 'Print or save PDF');
    const csv = node(document, 'button', 'Download CSV');
    const close = node(document, 'button', 'Close preview');
    for (const action of [print, csv, close]) action.type = 'button';
    print.disabled = csv.disabled = true;
    controls.append(options, status, print, csv, close);
    const content = node(document, 'div', null, 'report-export-content');
    content.setAttribute('aria-busy', 'true');
    dialog.append(controls, content);
    document.body.append(dialog);
    const reset = () => { ++version; preview = null; dialog.close(); button.focus(); };
    close.addEventListener('click', reset);
    dialog.addEventListener('cancel', event => { event.preventDefault(); reset(); });
    dialog.addEventListener('close', () => { ++version; preview = null; button.focus(); });
    const reload = async () => {
      const ticket = ++version;
      preview = null;
      print.disabled = csv.disabled = true;
      content.replaceChildren();
      content.setAttribute('aria-busy', 'true');
      status.textContent = 'Preparing your private preview…';
      try {
        const response = await request(sharePath(scanId, { includeIdentifiers: identifiers.checked, includeNotes: notes.checked }));
        if (ticket !== version || !dialog.open) return;
        if (response?.schema_version !== 1) throw Error('This report preview could not be read. Reload the saved report and try again.');
        preview = response;
        content.replaceChildren(renderShareReport(document, response));
        print.disabled = csv.disabled = false;
        status.textContent = 'Preview ready. Review the information below before sharing.';
      } catch (error) {
        if (ticket !== version || !dialog.open) return;
        status.textContent = error?.message || 'The share preview could not be prepared. Close it and try again.';
      } finally { if (ticket === version) content.setAttribute('aria-busy', 'false'); }
    };
    identifiers.addEventListener('change', reload);
    notes.addEventListener('change', reload);
    print.addEventListener('click', () => { if (preview && !print.disabled) window.print(); });
    csv.addEventListener('click', () => {
      if (!preview || csv.disabled) return;
      const url = window.URL.createObjectURL(new window.Blob([reportCsv(preview)], { type: 'text/csv;charset=utf-8' }));
      const link = node(document, 'a');
      link.href = url;
      link.download = reportFilename(preview);
      document.body.append(link);
      link.click();
      link.remove();
      window.setTimeout(() => window.URL.revokeObjectURL(url), 1000);
    });
    dialog.showModal();
    close.focus();
    reload();
  };
  button.addEventListener('click', onOpen);
  return { update, destroy() { ++version; button.removeEventListener('click', onOpen); dialog?.remove(); preview = null; } };
}
