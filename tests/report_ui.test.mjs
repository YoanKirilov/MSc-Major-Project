import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { prioritise, serviceLabel, coverageSummary, emptyFindingMessage, usableAiRecord, checkSummary, aiExplanationNote } from '../app/static/js/report.mjs';

test('high priority appears in top three even when recorded last; input is unchanged', () => {
  const findings = ['low', 'informational', 'low', 'high'].map((severity) => ({ severity }));
  assert.equal(prioritise(findings).slice(0, 3)[0].severity, 'high');
  assert.equal(findings[0].severity, 'low');
});

test('HTTPS tunnel and inferred service names are labelled honestly', () => {
  assert.match(serviceLabel({ name: 'http', tunnel: 'ssl', port: 443 }), /HTTPS/);
  assert.match(serviceLabel({ name: 'domain', port: 53 }), /name lookup/);
  assert.match(serviceLabel({ name: 'http', port: 80, detection_method: 'table' }), /inferred/);
});

test('incomplete and empty scans do not imply a successful clean assessment', () => {
  const data = { state: 'partial', target: { mode: 'discover' }, coverage: { discovered_count: 9, candidate_count: 254, service_completed_count: 8 } };
  assert.match(coverageSummary(data), /1 did not finish/);
  assert.doesNotMatch(coverageSummary(data), /254/);
  assert.match(emptyFindingMessage(data), /Scan incomplete/);
  assert.match(emptyFindingMessage({ state: 'failed' }), /Scan incomplete/);
  assert.match(emptyFindingMessage({ state: 'completed', coverage: { service_completed_count: 0 } }), /No devices were assessed/);
  assert.match(emptyFindingMessage({ state: 'running' }), /still running/);
});

test('old AI records cannot be displayed as currently validated guidance', () => {
  const data = { guidance_status: { ai_prompt_version: '3.0.0' } };
  const record = { status: 'ready', source: 'ai', content: {}, prompt_version: '2.0.0' };
  assert.equal(usableAiRecord(record, data), false);
  assert.equal(usableAiRecord({ ...record, prompt_version: '3.0.0' }, data), true);
});

test('service check summaries distinguish errors from observations', () => {
  assert.equal(checkSummary({ script_id: 'ssl-cert', output: 'Subject: test' }), 'Recorded certificate details.');
  assert.match(checkSummary({ script_id: 'ssl-cert', output: 'ERROR: failed' }), /Could not reliably check/);
});

test('unavailable AI and a rejected rewrite have different explanations', () => {
  assert.match(aiExplanationNote({ explanations: [{ fallback_reason: 'provider_timeout' }] }), /timed out/);
  assert.match(aiExplanationNote({ explanations: [{ fallback_reason: 'provider_unavailable' }] }), /unavailable/);
  assert.match(aiExplanationNote({ explanations: [{ fallback_reason: 'not_simpler' }] }), /No reviewed alternative/);
});

test('report renderer exposes failures, sorts recommendations and hides older AI wording', () => {
  // Exercise the actual page code with a minimal DOM; no browser dependency.
  class Element {
    constructor() {
      this.children = []; this.textContent = ''; this.dataset = {}; this.events = {};
      this.style = { setProperty() {} }; this.classList = { toggle() {} };
    }
    addEventListener(name, fn) { this.events[name] = fn; }
    setAttribute() {}
    append(...items) { this.children.push(...items); }
    replaceChildren(...items) { this.children = items; this.textContent = ''; }
    get childElementCount() { return this.children.length; }
  }
  const template = readFileSync(new URL('../app/templates/scan.html', import.meta.url), 'utf8');
  const elements = new Map();
  const document = {
    querySelector(id) {
      assert.ok(template.includes(`id="${id.slice(1)}"`), `missing template hook ${id}`);
      if (!elements.has(id)) elements.set(id, new Element());
      return elements.get(id);
    },
    querySelectorAll() { return []; },
    createElement() { return new Element(); },
  };
  const context = vm.createContext({ document, window: { location: { pathname: '/scans/test' } }, URL,
    prioritise, serviceLabel, coverageSummary, emptyFindingMessage, usableAiRecord, checkSummary, aiExplanationNote });
  const source = readFileSync(new URL('../app/static/js/scan.js', import.meta.url), 'utf8')
    .replace(/^import[^\n]*\n/gm, '').replace(/\npoll\(\);\s*$/, '');
  vm.runInContext(source, context);
  const finding = (severity) => ({ finding_id: severity, device_id: 'device', service_id: 'service', severity,
    title: `${severity} finding`, confidence: 'medium', limitations: [], evidence: [], references: [],
    fixed_explanation: { meaning: 'Observed service.', why_it_matters: 'Review its settings.' },
    actions: [{ action_id: 'review', text: 'Check settings.', verification: 'Consult the manual.' }] });
  context.data = {
    state: 'partial', phase: 'finished', revision: 1, ai_requests_used: 0,
    target: { mode: 'discover', cidr: '192.168.0.0/24' }, policy: {},
    coverage: { discovered_count: 2, service_completed_count: 1 },
    devices: [{ device_id: 'device', ip: '192.168.0.10', reachability: 'observed' }],
    services: [{ service_id: 'service', device_id: 'device', name: 'http', tunnel: 'ssl', port: 443, state: 'open', script_results: [{ script_id: 'ssl-cert', output: 'Certificate details' }] }],
    findings: ['low', 'informational', 'medium', 'high'].map(finding),
    explanations: [{ finding_id: 'high', status: 'ready', source: 'ai', prompt_version: '2.0.0', content: { meaning: 'OLD AI CLAIM' } }],
    guidance_status: { ai_prompt_version: '3.0.0', refresh_available: true },
    errors: [{ message: 'One device check timed out.' }], warnings: [],
  };
  vm.runInContext('render(data)', context);
  const text = (element) => [element.textContent, ...element.children.map(text)].join(' ');
  assert.match(text(elements.get('#scan-problems')), /One device check timed out/);
  assert.equal(elements.get('#scan-problems').hidden, false);
  assert.match(text(elements.get('#nextStepsList').children[0]), /high finding/);
  assert.doesNotMatch(text(elements.get('#findingsList')), /OLD AI CLAIM/);
  assert.match(text(elements.get('#device-table-body')), /HTTPS/);
  assert.match(text(elements.get('#device-table-body')), /Recorded certificate details/);
  assert.equal(elements.get('#refreshGuidanceButton').hidden, false);
  context.data.findings = []; context.data.state = 'failed';
  vm.runInContext('render(data)', context);
  assert.match(text(elements.get('#findingsList')), /Scan incomplete/);
  assert.match(text(elements.get('#report-first-step')), /retry the unfinished/);
  context.data.state = 'completed';
  context.data.analysis_status = 'ready';
  context.data.report_explanation = { prompt_version: '3.0.0', content: {
    meaning: 'Recorded observations.', why_it_matters: 'Review the selected checks.',
    recommended_steps: ['Reviewed report-level next step.'], how_to_check: ['Reviewed report-level verification.'],
  }, display_limitations: ['Other settings were not checked.'] };
  vm.runInContext('render(data)', context);
  assert.match(text(elements.get('#report-first-step')), /Reviewed report-level next step/);
  assert.match(text(elements.get('#report-checks')), /Reviewed report-level verification/);
  assert.match(text(elements.get('#nextStepsList')), /Reviewed report-level next step/);
  context.data.report_explanation.prompt_version = 'old';
  vm.runInContext('render(data)', context);
  assert.doesNotMatch(text(elements.get('#report-first-step')), /Reviewed report-level/);
});
