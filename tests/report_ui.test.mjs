import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import * as presentation from '../app/static/js/presentation.mjs';
import { createCvePanel } from '../app/static/js/cves.mjs';
import { renderDeviceSummaries as renderDeviceComponents, deviceResultEntries } from '../app/static/js/devices.mjs';
import * as reportView from '../app/static/js/report-view.mjs';
import { renderFindingList, findingDeviceOptions, repeatedUnknownReplies } from '../app/static/js/finding-list.mjs';
import { createTextEditor } from '../app/static/js/editor.mjs';
import { createNoteState, checkStatus, projectNotes, reviewProgress } from '../app/static/js/notes.mjs';
import { createNicknameState, projectNicknames } from '../app/static/js/nicknames.mjs';
import { unfinishedDeviceCount, partialScanTitle } from '../app/static/js/report.mjs';
import { prioritise, serviceLabel, coverageSummary, deviceCheckLabel, completedCheckSummary, emptyFindingMessage, usableAiRecord, checkSummary, aiExplanationNote, analysisProgressText, scanSetupLink, readScanSetup } from '../app/static/js/report.mjs';

test('complete IPv4 search is exact identity, not prefixes or addresses in names and notes', () => {
  for (const ip of ['192.168.0.1', '192.168.0.115', '192.168.0.154']) {
    const device = { ip, hostname: '192.168.0.1', details: [{ value: 'Previously at 192.168.0.1' }] };
    assert.equal(presentation.matchesSearch(' 192.168.0.1 ', presentation.deviceSearchValues(device), ip), ip === '192.168.0.1');
    assert.equal(presentation.matchesSearch('192.168.0.1', [ip]), ip === '192.168.0.1');
    assert.equal(presentation.matchesSearch('192.168.0.', [ip], ip), true);
  }
  assert.equal(presentation.matchesSearch('192.168.0.154', presentation.deviceSearchValues({ ip: '192.168.0.154' }), '192.168.0.154'), true);
  assert.equal(presentation.matchesSearch('192.168.0.99', ['Router'], '192.168.0.1'), false);
  assert.equal(presentation.matchesSearch('TV kitchen', ['Kitchen TV'], '192.168.0.1'), true);
});

test('saved dates display an unavailable label instead of guessing or Invalid Date', () => {
  for (const value of [null, undefined, '', 'invalid', '2026-10-08T11:00:00', '9999-12-31T23:59:59-23:00',
    '2026-10-08Z', '2026-02-30T00:00:00Z', '2026-02-29T00:00:00Z', '2026-10-08T24:00:00Z',
    '2026-10-08T00:00:00+24:00', '0000-10-08T00:00:00Z']) {
    assert.equal(presentation.recordedTimeLabel(value), 'Time unavailable');
    assert.equal(presentation.recordedTimeLabel(value, 'Date unavailable'), 'Date unavailable');
  }
  const value = '2026-10-08T01:00:00+03:00';
  assert.equal(presentation.recordedTimeLabel(value), new Date(value).toLocaleString());
  assert.equal(presentation.recordedTimeLabel('2026-10-07T22:00:00Z'), new Date(value).toLocaleString());
  assert.equal(presentation.recordedTimeLabel('2024-02-29T12:00:00Z'), new Date('2024-02-29T12:00:00Z').toLocaleString());
});

test('unfinished counts include cancelled and unstarted selected checks, not silent addresses', () => {
  for (const status of ['cancelled', 'pending', 'skipped', 'failed', 'timed_out']) {
    const data = { target: { mode: 'discover' }, coverage: { candidate_count: 254, discovered_count: 2, service_completed_count: 1, service_failed_count: 0,
      targets: [{ discovery_status: 'observed', service_status: 'completed' }, { discovery_status: 'observed', service_status: status }, { discovery_status: 'not_seen', service_status: 'skipped' }] } };
    assert.equal(unfinishedDeviceCount(data), 1);
    assert.match(partialScanTitle(data), /1 device could not be checked/);
    assert.match(coverageSummary(data), /1 did not finish/);
    assert.equal(unfinishedDeviceCount({ target: { mode: 'known_hosts' }, coverage: { candidate_count: 2, service_completed_count: 1 } }), 1);
  }
  assert.doesNotMatch(partialScanTitle({ coverage: { discovered_count: 0 } }), /0 devices/);
});

