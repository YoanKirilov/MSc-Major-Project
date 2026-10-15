// Best-effort reading state in this browser tab. No evidence, edit revisions,
// credentials, scan authority or API requests are stored or restored here.
import { validReportDeviceId } from './report-device-context.mjs?v=20261015-inclusive';
const filters = ['all', 'high', 'medium', 'low', 'informational'];
const taskFilters = ['all', 'to_check', 'checked', 'need_help'];
const sorts = ['priority', 'name', 'address'];
const boundedText = (value, limit) => typeof value === 'string' ? value.slice(0, limit) : '';

export function validatedReadingState(value) {
  if (!value || value.version !== 1 || !Array.isArray(value.open)) return null;
  return {
    version: 1, search: boundedText(value.search, 120), devices: boundedText(value.devices, 120),
    filter: filters.includes(value.filter) ? value.filter : 'all',
    tasks: taskFilters.includes(value.tasks) ? value.tasks : 'all',
    sort: sorts.includes(value.sort) ? value.sort : 'priority',
    // The extra device filter was retired. Ignore old hidden restrictions while
    // preserving the reader's useful search, sorting and scroll context.
    deviceFilter: 'all',
    contextDeviceId: validReportDeviceId(value.contextDeviceId) ? value.contextDeviceId : '',
    reviewDevice: boundedText(value.reviewDevice, 80) || 'all',
    selected: boundedText(value.selected, 80),
    limit: Number.isInteger(value.limit) ? Math.min(254, Math.max(24, value.limit)) : 24,
    y: Number.isFinite(value.y) ? Math.min(10000000, Math.max(0, value.y)) : 0,
    open: [...new Set(value.open.filter(key => typeof key === 'string' && key.length <= 1500))].slice(0, 2048),
  };
}

export function createReadingState(getStorage, scanId) {
  const key = `netguard-report-view-v1:${scanId}`;
  return {
    load() {
      try {
        const raw = getStorage()?.getItem(key);
        if (!raw || raw.length > 262144) return null;
        return validatedReadingState(JSON.parse(raw));
      } catch { return null; }
    },
    save(value) {
      try {
        const state = validatedReadingState(value);
        if (!state) return false;
        const raw = JSON.stringify(state);
        if (raw.length > 262144) return false;
        const storage = getStorage();
        if (!storage) return false;
        storage.setItem(key, raw);
        return true;
      } catch { return false; }
    },
  };
}

function disclosureKey(detail) {
  // Technical table rows have repeated anonymous summaries; their outer section
  // is remembered, but do not conflate unrelated row-level evidence.
  if (detail.closest('.device-table')) return null;
  const group = detail.closest('.device-summary-group');
  const step = detail.closest('.next-step-checklist');
  const panel = detail.closest('#detailPanel');
  const scope = group || step || panel;
  const prefix = group ? ['device', group.dataset.deviceIp]
    : step ? ['task', step.dataset.findingId]
      : panel ? ['item', panel.dataset.findingId] : ['report'];
  const path = [];
  for (let current = detail; current && current !== scope; current = current.parentElement) {
    if (current.tagName !== 'DETAILS') continue;
    const summary = [...current.children].find(child => child.tagName === 'SUMMARY');
    path.unshift(current.id || current.dataset.disclosureKey || summary?.textContent || 'details');
  }
  if (detail === scope) path.push(detail.dataset.disclosureKey || 'details');
  return JSON.stringify([...prefix, ...path]);
}

export function openDisclosureKeys(document) {
  return [...document.querySelectorAll('main details')].filter(detail => detail.open)
    .map(disclosureKey).filter(Boolean);
}

export function restoreDisclosures(document, keys) {
  const open = new Set(keys);
  // Earlier reading states stored one disclosure per feature. Opening the new
  // device-level group preserves that reading intent without altering evidence.
  for (const key of keys) {
    try {
      const parts = JSON.parse(key);
      if (Array.isArray(parts) && parts.length === 4 && parts[0] === 'device'
          && typeof parts[3] === 'string' && parts[3].startsWith('feature:')) {
        open.add(JSON.stringify([...parts.slice(0, 3), 'features']));
      }
    } catch { /* Malformed old UI state must not break a report. */ }
  }
  for (const detail of document.querySelectorAll('main details')) {
    const key = disclosureKey(detail);
    if (key) detail.open = open.has(key);
  }
}

