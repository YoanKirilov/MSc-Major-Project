import assert from 'node:assert/strict';
import test from 'node:test';
import { bindReportExport, csvCell, renderShareReport, reportCsv, reportFilename, sharePath } from '../app/static/js/report-export.mjs';

function report(overrides = {}) {
  return {
    schema_version: 1, title: 'Light scan report', profile_label: 'Light', state: 'partial',
    created_at: '2026-10-14T09:15:00Z', started_at: '2026-10-14T09:15:00Z', finished_at: '2026-10-14T09:16:00Z', generated_at: '2026-10-14T10:00:00Z',
    privacy: { include_identifiers: false, include_notes: false, notice: 'Review before sharing; anonymity is not guaranteed.' },
    scope: { mode: 'selected', tcp_ports: [21, 80, 443], udp_ports: [53] },
    coverage: { service_completed_count: 1, unfinished_device_count: 1, service_failed_count: 1, service_skipped_count: 0, discovery_complete: false, service_stage_complete: false,
      targets: [{ label: 'Device 1', service_status: 'completed', reason_code: '' }, { label: 'Selected target 2', service_status: 'timed_out', reason_code: 'host_scan_timeout' }] },
    overview: { content: { meaning: 'One responding feature.', why_it_matters: 'Review the observation.', recommended_steps: ['Review coverage.'], how_to_check: ['Repeat unfinished checks.'] }, limitations: ['Only completed checks are included.'], provenance: { source: 'reviewed_guidance' } },
    devices: [{ label: 'Device 1', observed_at: '2026-10-14T09:15:00Z', reachability: 'observed', features: [{ label: 'Feature 1', name: 'http', protocol: 'tcp', port: 80, state: 'open', detection_method: 'table' }] }],
    findings: [{ label: 'Review item 1', device_label: 'Device 1', feature_label: 'Feature 1', title: 'Accepted title', severity: 'high', confidence: 'medium', observed_at: '2026-10-14T09:15:00Z',
      content: { meaning: 'Accepted meaning.', why_it_matters: 'Check the feature.', recommended_steps: ['Accepted step.'], how_to_check: ['Accepted verification.'] }, limitations: ['Access was not confirmed.'],
      fixed_title: 'Original title', fixed_explanation: { meaning: 'Original meaning.', why_it_matters: 'Original importance.', recommended_steps: ['Original step.'], how_to_check: ['Original verification.'] }, fixed_limitations: ['Original limitation.'],
      provenance: { source: 'ai_assisted', ai_fields: ['title', 'meaning'], provider: 'ollama', model: 'synthetic-model', prompt_version: 'synthetic-v1', completed_at: '2026-10-14T09:16:00Z' },
      actions: [{ label: 'Task 1', step: 'Accepted step.', verification: 'Accepted verification.', review_status: 'checked', review_updated_at: '2026-10-14T09:17:00Z' }] }],
    review_status_note: 'Checked records your review, not a verified fix. Original observed priority is retained.',
    warnings: [{ code: 'SYNTHETIC', message: 'Review the incomplete check.' }], errors: [{ code: 'HOST_SCAN_TIMEOUT', message: 'One selected check timed out.' }],
    versions: { app: '0.1.0', rules: 'synthetic-rules' }, annotations_available: true,
    ...overrides,
  };
}

test('share request defaults private and URL components are encoded with strict boolean flags', () => {
  assert.equal(sharePath('report-id'), '/api/live-scans/report-id/share?include_identifiers=false&include_notes=false');
  assert.equal(sharePath('../danger?x=1', { includeIdentifiers: 'true', includeNotes: true }), '/api/live-scans/..%2Fdanger%3Fx%3D1/share?include_identifiers=false&include_notes=true');
});

test('CSV quotes delimiters and blocks spreadsheet formulas including whitespace and control prefixes', () => {
  for (const value of ['=SUM(1,2)', '+cmd', '-3+5', '@SUM(1)', '  =1', '\t=1', '\r=1', '\n=1', '\u0000=1']) {
    assert.ok(csvCell(value).startsWith('"\''), `Unsafe prefix: ${JSON.stringify(value)}`);
  }
  assert.equal(csvCell('a,"b"\nc'), '"a,""b""\nc"');
  assert.equal(csvCell(80), '"80"');
  assert.equal(csvCell(null), '""');
});

