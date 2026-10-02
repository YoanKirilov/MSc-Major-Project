import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import * as presentation from '../app/static/js/presentation.mjs';
import { prioritise, serviceLabel, coverageSummary, deviceCheckLabel, completedCheckSummary, emptyFindingMessage, usableAiRecord, checkSummary, aiExplanationNote, analysisProgressText, scanSetupLink, readScanSetup } from '../app/static/js/report.mjs';

test('equal priorities use rule, numeric address and service instead of completion order or scan IDs', () => {
  const devices = [{ device_id: 'a', ip: '192.168.0.2' }, { device_id: 'b', ip: '192.168.0.10' }];
  const findings = [{ severity: 'low', rule_id: 'HTTP', device_id: 'b' }, { severity: 'low', rule_id: 'HTTP', device_id: 'a' }];
  assert.deepEqual(prioritise(findings, devices).map(f => f.device_id), ['a', 'b']);
  assert.deepEqual(prioritise([...findings].reverse(), devices), prioritise(findings, devices));
  assert.equal(findings[0].device_id, 'b');
});

test('multiword search includes nicknames, friendly service labels and devices without findings', () => {
  const values = presentation.deviceSearchValues({ user_nickname: 'Kitchen TV', ip: '192.168.0.2', vendor: 'Example' }, [{ name: 'microsoft-ds', port: 445 }]);
  assert.equal(presentation.matchesSearch('TV kitchen', values), true);
  assert.equal(presentation.matchesSearch('file sharing', values), true);
  assert.equal(presentation.matchesSearch('missing kitchen', values), false);
  assert.equal(presentation.matchesSearch('', values), true);
});

test('coverage labels distinguish discovery, selection, incomplete and empty results', () => {
  const data = { state: 'completed', target: { mode: 'discover' }, coverage: { discovered_count: 12, service_completed_count: 12 } };
  assert.equal(deviceCheckLabel(data), '12 of 12 discovered');
  assert.match(completedCheckSummary(data), /All selected device checks finished/);
  assert.doesNotMatch(completedCheckSummary(data), /0 devices/);
  assert.equal(deviceCheckLabel({ ...data, target: { mode: 'known_hosts' }, coverage: { candidate_count: 2, service_completed_count: 1 } }), '1 of 2 selected');
  assert.doesNotMatch(completedCheckSummary({ ...data, state: 'partial', coverage: { discovered_count: 12, service_completed_count: 11 } }), /All selected/);
  assert.doesNotMatch(completedCheckSummary({ ...data, coverage: { discovered_count: 0, service_completed_count: 0 } }), /All selected/);
  assert.match(completedCheckSummary({ ...data, state: 'running' }), /In progress/);
});

