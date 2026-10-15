// Contextual label editing. This changes user notes, never recorded scan facts.
export function createUnsavedChangesGuard(target) {
  let active = false;
  const warn = event => { event.preventDefault(); event.returnValue = ''; };
  return {
    get active() { return active; },
    update(value) {
      const needed = Boolean(value);
      if (needed === active) return;
      if (needed) target.addEventListener('beforeunload', warn);
      else target.removeEventListener('beforeunload', warn);
      active = needed;
    },
  };
}

export function createTextEditor(document, { onChange = () => {} } = {}) {
  const dialog = document.querySelector('#annotationEditorDialog');
  const form = document.querySelector('#annotationEditorForm');
  const input = document.querySelector('#annotationEditorInput');
  const save = document.querySelector('#annotationEditorSave');
  const cancel = document.querySelector('#annotationEditorCancel');
  const status = document.querySelector('#annotationEditorStatus');
  let context = null;
  let busy = false;
  let saved = false;
  const message = value => { status.textContent = value; status.hidden = !value; };
  const close = () => {
    if (busy) return;
    dialog.close();
    // The native close event is queued. Stop guarding an explicitly discarded
    // draft immediately, even if navigation starts before that event runs.
    onChange();
  };
  input.addEventListener('input', onChange);
  cancel.addEventListener('click', close);
  dialog.addEventListener('cancel', event => { event.preventDefault(); close(); });
  dialog.addEventListener('keydown', event => {
    if (event.key !== 'Tab') return;
    const controls = [...dialog.querySelectorAll('input, button, select, textarea, a[href], [tabindex]')]
      .filter(control => !control.disabled && control.tabIndex >= 0 && control.getClientRects().length);
    const first = controls[0];
    const last = controls.at(-1);
    if (!first) { event.preventDefault(); return; }
    if (!dialog.contains(document.activeElement)
        || (event.shiftKey && document.activeElement === first)
        || (!event.shiftKey && document.activeElement === last)) {
      event.preventDefault();
      (event.shiftKey ? last : first).focus({ preventScroll: true });
    }
  });
  dialog.addEventListener('close', () => {
    const completed = context;
    const resolved = context?.resolveTrigger?.() || context?.trigger;
    const trigger = resolved?.isConnected && !resolved.disabled ? resolved
      : context?.resolveFallback?.() || document.querySelector('#main-content');
    context = null;
    onChange();
    if (trigger?.isConnected && !trigger.disabled) trigger.focus({ preventScroll: true });
    // Native modal content is no longer active. A successful operation may now
    // announce once outside; failures remain in the still-open local editor.
    if (saved) { saved = false; completed?.onSaved?.(); }
  });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!context || busy) return;
    if (input.value.length > context.maxLength || /[\r\n\t]/.test(input.value)) {
      input.setAttribute('aria-invalid', 'true');
      message(`Use up to ${context.maxLength} characters on one line.`);
      input.focus();
      return;
    }
    if ([...input.value].some(character => character !== ' ' && /[\p{C}\p{Z}]/u.test(character))) {
      input.setAttribute('aria-invalid', 'true');
      message('Use visible text on one line. Remove hidden or control characters.');
      input.focus();
      return;
    }
    busy = true;
    onChange();
    save.disabled = cancel.disabled = input.disabled = true;
    dialog.setAttribute('aria-busy', 'true');
    save.textContent = 'Saving…';
    input.removeAttribute('aria-invalid');
    message('');
    try {
      await context.onSave(input.value);
      busy = false;
      saved = true;
      dialog.close();
    } catch (error) {
      message(error.message || 'Your change could not be saved. Your draft is still here.');
    } finally {
      busy = false;
      save.disabled = cancel.disabled = input.disabled = false;
      save.textContent = 'Save';
      dialog.removeAttribute('aria-busy');
      if (dialog.open) input.focus({ preventScroll: true });
      onChange();
    }
  });
  return {
    get isOpen() { return dialog.open; },
    get hasUnsavedChanges() { return Boolean(context && dialog.open && (busy || input.value !== (context.value || ''))); },
    open(options) {
      if (dialog.open || busy) return;
      context = options;
      saved = false;
      document.querySelector('#annotationEditorTitle').textContent = options.title;
      document.querySelector('#annotationEditorLabel').textContent = options.label;
      document.querySelector('#annotationEditorHint').textContent = options.hint;
      input.value = options.value || '';
      input.maxLength = options.maxLength;
      input.removeAttribute('aria-invalid');
      message('');
      dialog.showModal();
      input.focus();
      input.select();
      onChange();
    },
  };
}
