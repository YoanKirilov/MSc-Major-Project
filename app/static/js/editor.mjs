// Contextual label editing. This changes user notes, never recorded scan facts.
export function createTextEditor(document) {
  const dialog = document.querySelector('#annotationEditorDialog');
  const form = document.querySelector('#annotationEditorForm');
  const input = document.querySelector('#annotationEditorInput');
  const save = document.querySelector('#annotationEditorSave');
  const cancel = document.querySelector('#annotationEditorCancel');
  const status = document.querySelector('#annotationEditorStatus');
  let context = null;
  let busy = false;
  const message = value => { status.textContent = value; status.hidden = !value; };
  const close = () => { if (!busy) dialog.close(); };
  cancel.addEventListener('click', close);
  dialog.addEventListener('cancel', event => { if (busy) event.preventDefault(); });
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
    const resolved = context?.resolveTrigger?.() || context?.trigger;
    const trigger = resolved?.isConnected && !resolved.disabled ? resolved
      : context?.resolveFallback?.() || document.querySelector('#main-content');
    context = null;
    if (trigger?.isConnected && !trigger.disabled) trigger.focus({ preventScroll: true });
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
    busy = true;
    save.disabled = cancel.disabled = input.disabled = true;
    dialog.setAttribute('aria-busy', 'true');
    save.textContent = 'Saving…';
    input.removeAttribute('aria-invalid');
    message('Saving your label…');
    try {
      await context.onSave(input.value);
      busy = false;
      dialog.close();
    } catch (error) {
      message(error.message || 'Your change could not be saved. Your draft is still here.');
    } finally {
      busy = false;
      save.disabled = cancel.disabled = input.disabled = false;
      save.textContent = 'Save';
      dialog.removeAttribute('aria-busy');
      if (dialog.open) input.focus({ preventScroll: true });
    }
  });
  return {
    get isOpen() { return dialog.open; },
    open(options) {
      if (dialog.open || busy) return;
      context = options;
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
    },
  };
}
