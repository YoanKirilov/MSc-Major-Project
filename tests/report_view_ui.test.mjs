import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { createReadingState, validatedReadingState, openDisclosureKeys, restoreDisclosures, bindReportNavigation } from '../app/static/js/report-view.mjs';
import { reviewItemTitle } from '../app/static/js/presentation.mjs';
import { findingDeviceOptions, repeatedUnknownReplies } from '../app/static/js/finding-list.mjs';

const state = () => ({ version: 1, search: 'web', devices: 'display', filter: 'low', tasks: 'to_check',
  sort: 'name', alignment: 'justify', reviewDevice: 'all', selected: 'finding-1', limit: 48, open: ['device-details'], y: 987 });

test('reading state is isolated by report and tab and never persists evidence or edits', () => {
  const values = new Map();
  const storage = { getItem: key => values.get(key), setItem: (key, value) => values.set(key, value) };
  const first = createReadingState(() => storage, 'report-a');
  assert.equal(first.save({ ...state(), evidence: ['private'], expected_revision: 99, token: 'secret' }), true);
  assert.deepEqual(first.load(), state());
  assert.equal(createReadingState(() => storage, 'report-b').load(), null);
  assert.equal(createReadingState(() => ({ getItem: () => null }), 'report-a').load(), null);
  assert.doesNotMatch([...values.values()].join(''), /private|secret|expected_revision/);
});

test('blocked, corrupt, unsupported and oversized storage cannot break report loading', () => {
  for (const raw of ['{bad', '{}', '{"version":2,"open":[]}', 'x'.repeat(262145)]) {
    assert.equal(createReadingState(() => ({ getItem: () => raw }), 'a').load(), null);
  }
  const unavailable = createReadingState(() => { throw Error('denied'); }, 'a');
  assert.equal(unavailable.load(), null);
  assert.equal(unavailable.save(state()), false);
  assert.equal(createReadingState(() => null, 'a').save(state()), false);
  assert.equal(createReadingState(() => ({ setItem() { throw Error('full'); } }), 'a').save(state()), false);
  assert.equal(unavailable.save({ ...state(), version: 0 }), false);
});

test('stored filters, lengths, scroll and disclosure keys are bounded and allowlisted', () => {
  const value = validatedReadingState({ ...state(), search: 's'.repeat(999), devices: 42, selected: 'f'.repeat(999),
    filter: '<script>', tasks: 'invalid', sort: 'delete', limit: 100000, y: Infinity,
    open: ['x', 'x', 4, 'a'.repeat(1501), ...Array.from({ length: 3000 }, (_, i) => `key-${i}`)] });
  assert.equal(value.search.length, 120);
  assert.equal(value.selected.length, 80);
  assert.equal(validatedReadingState({ ...state(), reviewDevice: 'd'.repeat(999) }).reviewDevice.length, 80);
  assert.equal(validatedReadingState({ ...state(), reviewDevice: 10 }).reviewDevice, 'all');
  assert.equal(value.devices, '');
  assert.equal(value.filter, 'all');
  assert.equal(value.tasks, 'all');
  assert.equal(value.sort, 'priority');
  assert.equal(validatedReadingState({ ...state(), alignment: 'script' }).alignment, 'justify');
  assert.equal(validatedReadingState({ ...state(), alignment: 'left' }).alignment, 'left');
  assert.equal(value.limit, 254);
  assert.equal(value.y, 0);
  assert.equal(value.open.length, 2048);
  assert.equal(value.open.filter(key => key === 'x').length, 1);
  assert.equal(validatedReadingState({ ...state(), y: -99, limit: 2 }).y, 0);
  assert.equal(validatedReadingState({ ...state(), y: 9e9, limit: 2 }).limit, 24);
});

test('device review options count every finding without mutating facts or inventing names', () => {
  const devices = [{ device_id: 'one', ip: '192.168.56.10', hostname: 'Example device' }];
  const findings = [{ device_id: 'one' }, { device_id: 'two' }, { device_id: 'one' }];
  const before = JSON.stringify([findings, devices]);
  assert.deepEqual(findingDeviceOptions(findings, devices, device => device.hostname), [
    { id: 'one', count: 2, label: 'Example device · 192.168.56.10' },
    { id: 'two', count: 1, label: 'Observed device' },
  ]);
  assert.equal(JSON.stringify([findings, devices]), before);
  assert.deepEqual(findingDeviceOptions([], devices, () => 'unused'), []);
});

