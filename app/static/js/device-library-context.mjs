// Best-effort reading context only: never drafts, labels, credentials or authority.
const key = 'netguard-device-library-context-v1';
const views = new Set(['all', 'favourites', 'not-recognised', 'unfinished', 'review']);
const maxAge = 24 * 60 * 60 * 1000;
export function createDeviceContext(getStorage, now = () => Date.now()) {
  function valid(value) {
    const instant = now();
    if (!Number.isFinite(instant) || !value || value.version !== 1 || typeof value.search !== 'string' || value.search.length > 120
      || /[\p{Cc}\p{Cf}\p{Zl}\p{Zp}]/u.test(value.search) || !views.has(value.view)
      || !Number.isSafeInteger(value.page) || value.page < 1 || value.page > 1000000
      || !Number.isFinite(value.y) || value.y < 0 || value.y > 10000000
      || !Number.isFinite(value.savedAt) || value.savedAt > instant || instant - value.savedAt > maxAge
      || !(value.focusKey === null || (typeof value.focusKey === 'string' && /^d-[a-f0-9]{64}$/.test(value.focusKey)))) return null;
    return { version: 1, search: value.search, view: value.view, page: value.page,
      y: value.y, focusKey: value.focusKey, savedAt: value.savedAt };
  }
  return {
    load() {
      try {
        const raw = getStorage()?.getItem(key);
        return raw && raw.length <= 2000 ? valid(JSON.parse(raw)) : null;
      } catch { return null; }
    },
    save(value) {
      const safe = valid({ ...value, version: 1, savedAt: now() });
      if (!safe) return false;
      try {
        const storage = getStorage();
        if (!storage) return false;
        storage.setItem(key, JSON.stringify(safe));
        return true;
      } catch { return false; }
    },
  };
}
