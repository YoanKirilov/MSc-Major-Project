import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { createReadingState, validatedReadingState, openDisclosureKeys, restoreDisclosures, bindReportNavigation, bindSupportingInformation } from '../app/static/js/report-view.mjs';
import { reviewItemTitle } from '../app/static/js/presentation.mjs';
import { findingDeviceOptions, repeatedUnknownReplies } from '../app/static/js/finding-list.mjs';

const state = () => ({ version: 1, search: 'web', devices: 'display', filter: 'low', tasks: 'to_check',
  sort: 'name', deviceFilter: 'all', contextDeviceId: '', reviewDevice: 'all', selected: 'finding-1', limit: 48, open: ['device-details'], y: 987 });

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
  assert.equal(validatedReadingState({ ...state(), deviceFilter: 'unsafe' }).deviceFilter, 'all');
  assert.equal(validatedReadingState({ ...state(), deviceFilter: 'unfinished' }).deviceFilter, 'all');
  assert.equal(value.limit, 254);
  assert.equal(value.y, 0);
  assert.equal(value.open.length, 2048);
  assert.equal(value.open.filter(key => key === 'x').length, 1);
  assert.equal(validatedReadingState({ ...state(), y: -99, limit: 2 }).y, 0);
  assert.equal(validatedReadingState({ ...state(), y: 9e9, limit: 2 }).limit, 24);
});

test('legacy alignment is ignored without losing per-report filters or scroll position', () => {
  for (const alignment of ['justify', 'left', 'script']) {
    const raw = JSON.stringify({ ...state(), alignment });
    const restored = createReadingState(() => ({ getItem: () => raw }), 'a').load();
    assert.deepEqual(restored, state());
    assert.equal(Object.hasOwn(restored, 'alignment'), false);
  }
  let stored;
  const reading = createReadingState(() => ({ setItem(_key, value) { stored = value; } }), 'a');
  assert.equal(reading.save({ ...state(), alignment: 'justify', theme: 'light', textSize: 'larger', motion: 'reduce' }), true);
  assert.deepEqual(JSON.parse(stored), state());
});

test('accessibility controls replace justified alignment with native labelled preferences', () => {
  const report = readFileSync(new URL('../app/templates/scan.html', import.meta.url), 'utf8');
  const display = readFileSync(new URL('../app/templates/includes/display-controls.html', import.meta.url), 'utf8');
  assert.doesNotMatch(report, /textAlignment|Paragraph alignment|Justified/);
  assert.match(report, /<h3 id="supporting-accessibility-title">Text and colour preferences<\/h3>/);
  for (const id of ['themePreference', 'textSizePreference']) {
    assert.match(display, new RegExp(`<label for="${id}">`));
    assert.match(display, new RegExp(`<select id="${id}"[^>]*aria-describedby=`));
  }
  assert.match(report, /include "includes\/display-controls.html"/);
  assert.match(display, /<option value="dark">Dark<\/option><option value="light">Light<\/option><option value="system">Use device theme<\/option>/);
  assert.match(report, /Reduced movement from your device settings is always respected\./);
  assert.doesNotMatch(report, /motionPreference|Movement on screen/);
  assert.match(report, /These preferences apply to this browser, not your scan results\./);
});

test('report keeps results before comparisons and removes redundant filters and shortcuts', () => {
  const report = readFileSync(new URL('../app/templates/scan.html', import.meta.url), 'utf8');
  assert.ok(report.indexOf('id="what-changed"') > report.indexOf('id="nextStepsList"'));
  assert.ok(report.indexOf('id="what-changed"') < report.indexOf('id="changes-title"'));
  assert.doesNotMatch(report, /deviceQuickFilter|resetDeviceFilters|needHelpShortcut|expandReviewTasks|collapseReviewTasks/);
  for (const id of ['deviceSearchInput', 'deviceSort', 'checklist-filter']) assert.match(report, new RegExp(`id="${id}"`));
  assert.match(report, /<dialog id="supportingInfoDialog"[^>]+aria-labelledby="supportingInfoTitle"/);
  assert.match(report, /id="closeSupportingInfo"[^>]*>Close<\/button>/);
});