export function bindReportNavigation(document, window) {
  const nav = document.querySelector('.report-jump-links');
  if (!nav?.getBoundingClientRect) return;
  const update = () => {
    const height = nav.getBoundingClientRect().height;
    // Enlarged text can wrap navigation into a screen-obscuring stack.
    nav.dataset.tooTall = String(height > Math.min(160, window.innerHeight / 4));
    const sticky = window.getComputedStyle(nav).position === 'sticky';
    document.documentElement.style.setProperty('--report-nav-offset',
      `${sticky ? Math.ceil(height) + 12 : 16}px`);
  };
  update();
  if (window.ResizeObserver) new window.ResizeObserver(update).observe(nav);
  window.addEventListener('resize', update);
}

// Keep optional supporting material out of the report's layout. Native modal
// behaviour supplies keyboard containment and Escape; no scroll or scan request
// is generated when readers switch topics. Each topic retains its inner position.
export function bindSupportingInformation(document) {
  const buttons = [...document.querySelectorAll('[data-supporting-topic]')];
  const dialog = document.querySelector('#supportingInfoDialog');
  if (!buttons.length || !dialog?.showModal) return { open: () => false, refresh() {} };
  const select = document.querySelector('#supportingInfoTopic');
  const heading = document.querySelector('#supportingInfoTitle');
  const content = dialog.querySelector('.supporting-dialog-content');
  const panels = new Map([...dialog.querySelectorAll('[data-supporting-panel]')]
    .map(panel => [panel.dataset.supportingPanel, panel]));
  const options = new Map([...select.querySelectorAll('option')].map(option => [option.value, option]));
  const positions = new Map();
  let selected = null;
  let invoker = null;
  const available = topic => panels.has(topic)
    && (topic !== 'announcements' || document.querySelector('#mdns-section')?.hidden === false);
  // Hidden modal contents can report zero after native close. Capture while
  // open, including the cancel event before Escape closes the modal.
  const savePosition = () => { if (selected && dialog.open) positions.set(selected, content.scrollTop); };
  const choose = topic => {
    if (!available(topic)) return false;
    savePosition();
    for (const [key, panel] of panels) panel.hidden = key !== topic;
    selected = topic;
    select.value = topic;
    content.scrollTop = positions.get(topic) || 0;
    return true;
  };
  const refresh = () => {
    for (const button of buttons) {
      const topic = button.dataset.supportingTopic;
      button.hidden = !available(topic);
      const option = options.get(topic);
      if (option) option.disabled = button.hidden;
    }
    if (selected && !available(selected)) choose('technical');
  };
  const open = (topic, trigger) => {
    refresh();
    if (!choose(topic)) return false;
    invoker = trigger || buttons.find(button => button.dataset.supportingTopic === topic);
    if (!dialog.open) {
      dialog.showModal();
      heading.focus({ preventScroll: true });
      content.scrollTop = positions.get(topic) || 0;
    }
    return true;
  };
  for (const button of buttons) button.addEventListener('click', () => open(button.dataset.supportingTopic, button));
  select.addEventListener('change', () => { if (!choose(select.value)) select.value = selected; });
  content.addEventListener('scroll', savePosition, { passive: true });
  dialog.addEventListener('keydown', event => {
    if (event.key !== 'Tab') return;
    const controls = [...dialog.querySelectorAll('button, input, select, textarea, a[href], [tabindex]')]
      .filter(control => !control.disabled && control.tabIndex >= 0
        && control.getClientRects().length
        && control.checkVisibility?.({ checkOpacity: true, checkVisibilityCSS: true }) !== false);
    const first = controls[0];
    const last = controls.at(-1);
    if (!first) { event.preventDefault(); heading.focus({ preventScroll: true }); return; }
    if (!controls.includes(document.activeElement)
        || (event.shiftKey && document.activeElement === first)
        || (!event.shiftKey && document.activeElement === last)) {
      event.preventDefault();
      (event.shiftKey ? last : first).focus({ preventScroll: true });
    }
  });
  document.querySelector('#closeSupportingInfo').addEventListener('click', () => { savePosition(); dialog.close(); });
  dialog.addEventListener('cancel', savePosition);
  dialog.addEventListener('close', () => {
    if (invoker?.isConnected && !invoker.disabled) invoker.focus({ preventScroll: true });
  });
  // An intentional link back into the report closes the modal before the browser
  // follows the fragment. Opening/switching/closing alone never moves the page.
  dialog.addEventListener('click', event => {
    const link = event.target?.closest?.('a');
    if (link?.getAttribute('href')?.startsWith('#')) { savePosition(); dialog.close(); }
  });
  refresh();
  return { open, refresh };
}
