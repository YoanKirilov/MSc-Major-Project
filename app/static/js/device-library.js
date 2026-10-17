import { request } from './api.js?v=20261001-network-recovery';
import { recordedTimeLabel } from './presentation.mjs?v=20261014-dates';
import { createDeviceLibrary, deviceReportHref, DEVICE_PAGE_SIZE, DEVICE_ROOM_LIMIT, DEVICE_VIEWS, validDeviceLabels } from './device-library-model.mjs?v=20261015-inclusive';
import { createDeviceContext } from './device-library-context.mjs?v=20261014-return-context';

const get = name => document.querySelector(`#device-library-${name}`);
const rows = new Map();
let lastRequested = { search: '', page: 1, view: 'all' };
const readingContext = createDeviceContext(() => window.sessionStorage);
const savedContext = readingContext.load();
let rememberedDeviceKey = savedContext?.focusKey || null;
let restoringContext = true;
let userInteracted = false;
for (const name of ['pointerdown', 'keydown', 'wheel', 'touchstart']) {
  window.addEventListener(name, () => { userInteracted = true; }, { once: true, passive: true });
}
const text = (tag, value, className = '') => {
  const node = document.createElement(tag);
  node.textContent = value;
  node.className = className;
  return node;
};
function values(row) {
  return { room: row.room.value, favourite: row.favourite.checked, recognised: row.recognised.checked };
}
function fill(row, draft) {
  row.room.value = draft.room;
  row.favourite.checked = draft.favourite;
  row.recognised.checked = draft.recognised;
  row.invalid = !validDeviceLabels(draft);
  if (row.invalid) {
    row.room.setAttribute('aria-invalid', 'true');
    row.status.textContent = 'Use up to 80 printable characters on one line for your room label.';
  } else row.room.removeAttribute('aria-invalid');
}
function householdSummary(item) {
  const labels = item.annotations;
  return `Latest saved labels: room ${labels.room || 'not set'}; favourite ${labels.favourite ? 'Yes' : 'No'}; recognised by you ${labels.recognised ? 'Yes' : 'No'}.`;
}
function updateSaved(row, item) {
  row.badges.replaceChildren();
  if (!item.editable) {
    row.saved.textContent = 'Saved household labels are unavailable. The room, favourite and recognition values below are not confirmed.';
    row.badges.append(text('span', 'Your recognition label is unavailable', 'device-library-badge device-library-recognition'));
    return;
  }
  row.saved.textContent = householdSummary(item);
  const badges = [];
  if (item.annotations.room) badges.push(`Your room: ${item.annotations.room}`);
  if (item.annotations.favourite) badges.push('Your favourite');
  badges.push(item.annotations.recognised ? 'Recognised by you · not verified' : 'Not marked recognised by you');
  row.badges.append(...badges.map(value => text('span', value, 'device-library-badge')));
  row.badges.lastElementChild.classList.add('device-library-recognition');
}
function deviceFacts(items, className = '') {
  const facts = document.createElement('dl');
  facts.className = `device-library-facts ${className}`.trim();
  for (const [label, value] of items) {
    const fact = document.createElement('div');
    fact.append(text('dt', label), text('dd', value));
    facts.append(fact);
  }
  return facts;
}
function deviceRow(item) {
  const key = item.device_key;
  const li = document.createElement('li');
  li.className = 'device-library-card';
  li.dataset.deviceKey = key;
  const name = item.display_name || 'Unnamed device';
  const heading = text('h3', name);
  heading.tabIndex = -1;
  const badges = text('div', '', 'device-library-badges');
  const primary = text('header', '', 'device-library-primary');
  primary.append(heading, badges);
  li.append(primary, text('p', 'Recorded in saved scans · current connection status is unknown', 'device-library-recorded'));
  if (item.identity_note) li.append(text('p', item.identity_note, 'field-hint'));
  li.append(deviceFacts([
    ['Last recorded check', recordedTimeLabel(item.last_observed)],
    ['Review items in latest report', String(item.review_count)],
    ['Unfinished checks in latest report', String(item.unfinished_count)],
  ], 'device-library-check-summary'));
  const reports = document.createElement('details');
  reports.className = 'device-library-history';
  reports.append(text('summary', 'Saved check details and reports'));
  reports.append(text('p', 'These links open saved results without running a scan. Dates cover the saved reports included here, not the device’s whole history.', 'field-hint'));
  reports.append(deviceFacts([
    ['Last recorded address', item.last_ip || 'Not recorded'],
    ['Recorded network', item.network || 'Not recorded'],
    ['First recorded observation', recordedTimeLabel(item.first_observed)],
    ['Saved reports in this inventory', String(item.report_count)],
  ]));
  const links = document.createElement('ol');
  links.className = 'device-library-report-links';
  const states = { completed: 'Finished', partial: 'Some checks unfinished', failed: 'Failed', cancelled: 'Cancelled' };
  item.reports.forEach((report, index) => {
    const entry = document.createElement('li');
    const link = text('a', `Saved report ${index + 1}: ${recordedTimeLabel(report.created_at)} · ${states[report.state]}`);
    link.href = deviceReportHref(report);
    entry.append(link);
    links.append(entry);
  });
  reports.append(links);
  if (!item.reports.length) reports.append(text('p', 'No readable report links were included. Reload the list to check again.'));
  if (item.report_count > item.reports.length) reports.append(text('p', `${item.reports.length} recent report links shown here, from ${item.report_count} included saved reports. Find older reports in Saved reports.`, 'field-hint'));

  const editor = document.createElement('details');
  editor.className = 'device-library-editor';
  editor.append(text('summary', 'Your household labels'));
  const form = document.createElement('form');
  form.noValidate = true;
  const fieldset = document.createElement('fieldset');
  fieldset.append(text('legend', `Household labels for ${name}`));
  const help = text('p', 'Room, favourite and recognition are your labels. Recognised does not mean verified or safe. Saving does not change scan facts or start a scan.', 'field-hint');
  help.id = `label-help-${key}`;
  fieldset.setAttribute('aria-describedby', help.id);
  fieldset.append(help);
  const saved = text('p', '', 'device-library-saved-labels');
  saved.id = `saved-labels-${key}`;
  fieldset.append(saved);
  if (!item.editable) fieldset.append(text('p', 'Household label editing is unavailable. Recorded observations remain readable; reload saved labels after the local label problem is resolved.', 'field-hint'));
  const field = text('div', '', 'form-field');
  const roomLabel = text('label', 'Your room or location');
  const room = document.createElement('input');
  room.id = `room-${key}`;
  room.type = 'text';
  room.maxLength = DEVICE_ROOM_LIMIT;
  room.autocomplete = 'off';
  roomLabel.htmlFor = room.id;
  field.append(roomLabel, room);
  fieldset.append(field);
  const checkbox = (label, suffix) => {
    const choice = text('label', '', 'device-library-check');
    const input = document.createElement('input');
    input.type = 'checkbox';
    input.id = `${suffix}-${key}`;
    choice.htmlFor = input.id;
    choice.append(input, text('span', label));
    fieldset.append(choice);
    return input;
  };
  const favourite = checkbox('Keep as my favourite', 'favourite');
  const recognised = checkbox('I recognise this device (my label, not a safety check)', 'recognised');
  const status = text('p', '', 'status-message');
  status.id = `label-status-${key}`;
  // Outcomes deliberately move focus here after Save becomes disabled. Do not
  // also make this a live region, which can announce the same outcome twice.
  status.tabIndex = -1;
  room.setAttribute('aria-describedby', `${help.id} ${status.id}`);
  const actions = text('div', '', 'form-actions');
  const save = text('button', 'Save my labels', 'primary-button');
  save.type = 'submit';
  const discard = text('button', 'Discard this draft', 'secondary-button');
  discard.type = 'button';
  const reload = text('button', 'Reload saved labels, keep draft', 'secondary-button');
  reload.type = 'button';
  reload.hidden = true;
  actions.append(save, discard, reload);
  fieldset.append(actions);
  form.append(fieldset, status);
  editor.append(form);
  li.append(editor, reports);
  const row = { li, editor, fieldset, room, favourite, recognised, status, save, discard, reload, saved, badges, invalid: false };
  rows.set(key, row);
  fill(row, item.draft);
  updateSaved(row, item);
  const draftChanged = () => {
    row.invalid = !validDeviceLabels(values(row));
    if (row.invalid) {
      library.change(key, values(row));
      room.setAttribute('aria-invalid', 'true');
      status.textContent = 'Use up to 80 printable characters on one line for your room label.';
      save.disabled = true;
      return false;
    }
    room.removeAttribute('aria-invalid');
    status.textContent = '';
    return library.change(key, values(row));
  };
  room.addEventListener('input', draftChanged);
  favourite.addEventListener('change', draftChanged);
  recognised.addEventListener('change', draftChanged);
  discard.addEventListener('click', () => {
    library.discard(key);
    status.textContent = 'Draft discarded. Your saved labels are shown.';
    status.focus({ preventScroll: true });
  });
  reload.addEventListener('click', () => void loadPage(library.getState().search, currentPage(), { focusKey: key }));
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!draftChanged()) { if (row.invalid) room.focus(); return; }
    await library.save(key);
  });
  return li;
}
function currentPage(state = library.getState()) { return Math.floor(state.offset / DEVICE_PAGE_SIZE) + 1; }
function pagination(state) {
  const pages = Math.ceil((state.total || 0) / DEVICE_PAGE_SIZE);
  const current = currentPage(state);
  const numbers = [...new Set([1, pages, current - 1, current, current + 1])].filter(page => page >= 1 && page <= pages).sort((a, b) => a - b);
  for (const id of ['pages', 'pages-bottom']) {
    const nav = get(id);
    nav.hidden = pages <= 1;
    const signature = `${current}:${pages}`;
    if (nav.dataset.signature !== signature) {
      nav.dataset.signature = signature;
      const controls = [];
      const add = (page, name) => {
        const button = text('button', name, 'secondary-button');
        button.type = 'button';
        button.setAttribute('aria-label', name === String(page) ? `Page ${page}` : `${name} page`);
        if (page === current && name === String(page)) button.setAttribute('aria-current', 'page');
        button.addEventListener('click', () => void loadPage(library.getState().search, page, { focus: true }));
        controls.push(button);
      };
      if (current > 1) add(current - 1, 'Previous');
      let previous = 0;
      for (const page of numbers) {
        if (previous && page > previous + 1) { const gap = text('span', '…'); gap.setAttribute('aria-hidden', 'true'); controls.push(gap); }
        add(page, String(page)); previous = page;
      }
      if (current < pages) add(current + 1, 'Next');
      nav.replaceChildren(...controls);
    }
    nav.querySelectorAll('button').forEach(button => { button.disabled = state.busy || Boolean(state.savingKey); });
  }
}
function render(state) {
  if (state.render === 'replace') {
    rows.clear();
    get('list').replaceChildren(...state.items.map(deviceRow));
  }
  const locked = state.busy || Boolean(state.savingKey);
  get('list').setAttribute('aria-busy', String(locked));
  get('search').querySelectorAll('button').forEach(button => { button.disabled = locked; });
  get('query').disabled = Boolean(state.savingKey);
  get('view').disabled = Boolean(state.savingKey);
  get('retry').disabled = locked;
  get('error').hidden = state.phase !== 'error';
  get('error-message').textContent = state.phase === 'error' ? `${state.error} ${state.items.length ? 'The previously loaded devices are still available.' : ''}` : '';
  get('warnings').textContent = state.warnings.join(' ');
  get('warnings').hidden = !state.warnings.length;
  get('applied').textContent = `Applied view: ${DEVICE_VIEWS[state.view]}.${state.search ? ` Search: ${state.search}.` : ''} Search and view apply to all saved devices included here, not just this page. Favourites appear first, then the latest saved checks.`;
  get('drafts').textContent = state.draftCount ? `${state.draftCount} unsaved device label${state.draftCount === 1 ? '' : 's'}. Drafts are kept while this page stays open, including when you change device pages.` : '';
  const empty = state.phase === 'ready' && state.total === 0;
  get('empty').hidden = !empty;
  const filtered = Boolean(state.search) || state.view !== 'all';
  get('empty-title').textContent = filtered ? 'No saved devices match this search and view' : 'No saved devices yet';
  get('empty-help').textContent = filtered ? 'Reset search and view to see all saved devices. A missing match does not mean a device is disconnected or safe.' : 'Devices from finished scans will be listed here. This saved list cannot show which devices are connected now.';
  get('start').hidden = filtered;
  if (state.busy) get('status').textContent = 'Loading saved devices…';
  else if (state.phase === 'error') get('status').textContent = 'The requested device list could not be loaded. Use Retry loading devices.';
  else if (state.total !== null) get('status').textContent = state.total ? `Page ${currentPage(state)} of ${Math.ceil(state.total / DEVICE_PAGE_SIZE)}: ${state.items.length} devices on this page; ${state.total} matching saved devices.` : filtered ? 'No devices match the applied search and view.' : 'No saved devices are available.';
  for (const item of state.items) {
    const row = rows.get(item.device_key);
    if (!row) continue;
    row.fieldset.disabled = locked || !item.editable;
    row.save.disabled = locked || !item.editable || !item.dirty || state.needsReload || row.invalid;
    row.save.textContent = state.savingKey === item.device_key ? 'Saving…' : 'Save my labels';
    if (state.savingKey === item.device_key) row.status.textContent = 'Saving your household labels…';
    row.discard.disabled = locked || !item.dirty;
    row.reload.hidden = !state.needsReload;
    row.reload.disabled = locked;
    if (state.render === 'discard' && state.key === item.device_key) fill(row, item.draft);
    if (state.render === 'saved' && state.key === item.device_key) {
      fill(row, item.draft); updateSaved(row, item);
      row.status.textContent = 'Your labels are saved. They do not change the scan results. Reload the list to update its order or view.';
      row.status.focus({ preventScroll: true });
    }
    if (state.render === 'save-error' && state.key === item.device_key) {
      row.status.textContent = state.error;
      row.status.focus({ preventScroll: true });
    }
  }
  pagination(state);
  if (state.total !== null) document.title = `My devices (page ${currentPage(state)} of ${Math.max(1, Math.ceil(state.total / DEVICE_PAGE_SIZE))}) · NetGuard AI`;
}
const library = createDeviceLibrary({ request, onChange: render });
async function loadPage(search, page, { focus = false, focusKey = null, view = library.getState().view } = {}) {
  lastRequested = { search, page, view };
  const loaded = await library.load(search, page, view);
  if (!loaded) { if (library.getState().phase === 'error') get('error').focus({ preventScroll: true }); return; }
  if (focusKey) {
    const row = rows.get(focusKey);
    if (row) {
      row.editor.open = true;
      row.status.textContent = 'Latest saved labels loaded. Your remaining draft is kept; compare the saved labels before saving again.';
      row.status.focus({ preventScroll: true });
    } else { get('heading').focus(); }
  } else if (focus) {
    rememberedDeviceKey = null;
    get('heading').focus(); get('heading').scrollIntoView({ block: 'start', behavior: 'instant' });
  }
  rememberContext();
}
function rememberContext(preferredKey = null) {
  const state = library.getState();
  if (restoringContext || state.total === null) return;
  // Pointer navigation need not focus an anchor (notably in WebKit). Save the
  // clicked card explicitly and retain it through pagehide, which may have BODY
  // as its active element. Never retain a key outside the current visible page.
  const activeKey = typeof preferredKey === 'string' ? preferredKey
    : document.activeElement?.closest?.('.device-library-card')?.dataset.deviceKey || rememberedDeviceKey;
  rememberedDeviceKey = rows.has(activeKey) ? activeKey : null;
  readingContext.save({ search: state.search, view: state.view, page: currentPage(state),
    y: Math.max(0, window.scrollY || 0), focusKey: rememberedDeviceKey });
}
get('search').addEventListener('submit', event => { event.preventDefault(); void loadPage(get('query').value, 1, { focus: true, view: get('view').value }); });
get('search').addEventListener('reset', event => {
  if (library.getState().savingKey) { event.preventDefault(); return; }
  window.setTimeout(() => void loadPage('', 1, { focus: true, view: 'all' }), 0);
});
get('reload').addEventListener('click', () => void loadPage(library.getState().search, currentPage()));
get('retry').addEventListener('click', () => void loadPage(lastRequested.search, lastRequested.page, { focus: true, view: lastRequested.view }));
window.addEventListener('beforeunload', event => {
  if (library.getState().draftCount) { event.preventDefault(); event.returnValue = ''; }
});
window.addEventListener('pagehide', rememberContext);
get('list').addEventListener('click', event => {
  const link = event.target.closest('a');
  if (link) rememberContext(link.closest('.device-library-card')?.dataset.deviceKey);
});
async function initialise() {
  get('query').value = savedContext?.search || '';
  get('view').value = savedContext?.view || 'all';
  await loadPage(savedContext?.search || '', savedContext?.page || 1, { view: savedContext?.view || 'all' });
  window.requestAnimationFrame(() => {
    const state = library.getState();
    if (savedContext && !userInteracted && state.phase === 'ready' && !window.location.hash) {
      const row = rows.get(savedContext.focusKey);
      window.scrollTo({ top: savedContext.y, behavior: 'instant' });
      if (row) {
        const heading = row.li.querySelector('h3');
        heading.focus({ preventScroll: true });
        const bounds = heading.getBoundingClientRect();
        if (bounds.top < 0 || bounds.bottom > window.innerHeight) heading.scrollIntoView({ block: 'nearest', behavior: 'instant' });
      }
    }
    restoringContext = false;
    rememberContext();
  });
}
void initialise();
