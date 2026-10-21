import { nameLookupMessage } from './presentation.mjs?v=20261018-lookup-outcomes';

// Later identification is a user operation, not evidence collected by this scan.
export async function refreshNameLookup({ device, trigger, localStatus, window, document, notes, request, scanId }) {
  if (!window.confirm(`Look up names for ${device.ip} on your authorised network? This address may now belong to a different device. Only DNS and enabled local announcements are checked; no port scan starts.`)) return;
  const hadFocus = document.activeElement === trigger;
  trigger.disabled = true; localStatus.hidden = false;
  localStatus.textContent = 'Looking for a name. The original report will not change.';
  try {
    notes.apply(await request(`/api/live-scans/${scanId}/devices/${device.device_id}/refresh-name`, {
      method: 'POST', body: JSON.stringify({ authorised: true }),
    }));
    localStatus.textContent = nameLookupMessage(notes.value?.name_refreshes?.find(item => item.device_id === device.device_id));
    localStatus.hidden = false;
  } catch (error) { localStatus.textContent = `Name lookup could not finish. ${error.message}`; }
  finally {
    trigger.disabled = false;
    if (hadFocus && document.activeElement === document.body && trigger.isConnected) trigger.focus({ preventScroll: true });
  }
}
