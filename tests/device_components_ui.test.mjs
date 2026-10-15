import assert from 'node:assert/strict';
import test from 'node:test';
import { renderDeviceSummaries, deviceResultEntries, deviceStatus, nameQualification } from '../app/static/js/devices.mjs';
import { createCvePanel } from '../app/static/js/cves.mjs';

// A small DOM verifies component ownership and data invariants offline. Real
// focus, target geometry and native disclosure behaviour require browser tests.
class Element {
  constructor(tag) {
    this.tagName = tag.toUpperCase(); this.children = []; this.dataset = {};
    this.events = {}; this.attributes = {}; this.className = ''; this.open = false;
    this._text = ''; this.hidden = false;
  }
  get textContent() { return this._text + this.children.map(child => child.textContent).join(' '); }
  set textContent(value) { this._text = String(value); this.children = []; }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  append(...nodes) { nodes.forEach(node => { node.parentElement = this; this.children.push(node); }); }
  replaceChildren(...nodes) {
    if (descendants(this).includes(document.activeElement)) document.activeElement = document.body;
    this.children.forEach(child => { child.parentElement = null; });
    this.children = []; this._text = ''; this.append(...nodes);
  }
  addEventListener(name, callback) { this.events[name] = callback; }
  querySelector(tag) { return descendants(this).find(node => node.tagName === tag.toUpperCase()) || null; }
  focus() { document.activeElement = this; }
}
const descendants = node => node.children.flatMap(child => [child, ...descendants(child)]);
const byClass = (node, name) => descendants(node).filter(child => child.className.split(/\s+/).includes(name));
const document = { createElement: tag => new Element(tag), body: new Element('body') };
const baseDevice = { device_id: 'device-1', ip: '192.168.1.10', hostname: 'Room screen',
  hostname_source: 'reverse_dns', hostname_confidence: 'low', reachability: 'observed',
  reachability_evidence: ['open_port_response'], profile: { category: 'unknown' } };
const fixture = overrides => ({ phase: 'finished', target: { mode: 'discover' },
  devices: [{ ...baseDevice }], services: [], findings: [], observations: [],
  coverage: { targets: [{ ip: baseDevice.ip, discovery_status: 'observed', service_status: 'completed' }] },
  ...overrides });
const render = (data, options = {}) => {
  const container = new Element('div');
  return { container, result: renderDeviceSummaries({ document, container, data, ...options }) };
};

test('host-level configuration replies are available once per device without implying safety', () => {
  const data = fixture({policy:{selected_scripts:['smb-protocols','smb2-security-mode']},
    devices:[{...baseDevice,host_script_results:[{script_id:'smb2-security-mode',output:'3.1.1: Message signing enabled and required',truncated:false}]}]});
  const before = JSON.stringify(data);
  const {container} = render(data);
  assert.match(container.textContent, /Recorded device checks/);
  assert.match(container.textContent, /negotiated version, not every possible connection/);
  assert.match(container.textContent, /File-sharing versions.*no usable reply.*no pass is assumed/);
  assert.equal((container.textContent.match(/Supporting feature details/g)||[]).length, 1);
  assert.equal(JSON.stringify(data), before);
});

test('shortened host output stays technical evidence rather than a complete configuration verdict', () => {
  const {container} = render(fixture({devices:[{...baseDevice,host_script_results:[{script_id:'smb-protocols',output:'dialects: SMBv1',truncated:true}]}]}));
  assert.match(container.textContent, /complete result was not established/);
  assert.match(container.textContent, /No review items were recorded.*not proof of safety/);
});