test('CSV preserves dates, coverage limits, original priority, both guidance sources and user review status', () => {
  const csv = reportCsv(report());
  for (const value of ['2026-10-14T09:15:00Z', 'host_scan_timeout', 'service_failed_count', 'unfinished_device_count', 'Original meaning.', 'Accepted meaning.', 'Original observed priority', 'synthetic-model', 'Checked by you', 'not a verified fix', '"severity","high"']) assert.ok(csv.includes(value), value);
  assert.ok(csv.startsWith('\ufeff"Section"'));
  assert.ok(csv.endsWith('\r\n'));
  assert.ok(!csv.includes('192.168.56.10'));
  const input = report({ title: '=1+2', notes: { title: '=HYPERLINK("https://example.invalid")', identification_notes: [] } });
  const safe = reportCsv(input);
  assert.ok(safe.includes('"\'=1+2"'));
  assert.ok(safe.includes('"\'=HYPERLINK(""https://example.invalid"")"'));
  assert.equal(input.title, '=1+2');
});

test('filenames only use a bounded saved date and empty coverage is explicit', () => {
  assert.equal(reportFilename(report()), 'netguard-report-2026-10-14.csv');
  assert.equal(reportFilename(report({ created_at: '../../private' })), 'netguard-report-undated.csv');
  const csv = reportCsv(report({ scope: {}, devices: [], findings: [], annotations_available: false }));
  assert.match(csv, /Port selection not recorded/);
  assert.match(csv, /Saved review statuses and notes could not be read/);
});

class Element {
  constructor(tag, document) {
    this.tagName = tag.toUpperCase(); this.document = document; this.children = []; this.attributes = new Map(); this.listeners = new Map(); this.disabled = false; this.open = false; this._text = '';
  }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map(child => child.textContent).join(' '); }
  set innerHTML(_value) { throw Error('HTML injection attempted'); }
  append(...children) { for (const child of children) { child.parent = this; this.children.push(child); } }
  replaceChildren(...children) { this.children = []; this._text = ''; this.append(...children); }
  setAttribute(name, value) { this.attributes.set(name, String(value)); }
  addEventListener(name, handler) { this.listeners.set(name, [...(this.listeners.get(name) || []), handler]); }
  removeEventListener(name, handler) { this.listeners.set(name, (this.listeners.get(name) || []).filter(value => value !== handler)); }
  fire(name, event = {}) { for (const listener of this.listeners.get(name) || []) listener(event); }
  click() { if (!this.disabled) this.fire('click'); }
  focus() { this.document.focused = this; }
  remove() { if (this.parent) this.parent.children = this.parent.children.filter(value => value !== this); }
  showModal() { this.open = true; }
  close() { this.open = false; this.fire('close'); }
}

function fakeDocument() {
  const document = { createElement(tag) { return new Element(tag, document); } };
  document.body = document.createElement('body');
  return document;
}

function all(element) { return [element, ...element.children.flatMap(all)]; }
function find(element, predicate) { return all(element).find(predicate); }
function action(document, label) { return find(document.body, item => item.tagName === 'BUTTON' && item.textContent === label); }
const settle = () => new Promise(resolve => setImmediate(resolve));

test('print preview is semantic text-only DOM with complete limits and compact final guidance', () => {
  const document = fakeDocument();
  const payload = report({ title: '<script>alert("private")</script>' });
  payload.findings[0].content.meaning = '<img src=x onerror=alert(1)>';
  const article = renderShareReport(document, payload);
  assert.equal(article.tagName, 'ARTICLE');
  assert.ok(article.textContent.includes('<script>alert("private")</script>'));
  assert.ok(article.textContent.includes('<img src=x onerror=alert(1)>'));
  assert.equal(all(article).some(item => ['SCRIPT', 'IMG', 'IFRAME'].includes(item.tagName)), false);
  for (const text of ['Only completed checks', '1 did not finish', 'host_scan_timeout', 'Original observed priority: high', 'Accepted verification.', 'Checked by you', 'synthetic-model', 'Inferred from port']) assert.ok(article.textContent.includes(text), text);
  assert.equal(article.textContent.includes('Original meaning.'), false);
  assert.equal(article.textContent.includes('Original reviewed guidance'), false);
  assert.ok(all(article).filter(item => item.tagName === 'TH').every(item => item.attributes.get('scope') === 'col'));
});

test('discovery preview explains omitted addresses and preserves aggregate coverage and unfinished rows', () => {
  const document = fakeDocument();
  const payload = report({ scope: { mode: 'discovered', tcp_ports: [80], udp_ports: [53] } });
  Object.assign(payload.coverage, { candidate_count: 254, discovered_count: 2, service_attempted_count: 2, service_skipped_count: 126,
    unlisted_target_count: 252, unlisted_not_observed_count: 252, unlisted_skipped_count: 126, unlisted_not_scheduled_count: 126 });
  const preview = renderShareReport(document, payload);
  for (const text of ['254', 'observed during discovery: 2', 'device checks attempted: 2', 'failed: 1', 'skipped: 126', '252 other candidate addresses are not listed', '252 not observed during discovery', '126 skipped', '126 not scheduled', 'counts can overlap', 'host_scan_timeout', 'including unfinished checks']) assert.ok(preview.textContent.includes(text), text);
  const targetTable = find(preview, item => item.tagName === 'TABLE');
  assert.equal(targetTable.children[1].children.length, 2);
  const csv = reportCsv(payload);
  for (const text of ['"candidate_count","254"', '"service_skipped_count","126"', '"unlisted_target_count","252"', '"unlisted_not_observed_count","252"', 'host_scan_timeout']) assert.ok(csv.includes(text), text);
});

