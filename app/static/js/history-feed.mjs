const FILTER_FIELDS = ['q', 'profile', 'state', 'after', 'before'];

function submittedFilters(input = {}) {
  return Object.fromEntries(FILTER_FIELDS.map(key => [key, String(input[key] || '').trim()])
    .filter(([, value]) => value));
}

/** Start empty; each explicit demand reads at most one report. No automatic loads. */
export function createHistoryFeed({ request, onChange, limit = 1 }) {
  if (limit !== 1) throw new TypeError('History reveals exactly one report at a time');
  let generation = 0;
  let failedRequest = null;
  let state = { items: [], offset: 0, total: null, filters: {}, busy: false, phase: 'idle',
    hasMore: false, warnings: [], unreadableCount: 0, error: '', retryMode: null, changed: false };

  function publish(changes, render = 'none', added = []) {
    state = { ...state, ...changes };
    onChange({ ...state, render, added });
  }

  function reset(filters = {}) {
    generation += 1;
    failedRequest = null;
    publish({ items: [], offset: 0, total: null, filters: submittedFilters(filters), busy: false,
      phase: 'waiting', hasMore: true, warnings: [], unreadableCount: 0, error: '',
      retryMode: null, changed: false }, 'replace');
  }

  async function load(filters = state.filters) {
    if (state.busy) return false;
    const current = ++generation;
    const snapshot = submittedFilters(filters);
    const offset = state.offset;
    failedRequest = null;
    publish({ busy: true, phase: 'loading', error: '', retryMode: null,
      filters: snapshot, hasMore: false });
    try {
      const params = new URLSearchParams({ ...snapshot, offset, limit });
      const page = await request(`/api/reports?${params}`);
      if (current !== generation) return false;
      if (!Array.isArray(page?.items) || page.items.length > limit
        || !Number.isInteger(page.total) || page.total < 0
        || page.items.some(item => !item || typeof item.scan_id !== 'string')) {
        throw new Error('The saved report list could not be read.');
      }
      const items = [...state.items];
      const seen = new Set(items.map(item => item.scan_id));
      const added = page.items.filter(item => {
        if (seen.has(item.scan_id)) return false;
        seen.add(item.scan_id);
        return true;
      });
      items.push(...added);
      const nextOffset = offset + page.items.length;
      const changed = state.changed || added.length < page.items.length
        || (state.total !== null && page.total !== state.total)
        || (page.items.length === 0 && offset < page.total);
      const warnings = new Set(state.warnings);
      for (const warning of page.warnings || []) if (typeof warning === 'string') warnings.add(warning);
      if (changed) warnings.add('The saved report list changed while you were browsing. Use Search reports to refresh it.');
      publish({ items, offset: nextOffset, total: page.total, filters: snapshot, busy: false,
        phase: 'ready', hasMore: page.items.length > 0 && nextOffset < page.total,
        warnings: [...warnings], unreadableCount: page.unreadable_count || 0,
        error: '', retryMode: null, changed }, 'append', added);
      return true;
    } catch (error) {
      if (current !== generation) return false;
      failedRequest = { filters: snapshot };
      publish({ busy: false, phase: 'error', hasMore: false, retryMode: 'append',
        error: error instanceof Error ? error.message : 'Saved reports could not be loaded.' });
      return false;
    }
  }

  return {
    reset,
    more: () => state.hasMore && !state.busy ? load() : Promise.resolve(false),
    retry: () => failedRequest ? load(failedRequest.filters) : Promise.resolve(false),
    getState: () => ({ ...state, filters: { ...state.filters }, items: [...state.items], warnings: [...state.warnings] }),
  };
}
