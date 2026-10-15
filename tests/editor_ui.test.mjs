import test from 'node:test';
import assert from 'node:assert/strict';
import { createTextEditor, createUnsavedChangesGuard } from '../app/static/js/editor.mjs';

function fixture(onChange = () => {}, { deferClose = false } = {}) {
  const events = [];
  const elements = new Map();
  const node = (id, extra = {}) => ({ events: {}, isConnected: true, disabled: false, value: '',
    addEventListener(name, handler) { this.events[name] = handler; },
    setAttribute() {}, removeAttribute() {}, select() {},
    focus() { document.activeElement = this; }, ...extra });
  for (const id of ['annotationEditorDialog', 'annotationEditorForm', 'annotationEditorInput',
    'annotationEditorSave', 'annotationEditorCancel', 'annotationEditorStatus', 'annotationEditorTitle',
    'annotationEditorLabel', 'annotationEditorHint', 'main-content']) elements.set('#' + id, node(id));
  const document = { activeElement: null, querySelector: id => elements.get(id) };
  const dialog = elements.get('#annotationEditorDialog');
  dialog.open = false;
  dialog.showModal = () => { dialog.open = true; };
  dialog.close = () => {
    dialog.open = false; events.push('closed');
    if (!deferClose) dialog.events.close?.();
  };
  const status = elements.get('#annotationEditorStatus');
  Object.defineProperty(status, 'textContent', { get: () => status.message || '', set(value) {
    status.message = value; if (value) events.push(value);
  } });
  const editor = createTextEditor(document, { onChange });
  return { elements, document, dialog, status, editor, events };
}

test('successful editor outcome is announced by its owner only after native close and focus return', async () => {
  const ui = fixture();
  const trigger = { isConnected: true, focus() { ui.events.push('focus-returned'); } };
  ui.editor.open({ title: 'Nickname', label: 'Your nickname', value: '', maxLength: 80, hint: '', trigger,
    onSave: async () => { ui.events.push('write'); }, onSaved: () => {
      assert.equal(ui.dialog.open, false); ui.events.push('one-success');
    } });
  ui.elements.get('#annotationEditorInput').value = 'Room device';
  await ui.elements.get('#annotationEditorForm').events.submit({ preventDefault() {} });
  assert.deepEqual(ui.events, ['write', 'closed', 'focus-returned', 'one-success']);
  assert.equal(ui.status.textContent, '');
});

test('failed editor save preserves the draft and local message without global outcome callback', async () => {
  const ui = fixture();
  let writes = 0, outcomes = 0;
  ui.editor.open({ title: 'Nickname', label: 'Your nickname', maxLength: 80, hint: '',
    onSave: async () => { writes++; throw Error('Save not confirmed. Your draft is kept.'); },
    onSaved: () => outcomes++ });
  ui.elements.get('#annotationEditorInput').value = 'Unconfirmed draft';
  await ui.elements.get('#annotationEditorForm').events.submit({ preventDefault() {} });
  assert.equal(ui.dialog.open, true);
  assert.equal(ui.elements.get('#annotationEditorInput').value, 'Unconfirmed draft');
  assert.equal(writes, 1);
  assert.equal(outcomes, 0);
  assert.deepEqual(ui.events, ['Save not confirmed. Your draft is kept.']);
  ui.elements.get('#annotationEditorCancel').events.click();
  assert.equal(outcomes, 0);
});

test('local validation and Cancel never write or trigger success callbacks', async () => {
  const ui = fixture();
  let writes = 0, outcomes = 0;
  ui.editor.open({ title: 'Report title', label: 'Title', maxLength: 5, hint: '',
    onSave: async () => writes++, onSaved: () => outcomes++ });
  ui.elements.get('#annotationEditorInput').value = 'Too long';
  await ui.elements.get('#annotationEditorForm').events.submit({ preventDefault() {} });
  assert.equal(ui.status.textContent, 'Use up to 5 characters on one line.');
  assert.equal(ui.dialog.open, true);
  assert.equal(writes, 0);
  ui.elements.get('#annotationEditorCancel').events.click();
  assert.equal(outcomes, 0);
});

