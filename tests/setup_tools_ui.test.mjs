import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { recordedTimeLabel } from '../app/static/js/presentation.mjs';

const address = '192.168.0.10';
const item = { name: 'Kitchen TV', ip: address, last_check: 'Address saved; response not confirmed', observed_at: '2026-10-12T18:00:00Z' };

function setup(load = async () => ({ items: [item] }), target = '', running = []) {
  class Element {
    constructor() { this.value = ''; this.textContent = ''; this.events = {}; this.children = []; this.attributes = {}; this.dataset = {}; }
    setAttribute(name, value) { this.attributes[name] = String(value); }
    addEventListener(name, handler) { this.events[name] = handler; }
    replaceChildren() { this.children = []; }
    append(...items) { this.children.push(...items); }
    get options() { return this.children; }
    get textContent() { return this._textContent; }
    set textContent(value) { this._textContent = value; this.textWrites = (this.textWrites || 0) + 1; }
  }
  const elements = new Map();
  const requests = [];
  const document = {
    querySelector(id) { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); },
    createElement() { return new Element(); },
    createTextNode(text) { return { textContent: text }; },
  };
  const input = document.querySelector('#deepHostInput');
  input.value = target;
  document.querySelector('#recentDeviceDetails').hidden = true;
  const context = vm.createContext({ document, recordedTimeLabel, window: { setTimeout() {}, confirm: () => true }, request: async path => {
    requests.push(path);
    return path === '/api/recent-devices' ? load() : { items: running };
  } });
  const source = readFileSync(new URL('../app/static/js/setup-tools.mjs', import.meta.url), 'utf8').replace(/^import .*;\r?\n/gm, '').replace(/export /g, '');
  vm.runInContext(source, context);
  context.startSetupTools();
  return { elements, input, requests, configure: context.configurePicker, select: document.querySelector('#recentDeviceSelect'),
    note: document.querySelector('#recentDeviceNote'), details: document.querySelector('#recentDeviceDetails'),
    type(value) { input.value = value; input.events.input({ target: input }); },
    choose(value) { const select = document.querySelector('#recentDeviceSelect'); select.value = value; select.events.change({ target: select }); } };
}

test('native device choices contain only names and addresses, with saved evidence nearby', async () => {
  const app = setup();
  await app.configure(true);
  assert.equal(app.select.options[1].textContent, 'Kitchen TV — 192.168.0.10');
  assert.doesNotMatch(app.select.options[1].textContent, /response|saved|2026/);
  assert.match(app.details.textContent, /Choose a device/);
  assert.equal(app.details.hidden, true);
  app.choose(address);
  assert.equal(app.input.value, address);
  assert.match(app.details.textContent, /Address saved; response not confirmed/);
  assert.equal(app.details.hidden, false);
  assert.match(app.details.textContent, /Saved /);
  assert.match(app.details.textContent, /not a check of whether the device is connected now/);
  assert.equal(app.requests.filter(path => path === '/api/recent-devices').length, 1);
  assert.equal(app.requests.some(path => path.includes('/live-scans')), false);
});

test('saved names are displayed literally, without inventing identity or confirmed connection', async () => {
  const app = setup(async () => ({ items: [item, { ip: '192.168.0.11', name: '<Unknown / conflicting names>' }] }));
  await app.configure(true);
  assert.equal(app.select.options[2].textContent, '<Unknown / conflicting names> — 192.168.0.11');
  app.choose('192.168.0.11');
  assert.match(app.details.textContent, /Check status not recorded/);
  assert.match(app.details.textContent, /recording time is unavailable/);
  assert.doesNotMatch(app.details.textContent, /NaN|Invalid Date/);
  assert.match(app.details.textContent, /not a check of whether the device is connected now/);
});

test('typing an address synchronises saved context and removes stale manual-address notices', async () => {
  const app = setup(async () => ({ items: [item], warnings: ['One saved report could not be read.'] }));
  await app.configure(true);
  app.type('192.168.0.99');
  assert.equal(app.select.value, '');
  assert.match(app.note.textContent, /It has been kept/);
  assert.match(app.details.textContent, /entered address/);
  assert.doesNotMatch(app.details.textContent, /response not confirmed/);
  app.type(` ${address} `);
  assert.equal(app.select.value, address);
  assert.match(app.details.textContent, /response not confirmed/);
  assert.doesNotMatch(app.note.textContent, /It has been kept/);
  assert.match(app.note.textContent, /report could not be read/);
  app.type('');
  assert.match(app.details.textContent, /Choose a device/);
  assert.equal(app.details.hidden, true);
});