test('device identity, status and counts stay visible in a compact shared anatomy', () => {
  const data = fixture({ devices: [{ ...baseDevice }, { device_id: 'device-2', ip: '192.168.1.11' }] });
  const before = JSON.stringify(data);
  const { container } = render(data, { nicknameAvailable: true, onEditNickname() {}, onRefreshName() {} });
  assert.equal(container.children.length, 2);
  for (const group of container.children) {
    assert.equal(group.tagName, 'ARTICLE');
    assert.equal(group.className, 'device-summary-group');
    assert.deepEqual(group.children.map(node => node.className), ['device-summary', 'device-name-tools']);
    const [card, footer] = group.children;
    assert.equal(card.open, false);
    const summary = card.children[0];
    assert.equal(summary.tagName, 'SUMMARY');
    assert.match(summary.textContent, new RegExp(group.dataset.deviceIp.replaceAll('.', '\\.')));
    assert.match(summary.textContent, /observed features.*review items/);
    assert.equal(footer.parentElement, group);
    const buttons = descendants(footer).filter(node => node.tagName === 'BUTTON');
    assert.equal(buttons.length, 2);
    assert.equal(footer.children[0].className, 'device-action-buttons');
    assert.deepEqual(footer.children[0].children, buttons);
    assert.ok(buttons.every(button => button.className === 'secondary-button'));
    assert.ok(buttons.every(button => button.attributes['aria-describedby'] === summary.id));
  }
  assert.match(container.children[1].children[0].children[0].textContent, /Name not identified.*does not mean an intruder/);
  assert.equal(JSON.stringify(data), before);
});

test('all thirteen open features have plain labels within their own device', () => {
  const services = Array.from({ length: 13 }, (_, index) => ({ service_id: `service-${index}`,
    device_id: baseDevice.device_id, state: 'open', name: index === 12 ? 'invented-application' : 'http',
    port: 8000 + index, detection_method: index === 12 ? 'table' : 'probed', protocol: 'tcp' }));
  services.push({ device_id: baseDevice.device_id, state: 'closed', name: 'ssh', port: 22 });
  const { container } = render(fixture({ services }));
  const features = byClass(container, 'device-feature');
  assert.equal(features.length, 13);
  assert.match(features[12].textContent, /Unidentified feature.*type unconfirmed/);
  assert.match(container.textContent, /application was not identified/);
  assert.match(features[12].textContent, /TCP port 8012/);
  assert.doesNotMatch(container.textContent, /connection number|contact number/);
  assert.match(container.textContent, /A port is a numbered connection point for a feature/);
  assert.doesNotMatch(container.textContent, /more features are listed in the device table/);
  assert.match(container.textContent, /does not show that anyone used.*vulnerability/);
});

test('one grouped feature disclosure sits beside About this device, with all evidence retained', () => {
  const services = [80, 8080].map(port => ({ service_id: `s-${port}`, device_id: baseDevice.device_id,
    name: 'http', state: 'open', protocol: 'tcp', port, product: 'Test server', version: '1.2',
    script_results: [{ script_id: 'http-title', output: `<page-${port}>`, truncated: true }] }));
  const data = fixture({ services });
  const before = JSON.stringify(data);
  const { container } = render(data);
  const summaries = descendants(container).filter(node => node.tagName === 'SUMMARY' && node.textContent === 'Supporting feature details');
  assert.equal(summaries.length, 1);
  const evidence = summaries[0].parentElement;
  assert.equal(evidence.parentElement.className, 'device-info-disclosures');
  assert.equal(evidence.parentElement.children[0].children[0].textContent, 'About this device');
  assert.equal(byClass(evidence, 'feature-evidence').length, 2);
  for (const port of [80, 8080]) assert.match(evidence.textContent, new RegExp(`TCP port ${port}.*Test server 1.2.*<page-${port}>`));
  assert.match(evidence.textContent, /output was shortened/);
  assert.ok(byClass(container, 'device-feature').every(node => !descendants(node).some(child => child.tagName === 'DETAILS')));
  assert.equal(JSON.stringify(data), before);
});

test('unchecked previews never look like successful empty checks; partial facts remain visible', () => {
  for (const service_status of ['failed', 'timed_out', 'cancelled', 'pending', 'running']) {
    const data = fixture({ devices: [], coverage: { targets: [{ ip: baseDevice.ip, discovery_status: 'observed', service_status }] } });
    const { container } = render(data);
    assert.match(byClass(container, 'device-summary-preview')[0].textContent, /not assessed/);
    assert.doesNotMatch(byClass(container, 'device-summary-preview')[0].textContent, /0.*features|0.*review/);
  }
  const { container } = render(fixture({ services: [{ device_id: baseDevice.device_id, state: 'open', port: 80, name: 'http' }],
    coverage: { targets: [{ ip: baseDevice.ip, service_status: 'failed' }] } }));
  assert.match(byClass(container, 'device-summary-preview')[0].textContent, /1 observed feature.*remaining checks not assessed/);
  assert.match(byClass(render(fixture()).container, 'device-summary-preview')[0].textContent, /0 observed features/);
});