test('recognised local features get conditional help, never a diagnosis from a port', () => {
  const device = { ip: '192.168.0.10' };
  const data = { policy: { network_context: { address: device.ip } } };
  const base = { name: 'msrpc', state: 'open', protocol: 'tcp', detection_method: 'probed', nmap_confidence: 9 };
  const help = presentation.localFeatureHelp(device, base, data);
  assert.match(help.meaning, /consistent with.*Windows/);
  assert.match(help.check, /Windows Security.*Do not switch off/);
  assert.match(help.limitation, /computer to itself.*does not establish/);
  for (const changed of [{ detection_method: 'table' }, { nmap_confidence: 6 }, { state: 'open_filtered' }, { protocol: 'udp' }, { name: 'unknown' }]) {
    assert.equal(presentation.localFeatureHelp(device, { ...base, ...changed }, data), null);
  }
  assert.match(presentation.localFeatureHelp(device, { ...base, name: 'netbios-ssn' }, {}).check, /Advanced sharing settings/);
  assert.match(presentation.localFeatureHelp(device, { ...base, name: 'vmware-auth' }, {}).meaning, /not confirmation/);
  assert.match(presentation.localFeatureHelp(device, { ...base, name: 'microsoft-ds' }, {}).check, /Do not enable sharing/);
});

test('Light self-coverage is read from saved ledger without changing counts', () => {
  const data = { phase: 'finished', target: { mode: 'discover' }, policy: { network_context: { address: '192.168.0.10' } },
    coverage: { service_completed_count: 2, targets: [{ ip: '192.168.0.10', discovery_status: 'not_seen', service_status: 'skipped' }] } };
  const before = JSON.stringify(data);
  assert.match(presentation.scanComputerCoverage(data), /not discovered.*not included.*not start automatically/);
  assert.equal(JSON.stringify(data), before);
  data.coverage.targets[0].discovery_status = 'observed';
  assert.match(presentation.scanComputerCoverage(data), /did not finish/);
  data.coverage.targets[0].service_status = 'completed';
  assert.match(presentation.scanComputerCoverage(data), /included.*self-check/);
  assert.equal(presentation.scanComputerCoverage({ ...data, target: { mode: 'known_hosts' } }), '');
  assert.equal(presentation.scanComputerCoverage({ ...data, coverage: {} }), '');
});

