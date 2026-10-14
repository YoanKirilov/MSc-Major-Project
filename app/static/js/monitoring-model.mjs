const uuid = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/;
const string = (value, max) => typeof value === 'string' && value.length <= max;
const optional = (value, max) => value === null || string(value, max);
const interval = value => Number.isSafeInteger(value) && value >= 30 && value <= 1440;
const count = value => Number.isSafeInteger(value) && value >= 0;
const outcome = value => value === null || ['queued', 'completed', 'partial', 'failed', 'cancelled', 'unavailable'].includes(value);
const countFields = ['device_count', 'finding_count', 'completed_count', 'unfinished_count', 'comparable_device_count', 'changed_device_count'];

export function boundedPrivateScope(value) {
  if (!string(value, 18)) return false;
  const match = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\/(\d{1,2})$/.exec(value);
  if (!match || match.slice(1).some(part => String(Number(part)) !== part)) return false;
  const numbers = match.slice(1).map(Number);
  const [a, b, , d, prefix] = numbers;
  return numbers.slice(0, 4).every(part => part <= 255) && prefix >= 24 && prefix <= 32
    && (a === 10 || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168))
    && d % (2 ** (32 - prefix)) === 0;
}

export function validateMonitoringStatus(value) {
  if (!value || !(value.revision === null || (Number.isSafeInteger(value.revision) && value.revision >= 1))
    || typeof value.enabled !== 'boolean' || typeof value.available !== 'boolean'
    || !optional(value.scope, 128) || !optional(value.current_scope, 128) || !interval(value.interval_minutes)
    || !optional(value.next_check_at, 64) || !(value.last_scan_id === null || uuid.test(value.last_scan_id))
    || !outcome(value.last_outcome) || !optional(value.pause_reason, 100)
    || !optional(value.configuration_error, 4000) || !Array.isArray(value.events) || value.events.length > 100
    || (value.enabled && (!boundedPrivateScope(value.scope) || !value.next_check_at || value.pause_reason !== null))
    || (!value.enabled && value.next_check_at !== null)
    || value.events.some(event => !event || !uuid.test(event.event_id) || !string(event.occurred_at, 64)
      || !string(event.kind, 100) || !string(event.message, 4000)
      || !(event.scan_id === null || uuid.test(event.scan_id)) || !optional(event.outcome, 100)
      || !(event.counts === null || (typeof event.counts === 'object'
        && countFields.every(field => event.counts[field] === undefined || count(event.counts[field])))))) {
    throw new Error('The periodic-check status could not be read. Reload status before changing it.');
  }
  return value;
}

export function intervalLabel(minutes) {
  return ({ 30: '30 minutes', 60: '1 hour', 360: '6 hours', 1440: '24 hours' })[minutes] || `${minutes} minutes`;
}

/** Permission is current-page intent, never persisted or inferred from an interval. */
export function createMonitoringModel({ request, onChange = () => {} }) {
  let generation = 0;
  let state = { status: null, draftInterval: 60, intervalDirty: false, authorised: false,
    confirmedScope: null, loading: false, saving: false, needsReload: false,
    scopeInvalidated: false, error: '', notice: '' };
  function snapshot() {
    const known = state.status && state.status.revision !== null;
    const idle = !state.loading && !state.saving && !state.needsReload;
    return { ...state, status: state.status ? { ...state.status, events: state.status.events.map(event => ({
      ...event, counts: event.counts ? { ...event.counts } : null,
    })) } : null,
    canAuthorise: Boolean(known && idle && state.status.available && boundedPrivateScope(state.status.current_scope) && !state.scopeInvalidated),
    canEnable: Boolean(known && idle && state.status.available && boundedPrivateScope(state.status.current_scope)
      && !state.scopeInvalidated && state.authorised && state.confirmedScope === state.status.current_scope),
    canStop: Boolean(known && idle && state.status.enabled) };
  }
  function publish(changes = {}, action = 'none') {
    state = { ...state, ...changes };
    onChange({ ...snapshot(), action });
  }
  function adopt(response, keepDraft = true) {
    const draftInterval = keepDraft && state.intervalDirty ? state.draftInterval : response.interval_minutes;
    publish({ status: response, draftInterval, intervalDirty: draftInterval !== response.interval_minutes,
      authorised: false, confirmedScope: null, loading: false, saving: false,
      needsReload: false, scopeInvalidated: false, error: '' }, 'loaded');
  }
  async function load() {
    if (state.saving) return false;
    const current = ++generation;
    publish({ loading: true, authorised: false, confirmedScope: null, scopeInvalidated: true, error: '', notice: '' });
    try {
      const response = validateMonitoringStatus(await request('/api/monitoring'));
      if (current !== generation) return false;
      adopt(response);
      return true;
    } catch (error) {
      if (current !== generation) return false;
      publish({ loading: false, error: `${error.message || 'Status is unavailable.'} No change was made by this reload.` }, 'load-error');
      return false;
    }
  }
  function chooseInterval(value) {
    if (state.saving || state.loading || !interval(Number(value))) return false;
    const draftInterval = Number(value);
    publish({ draftInterval, intervalDirty: draftInterval !== (state.status?.interval_minutes || 60), notice: '' });
    return true;
  }
  function authorise(value) {
    if (value && !snapshot().canAuthorise) return false;
    publish({ authorised: Boolean(value), confirmedScope: value ? state.status.current_scope : null, notice: '' });
    return true;
  }
  function invalidateScope() {
    publish({ authorised: false, confirmedScope: null, scopeInvalidated: true,
      notice: 'Network settings were edited here. Save or discard them, then reload periodic-check status before authorising the displayed network.' });
  }
  async function update(enabled) {
    if (enabled ? !snapshot().canEnable : !snapshot().canStop) return false;
    const previous = state.status;
    const payload = { expected_revision: previous.revision, enabled,
      authorised: enabled, confirmed_scope: enabled ? state.confirmedScope : previous.current_scope,
      interval_minutes: enabled ? state.draftInterval : previous.interval_minutes };
    ++generation;
    publish({ saving: true, authorised: false, confirmedScope: null, error: '', notice: '' });
    try {
      const response = validateMonitoringStatus(await request('/api/monitoring', {
        method: 'PUT', body: JSON.stringify(payload),
      }));
      if (response.revision === null || response.revision <= previous.revision || response.enabled !== enabled) {
        throw new Error('The change could not be confirmed from its response.');
      }
      adopt(response, !enabled);
      publish({ notice: response.enabled
        ? 'Periodic Light checks are enabled for the recorded authorised network while the app is running. Saved observations are not a security guarantee.'
        : 'Periodic checks are off. Already-running scans are not cancelled by this setting.' }, 'saved');
      return true;
    } catch (error) {
      // Configuration might have changed before the response failed; do not replay it.
      publish({ saving: false, authorised: false, confirmedScope: null, needsReload: true,
        error: `${error.message || 'The change could not be confirmed.'} Your interval draft is kept. Reload periodic-check status to check the outcome and latest saved version before trying again.` }, 'save-error');
      return false;
    }
  }
  return { load, chooseInterval, authorise, invalidateScope,
    enable: () => update(true), stop: () => update(false), getState: snapshot };
}