test('unparsed unfinished targets remain distinct from successful devices and naming totals', () => {
  const data = fixture({ coverage: { targets: [
    { ip: baseDevice.ip, service_status: 'completed', discovery_status: 'observed' },
    { ip: '192.168.1.12', service_status: 'timed_out', reason_code: 'host_timeout', attempts: 2 },
    { ip: '192.168.1.13', service_status: 'pending', discovery_status: 'observed' },
    { ip: '192.168.1.14', service_status: 'skipped', discovery_status: 'not_seen' },
  ] } });
  const { container, result } = render(data, { onEditNickname() {}, onRefreshName() {} });
  assert.equal(result.entries.length, 3);
  assert.equal(container.children[1].children[1].querySelector('button'), null);
  assert.match(container.children[1].textContent, /ran out of time.*host timeout.*Attempts 2/);
  assert.match(result.namingText, /1 device with usable saved results/);
  assert.match(result.countText, /2 shown addresses without a usable device result/);
  assert.doesNotMatch(container.textContent, /192\.168\.1\.14/);
  assert.match(container.children[2].textContent, /Waiting for device checks/);
});

test('known-host unstarted targets do not disappear, but nonselected silent subnet addresses do', () => {
  const targets = [{ ip: '192.168.1.15', service_status: 'not_scheduled', discovery_status: 'not_run' }];
  assert.equal(deviceResultEntries(fixture({ devices: [], coverage: { targets } })).length, 0);
  assert.equal(deviceResultEntries(fixture({ devices: [], target: { mode: 'known_hosts' }, coverage: { targets } })).length, 1);
});

test('advertisement-only, historical and conflicting identity remains qualified', () => {
  assert.match(deviceStatus({ discovery_method: 'mdns_advertisement' }), /service response not confirmed/);
  assert.match(deviceStatus({ discovery_method: 'mdns_advertisement' }, { service_status: 'completed' }), /advertised device.*not confirmed/);
  assert.match(nameQualification({ ...baseDevice, hostname_source: 'saved_report', hostname_conflict: true }), /not confirmed this time.*sources disagree/);
  const device = { ...baseDevice, hostname_source: 'saved_report', hostname_conflict: true,
    vendor: 'Adapter manufacturer', profile: { category: 'camera', conflict: true },
    details: [{ kind: 'upnp', label: 'modelName', value: 'Model A', source: 'Device description',
      status: 'advertised', observed_at: '2026-10-08T10:00:00Z' }],
    name_candidates: [{ name: 'Other name', source: 'mdns', observed_at: '2026-10-08T10:00:00Z' }] };
  const { container } = render(fixture({ devices: [device] }));
  assert.match(container.textContent, /Reported model: Model A/);
  assert.match(container.textContent, /unverified claim/);
  assert.match(container.textContent, /Adapter manufacturer.*does not identify the device model/);
  assert.match(container.textContent, /Clues disagree; device type not identified/);
  assert.doesNotMatch(container.textContent, /Possible camera/);
  assert.match(container.textContent, /Other name.*Device announcement/);
});

test('matched announcements and comparisons appear with their device without inventing a check', () => {
  const data = fixture({ devices: [{ ...baseDevice, details: [{ kind: 'history', label: 'Service comparison',
    value: 'A saved service was not observed this time.', source: 'Earlier report', status: 'inferred', observed_at: '2026-10-07T12:00:00Z' }] }],
    observations: [{ source: 'mdns', ip: baseDevice.ip, advertised_name: 'Room announcement',
      service_type: '_airplay._tcp.local.', port: 7000, observed_at: '2026-10-08T10:00:00Z' },
    { source: 'mdns', ip: '192.168.1.99', advertised_name: 'Unmatched announcement' }] });
  const { container } = render(data);
  assert.match(container.textContent, /Room announcement advertised AirPlay media sharing/);
  assert.doesNotMatch(container.textContent, /Unmatched announcement/);
  assert.match(container.textContent, /not proof that the same physical device/);
  assert.match(container.textContent, /do not verify the device identity or an open feature/);
  assert.match(container.children[0].children[0].children[0].textContent, /0 observed features/);
});

