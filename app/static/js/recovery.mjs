import { reportIdentity } from './history-context.mjs?v=20261014-context';
import { recordedTimeLabel } from './presentation.mjs?v=20261014-dates';
import { validateRestoreReceipt } from './history-selection.mjs?v=20261013-management';

/** Explicit, authenticated browsing. Restore rechecks revisions on the server. */
export function startRecoveryBrowser({ document, request, isBusy, setBusy, onRestored }) {
  const get = name => document.querySelector(`#recovery-${name}`);
  let offset = 0, total = 0, loading = false;
  function controls() {
    get('load').disabled = loading || isBusy();
    get('previous').disabled = loading || isBusy() || offset === 0;
    get('next').disabled = loading || isBusy() || offset + 24 >= total;
    get('list').querySelectorAll('button').forEach(button => { button.disabled = loading || isBusy() || button.dataset.restorable !== 'true'; });
  }
  async function load(nextOffset = offset) {
    if (loading || isBusy()) return;
    loading = true;
    controls();
    get('list').setAttribute('aria-busy', 'true');
    get('status').textContent = 'Loading recovery copies...';
    try {
      let data = await request(`/api/reports/recovery?offset=${nextOffset}&limit=24`);
      if (!Array.isArray(data?.items) || data.items.length > 24 || !Number.isSafeInteger(data.total) || data.total < 0) throw new Error('Recovery list could not be read.');
      if (nextOffset >= data.total && nextOffset > 0) {
        nextOffset = Math.max(0, (Math.ceil(data.total / 24) - 1) * 24);
        data = await request(`/api/reports/recovery?offset=${nextOffset}&limit=24`);
        if (!Array.isArray(data?.items) || data.items.length > 24 || !Number.isSafeInteger(data.total) || data.total < 0) throw new Error('Recovery list could not be read.');
      }
      offset = nextOffset; total = data.total;
      get('list').replaceChildren(...data.items.map(item => {
        const row = document.createElement('li');
        row.className = 'recovery-report';
        const description = document.createElement('div');
        const identity = reportIdentity(item);
        const label = document.createElement('strong'); label.textContent = identity;
        const meta = document.createElement('p');
        meta.textContent = `Removed ${recordedTimeLabel(item.removed_at)} · ${Number.isFinite(item.bytes) ? (item.bytes / 1048576).toFixed(2) + ' MiB' : 'Size unavailable'}.`;
        description.append(label, meta);
        const restore = document.createElement('button');
        restore.type = 'button'; restore.className = 'secondary-button'; restore.textContent = 'Restore';
        restore.setAttribute('aria-label', `Restore report ${identity}`);
        restore.disabled = item.restorable !== true;
        restore.dataset.restorable = String(item.restorable === true);
        if (restore.disabled) meta.textContent += ' This copy needs technical attention; its evidence is preserved.';
        restore.addEventListener('click', async () => {
          if (loading || isBusy()) return;
          setBusy(true); restore.disabled = true; controls();
          let restored = false;
          try {
            const receipt = await request('/api/reports/restore', { method: 'POST', body: JSON.stringify({ trash_ids: [item.trash_id] }), timeoutMs: 60000 });
            const result = validateRestoreReceipt(receipt, [item.trash_id])[0];
            restored = result.status === 'restored';
            get('status').textContent = restored ? 'Report and its notes restored. Shared nicknames and settings are unchanged.' : result.message || 'Report could not be restored. Neither copy was overwritten.';
            if (restored) await onRestored();
          } catch (error) {
            get('status').textContent = `${error.message} Reload recovery copies and Saved reports to check the outcome before trying again. No request is repeated automatically.`;
          } finally {
            setBusy(false);
            restore.disabled = restored;
            controls();
            get('status').focus({ preventScroll: true });
          }
          // Keep the outcome visible rather than replacing it with loading feedback.
          if (restored) { row.remove(); total -= 1; controls(); }
        });
        row.append(description, restore);
        return row;
      }));
      get('status').textContent = total ? `Page ${Math.floor(offset / 24) + 1} of ${Math.ceil(total / 24)} · ${total} recovery copies. ${(data.warnings || []).join(' ')}`
        : 'No recovery copies found. ' + (data.warnings || []).join(' ');
      get('pages').hidden = total <= 24;
    } catch (error) {
      get('status').textContent = error.status === 404 ? 'Recovery browsing is unavailable in this running backend. Restart the NetGuard backend task to load the updated code. Saved files are unchanged.' : `${error.message} Existing recovery copies are unchanged. Use Reload recovery copies to retry.`;
    } finally { loading = false; controls(); get('list').removeAttribute('aria-busy'); }
  }
  get('load').addEventListener('click', () => void load());
  get('previous').addEventListener('click', () => void load(Math.max(0, offset - 24)));
  get('next').addEventListener('click', () => void load(offset + 24));
  return { sync: controls };
}
