import { validReportDeviceId } from './report-device-context.mjs?v=20261015-inclusive';

export const DEVICE_PAGE_SIZE = 24;
export const DEVICE_ROOM_LIMIT = 80;
export const DEVICE_VIEWS = Object.freeze({ all: 'All devices', favourites: 'My favourites',
  'not-recognised': 'Not marked recognised by me', unfinished: 'With unfinished checks', review: 'With items to review' });
const validView = value => typeof value === 'string' && Object.hasOwn(DEVICE_VIEWS, value);
const deviceKey = /^d-[a-f0-9]{64}$/;
const scanId = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/;
const count = value => Number.isSafeInteger(value) && value >= 0;
const label = (value, limit) => typeof value === 'string' && value.length <= limit;
const same = (left, right) => left.room === right.room && left.favourite === right.favourite
  && left.recognised === right.recognised;

/** Read-only report navigation, never an API request or authority to scan. */
export function deviceReportHref(report) {
  if (!report || typeof report.scan_id !== 'string' || !scanId.test(report.scan_id)) return null;
  const path = `/scans/${encodeURIComponent(report.scan_id)}`;
  if (!validReportDeviceId(report.device_id)) return path;
  const query = new URLSearchParams({ device: report.device_id });
  return `${path}?${query}#devices-title`;
}

export function validDeviceLabels(value) {
  return value && label(value.room, DEVICE_ROOM_LIMIT) && !/[\p{Cc}\p{Cf}\p{Zl}\p{Zp}]/u.test(value.room)
    && typeof value.favourite === 'boolean' && typeof value.recognised === 'boolean';
}

export function validateDevicePage(value) {
  if (!value || !Array.isArray(value.items) || value.items.length > DEVICE_PAGE_SIZE
    || !count(value.total) || value.items.length > value.total || !count(value.offset)
    || !(value.view === undefined || validView(value.view))
    || value.offset % DEVICE_PAGE_SIZE !== 0 || value.limit !== DEVICE_PAGE_SIZE
    || !(value.revision === null || (Number.isSafeInteger(value.revision) && value.revision >= 1))
    || !Array.isArray(value.warnings) || value.warnings.some(item => !label(item, 4000))) {
    throw new Error('The saved device list could not be read. Existing observations are unchanged.');
  }
  const seen = new Set();
  for (const item of value.items) {
    if (!item || !deviceKey.test(item.device_key) || seen.has(item.device_key)
      || !label(item.display_name, 500) || !label(item.last_ip, 128)
      || !(item.network === null || label(item.network, 128))
      || ![item.first_observed, item.last_observed].every(time => time === null || label(time, 64))
      || ![item.report_count, item.review_count, item.unfinished_count].every(count)
      || !validDeviceLabels(item.annotations) || typeof item.editable !== 'boolean'
      || !(item.identity_note === undefined || label(item.identity_note, 500))
      || (value.revision === null && item.editable)
      || !Array.isArray(item.reports) || item.reports.length > DEVICE_PAGE_SIZE
      || item.reports.some(report => !report || !scanId.test(report.scan_id)
        || !(report.device_id === null || label(report.device_id, 200)) || !label(report.created_at, 64)
        || !['completed', 'partial', 'failed', 'cancelled'].includes(report.state))) {
      throw new Error('The saved device list could not be read. Existing observations are unchanged.');
    }
    seen.add(item.device_key);
  }
  return value;
}

