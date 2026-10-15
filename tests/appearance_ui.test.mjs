import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const source = readFileSync(new URL('../app/static/js/appearance.js', import.meta.url), 'utf8');
const displayControls = readFileSync(new URL('../app/templates/includes/display-controls.html', import.meta.url), 'utf8');
function setup({ raw = null, blocked = false, media = false, systemLight = false, loading = false } = {}) {
  const values = new Map(raw === null ? [] : [['netguard-appearance-v1', raw]]);
  const writes = [], windowEvents = {}, documentEvents = {}, controls = new Map();
  const motion = { matches: media, addEventListener(type, callback) { this[type] = callback; } };
  const theme = { matches: systemLight, addEventListener(type, callback) { this[type] = callback; } };
  const options = { notices: [], append(node) { this.notices.push(node); controls.set(node.id, node); } };
  const document = {
    readyState: loading ? 'loading' : 'complete', documentElement: { dataset: {} },
    getElementById: id => controls.get(id) || null,
    querySelector: () => options,
    createElement: () => ({ setAttribute(name, value) { this[name] = value; } }),
    addEventListener: (name, callback) => { documentEvents[name] = callback; },
  };
  for (const id of ['themePreference', 'textSizePreference']) {
    controls.set(id, { value: '', events: [], addEventListener(name, callback) { this.events.push(callback); } });
  }
  controls.set('appearance-feedback', { textContent: '' });
  const window = {
    get localStorage() {
      if (blocked) throw new Error('Storage denied');
      return { getItem: key => values.get(key) || null,
        setItem(key, value) { writes.push(value); values.set(key, value); } };
    },
    matchMedia: query => query.includes('color-scheme') ? theme : motion,
    addEventListener: (name, callback) => { windowEvents[name] = callback; },
  };
  vm.runInNewContext(source, { window, document });
  return { api: window.NetGuardAppearance, window, document, values, writes, controls, motion, theme, windowEvents, documentEvents, options };
}

test('device theme is opt-in; explicit choices win across system changes and storage failure', () => {
  const app = setup({ systemLight: true, blocked: true });
  assert.equal(app.document.documentElement.dataset.theme, 'dark');
  app.api.applyAppearancePreferences({ theme: 'system' });
  assert.equal(app.document.documentElement.dataset.theme, 'light');
  app.theme.matches = false; app.theme.change();
  assert.equal(app.document.documentElement.dataset.theme, 'dark');
  app.api.applyAppearancePreferences({ theme: 'light' });
  app.theme.change();
  assert.equal(app.document.documentElement.dataset.theme, 'light');
  assert.equal(app.api.getAppearancePreferences().theme, 'light');
});
const plain = value => JSON.parse(JSON.stringify(value));

test('appearance initializes before paint without saving or reading any scan data', () => {
  const app = setup({ loading: true });
  assert.deepEqual(app.document.documentElement.dataset, { theme: 'dark', textSize: 'standard', reduceMotion: 'false' });
  assert.deepEqual(plain(app.api.getAppearancePreferences()), { theme: 'dark', textSize: 'standard' });
  assert.equal(app.writes.length, 0);
  assert.equal(app.controls.get('themePreference').events.length, 0);
  app.documentEvents.DOMContentLoaded();
  assert.equal(app.controls.get('themePreference').events.length, 1);
});

test('saved light theme is adopted before paint while removed movement choice is ignored', () => {
  const app = setup({ raw: JSON.stringify({ version: 1, theme: 'light', textSize: 'larger', motion: 'reduce' }), loading: true });
  assert.equal(app.document.documentElement.dataset.theme, 'light');
  assert.equal(app.document.documentElement.dataset.textSize, 'larger');
  assert.equal(app.document.documentElement.dataset.reduceMotion, 'false');
  assert.equal(Object.hasOwn(app.api.getAppearancePreferences(), 'motion'), false);
  assert.equal(app.writes.length, 0);
});

test('appearance persists only versioned allowlisted choices, never evidence or secrets', () => {
  const app = setup();
  app.api.applyAppearancePreferences({ theme: 'light', textSize: 'larger', motion: 'reduce', token: 'secret', devices: ['private'] });
  assert.equal(app.writes.length, 1);
  assert.deepEqual(JSON.parse(app.writes[0]), { version: 1, theme: 'light', textSize: 'larger' });
  assert.doesNotMatch(app.writes[0], /secret|private|token|devices|motion/);
  app.api.applyAppearancePreferences({ theme: 'light' });
  assert.equal(app.writes.length, 1);
  const snapshot = app.api.getAppearancePreferences();
  snapshot.theme = 'dark';
  assert.equal(app.api.getAppearancePreferences().theme, 'light');
});

test('invalid, unsupported, oversized or blocked storage cannot prevent displaying reports', () => {
  for (const raw of ['{bad', '[]', '{"version":2,"theme":"light"}', 'x'.repeat(1025), '{"version":1,"theme":"script","textSize":999}']) {
    assert.equal(setup({ raw }).document.documentElement.dataset.theme, 'dark');
  }
  const blocked = setup({ blocked: true });
  blocked.api.applyAppearancePreferences({ theme: 'light' });
  assert.equal(blocked.document.documentElement.dataset.theme, 'light');
  assert.equal(blocked.options.notices.length, 1);
  assert.equal(blocked.options.notices[0].role, undefined);
  blocked.api.bindAppearancePreferences();
  assert.equal(blocked.options.notices.length, 1);
});