test('identification guidance uses exactly the rendered control label and matching glossary', () => {
  assert.ok(presentation.namingCoverage([]).includes(presentation.IDENTIFY_DEVICE_LABEL));
  const source = readFileSync(new URL('../app/static/js/devices.mjs', import.meta.url), 'utf8');
  assert.match(source, /text\('button', IDENTIFY_DEVICE_LABEL/);
  assert.match(readFileSync(new URL('../app/templates/scan.html', import.meta.url), 'utf8'), /<dt>Device not identified<\/dt>/);
});

test('gateway role is sourced from the saved connection, never from a guessed address', () => {
  const device = { ip: '192.168.0.1' };
  assert.equal(presentation.recordedDeviceRole(device, {}), '');
  const data = { policy: { network_context: { address: '192.168.0.2', connection: { Gateways: ['192.168.0.1'] } } } };
  assert.match(presentation.recordedDeviceRole(device, data), /when this scan started/);
  assert.equal(presentation.recordedDeviceRole({ ip: '192.168.0.2' }, data), 'Computer that ran this scan');
  assert.equal(presentation.recordedDeviceRole({ ip: '192.168.0.3' }, data), '');
  assert.equal(device.hostname, undefined);
});

test('action labels preserve nicknames and add only recorded roles', () => {
  const device = { ip: '192.168.0.1', user_nickname: 'Home router' };
  const data = { policy: { network_context: { address: '192.168.0.2', connection: { Gateways: [device.ip] } } } };
  assert.match(presentation.actionDeviceLabel(device, data), /Home router \(your nickname\).*Network gateway/);
  assert.match(presentation.actionDeviceLabel(device, data), /not a verified device name/);
  assert.equal(presentation.actionDeviceLabel(device, {}), 'Home router (your nickname) (192.168.0.1)');
  assert.equal(presentation.actionDeviceLabel(null, data), 'Observed device');
  assert.match(presentation.actionDeviceLabel({ ip: '192.168.0.2' }, data), /Computer that ran this scan/);
  const duplicateNames = ['192.168.0.3', '192.168.0.4', '192.168.0.5'].map(ip => presentation.actionDeviceLabel({ ip, hostname: 'Display' }, {}));
  assert.equal(new Set(duplicateNames).size, 3);
});

test('Windows feature labels are readable and retain service evidence provenance', () => {
  for (const [name, port, plain] of [['msrpc', 135, 'Windows communication'], ['netbios-ssn', 139, 'Older Windows sharing'], ['vmware-auth', 902, 'Virtual computer software']]) {
    assert.match(presentation.featureLabel({ name }), new RegExp(plain));
    assert.match(serviceLabel({ name, port, detection_method: 'table' }), new RegExp(plain));
    assert.match(serviceLabel({ name, port, detection_method: 'table' }), /name inferred from port/);
  }
});

test('feature decision aids require a strong observed identity and web precautions are adjacent-ready', () => {
  const device = { ip: '192.168.0.1' };
  const service = { state: 'open', protocol: 'tcp', detection_method: 'probed', nmap_confidence: 9, name: 'rtsp', port: 554 };
  assert.match(presentation.localFeatureHelp(device, service, {}).meaning, /video or sound.*does not identify/);
  assert.match(presentation.localFeatureHelp(device, service, {}).check, /Leave settings unchanged/);
  for (const name of ['rtsp', 'domain', 'vmware-auth', 'tcpwrapped']) assert.doesNotMatch(presentation.localFeatureHelp(device, { ...service, name }, {}).limitation, /Windows steps/);
  assert.match(presentation.localFeatureHelp(device, { ...service, protocol: 'udp', name: 'domain', port: 53 }, {}).check, /Do not switch.*off/);
  for (const patch of [{ detection_method: 'table' }, { nmap_confidence: 2 }, { state: 'filtered' }]) assert.equal(presentation.localFeatureHelp(device, { ...service, ...patch }, {}), null);
  assert.match(presentation.firstActionPrecaution(device, { ...service, name: 'http', port: 80 }), /Do not enter passwords.*HTTP.*certificate warnings/);
  assert.equal(presentation.firstActionPrecaution(device, service), '');
});

test('closed-early connections explain unknown identity without guessing software from the port', () => {
  const service = { state: 'open', name: 'tcpwrapped', protocol: 'tcp', port: 135, detection_method: 'probed', nmap_confidence: 8 };
  const help = presentation.localFeatureHelp({ ip: '192.168.0.10' }, service, {});
  assert.match(help.meaning, /closed it before.*identify.*does not reveal/);
  assert.doesNotMatch(help.meaning, /RPC|VMware|identified Windows|vulnerable/);
  assert.match(help.check, /Do not switch off protection/);
  assert.equal(presentation.reviewItemTitle({ severity: 'informational' }, service), 'Feature not identified · port 135');
});

test('naming coverage separates saved, current, missing and user-assigned names', () => {
  const devices = [{ hostname: 'PC', hostname_source: 'reverse_dns' },
    { hostname: 'TV', hostname_source: 'saved_report' }, { user_nickname: 'Camera' }];
  const message = presentation.namingCoverage(devices);
  assert.match(message, /1 device with names reported in this scan; 1 with earlier saved names; 1 without a detected name/);
  assert.match(message, /nicknames label 1 device separately/);
  assert.match(message, /not verified identities.*does not mean an intruder/);
  assert.match(message, /no name is guaranteed/);
});

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
  const walk = node => node.children.flatMap(child => [child, ...walk(child)]);
  const matches = (node, selector) => {
    const parts = selector.trim().split(/\s+/);
    const compound = (element, part) => {
      const tag = /^[a-z][\w-]*/i.exec(part)?.[0];
      if (tag && element.tagName !== tag.toUpperCase()) return false;
      for (const match of part.matchAll(/([.#])([\w-]+)/g)) {
        if (match[1] === '#' ? element.id !== match[2] : !element.className.split(/\s+/).includes(match[2])) return false;
      }
      for (const match of part.matchAll(/\[([^\]=]+)(?:="([^"]*)")?\]/g)) {
        const key = match[1].startsWith('data-') ? match[1].slice(5).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase()) : null;
        const value = key ? element.dataset[key] : element.attributes[match[1]];
        if (value === undefined || (match[2] !== undefined && value !== match[2])) return false;
      }
      return true;
    };
    if (!compound(node, parts.pop())) return false;
    while (parts.length) {
      let part = parts.pop();
      if (part === '>') {
        part = parts.pop(); node = node.parentElement;
        if (!node || !compound(node, part)) return false;
        continue;
      }
      let ancestor = node.parentElement;
      while (ancestor && !compound(ancestor, part)) ancestor = ancestor.parentElement;
      if (!ancestor) return false;
      node = ancestor;
    }
    return true;
  };
  class Element {
    constructor(tag = 'div') {
      this.tagName = tag.toUpperCase(); this.children = []; this._text = ''; this.dataset = {}; this.events = {};
      this.attributes = {}; this.className = ''; this.value = ''; this.open = false;
      this.style = { setProperty() {} };
      this.classList = { toggle: (name, force) => {
        const classes = new Set(this.className.split(/\s+/).filter(Boolean));
        if (force ?? !classes.has(name)) classes.add(name); else classes.delete(name);
        this.className = [...classes].join(' ');
      } };
    }
    addEventListener(name, fn) { this.events[name] = fn; }
    setAttribute(name, value) {
      this.attributes[name] = String(value);
      if (name === 'id') this.id = String(value);
      if (name.startsWith('data-')) this.dataset[name.slice(5).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase())] = String(value);
    }
    removeAttribute(name) { delete this.attributes[name]; }
    append(...items) { items.forEach(item => this.insertBefore(item, null)); }
    insertBefore(item, reference) {
      item.remove();
      const index = reference ? this.children.indexOf(reference) : this.children.length;
      this.children.splice(index, 0, item); item.parentElement = this;
    }
    remove() {
      if (!this.parentElement) return;
      if (this === document.activeElement || walk(this).includes(document.activeElement)) document.activeElement = document.body;
      const siblings = this.parentElement.children;
      siblings.splice(siblings.indexOf(this), 1); this.parentElement = null;
    }
    replaceChildren(...items) { [...this.children].forEach(child => child.remove()); this._text = ''; this.append(...items); }
    get textContent() { return [this._text, ...this.children.map(child => child.textContent)].filter(Boolean).join(' '); }
    set textContent(value) { this.replaceChildren(); this._text = String(value); }
    querySelectorAll(selector) { return walk(this).filter(node => matches(node, selector)); }
    querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
    closest(selector) {
      for (let node = this; node; node = node.parentElement) if (matches(node, selector)) return node;
      return null;
    }
    focus() { document.activeElement = this; }
    select() {}
    scrollIntoView() {}
    get isConnected() { return this === document.body || Boolean(this.parentElement?.isConnected); }
    showModal() { this.open = true; }
    close() { this.open = false; this.events.close?.(); }
    get childElementCount() { return this.children.length; }
  }
  const template = readFileSync(new URL('../app/templates/scan.html', import.meta.url), 'utf8');
  const elements = new Map();
  const document = {
    body: new Element('body'),
    querySelector(id) {
      if (!/^#[\w-]+$/.test(id)) return this.body.querySelector(id);
      assert.ok(template.includes(`id="${id.slice(1)}"`), `missing template hook ${id}`);
      if (!elements.has(id)) {
        const tag = new RegExp(`<([\\w-]+)\\b[^>]*id="${id.slice(1)}"`).exec(template)?.[1];
        const element = new Element(tag); element.id = id.slice(1);
        elements.set(id, element); this.body.append(element);
      }
      return elements.get(id);
    },
    querySelectorAll(selector) { return this.body.querySelectorAll(selector); },
    createElement(tag) { return new Element(tag); },
  };
  document.activeElement = document.body;
  const layout = new Element(); layout.className = 'findings-layout'; document.body.append(layout);
  layout.append(document.querySelector('#findingsList'), document.querySelector('#detailPanel'));
  for (const filter of ['all', 'high', 'medium', 'low', 'informational']) {
    const button = new Element('button'); button.className = 'filter-chip'; button.dataset.filter = filter;
    document.body.append(button);
  }
  const context = vm.createContext({ document, window: { location: { pathname: '/scans/test' },
    matchMedia: () => ({ matches: false, addEventListener() {} }) }, URL,
    ...presentation, ...reportView, deviceResultEntries, renderDeviceComponents, renderFindingList,
    findingDeviceOptions, repeatedUnknownReplies, createTextEditor,
    createNicknameState, projectNicknames, createNoteState, checkStatus, projectNotes, partialScanTitle, createCvePanel, prioritise, formatServiceLabel: serviceLabel, coverageSummary, deviceCheckLabel, completedCheckSummary, emptyFindingMessage, usableAiRecord, checkSummary, aiExplanationNote, analysisProgressText, scanSetupLink, readScanSetup });
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
  const text = element => element.textContent;
  assert.match(text(elements.get('#scan-problems')), /One device check timed out/);
  assert.equal(elements.get('#scan-problems').hidden, false);
  assert.match(text(elements.get('#nextStepsList').children[0]), /high finding/);
  assert.doesNotMatch(text(elements.get('#findingsList')), /OLD AI CLAIM/);
  assert.match(text(elements.get('#device-table-body')), /HTTPS/);
  assert.match(text(elements.get('#device-table-body')), /Recorded certificate details/);
  // Exercise real stable-node selection, including the mobile in-place panel.
  const cards = elements.get('#findingsList').querySelectorAll('.finding-card');
  const highCard = cards.find(card => card.dataset.findingId === 'high');
  const mediumCard = cards.find(card => card.dataset.findingId === 'medium');
  mediumCard.focus(); mediumCard.events.click();
  assert.equal(document.activeElement, mediumCard);
  assert.equal(mediumCard.attributes['aria-pressed'], 'true');
  assert.equal(elements.get('#findingsList').querySelectorAll('.finding-card').find(card => card.dataset.findingId === 'medium'), mediumCard);
  highCard.focus(); highCard.events.click();
  vm.runInContext('compactResults.matches = true; renderFindings(data)', context);
  const mobileNodes = elements.get('#findingsList').children;
  assert.equal(mobileNodes[mobileNodes.indexOf(highCard) + 1], elements.get('#detailPanel'));
  assert.equal(document.activeElement, highCard);
  vm.runInContext('compactResults.matches = false; renderFindings(data)', context);
  assert.equal(elements.get('#detailPanel').parentElement, layout);
  context.data.earlier_observations = { status: 'available', reason: 'Not matched; not proof of removal.',
    source_scan_id: '11111111-1111-4111-8111-111111111111', omitted_count: 2,
    items: [{ reported_name: '<script>Earlier TV</script>', last_ip: '192.168.0.20', name_source: 'mdns', observed_at: '2026-10-06T12:00:00Z' }] };
  vm.runInContext('render(data)', context);
  assert.match(text(elements.get('#earlier-devices-list')), /Earlier TV.*reported earlier/);
  assert.match(text(elements.get('#earlier-devices-list')), /2 additional earlier observations/);
  assert.match(elements.get('#earlier-devices-note').textContent, /not proof/);
  assert.match(elements.get('#naming-coverage').textContent, /without a detected name/);
  context.data.policy = { network_context: { address: '192.168.0.10' } };
  vm.runInContext('render(data)', context);
  assert.match(elements.get('#report-first-step').textContent, /Computer that ran this scan.*Confirm you recognise it before changing settings/);
  assert.doesNotMatch(elements.get('#report-first-step').textContent, /router's device list/);
  context.data.policy = {};
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
  elements.get('#device-summaries').children.forEach(group => {
    assert.equal(group.className, 'device-summary-group');
    assert.equal(group.children[0].className, 'device-summary');
    assert.equal(group.children[1].className, 'device-name-tools');
  });
  assert.match(text(elements.get('#device-summaries')), /Room TV \(previously reported\)/);
  assert.match(text(elements.get('#device-summaries')), /192.168.0.53/);
  assert.match(text(elements.get('#device-summaries')), /Missing checks do not mean the device is safe/);
  assert.match(text(elements.get('#device-summaries')), /does not show that anyone used.*vulnerability/);
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
  assert.match(text(elements.get('#detailPanel')), /What we found Observed service/);
  assert.doesNotMatch(text(elements.get('#detailPanel')), /Plain explanation/);
  assert.match(text(elements.get('#detailPanel')), /Plain action/);
  assert.doesNotMatch(text(elements.get('#detailPanel')), /Original rule-based explanation|Original rule-based step|Guidance saved before/);
  context.data.explanations = [];
  assert.equal(elements.get('#refreshGuidanceButton').hidden, false);
  context.data.findings = []; context.data.state = 'failed';
  vm.runInContext('render(data)', context);
  assert.match(text(elements.get('#findingsList')), /Scan incomplete/);
  context.data.services[0].cve_lookup_available = true;
  vm.runInContext('render(data)', context);
  assert.match(text(elements.get('#device-summaries')), /Check CVEs for this software/);
  assert.match(text(elements.get('#report-first-step')), /Retry the unfinished.*Missing results cannot tell you whether a device is safe/);
  context.data.state = 'completed';
  context.data.analysis_status = 'ready';
  context.data.report_explanation = { status: 'ready', source: 'ai', ai_fields: ['meaning', 'why_it_matters', 'recommended_steps', 'how_to_check', 'limitations'], prompt_version: '3.0.0', content: {
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
  assert.match(text(elements.get('#nextStepsList')), /Reviewed report-level next step/);
  assert.match(text(elements.get('#result-lead')), /Recorded observations/);
  context.data.report_explanation.status = 'fallback';
  vm.runInContext('render(data)', context);
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
  context.data.state = 'partial';
  context.data.coverage = { candidate_count: 2, service_completed_count: 1, service_failed_count: 0,
    targets: [{ ip: '192.168.0.53', service_status: 'completed' }, { ip: '192.168.0.54', service_status: 'cancelled', reason_code: 'network_interrupted' }] };
  vm.runInContext('render(data)', context);
  assert.match(elements.get('#result-title').textContent, /1 device could not be checked/);
  assert.match(text(elements.get('#scan-problems')), /network safety check/);
});