test('sorting and show-more account for full matching population including failed targets', () => {
  const devices = Array.from({ length: 100 }, (_, index) => ({ device_id: `device-${index}`, ip: `192.168.1.${index + 1}` }));
  const data = fixture({ devices, coverage: { targets: [{ ip: '192.168.1.200', service_status: 'failed' }] } });
  const options = { matchesDevice: device => Number(device.ip.split('.').at(-1)) % 2 === 0,
    sortDevices: (a, b) => b.ip.localeCompare(a.ip, 'en', { numeric: true }) };
  const { container, result } = render(data, options);
  assert.equal(result.entries.length, 101);
  assert.equal(result.matching.length, 51);
  assert.equal(result.visibleCount, 24);
  assert.equal(container.children.length, 24);
  assert.equal(container.children[0].dataset.deviceIp, '192.168.1.200');
  assert.match(result.countText, /24 of 51 matching device results \(101 recorded in total\)/);
  assert.equal(render(data, { ...options, deviceLimit: Infinity }).result.visibleCount, 51);
});

test('disclosure state and callback context survive component reconstruction', () => {
  const expandedDevices = new Map([[baseDevice.ip, true]]);
  const calls = [];
  const finding = { finding_id: 'finding-1', device_id: baseDevice.device_id, title: 'Review file sharing', severity: 'low' };
  const { container } = render(fixture({ findings: [finding] }), { expandedDevices, nicknameAvailable: true,
    onEditNickname: (...args) => calls.push(['nickname', ...args]),
    onRefreshName: (...args) => calls.push(['lookup', ...args]),
    onViewFinding: (...args) => calls.push(['finding', ...args]) });
  const [card, tools] = container.children[0].children;
  assert.equal(card.open, true);
  const [actions, localStatus] = tools.children;
  const [edit, refresh] = actions.children;
  edit.events.click(); refresh.events.click();
  const review = byClass(container, 'device-review-links')[0].querySelector('button');
  review.events.click();
  assert.equal(calls[0][1].device_id, baseDevice.device_id);
  assert.equal(calls[0][2], edit);
  assert.equal(calls[1][2], refresh);
  assert.equal(calls[1][3], localStatus);
  assert.equal(calls[2][1], 'finding-1');
  assert.equal(calls[2][2], review);
  card.open = false; card.events.toggle();
  assert.equal(expandedDevices.get(baseDevice.ip), false);
});

test('nickname rerenders retain nested feature evidence and native summary focus', () => {
  const data = fixture({ services: [{ service_id: 'http', device_id: baseDevice.device_id,
    state: 'open', name: 'http', port: 80, detection_method: 'probed', protocol: 'tcp' }] });
  const container = new Element('div');
  const options = { document, container, data, expandedDevices: new Map([[baseDevice.ip, true]]) };
  renderDeviceSummaries(options);
  const about = descendants(container).find(node => node.dataset.disclosureKey === 'About this device');
  const feature = descendants(container).find(node => node.dataset.disclosureKey === 'features');
  about.open = true; feature.open = true; about.children[0].focus();
  const oldFocused = document.activeElement;
  data.devices[0].user_nickname = 'Family screen';
  renderDeviceSummaries(options);
  const restoredAbout = descendants(container).find(node => node.dataset.disclosureKey === 'About this device');
  assert.equal(restoredAbout.open, true);
  assert.equal(descendants(container).find(node => node.dataset.disclosureKey === 'features').open, true);
  assert.equal(document.activeElement, restoredAbout.children[0]);
  assert.notEqual(document.activeElement, oldFocused);
  assert.equal(document.activeElement.tagName, 'SUMMARY');
});

test('a user-collapsed device stays closed even before its toggle event updates shared state', () => {
  const data = fixture();
  const container = new Element('div');
  const expandedDevices = new Map([[baseDevice.ip, true]]);
  const options = { document, container, data, expandedDevices };
  renderDeviceSummaries(options);
  const card = container.children[0].children[0];
  card.open = false; // Native close; toggle delivery can still be queued.
  card.children[0].focus();
  assert.equal(expandedDevices.get(baseDevice.ip), true);
  renderDeviceSummaries(options);
  assert.equal(container.children[0].children[0].open, false);
  assert.equal(expandedDevices.get(baseDevice.ip), false);
  assert.equal(document.activeElement, container.children[0].children[0].children[0]);
});

