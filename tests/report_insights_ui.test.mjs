import test from 'node:test';
import assert from 'node:assert/strict';
import { serviceGroups, comparisonEntries, renderReportInsights } from '../app/static/js/report-insights.mjs';

const device = { device_id: 'd', ip: '192.168.56.2' };
const data = { devices: [device], findings: [], services: [], coverage: { targets: [{ip: device.ip, service_status: 'completed'}] } };
test('features group answering services only, retaining inferred names and individual ports', () => {
  const values = serviceGroups({...data, services: [
    {device_id:'d',name:'http',port:80,state:'open',detection_method:'probed'},
    {device_id:'d',name:'http',port:8080,state:'open',detection_method:'table'},
    {device_id:'d',name:'http',port:443,state:'closed'},
    {device_id:'other',name:'ssh',port:22,state:'open'},
  ]});
  assert.equal(values.length, 2);
  assert.match(values[1][0], /type unconfirmed/);
  assert.deepEqual(values.map(([,entries])=>entries[0].service.port), [80,8080]);
});
test('older textual comparisons remain available but never become a zero-change verdict', () => {
  const values = comparisonEntries({...data, devices:[{...device, details:[{kind:'history',label:'Service comparison',value:'Newly observed open: TCP 80.'}]}]});
  assert.equal(values[0].status, 'not_compared');
  assert.match(values[0].reason, /text-only.*TCP 80/);
  assert.equal(values[0].added_count, undefined);
});
test('structured dates and exact totals survive the presentation projection', () => {
  const value = {status:'available',source_created_at:'2026-10-13T10:00:00Z',current_created_at:'2026-10-14T10:00:00Z',added:[],added_count:300,not_observed:[],not_observed_count:2};
  assert.deepEqual(comparisonEntries({...data,devices:[{...device,comparison:value}]}),[{device:{...device,comparison:value},...value}]);
});

function insightDocument() {
  const element = () => ({ children: [], ownText: '',
    append(...items) { this.children.push(...items); },
    replaceChildren(...items) { this.children = items; },
    addEventListener() {},
    get childElementCount() { return this.children.length; },
    set textContent(value) { this.ownText = String(value); this.children = []; },
    get textContent() { return [this.ownText, ...this.children.map(item => item.textContent)].filter(Boolean).join(' '); },
  });
  const hooks = new Map();
  return { createElement: element, querySelector(selector) {
    if (!hooks.has(selector)) hooks.set(selector, element());
    return hooks.get(selector);
  } };
}

test('comparison display keeps exact differences and uncertainty instead of equating no open result with no reply', () => {
  const comparison = { status: 'available', added: [{ protocol: 'tcp', port: 80 }], added_count: 1,
    not_observed: [{ protocol: 'tcp', port: 445 }], not_observed_count: 1,
    source_created_at: '2026-10-13T10:00:00Z', current_created_at: '2026-10-14T10:00:00Z',
    reason: 'Original comparison limits remain accessible.' };
  const report = { ...data, devices: [{ ...device, comparison }, { device_id: 'unknown', ip: '192.168.56.3' }] };
  const before = JSON.stringify(report);
  const document = insightDocument();
  renderReportInsights({ document, data: report, onShowDevice() { throw Error('No interaction expected'); } });
  const summary = document.querySelector('#changes-overview').textContent;
  assert.match(summary, /compared 1 device.*1 feature accepted requests.*not recorded doing so earlier/);
  assert.match(summary, /1 previously available feature was not recorded accepting requests this time/);
  assert.match(summary, /1 device could not be compared/);
  assert.doesNotMatch(summary, /did not reply|first time|fixed|removed/);
  const details = document.querySelector('#changes-list').textContent;
  assert.match(details, /TCP 80.*TCP 445/);
  assert.match(details, /Original comparison limits remain accessible/);
  assert.match(details, /could not compare this device.*does not mean nothing changed/);
  assert.equal(JSON.stringify(report), before);
});

test('empty and unmatched comparison summaries do not become a no-change or safety verdict', () => {
  for (const devices of [[], [device]]) {
    const document = insightDocument();
    renderReportInsights({ document, data: { ...data, devices }, onShowDevice() {} });
    assert.match(document.querySelector('#changes-overview').textContent, /comparison.*not available.*does not mean nothing changed/);
    assert.match(document.querySelector('#feature-inventory-list').textContent, /No features were recorded accepting requests.*Not every possible feature was checked.*does not prove.*safe/);
  }
});
