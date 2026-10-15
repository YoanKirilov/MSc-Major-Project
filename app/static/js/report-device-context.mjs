// Reading context only. These helpers never make requests, change evidence or
// grant permission. Match a saved ID exactly; never guess from an address/name.
const MAX_QUERY_LENGTH = 4096;
const MAX_DEVICE_ID_LENGTH = 200;
const MAX_DEVICE_COUNT = 4096;
const unsafeFormatting = /[\p{Cc}\p{Cf}\p{Cs}\p{Zl}\p{Zp}]/u;

export function validReportDeviceId(value) {
  return typeof value === 'string' && value.length > 0 && value.length <= MAX_DEVICE_ID_LENGTH
    && value.trim() === value && !unsafeFormatting.test(value);
}

export function readReportDeviceContext(search) {
  if (!search) return { status: 'none' };
  if (typeof search !== 'string' || search.length > MAX_QUERY_LENGTH) return { status: 'invalid' };
  try {
    const values = new URLSearchParams(search).getAll('device');
    if (!values.length) return { status: 'none' };
    if (values.length !== 1 || !validReportDeviceId(values[0])) return { status: 'invalid' };
    return { status: 'requested', deviceId: values[0] };
  } catch { return { status: 'invalid' }; }
}

export function resolveReportDeviceContext(data, context) {
  if (context.status === 'none') return { status: 'none', message: '' };
  if (context.status !== 'requested') return { status: 'invalid', message:
    'The device link is incomplete or invalid. No other device was selected. Your saved report is still available.' };
  if (!Array.isArray(data?.devices) || data.devices.length > MAX_DEVICE_COUNT) return {
    status: 'unavailable', message: 'The selected device could not be located safely in this report. No other device was selected.' };
  const matches = data.devices.filter(device => device.device_id === context.deviceId);
  if (matches.length !== 1) return { status: matches.length ? 'ambiguous' : 'missing', message:
    'The selected device could not be found uniquely in this saved report. No other device was selected. The report is still available.' };
  return { status: 'available', device: matches[0], deviceId: context.deviceId,
    message: 'Showing the saved device selected from My devices. All other devices remain in this report.' };
}

export function resumeReportDeviceContext(context, reading, navigation) {
  return context.status === 'requested' && reading?.contextDeviceId === context.deviceId
    && ['reload', 'back_forward'].includes(navigation);
}