test('controls are bound once and changing a native selection updates display without any request', () => {
  const app = setup();
  app.api.bindAppearancePreferences();
  const select = app.controls.get('themePreference');
  assert.equal(select.events.length, 1);
  select.value = 'light';
  select.events[0]();
  assert.equal(app.document.documentElement.dataset.theme, 'light');
  assert.equal(app.writes.length, 1);
  assert.equal(app.controls.get('textSizePreference').value, 'standard');
  assert.match(app.controls.get('appearance-feedback').textContent, /applied and remembered/);
});

test('blocked preference edits have one live feedback message and persistent non-live help', () => {
  const app = setup({ blocked: true });
  const control = app.controls.get('themePreference');
  control.value = 'system';
  control.events[0]();
  assert.equal(app.api.getAppearancePreferences().theme, 'system');
  assert.match(app.controls.get('appearance-feedback').textContent, /applied on this page.*could not remember/);
  assert.equal(app.options.notices.length, 1);
  assert.equal(app.options.notices[0].role, undefined);
  assert.equal((displayControls.match(/role="status"/g) || []).length, 1);
  assert.match(displayControls, /id="appearance-feedback"[^>]*aria-atomic="true"/);
});

test('Settings and the report render the same native display choices', () => {
  for (const name of ['settings.html', 'scan.html']) {
    const html = readFileSync(new URL(`../app/templates/${name}`, import.meta.url), 'utf8');
    assert.match(html, /include "includes\/display-controls\.html"/);
    assert.doesNotMatch(html, /<select id="(?:themePreference|textSizePreference)"/);
    assert.match(html, /set display_preferences_note = '[a-z-]+'/);
  }
  for (const choice of ['dark', 'light', 'system']) assert.match(displayControls, new RegExp(`option value="${choice}"`));
  for (const id of ['themePreference', 'textSizePreference']) {
    assert.match(displayControls, new RegExp(`<label for="${id}">`));
    assert.equal((displayControls.match(new RegExp(`id="${id}"`, 'g')) || []).length, 1);
  }
});

test('movement follows device automatically and legacy app choices cannot override it', () => {
  const app = setup({ media: true });
  assert.equal(app.document.documentElement.dataset.reduceMotion, 'true');
  app.api.applyAppearancePreferences({ motion: 'device' });
  assert.equal(app.document.documentElement.dataset.reduceMotion, 'true');
  app.motion.matches = false;
  app.motion.change();
  assert.equal(app.document.documentElement.dataset.reduceMotion, 'false');
  app.api.applyAppearancePreferences({ motion: 'reduce' });
  app.motion.change();
  assert.equal(app.document.documentElement.dataset.reduceMotion, 'false');
  assert.equal(app.writes.length, 0);
  app.motion.matches = true;
  app.motion.change();
  assert.equal(app.document.documentElement.dataset.reduceMotion, 'true');
});

test('cross-tab updates synchronize controls without echo writes; deletion resets defaults', () => {
  const app = setup();
  app.windowEvents.storage({ key: 'netguard-appearance-v1', newValue: '{"version":1,"theme":"light","textSize":"larger"}' });
  assert.equal(app.controls.get('themePreference').value, 'light');
  assert.equal(app.controls.get('textSizePreference').value, 'larger');
  assert.equal(app.writes.length, 0);
  app.windowEvents.storage({ key: 'netguard-appearance-v1', newValue: '{bad' });
  app.windowEvents.storage({ key: 'unrelated', newValue: null });
  assert.equal(app.api.getAppearancePreferences().theme, 'light');
  app.windowEvents.storage({ key: 'netguard-appearance-v1', newValue: null });
  assert.equal(app.api.getAppearancePreferences().theme, 'dark');
});

test('subscribers cannot mutate internal choices or break another subscriber', () => {
  const app = setup();
  let notified = 0;
  app.api.subscribeAppearancePreferences(() => { throw Error('Bad widget'); });
  const unsubscribe = app.api.subscribeAppearancePreferences(value => { value.theme = 'script'; notified++; });
  app.api.applyAppearancePreferences({ theme: 'light' });
  assert.equal(app.api.getAppearancePreferences().theme, 'light');
  assert.equal(notified, 1);
  unsubscribe();
  app.api.applyAppearancePreferences({ theme: 'dark' });
  assert.equal(notified, 1);
});

test('all page shells initialize appearance before the stylesheet without inline scripting', () => {
  for (const file of ['base.html', 'dashboard.html', 'scan.html']) {
    const html = readFileSync(new URL(`../app/templates/${file}`, import.meta.url), 'utf8');
    const boot = html.indexOf('<script src="/static/js/appearance.js?v=20261015-inclusive"></script>');
    assert.ok(boot >= 0 && boot < html.indexOf('<link rel="stylesheet"'));
  }
});

test('display choices stay in Settings without a duplicate global navigation shortcut', () => {
  const header = readFileSync(new URL('../app/templates/includes/shared-header.html', import.meta.url), 'utf8');
  const html = readFileSync(new URL('../app/templates/settings.html', import.meta.url), 'utf8');
  assert.doesNotMatch(header, /Display preferences/);
  assert.match(header, /href="\/settings"/);
  const section = html.slice(html.indexOf('<section id="display-preferences"'), html.indexOf('<section class="card settings-card" aria-label="App settings">'));
  assert.match(section, /tabindex="-1"/);
  assert.match(section, /Changes apply straight away, without pressing Save settings/);
  assert.doesNotMatch(section, /<form\b|<details\b/);
  for (const id of ['themePreference', 'textSizePreference']) {
    assert.equal((displayControls.match(new RegExp(`id="${id}"`, 'g')) || []).length, 1);
    assert.match(displayControls, new RegExp(`<label for="${id}">`));
  }
  assert.doesNotMatch(section, /motionPreference|Movement on screen/);
  assert.match(section, /reduced-motion setting is respected automatically/);
});