function binding(request) {
  const document = fakeDocument();
  const button = document.createElement('button'); button.textContent = 'Print or export'; document.body.append(button);
  let prints = 0, revoked = null, blob = null;
  const window = { print() { prints += 1; }, Blob,
    URL: { createObjectURL(value) { blob = value; return 'blob:synthetic'; }, revokeObjectURL(value) { revoked = value; } },
    setTimeout(callback) { callback(); } };
  const data = { source: 'live', phase: 'finished', state: 'partial' };
  const controller = bindReportExport({ button, scanId: 'synthetic-id', request, getData: () => data, document, window });
  return { document, button, controller, data, prints: () => prints, download: () => ({ blob, revoked }) };
}

test('preview opens explicitly, starts private, prints only after ready and closes with focus restored', async () => {
  const calls = [];
  const ui = binding(async path => { calls.push(path); return report(); });
  assert.equal(calls.length, 0);
  ui.button.click();
  assert.equal(action(ui.document, 'Print or save PDF').disabled, true);
  await settle();
  assert.equal(calls.length, 1);
  assert.ok(calls[0].endsWith('include_identifiers=false&include_notes=false'));
  const dialog = find(ui.document.body, item => item.tagName === 'DIALOG');
  assert.equal(dialog.open, true);
  assert.ok(all(dialog).filter(item => item.type === 'checkbox').every(item => item.checked === false));
  action(ui.document, 'Print or save PDF').click();
  assert.equal(ui.prints(), 1);
  action(ui.document, 'Download CSV').click();
  assert.ok((await ui.download().blob.text()).includes('Original meaning.'));
  assert.equal(ui.download().revoked, 'blob:synthetic');
  action(ui.document, 'Close preview').click();
  assert.equal(dialog.open, false);
  assert.equal(ui.document.focused, ui.button);
  ui.button.click(); await settle();
  assert.ok(calls[1].endsWith('include_identifiers=false&include_notes=false'));
  ui.controller.destroy();
  assert.equal(find(ui.document.body, item => item.tagName === 'DIALOG'), undefined);
});

test('privacy changes clear the old preview and stale responses never restore removed identifiers', async () => {
  const pending = [];
  const ui = binding(path => new Promise(resolve => pending.push({ path, resolve })));
  ui.button.click();
  pending[0].resolve(report()); await settle();
  const dialog = find(ui.document.body, item => item.tagName === 'DIALOG');
  const identifiers = find(dialog, item => item.type === 'checkbox');
  identifiers.checked = true; identifiers.fire('change');
  assert.equal(action(ui.document, 'Print or save PDF').disabled, true);
  assert.equal(find(dialog, item => item.className === 'report-export-content').textContent, '');
  identifiers.checked = false; identifiers.fire('change');
  pending[2].resolve(report()); await settle();
  pending[1].resolve(report({ title: 'PRIVATE OLD RESPONSE', privacy: { include_identifiers: true } })); await settle();
  assert.equal(dialog.textContent.includes('PRIVATE OLD RESPONSE'), false);
  assert.ok(pending[1].path.includes('include_identifiers=true'));
  assert.ok(pending[2].path.includes('include_identifiers=false'));
  action(ui.document, 'Print or save PDF').click();
  assert.equal(ui.prints(), 1);
});

test('failed preview disables export and sharing is unavailable while a live report is unfinished', async () => {
  const ui = binding(async () => { throw Error('Synthetic storage failure'); });
  ui.controller.update({ source: 'live', phase: 'analysis', state: 'running' });
  assert.equal(ui.button.disabled, true);
  ui.controller.update({ source: 'demo', phase: 'finished', state: 'completed' });
  assert.equal(ui.button.disabled, true);
  ui.controller.update(ui.data); ui.button.click(); await settle();
  assert.ok(ui.document.body.textContent.includes('Synthetic storage failure'));
  assert.equal(action(ui.document, 'Print or save PDF').disabled, true);
  assert.equal(action(ui.document, 'Download CSV').disabled, true);
  const content = find(ui.document.body, item => item.className === 'report-export-content');
  assert.equal(content.attributes.get('aria-busy'), 'false');
  const dialog = find(ui.document.body, item => item.tagName === 'DIALOG');
  let prevented = false; dialog.fire('cancel', { preventDefault() { prevented = true; } });
  assert.equal(prevented, true); assert.equal(dialog.open, false); assert.equal(ui.document.focused, ui.button);
});
