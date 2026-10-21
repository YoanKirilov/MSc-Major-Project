import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

for (const name of ['dashboard', 'scan']) {
  test(`${name}: static preview opens the backend, backend page does not loop`, () => {
    const html = readFileSync(new URL(`../app/templates/${name}.html`, import.meta.url), 'utf8');
    assert.match(html, /src="\.\.\/static\/js\/startup\.js\?/);
    assert.doesNotMatch(html, /<script\s*>|onerror=/);
    const script = readFileSync(new URL('../app/static/js/startup.js', import.meta.url), 'utf8');
    const redirects = [];
    const handlers = [];
    const window = { location: { replace(url) { redirects.push(url); } }, addEventListener(...args) { handlers.push(args); } };
    const document = { documentElement: { dataset: { localApp: "{{ 'backend' }}" } } };
    vm.runInNewContext(script, { window, document });
    assert.deepEqual(redirects, ['http://127.0.0.1:8765/']);
    assert.equal(handlers.length, 0);
    redirects.length = 0;
    document.documentElement.dataset.localApp = 'backend';
    vm.runInNewContext(script, { window, document });
    assert.deepEqual(redirects, []);
    assert.equal(handlers.length, 1);
    assert.equal(handlers[0][0], 'error');
    assert.equal(handlers[0][2], true);
  });
}

test('the external startup guard recovers a broken module without starting a scan', () => {
  const script = readFileSync(new URL('../app/static/js/startup.js', import.meta.url), 'utf8');
  const label = { textContent: 'Checking scanner...' };
  const button = { disabled: true, querySelector: () => label };
  const notice = {};
  let listener;
  let reloads = 0;
  const window = { location: { reload() { reloads++; } }, addEventListener(_name, callback) { listener = callback; } };
  const document = { documentElement: { dataset: { localApp: 'backend' } },
    querySelector: selector => selector === '#scanLaunchButton' ? button : notice };
  vm.runInNewContext(script, { window, document });
  listener();
  assert.equal(label.textContent, 'Reload page');
  assert.equal(button.disabled, false);
  assert.match(notice.textContent, /No scan was started/);
  button.onclick();
  assert.equal(reloads, 1);
  label.textContent = 'Scan';
  listener();
  assert.equal(label.textContent, 'Scan');
});

test('the report bootstrap explains module failure and never starts a replacement scan', () => {
  const source = readFileSync(new URL('../app/static/js/startup.js', import.meta.url), 'utf8');
  const nodes = { '#result-title': { textContent: 'Loading your report' }, '#result-lead': {}, '#retryReportLoad': { hidden: true, disabled: true } };
  let handler;
  let reloads = 0;
  vm.runInNewContext(source, {
    document: { documentElement: { dataset: { localApp: 'backend' } }, querySelector: id => nodes[id] || null },
    window: { addEventListener: (_name, fn) => { handler = fn; }, location: { reload: () => { reloads++; } } },
  });
  handler();
  assert.match(nodes['#result-lead'].textContent, /no scan was started/);
  assert.equal(nodes['#retryReportLoad'].hidden, false);
  nodes['#retryReportLoad'].onclick();
  assert.equal(reloads, 1);
});
