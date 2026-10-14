import { recordedTimeLabel, recordedUtcDay } from './presentation.mjs?v=20261014-dates';

const key = 'netguard-history-context-v1';
const maxAge = 24 * 60 * 60 * 1000;
const fields = ['q', 'profile', 'state', 'after', 'before'];
export function reportIdentity(report) {
  const type = report.profile === 'deep-tcp-v1' ? 'Deep' : report.profile === 'light' ? 'Light' : 'Scan';
  const title = report.title || `${type} report`;
  const target = report.target?.cidr || report.target?.hosts?.join(', ') || 'Target not recorded';
  return `${title} · ${type} · ${recordedTimeLabel(report.created_at, 'Date unavailable')} · ${target} · reference ${report.scan_id}`;
}
export function reportDateLabel(report) {
  const day = recordedUtcDay(report.created_at);
  return `${recordedTimeLabel(report.created_at, 'Date unavailable')}${day ? ` · filter date ${day} UTC` : ''}`;
}
export function historyContext(storage, now = () => Date.now()) {
  function normalise(value) {
    const currentTime = typeof now === 'function' ? now() : now;
    if (!value || value.version !== 1 || !Number.isSafeInteger(value.page) || value.page < 1
      || value.page > 1000000 || !Number.isFinite(value.savedAt) || value.savedAt > currentTime
      || currentTime - value.savedAt > maxAge || !value.filters || typeof value.filters !== 'object') return null;
    const filters = {};
    for (const field of fields) {
      const item = value.filters[field];
      if (item === undefined || item === '') continue;
      if (typeof item !== 'string' || item.length > (field === 'q' ? 120 : 20)) return null;
      if (field === 'profile' && !['light', 'deep-tcp-v1'].includes(item)) return null;
      if (field === 'state' && !['completed', 'partial', 'failed', 'cancelled', 'running', 'queued'].includes(item)) return null;
      if (['after', 'before'].includes(field) && !/^\d{4}-\d{2}-\d{2}$/.test(item)) return null;
      filters[field] = item;
    }
    if (filters.after && filters.before && filters.after > filters.before) return null;
    return { filters, page: value.page };
  }
  return {
    read() { try { const raw = storage.getItem(key); return raw && raw.length <= 2000 ? normalise(JSON.parse(raw)) : null; } catch { return null; } },
    save(filters, page) {
      const value = { version: 1, filters, page, savedAt: typeof now === 'function' ? now() : now };
      const safe = normalise(value);
      if (!safe) return false;
      try { storage.setItem(key, JSON.stringify({ version: 1, ...safe, savedAt: value.savedAt })); return true; } catch { return false; }
    },
  };
}