/** Recorded evidence stays separate from drafts and user-entered labels. */
export function createDeviceLibrary({ request, onChange = () => {} }) {
  let generation = 0;
  const drafts = new Map();
  let state = { items: [], total: null, offset: 0, search: '', view: 'all', revision: null,
    busy: false, savingKey: null, needsReload: false, warnings: [], error: '', phase: 'idle' };
  function snapshot() {
    return { ...state, warnings: [...state.warnings], draftCount: drafts.size,
      items: state.items.map(item => ({ ...item, annotations: { ...item.annotations },
        draft: { ...(drafts.get(item.device_key) || item.annotations) },
        dirty: drafts.has(item.device_key) })) };
  }
  function publish(changes = {}, render = 'none', key = null) {
    state = { ...state, ...changes };
    onChange({ ...snapshot(), render, key });
  }
  function reconcileDrafts() {
    for (const item of state.items) {
      if (drafts.has(item.device_key) && same(drafts.get(item.device_key), item.annotations)) {
        drafts.delete(item.device_key);
      }
    }
  }
  async function load(search = state.search, page = Math.floor(state.offset / DEVICE_PAGE_SIZE) + 1, view = state.view) {
    if (state.savingKey) return false;
    const query = String(search || '').trim();
    if (!validView(view) || query.length > 120 || !Number.isSafeInteger(page) || page < 1
      || !Number.isSafeInteger((page - 1) * DEVICE_PAGE_SIZE)) return false;
    const current = ++generation;
    publish({ busy: true, phase: 'loading', error: '' });
    try {
      let offset = (page - 1) * DEVICE_PAGE_SIZE;
      let response;
      for (let correction = 0; correction <= 1; correction += 1) {
        const params = new URLSearchParams({ offset, limit: DEVICE_PAGE_SIZE });
        if (query) params.set('search', query);
        if (view !== 'all') params.set('view', view);
        response = validateDevicePage(await request(`/api/devices?${params}`));
        if (current !== generation) return false;
        if ((response.view ?? 'all') !== view) throw new Error('The running backend did not confirm this device view. Let active scans finish, restart the backend task and reload this page. Your saved observations are unchanged.');
        if (response.offset !== offset) throw new Error('The device page changed unexpectedly. Reload the list.');
        if (offset > 0 && offset >= response.total) {
          if (correction === 1) throw new Error('The saved device list changed again. Please retry.');
          offset = Math.max(0, (Math.ceil(response.total / DEVICE_PAGE_SIZE) - 1) * DEVICE_PAGE_SIZE);
          continue;
        }
        break;
      }
      state = { ...state, items: response.items.map(item => ({ ...item,
        annotations: { ...item.annotations }, reports: item.reports.map(report => ({ ...report })) })) };
      reconcileDrafts();
      publish({ total: response.total, offset, search: query, view, revision: response.revision,
        warnings: response.warnings, busy: false, phase: 'ready', error: '', needsReload: false }, 'replace');
      return true;
    } catch (error) {
      if (current !== generation) return false;
      const message = error.status === 404 ? 'The running backend does not provide the saved-device API. Let active scans finish, restart the backend task and reload this page. Saved reports are unchanged.' : error.message;
      publish({ busy: false, phase: 'error', error: message || 'Saved devices are unavailable.' });
      return false;
    }
  }
  function change(key, value) {
    const item = state.items.find(item => item.device_key === key);
    // Keep invalid room drafts too; validation must not erase entered text.
    if (!item?.editable || state.busy || state.savingKey || !value
      || !label(value.room, DEVICE_ROOM_LIMIT) || typeof value.favourite !== 'boolean'
      || typeof value.recognised !== 'boolean') return false;
    if (same(value, item.annotations)) drafts.delete(key);
    else drafts.set(key, { room: value.room, favourite: value.favourite, recognised: value.recognised });
    publish({}, 'draft', key);
    return true;
  }
  function discard(key) {
    if (state.busy || state.savingKey) return false;
    drafts.delete(key);
    publish({}, 'discard', key);
    return true;
  }
  async function save(key) {
    const item = state.items.find(item => item.device_key === key);
    const draft = drafts.get(key);
    if (!item?.editable || !draft || state.busy || state.savingKey || state.needsReload
      || state.revision === null || !validDeviceLabels(draft)) return false;
    const expectedRevision = state.revision;
    const annotations = { ...draft, room: draft.room.trim() };
    publish({ savingKey: key, error: '' });
    try {
      const response = await request(`/api/devices/${encodeURIComponent(key)}`, {
        method: 'PUT', body: JSON.stringify({ expected_revision: expectedRevision, ...annotations }),
      });
      if (!response || response.device_key !== key || response.editable !== true
        || !Number.isSafeInteger(response.revision) || response.revision <= expectedRevision
        || !validDeviceLabels(response.annotations) || !same(response.annotations, annotations)) {
        throw new Error('The save response could not be read. Reload saved labels to check the outcome before saving again.');
      }
      item.annotations = { ...response.annotations };
      drafts.delete(key);
      publish({ revision: response.revision, savingKey: null }, 'saved', key);
      return true;
    } catch (error) {
      // A write may have succeeded before an interrupted response; never repeat it automatically.
      publish({ savingKey: null, needsReload: true,
        error: `${error.message || 'Labels could not be saved.'} Your draft is kept. Reload saved labels to check the latest values before trying again.` }, 'save-error', key);
      return false;
    }
  }
  return { load, change, discard, save, getState: snapshot };
}