test('a bounded loading request cannot overwrite an address typed while waiting', async () => {
  let resolve;
  const app = setup(() => new Promise(done => { resolve = done; }), address);
  const pending = app.configure(true);
  assert.equal(app.elements.get('#recentDevicePanel').attributes['aria-busy'], 'true');
  await app.configure(true, true);
  app.type('192.168.0.99');
  resolve({ items: [item] });
  await pending;
  assert.equal(app.input.value, '192.168.0.99');
  assert.equal(app.select.value, '');
  assert.match(app.details.textContent, /entered address/);
  assert.equal(app.requests.filter(path => path === '/api/recent-devices').length, 1);
  assert.equal(app.elements.get('#recentDevicePanel').attributes['aria-busy'], 'false');
});

test('typing a manual address does not repeatedly replace unchanged live-region descriptions', async () => {
  const app = setup();
  await app.configure(true);
  app.type('192.168.0.99');
  const noteWrites = app.note.textWrites;
  const detailsWrites = app.details.textWrites;
  app.type('192.168.0.98');
  assert.equal(app.note.textWrites, noteWrites);
  assert.equal(app.details.textWrites, detailsWrites);
  app.type(address);
  assert.ok(app.details.textWrites > detailsWrites);
});

test('refreshing an empty list keeps the authorised entered target and removes old saved details', async () => {
  let items = [item];
  const app = setup(async () => ({ items }), address);
  await app.configure(true);
  assert.match(app.details.textContent, /response not confirmed/);
  items = [];
  await app.configure(true, true);
  assert.equal(app.input.value, address);
  assert.equal(app.select.value, '');
  assert.match(app.note.textContent, /No recent Light results/);
  assert.match(app.note.textContent, /It has been kept/);
  assert.match(app.details.textContent, /No saved device check/);
});

test('an update outage preserves previous choices and clearly labels their saved evidence', async () => {
  let fail = false;
  let malformed = false;
  const app = setup(async () => { if (fail) throw new Error('Try again.'); return { items: malformed ? [null] : [item] }; }, address);
  await app.configure(true);
  fail = true;
  await app.configure(true, true);
  assert.equal(app.input.value, address);
  assert.equal(app.select.options[1].textContent, 'Kitchen TV — 192.168.0.10');
  assert.match(app.note.textContent, /Recent devices unavailable/);
  assert.match(app.details.textContent, /saved information/);
  assert.equal(app.elements.get('#recentDevicePanel').attributes['aria-busy'], 'false');
  fail = false;
  malformed = true;
  await app.configure(true, true);
  assert.equal(app.input.value, address);
  assert.equal(app.select.options[1].textContent, 'Kitchen TV — 192.168.0.10');
  assert.match(app.note.textContent, /saved device list could not be read/);
});

test('the native picker does not modify a locked running scan target', async () => {
  const app = setup(undefined, '192.168.0.99');
  await app.configure(true);
  app.input.disabled = true;
  app.choose(address);
  assert.equal(app.input.value, '192.168.0.99');
});

test('Light setup does not fetch choices and a loaded Deep list only refetches on explicit refresh', async () => {
  const app = setup();
  await app.configure(false);
  assert.equal(app.requests.filter(path => path === '/api/recent-devices').length, 0);
  assert.equal(app.elements.get('#recentDevicePanel').hidden, true);
  await app.configure(true);
  app.input.value = address;
  await app.configure(true);
  assert.match(app.details.textContent, /response not confirmed/);
  assert.equal(app.details.hidden, false);
  assert.equal(app.requests.filter(path => path === '/api/recent-devices').length, 1);
  await app.configure(true, true);
  assert.equal(app.requests.filter(path => path === '/api/recent-devices').length, 2);
});

test('running overview groups independent links and cancellation without changing job identity', async () => {
  const id = '11111111-1111-4111-8111-111111111111';
  const app = setup(undefined, '', [{ scan_id: id, profile: 'light', target: { hosts: [address] }, phase: 'service_scan', completed: 0, total: 1 }]);
  await app.configure(false);
  const row = app.elements.get('#runningScans').children[0];
  const actions = row.children[1];
  assert.equal(actions.className, 'running-scan-actions');
  assert.equal(actions.attributes.role, 'group');
  assert.equal(actions.attributes['aria-label'], `Actions for Light scan of ${address}`);
  assert.equal(actions.children.length, 3);
  const [progress, report, cancel] = actions.children;
  assert.equal(progress.href, `/#scan=${id}`);
  assert.equal(report.href, `/scans/${id}`);
  assert.equal(progress.rel, 'noopener');
  assert.equal(report.rel, 'noopener');
  await cancel.events.click();
  assert.equal(cancel.textContent, 'Cancellation requested');
  assert.equal(cancel.disabled, true);
  assert.equal(app.requests.filter(path => path.includes('/api/live-scans/')).length, 1);
});
