const FILTER_FIELDS = ['q', 'profile', 'state', 'after', 'before'];
export const HISTORY_PAGE_SIZE = 24;

function submittedFilters(input = {}) {
  return Object.fromEntries(FILTER_FIELDS.map(key => [key, String(input[key] || '').trim()])
    .filter(([, value]) => value));
}

/** Start empty. Fetch one bounded page on demand; reveal its reports one by one. */
export function createHistoryFeed({ request, onChange, pageSize = HISTORY_PAGE_SIZE }) {
  if (pageSize !== HISTORY_PAGE_SIZE) throw new TypeError('History pages contain at most 24 reports');
  let generation = 0;
  let failedRequest = null;
  let state = { items: [], pageItems: [], page: 1, pageSize, pageCount: 0,
    revealedCount: 0, offset: 0, pageEndOffset: 0, total: null, filters: {}, busy: false,
    phase: 'idle', hasMore: false, hasMoreWithinPage: false, warnings: [],
    unreadableCount: 0, error: '', retryMode: null, changed: false, loadingPage: null };

  function snapshot() {
    return { ...state, filters: { ...state.filters }, items: [...state.items],
      pageItems: [...state.pageItems], warnings: [...state.warnings] };
  }

  function publish(changes, render = 'none', added = []) {
    state = { ...state, ...changes };
    onChange({ ...snapshot(), render, added });
  }

  function reset(filters = {}, page = 1) {
    generation += 1;
    failedRequest = null;
    publish({ items: [], pageItems: [], page: Number.isSafeInteger(page) && page > 0 ? page : 1, pageCount: 0, revealedCount: 0,
      offset: 0, pageEndOffset: 0, total: null, filters: submittedFilters(filters), busy: false,
      phase: 'waiting', hasMore: true, hasMoreWithinPage: false, warnings: [],
      unreadableCount: 0, error: '', retryMode: null, changed: false, loadingPage: null }, 'replace');
  }

  async function loadPage(targetPage, revealCount = 1, afterDelete = false) {
    if (state.busy) return false;
    const current = ++generation;
    const filters = submittedFilters(state.filters);
    const previousTotal = state.total;
    failedRequest = null;
    publish({ busy: true, phase: 'loading', error: '', retryMode: null, loadingPage: targetPage,
      hasMore: false, hasMoreWithinPage: false });
    try {
      let requestedPage = targetPage;
      // A deletion or concurrent library change can invalidate the current last page.
      // Correct once, never recursively chase a continuously changing library.
      for (let correction = 0; correction <= 1; correction += 1) {
        const offset = (requestedPage - 1) * pageSize;
        const params = new URLSearchParams({ ...filters, offset, limit: pageSize });
        const response = await request(`/api/reports?${params}`);
        if (current !== generation) return false;
        if (!Array.isArray(response?.items) || response.items.length > pageSize
          || !Number.isSafeInteger(response.total) || response.total < 0
          || response.items.length > response.total
          || (response.warnings !== undefined && !Array.isArray(response.warnings))
          || response.items.some(item => !item || typeof item.scan_id !== 'string' || !item.scan_id)) {
          throw new Error('The saved report list could not be read.');
        }
        const pageCount = Math.ceil(response.total / pageSize);
        const lastPage = Math.max(1, pageCount);
        if (requestedPage > lastPage && response.total > 0) {
          if (correction === 1) throw new Error('The saved report list changed again. Please retry loading reports.');
          requestedPage = lastPage;
          publish({ loadingPage: requestedPage });
          continue;
        }
        if (response.total === 0) requestedPage = 1;
        const seen = new Set();
        const pageItems = response.items.filter(item => {
          if (seen.has(item.scan_id)) return false;
          seen.add(item.scan_id);
          return true;
        });
        const items = pageItems.slice(0, Math.max(1, Math.min(pageSize, revealCount)));
        const expectedCount = Math.max(0, Math.min(pageSize, response.total - offset));
        const changed = pageItems.length !== response.items.length
          || response.items.length !== expectedCount
          || (!afterDelete && previousTotal !== null && response.total !== previousTotal);
        const warnings = new Set((response.warnings || []).filter(warning => typeof warning === 'string'));
        if (changed) warnings.add('The saved report list changed while you were browsing. Search again to refresh it.');
        const hasMore = items.length < pageItems.length;
        publish({ items, pageItems, page: requestedPage, pageCount, revealedCount: items.length,
          offset: (requestedPage - 1) * pageSize,
          pageEndOffset: (requestedPage - 1) * pageSize + response.items.length,
          total: response.total, filters, busy: false, phase: 'ready', hasMore,
          hasMoreWithinPage: hasMore, warnings: [...warnings],
          unreadableCount: response.unreadable_count || 0, error: '', retryMode: null,
          changed, loadingPage: null }, 'replace', items);
        return true;
      }
      return false;
    } catch (error) {
      if (current !== generation) return false;
      failedRequest = { targetPage, revealCount, afterDelete };
      publish({ busy: false, phase: 'error', hasMore: false, hasMoreWithinPage: false,
        retryMode: 'page', loadingPage: null,
        error: error instanceof Error ? error.message : 'Saved reports could not be loaded.' });
      return false;
    }
  }

  function reveal() {
    if (state.busy || !state.hasMore) return Promise.resolve(false);
    if (state.phase === 'waiting') return loadPage(state.page);
    const added = state.pageItems.slice(state.revealedCount, state.revealedCount + 1);
    if (!added.length) return Promise.resolve(false);
    const items = [...state.items, ...added];
    const hasMore = items.length < state.pageItems.length;
    publish({ items, revealedCount: items.length, hasMore, hasMoreWithinPage: hasMore }, 'append', added);
    return Promise.resolve(true);
  }

  function goToPage(page) {
    if (!Number.isSafeInteger(page) || page < 1 || !Number.isSafeInteger((page - 1) * pageSize)
      || state.busy) return Promise.resolve(false);
    if (state.total !== null && page > Math.max(1, state.pageCount)) return Promise.resolve(false);
    if (page === state.page && state.phase === 'ready') return Promise.resolve(false);
    return loadPage(page);
  }

  function reloadAfterDelete() {
    // Keep the initial zero-report view if deletion was triggered from elsewhere.
    if (state.total === null && state.phase === 'waiting') return Promise.resolve(false);
    const page = state.page;
    const count = Math.max(1, state.revealedCount);
    generation += 1;
    state = { ...state, busy: false };
    return loadPage(page, count, true);
  }

  return {
    reset,
    more: reveal,
    reveal,
    goToPage,
    reloadAfterDelete,
    retry: () => failedRequest
      ? loadPage(failedRequest.targetPage, failedRequest.revealCount, failedRequest.afterDelete)
      : Promise.resolve(false),
    getState: snapshot,
  };
}