test('repeated reply context applies only to actual repeated informational observations on a device', () => {
  const finding = { rule_id: 'R07', severity: 'informational', device_id: 'one', service_id: 'a' };
  const service = { service_id: 'a', state: 'open', name: 'tcpwrapped', detection_method: 'probed', nmap_confidence: 8 };
  assert.equal(repeatedUnknownReplies([finding, { ...finding, service_id: 'b' }], [service, { ...service, service_id: 'b' }]), 2);
  assert.equal(repeatedUnknownReplies([finding, { ...finding, device_id: 'two' }], [service]), 0);
  for (const changed of [{ severity: 'low' }, { rule_id: 'R01' }, { service_id: 'missing' }]) {
    assert.equal(repeatedUnknownReplies([{ ...finding, ...changed }, { ...finding, ...changed }], [service]), 0);
  }
  for (const changed of [{ state: 'filtered' }, { name: 'http' }, { detection_method: 'table' }, { nmap_confidence: 2 }, { nmap_confidence: undefined }]) {
    assert.equal(repeatedUnknownReplies([finding, finding], [{ ...service, ...changed }]), 0);
  }
});

test('disclosure restore keys distinguish devices and selected items without selectors from storage', () => {
  const group = ip => ({ dataset: { deviceIp: ip } });
  const detail = (scope, kind = 'device', open = false) => ({
    tagName: 'DETAILS', dataset: {}, children: [{ tagName: 'SUMMARY', textContent: 'About this device' }], open,
    parentElement: scope, closest(selector) {
      if (selector === '.device-summary-group' && kind === 'device') return scope;
      if (selector === '#detailPanel' && kind === 'item') return scope;
      return null;
    },
  });
  const first = detail(group('192.168.56.10'), 'device', true);
  const second = detail(group('192.168.56.11'));
  const item = detail({ dataset: { findingId: 'one' } }, 'item', true);
  const otherItem = detail({ dataset: { findingId: 'two' } }, 'item');
  const technical = { open: true, closest: selector => selector === '.device-table' ? {} : null };
  const document = { querySelectorAll: () => [first, second, item, otherItem, technical] };
  const keys = openDisclosureKeys(document);
  assert.equal(keys.length, 2);
  first.open = false; second.open = true; item.open = false; otherItem.open = true;
  restoreDisclosures(document, [...keys, '<script>']);
  assert.equal(first.open, true);
  assert.equal(second.open, false);
  assert.equal(item.open, true);
  assert.equal(otherItem.open, false);
  assert.equal(technical.open, true);
});

test('navigation offset follows its height and stops sticking when enlarged text obscures the screen', () => {
  let height = 70, offset, resize;
  const nav = { dataset: {}, getBoundingClientRect: () => ({ height }) };
  const document = { querySelector: () => nav, documentElement: { style: { setProperty(_key, value) { offset = value; } } } };
  const window = { innerHeight: 900, getComputedStyle: () => ({ position: nav.dataset.tooTall === 'true' ? 'static' : 'sticky' }),
    addEventListener(name, fn) { assert.equal(name, 'resize'); resize = fn; } };
  bindReportNavigation(document, window);
  assert.equal(offset, '82px');
  height = 240; resize();
  assert.equal(nav.dataset.tooTall, 'true');
  assert.equal(offset, '16px');
  height = 120; resize();
  assert.equal(nav.dataset.tooTall, 'false');
  assert.equal(offset, '132px');
});

test('feature-specific review titles distinguish ports and leave source titles untouched', () => {
  const finding = { title: 'Generic software observation', severity: 'informational' };
  const service = { name: 'msrpc', protocol: 'tcp', port: 135 };
  assert.equal(reviewItemTitle(finding, service), 'Windows communication between programs · port 135');
  assert.equal(finding.title, 'Generic software observation');
  assert.notEqual(reviewItemTitle(finding, { ...service, name: 'http', port: 80 }),
    reviewItemTitle(finding, { ...service, name: 'http', port: 5357 }));
  assert.equal(reviewItemTitle({ ...finding, severity: 'medium' }, service, 'Reviewed title'), 'Reviewed title · port 135');
  assert.equal(reviewItemTitle({}, null), 'Review this item');
});

test('loading placeholders are not zero observations and the entire progress block is not live', () => {
  const report = readFileSync(new URL('../app/templates/scan.html', import.meta.url), 'utf8');
  assert.match(report, /id="report-content"[^>]*hidden[^>]*aria-busy="true"/);
  for (const id of ['result-count', 'device-metric', 'service-metric']) assert.match(report, new RegExp(`id="${id}"[^>]*>—<`));
  const dashboard = readFileSync(new URL('../app/templates/dashboard.html', import.meta.url), 'utf8');
  assert.match(dashboard, /id="scan-progress-status"[^>]*role="status"[^>]*aria-live="polite"/);
  assert.doesNotMatch(dashboard, /id="scanProgress"[^>]*aria-live/);
});