function supportingFixture() {
  const node = (extra = {}) => ({ hidden: false, disabled: false, isConnected: true, events: {},
    tabIndex: 0, getClientRects: () => [1], checkVisibility() { return !this.hidden; },
    addEventListener(name, handler) { this.events[name] = handler; },
    focus(options) { document.activeElement = this; this.focusOptions = options; }, ...extra });
  const topics = ['comparisons', 'announcements', 'technical', 'explanations', 'glossary', 'accessibility'];
  const buttons = topics.map(topic => node({ dataset: { supportingTopic: topic } }));
  const panels = topics.map(topic => node({ dataset: { supportingPanel: topic }, hidden: true }));
  const options = topics.map(value => node({ value }));
  const content = node({ scrollTop: 0 });
  const heading = node();
  const select = node({ value: '', querySelectorAll: () => options });
  const announcement = node({ hidden: true });
  const close = node();
  const focusable = [close, select, content];
  const dialog = node({ open: false, showModal() { this.open = true; },
    close() { this.open = false; this.events.close?.(); },
    querySelector: () => content, querySelectorAll: selector => selector === '[data-supporting-panel]' ? panels : focusable });
  const ids = new Map([['#supportingInfoDialog', dialog], ['#supportingInfoTopic', select],
    ['#supportingInfoTitle', heading], ['#closeSupportingInfo', close], ['#mdns-section', announcement]]);
  const document = { activeElement: null, querySelectorAll: () => buttons, querySelector: id => ids.get(id) };
  const controller = bindSupportingInformation(document);
  return { buttons, panels, options, content, heading, select, announcement, close, dialog, document, controller, focusable };
}

test('supporting topics use one native modal without moving the page or stealing topic-selector focus', () => {
  const ui = supportingFixture();
  ui.buttons[4].events.click();
  assert.equal(ui.dialog.open, true);
  assert.equal(ui.select.value, 'glossary');
  assert.equal(ui.document.activeElement, ui.heading);
  assert.deepEqual(ui.heading.focusOptions, { preventScroll: true });
  assert.deepEqual(ui.panels.filter(panel => !panel.hidden).map(panel => panel.dataset.supportingPanel), ['glossary']);
  ui.content.scrollTop = 280;
  ui.select.focus(); ui.select.value = 'technical'; ui.select.events.change();
  assert.equal(ui.document.activeElement, ui.select);
  assert.equal(ui.content.scrollTop, 0);
  ui.content.scrollTop = 30;
  ui.select.value = 'glossary'; ui.select.events.change();
  assert.equal(ui.content.scrollTop, 280);
  ui.close.events.click();
  assert.equal(ui.dialog.open, false);
  assert.equal(ui.document.activeElement, ui.buttons[4]);
  assert.deepEqual(ui.buttons[4].focusOptions, { preventScroll: true });
  ui.content.scrollTop = 0; // Browsers can zero hidden dialog geometry.
  ui.buttons[4].events.click();
  assert.equal(ui.content.scrollTop, 280);
  ui.content.scrollTop = 140; ui.dialog.events.cancel(); ui.dialog.close();
  ui.content.scrollTop = 0;
  ui.buttons[4].events.click();
  assert.equal(ui.content.scrollTop, 140);
});

test('supporting availability follows saved announcements and rejects unrecognised topics', () => {
  const ui = supportingFixture();
  assert.equal(ui.buttons[1].hidden, true);
  assert.equal(ui.options[1].disabled, true);
  assert.equal(ui.controller.open('announcements'), false);
  assert.equal(ui.controller.open('<script>'), false);
  ui.announcement.hidden = false; ui.controller.refresh();
  assert.equal(ui.buttons[1].hidden, false);
  assert.equal(ui.options[1].disabled, false);
  assert.equal(ui.controller.open('announcements'), true);
  ui.announcement.hidden = true; ui.controller.refresh();
  assert.equal(ui.select.value, 'technical');
  assert.equal(ui.panels[1].hidden, true);
});

test('supporting close returns to the actual glossary invoker and fragment navigation closes the dialog', () => {
  const ui = supportingFixture();
  const trigger = { isConnected: true, focus(options) { this.focusOptions = options; } };
  assert.equal(ui.controller.open('glossary', trigger), true);
  const fragment = { getAttribute: () => '#devices-title' };
  ui.dialog.events.click({ target: { closest: () => fragment } });
  assert.equal(ui.dialog.open, false);
  assert.deepEqual(trigger.focusOptions, { preventScroll: true });
  const unsupported = bindSupportingInformation({ querySelectorAll: () => [], querySelector: () => null });
  assert.equal(unsupported.open('glossary'), false);
  unsupported.refresh();
});

test('supporting Tab boundaries contain focus and skip disabled, hidden and negative-tabindex controls', () => {
  const ui = supportingFixture();
  ui.controller.open('accessibility');
  let prevented = 0;
  const tab = shiftKey => ui.dialog.events.keydown({ key: 'Tab', shiftKey, preventDefault() { prevented++; } });
  ui.heading.focus(); tab(false);
  assert.equal(ui.document.activeElement, ui.close);
  tab(true);
  assert.equal(ui.document.activeElement, ui.content);
  tab(false);
  assert.equal(ui.document.activeElement, ui.close);
  ui.focusable.push({ disabled: true }, { tabIndex: -1 }, { tabIndex: 0, getClientRects: () => [] },
    { tabIndex: 0, getClientRects: () => [1], checkVisibility: () => false });
  ui.content.focus(); tab(false);
  assert.equal(ui.document.activeElement, ui.close);
  assert.equal(prevented, 4);
  ui.close.focus(); tab(false);
  assert.equal(prevented, 4, 'native sequential movement within the dialog is not intercepted');
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