test('beginner feature labels and concise actions preserve uncertainty and safety instructions', () => {
  assert.equal(presentation.featureLabel({ name: 'http', port: 80 }), 'Device web page');
  assert.match(presentation.featureLabel({ name: 'https-alt', detection_method: 'table', port: 8443 }), /unconfirmed/);
  assert.doesNotMatch(presentation.featureLabel({ name: 'http-proxy', detection_method: 'table', port: 8080 }), /TCP|8080/);
  assert.match(presentation.confidenceLabel('medium'), /Some supporting evidence/);
  const step = 'Check whether the address starts with https://, which indicates a protected web connection.';
  const check = 'Look for https:// at the start of the address. Ask the device maker if you are unsure.';
  assert.equal((presentation.actionGuidance(step, check).match(/https:\/\//g) || []).length, 1);
  assert.match(presentation.actionGuidance(step, check), /Ask the device maker/);
  assert.match(presentation.actionGuidance('Read the manual.', 'Do not enter passwords over HTTP.'), /Do not enter passwords/);
});

test('high priority appears in top three even when recorded last; input is unchanged', () => {
  const findings = ['low', 'informational', 'low', 'high'].map((severity) => ({ severity }));
  assert.equal(prioritise(findings).slice(0, 3)[0].severity, 'high');
  assert.equal(findings[0].severity, 'low');
});

test('HTTPS tunnel and inferred service names are labelled honestly', () => {
  assert.match(serviceLabel({ name: 'http', tunnel: 'ssl', port: 443 }), /HTTPS/);
  assert.match(serviceLabel({ name: 'domain', port: 53 }), /name lookup/);
  assert.match(serviceLabel({ name: 'http', port: 80, detection_method: 'table' }), /inferred/);
  assert.match(serviceLabel({ name: 'tcpwrapped', port: 1234 }), /closed before.*identified/);
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
  assert.match(aiExplanationNote({ ...data, phase: 'finished', analysis_status: 'ready', explanations: [record] }), /Older AI wording is hidden/);
  assert.match(aiExplanationNote({ ...data, phase: 'finished', analysis_status: 'ready', report_explanation: record }), /Older AI wording is hidden/);
  assert.doesNotMatch(aiExplanationNote({ ...data, analysis_status: 'ready', explanations: [] }), /reviewed the report overview/);
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

test('partial wording and saved HTTP checks use honest beginner language', () => {
  const partial = { analysis_status: 'ready', explanations: [{ rejected_fields: { 'limitations[0]': 'condition_removed' } }] };
  assert.match(aiExplanationNote(partial), /Some explanations are simplified/);
  assert.equal(presentation.wordingLabels({ recommended_steps: 'bad', 'limitations[0]': 'bad' }), 'suggested actions, what we could not confirm');
  const device = { details: [{ kind: 'web', source: 'Bounded HTTP check', label: 'Web connection (port 80)', status: 'observed', value: 'Redirected to HTTPS on this device; the TLS certificate passed verification for this address.' }] };
  assert.match(presentation.savedCheckNote(device, { port: 80 }), /only the starting page/);
  assert.equal(presentation.savedCheckNote(device, { port: 8080 }), '');
  device.details[0].source = 'Untrusted advertisement';
  assert.equal(presentation.savedCheckNote(device, { port: 80 }), '');
  assert.match(presentation.deviceLabel({ user_nickname: '<script>Room TV</script>' }), /your nickname/);
});

test('web-page help is bounded to observed web features and warns before sign-in', () => {
  const device = { ip: '192.168.56.10' };
  const service = { name: 'http', protocol: 'tcp', port: 8080, state: 'open', detection_method: 'probed' };
  assert.match(presentation.webPageInstructions(device, service), /http:\/\/192.168.56.10:8080\//);
  assert.match(presentation.webPageInstructions(device, service), /Do not enter passwords/);
  assert.match(presentation.webPageInstructions(device, { ...service, tunnel: 'ssl' }), /https:\/\//);
  assert.equal(presentation.webPageInstructions(device, { ...service, detection_method: 'table' }), '');
  assert.equal(presentation.webPageInstructions({ ip: 'device.invalid' }, service), '');
  assert.equal(presentation.webPageInstructions(device, { ...service, state: 'filtered' }), '');
});

test('rescan links only prefill bounded setup data and never include authorisation', () => {
  const data = { policy: { profile: 'deep-tcp-v1' }, target: { mode: 'known_hosts', hosts: ['192.168.0.53'] } };
  assert.deepEqual(readScanSetup(scanSetupLink(data).slice(1)), { profile: 'deep-tcp-v1', hosts: ['192.168.0.53'] });
  assert.deepEqual(readScanSetup(scanSetupLink(data, false).slice(1)), { profile: 'deep-tcp-v1', hosts: [] });
  assert.doesNotMatch(scanSetupLink(data), /authorised/);
  assert.equal(readScanSetup('#setup=1&profile=unknown'), null);
  assert.equal(readScanSetup('#setup=1&hosts=javascript:alert(1)'), null);
  assert.equal(readScanSetup('#setup=1&hosts=999.1.1.1'), null);
  assert.equal(readScanSetup('#setup=1&profile=deep-tcp-v1&hosts=192.168.0.53,192.168.0.54'), null);
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
    showModal() { this.open = true; }
    close() { this.open = false; }
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
    ...presentation, prioritise, serviceLabel, coverageSummary, deviceCheckLabel, completedCheckSummary, emptyFindingMessage, usableAiRecord, checkSummary, aiExplanationNote, analysisProgressText, scanSetupLink, readScanSetup });
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
  context.data.devices[0].hostname = 'Room TV';
  context.data.devices[0].hostname_source = 'saved_report';
  context.data.devices[0].name_candidates = [{ name: 'Room TV', source: 'saved_report', observed_at: '2026-09-25T21:00:00Z' }];
  vm.runInContext('render(data)', context);
  assert.match(text(elements.get('#device-table-body')), /Room TV \(previously reported\)/);
  assert.match(text(elements.get('#device-table-body')), /not confirmed this time/);
  assert.match(text(elements.get('#findingsList')), /Room TV \(previously reported\)/);
  context.data.coverage.targets = [
    { ip: '192.168.0.10', service_status: 'completed' },
    { ip: '192.168.0.53', service_status: 'failed' },
  ];
  vm.runInContext('render(data)', context);
  assert.equal(elements.get('#device-summaries').children.length, 2);
  assert.match(text(elements.get('#device-summaries')), /Room TV \(previously reported\)/);
  assert.match(text(elements.get('#device-summaries')), /192.168.0.53/);
  assert.match(text(elements.get('#device-summaries')), /Missing results do not mean it is safe/);
  assert.match(text(elements.get('#device-summaries')), /does not show that anyone was using/);
  assert.match(elements.get('#priority-breakdown').textContent, /1 high priority/);
  assert.equal(elements.has('#result-ring'), false);
  context.data.analysis_status = 'ready';
  context.data.explanations = [{ finding_id: 'high', status: 'ready', source: 'ai', prompt_version: '3.0.0',
    rejected_fields: { recommended_steps: 'list_length_changed' }, content: { meaning: 'Observed service.', why_it_matters: 'Review settings.' } }];
  vm.runInContext('render(data)', context);
  assert.equal(elements.get('#simplifyButton').hidden, false);
  assert.equal(elements.get('#simplifyButton').textContent, 'Retry remaining wording');
  assert.match(text(elements.get('#detailPanel')), /suggested actions/);
  context.data.plain_guidance = { high: { title: 'Plain finding title', limitations: ['Plain limitation.'], content: {
    meaning: 'Plain explanation.', why_it_matters: 'Plain reason.',
    recommended_steps: ['Plain action.'], how_to_check: ['Plain verification.'],
  } } };
  vm.runInContext('render(data)', context);
  assert.match(text(elements.get('#nextStepsList').children[0]), /Plain action/);
  assert.match(text(elements.get('#detailPanel')), /Plain explanation/);
  assert.match(text(elements.get('#detailPanel')), /Original rule-based explanation/);
  context.data.explanations = [];
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
  assert.match(text(elements.get('#report-checks')), /1 device check finished/);
  assert.doesNotMatch(text(elements.get('#report-checks')), /Reviewed report-level verification/);
  assert.match(text(elements.get('#nextStepsList')), /Reviewed report-level next step/);
  context.data.plain_overview = { content: {
    meaning: 'Plain overview.', why_it_matters: 'Plain caution.',
    recommended_steps: ['Plain report-level next step.'], how_to_check: ['Plain report check.'],
  }, limitations: ['Plain limits.'] };
  vm.runInContext('render(data)', context);
  assert.match(text(elements.get('#nextStepsList')), /Plain report-level next step/);
  assert.match(text(elements.get('#result-lead')), /Plain overview/);
  delete context.data.plain_overview;
  context.data.report_explanation.prompt_version = 'old';
  vm.runInContext('render(data)', context);
  assert.doesNotMatch(text(elements.get('#report-first-step')), /Reviewed report-level/);
  elements.get('#runAgainButton').events.click();
  assert.match(context.window.location.href, /^\/#setup=1&profile=light/);
  context.data.policy.profile = 'deep-tcp-v1';
  context.data.target = { mode: 'known_hosts', hosts: ['192.168.0.53'] };
  context.window.location.href = '/scans/test';
  elements.get('#runAgainButton').events.click();
  assert.equal(elements.get('#runAgainDialog').open, true);
  assert.equal(context.window.location.href, '/scans/test');
  elements.get('#cancelRunAgainButton').events.click();
  assert.equal(elements.get('#runAgainDialog').open, false);
  elements.get('#runAgainButton').events.click();
  elements.get('#sameDeviceButton').events.click();
  assert.match(context.window.location.href, /hosts=192.168.0.53/);
  elements.get('#anotherDeviceButton').events.click();
  assert.doesNotMatch(context.window.location.href, /hosts=/);
});