test('editor dirty state follows actual changes, pending writes and explicit discard', async () => {
  let notifications = 0, finish;
  const ui = fixture(() => notifications++);
  const input = ui.elements.get('#annotationEditorInput');
  const options = { title: 'Title', label: 'Title', value: 'Original', maxLength: 100,
    onSave: () => new Promise(resolve => { finish = resolve; }) };
  ui.editor.open(options);
  assert.equal(ui.editor.hasUnsavedChanges, false);
  input.value = 'Draft'; input.events.input();
  assert.equal(ui.editor.hasUnsavedChanges, true);
  input.value = 'Original'; input.events.input();
  assert.equal(ui.editor.hasUnsavedChanges, false);
  const saving = ui.elements.get('#annotationEditorForm').events.submit({ preventDefault() {} });
  assert.equal(ui.editor.hasUnsavedChanges, true, 'Even an unchanged pending save needs protection');
  finish(); await saving;
  assert.equal(ui.editor.hasUnsavedChanges, false);
  ui.editor.open(options);
  input.value = 'Another draft'; input.events.input();
  ui.elements.get('#annotationEditorCancel').events.click();
  assert.equal(ui.editor.hasUnsavedChanges, false);
  assert.ok(notifications >= 7);
});

test('hidden characters are rejected locally while ordinary Unicode labels remain supported', async () => {
  for (const value of ['hidden\0text', 'title\u202e', '\u200bname', 'non\u00a0breaking', '\ud800']) {
    const ui = fixture();
    let writes = 0;
    ui.editor.open({ title: 'Title', label: 'Title', maxLength: 100, onSave: async () => writes++ });
    const input = ui.elements.get('#annotationEditorInput'); input.value = value;
    await ui.elements.get('#annotationEditorForm').events.submit({ preventDefault() {} });
    assert.match(ui.status.textContent, /visible text.*hidden or control/);
    assert.equal(input.value, value);
    assert.equal(ui.editor.hasUnsavedChanges, true);
    assert.equal(writes, 0);
  }
  const ui = fixture();
  const labels = [];
  ui.editor.open({ title: 'Title', label: 'Title', maxLength: 100, onSave: async value => labels.push(value) });
  ui.elements.get('#annotationEditorInput').value = 'Télévision 東京';
  await ui.elements.get('#annotationEditorForm').events.submit({ preventDefault() {} });
  assert.deepEqual(labels, ['Télévision 東京']);
});

test('leave guard attaches only while needed and does not save or persist data', () => {
  const listeners = new Set(), changes = [];
  const guard = createUnsavedChangesGuard({
    addEventListener(name, handler) { assert.equal(name, 'beforeunload'); listeners.add(handler); changes.push('add'); },
    removeEventListener(name, handler) { assert.equal(name, 'beforeunload'); listeners.delete(handler); changes.push('remove'); },
  });
  guard.update(false);
  assert.equal(guard.active, false);
  assert.equal(listeners.size, 0);
  guard.update(true); guard.update(true);
  let prevented = false;
  const event = { preventDefault() { prevented = true; } };
  [...listeners][0](event);
  assert.equal(prevented, true);
  assert.equal(event.returnValue, '');
  guard.update(false); guard.update(false);
  assert.equal(listeners.size, 0);
  assert.deepEqual(changes, ['add', 'remove']);
});

test('Cancel and Escape clear dirty protection before the queued native close event', () => {
  for (const dismissal of ['cancel-button', 'escape']) {
    let guarded = false, writes = 0, ui;
    ui = fixture(() => { guarded = ui.editor.hasUnsavedChanges; }, { deferClose: true });
    ui.editor.open({ title: 'Title', label: 'Title', value: '', maxLength: 100,
      onSave: async () => writes++ });
    const input = ui.elements.get('#annotationEditorInput');
    input.value = 'Discard this draft'; input.events.input();
    assert.equal(guarded, true);
    if (dismissal === 'cancel-button') ui.elements.get('#annotationEditorCancel').events.click();
    else {
      let prevented = false;
      ui.dialog.events.cancel({ preventDefault() { prevented = true; } });
      assert.equal(prevented, true);
    }
    assert.equal(ui.dialog.open, false);
    assert.equal(guarded, false, 'Explicit discard must not wait for the native close event');
    assert.equal(writes, 0);
    ui.dialog.events.close();
    assert.equal(guarded, false);
  }
});