test('an explicit parent identification action opens a closed device while preserving nested evidence', () => {
  const data = fixture();
  const container = new Element('div');
  const expandedDevices = new Map();
  const options = { document, container, data, expandedDevices };
  renderDeviceSummaries(options);
  assert.equal(container.children[0].children[0].open, false);
  descendants(container).find(node => node.dataset.disclosureKey === 'About this device').open = true;
  expandedDevices.set(baseDevice.ip, true); // Parent's explicit "Find this device" intent.
  renderDeviceSummaries(options);
  assert.equal(container.children[0].children[0].open, true);
  assert.equal(descendants(container).find(node => node.dataset.disclosureKey === 'About this device').open, true);
  expandedDevices.set(baseDevice.ip, false); // Explicit parent close is honoured too.
  renderDeviceSummaries(options);
  assert.equal(container.children[0].children[0].open, false);
});

test('filtered device details return in the same state and nickname action retains focus after its label changes', () => {
  const data = fixture();
  const container = new Element('div');
  const options = { document, container, data, expandedDevices: new Map([[baseDevice.ip, true]]),
    nicknameAvailable: true, onEditNickname() {} };
  renderDeviceSummaries(options);
  descendants(container).find(node => node.dataset.disclosureKey === 'About this device').open = true;
  renderDeviceSummaries({ ...options, matchesDevice: () => false });
  assert.equal(container.children.length, 1);
  renderDeviceSummaries(options);
  assert.equal(descendants(container).find(node => node.dataset.disclosureKey === 'About this device').open, true);
  container.querySelector('button').focus();
  data.devices[0].user_nickname = 'Family screen';
  renderDeviceSummaries(options);
  assert.equal(document.activeElement, container.querySelector('button'));
  assert.equal(document.activeElement.textContent, 'Edit or remove your nickname');
});

test('later naming notes update locally and preserve an open disclosure without changing scan names', () => {
  const data = fixture();
  const { container } = render(data, { onRefreshName() {} });
  const notesPanel = descendants(container).find(node => node.dataset.notePanel === 'name');
  const snapshot = { name_refreshes: [{ device_id: baseDevice.device_id, checked_at: '2026-10-08T12:00:00Z',
    names: [{ name: '<script>Reported name</script>', source: 'mdns', observed_at: '2026-10-08T12:00:00Z' }], notes: [] }] };
  notesPanel.updateNotes(snapshot);
  const disclosure = notesPanel.querySelector('details'); disclosure.open = true;
  notesPanel.updateNotes({ name_refreshes: [{ ...snapshot.name_refreshes[0], notes: ['Saved lookup note.'] }] });
  assert.equal(notesPanel.querySelector('details').open, true);
  assert.match(container.textContent, /saved device name has not changed/);
  assert.match(notesPanel.textContent, /<script>Reported name<\/script>/);
  assert.equal(notesPanel.querySelector('script'), null);
  assert.equal(data.devices[0].hostname, 'Room screen');
});

test('nickname-unavailable controls are disabled without dropping original device information', () => {
  const { container } = render(fixture(), { onEditNickname() {}, nicknameAvailable: false });
  assert.equal(container.querySelector('button').disabled, true);
  assert.match(container.textContent, /Room screen.*Selected checks finished/);
  const { container: empty } = render(fixture({ devices: [], coverage: {} }));
  assert.match(empty.textContent, /No device results were recorded.*does not prove/);
});

test('CVE research is collapsed and has concise eligible versus ineligible status without requests', () => {
  const originalFetch = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = () => { calls++; throw new Error('No request expected'); };
  try {
    const eligible = createCvePanel(document, 'scan', { service_id: 'service', cve_lookup_available: true }, null, () => true);
    assert.equal(eligible.dataset.notePanel, 'cve');
    assert.match(byClass(eligible, 'cve-status')[0].textContent, /research is available.*No online lookup has started/);
    const disclosure = byClass(eligible, 'cve-research')[0];
    assert.equal(disclosure.open, false);
    disclosure.open = true;
    assert.equal(calls, 0);
    assert.match(disclosure.textContent, /Opening this section does not start a lookup/);
    assert.match(disclosure.textContent, /not endorsed or certified/);
    const unavailable = createCvePanel(document, 'scan', { service_id: 'service' }, null, () => true);
    assert.equal(unavailable.querySelector('button'), null);
    assert.match(byClass(unavailable, 'cve-status')[0].textContent, /precise software fingerprint and version were not recorded/);
    assert.equal(calls, 0);
  } finally { globalThis.fetch = originalFetch; }
});

test('saved CVE outcomes remain distinct and never claim a port proves vulnerability or safety', () => {
  const records = [
    ['candidates', /saved possible CVE match.*not confirmed vulnerabilities/],
    ['no_matches', /not proof of safety/], ['identity_unresolved', /no match is confirmed/],
    ['insufficient_evidence', /not have enough software evidence/], ['unavailable', /evidence remains accessible/],
  ];
  for (const [status, expected] of records) {
    const saved = { service_id: 'service', status, checked_at: 'unknown', message: 'Saved lookup result.',
      results: status === 'candidates' ? [{ cve_id: 'CVE-2026-10001', description: '<script>Published text</script>' },
        { cve_id: 'javascript:alert(1)', description: 'Invalid link' }] : [], total: 2 };
    const panel = createCvePanel(document, 'scan', { service_id: 'service' }, saved, () => true);
    assert.match(byClass(panel, 'cve-status')[0].textContent, expected);
    assert.equal(byClass(panel, 'cve-research')[0].open, false);
    assert.match(panel.textContent, /Time unavailable/);
    assert.doesNotMatch(panel.textContent, /Invalid Date/);
    const links = descendants(panel).filter(node => node.tagName === 'A' && node.textContent.startsWith('CVE-'));
    if (status === 'candidates') {
      assert.equal(links.length, 1);
      assert.equal(links[0].href, 'https://nvd.nist.gov/vuln/detail/CVE-2026-10001');
      assert.equal(panel.querySelector('script'), null);
    }
  }
});

test('CVE snapshot projection keeps research open and does not erase unchanged rendered nodes', () => {
  const panel = createCvePanel(document, 'scan', { service_id: 'service', cve_lookup_available: true }, null, () => true);
  const disclosure = byClass(panel, 'cve-research')[0]; disclosure.open = true;
  const saved = { service_id: 'service', status: 'no_matches', message: 'No records found.', results: [] };
  panel.updateNotes({ cve_lookups: [saved] });
  const button = panel.querySelector('button');
  assert.equal(button.textContent, 'Check CVEs again');
  panel.updateNotes({ cve_lookups: [saved] });
  assert.equal(panel.querySelector('button'), button);
  assert.equal(disclosure.open, true);
  panel.updateNotes(null);
  assert.match(byClass(panel, 'cve-status')[0].textContent, /No online lookup has started/);
  assert.equal(button.textContent, 'Check CVEs for this software');
});

test('only an explicit CVE action posts a lookup; stale receipts retain newer saved research', async () => {
  const originalFetch = globalThis.fetch;
  const originalWindow = globalThis.window;
  const calls = [];
  let finish;
  globalThis.window = { location: { hash: '' }, sessionStorage: { setItem() {} } };
  globalThis.fetch = async (path, options) => {
    calls.push([path, options.method]);
    if (path === '/api/session') return { ok: true, json: async () => ({ csrf_token: 'synthetic-session' }) };
    return new Promise(resolve => { finish = payload => resolve({ ok: true, json: async () => payload }); });
  };
  try {
    const service = { service_id: 'service/one', cve_lookup_available: true };
    const panel = createCvePanel(document, 'scan/one', service, null, () => false);
    const button = panel.querySelector('button');
    assert.equal(calls.length, 0);
    const work = button.events.click();
    // Allow session bootstrap and the delayed lookup to start without timers.
    while (!finish) await new Promise(resolve => setImmediate(resolve));
    assert.deepEqual(calls, [['/api/session', undefined], ['/api/live-scans/scan%2Fone/services/service%2Fone/cves', 'POST']]);
    assert.equal(button.disabled, true);
    assert.match(byClass(panel, 'cve-status')[0].textContent, /does not run another device scan/);
    const newer = { service_id: 'service/one', status: 'no_matches', message: 'Newer saved lookup.', results: [] };
    panel.updateNotes({ cve_lookups: [newer] });
    finish({ lookup: { ...newer, status: 'unavailable', message: 'Stale lookup.' } });
    await work;
    assert.equal(button.disabled, false);
    assert.match(panel.textContent, /Newer saved lookup/);
    assert.doesNotMatch(panel.textContent, /Stale lookup/);
    assert.match(byClass(panel, 'cve-status')[0].textContent, /No matching CVE records/);
  } finally { globalThis.fetch = originalFetch; globalThis.window = originalWindow; }
});
