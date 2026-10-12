// A report's nickname projection is mutable; scan evidence is not.
export function createNicknameState() {
  let current = null;
  let available = false;
  let minimumRevision = 0;
  const namesValid = names => names && typeof names === 'object' && !Array.isArray(names)
    && Object.entries(names).length <= 200
    && Object.entries(names).every(([id, name]) => id.length > 0 && id.length <= 100
      && typeof name === 'string' && name.length > 0 && name.length <= 80 && !/[\x00-\x1f\x7f]/.test(name));
  const signature = names => JSON.stringify(Object.entries(names).sort(([a], [b]) => a.localeCompare(b)));
  return {
    get value() { return current; },
    get available() { return available; },
    unavailable() { available = false; },
    confirmRevision(revision) {
      if (!Number.isSafeInteger(revision) || revision < 1) return false;
      minimumRevision = Math.max(minimumRevision, revision);
      available = Boolean(current && current.revision >= minimumRevision);
      return true;
    },
    apply(snapshot) {
      if (!snapshot || !Number.isSafeInteger(snapshot.revision) || snapshot.revision < 1
          || typeof snapshot.changed !== 'boolean' || snapshot.revision < minimumRevision
          || (current && snapshot.revision < current.revision)
          || (snapshot.recovery_notice != null && (typeof snapshot.recovery_notice !== 'string'
            || snapshot.recovery_notice.length > 300))) return false;
      if (!snapshot.changed && (!current || snapshot.revision !== current.revision || !available)) return false;
      if (snapshot.changed && !namesValid(snapshot.names)) return false;
      const names = snapshot.changed ? snapshot.names : current.names;
      if (current && snapshot.revision === current.revision && signature(names) !== signature(current.names)) return false;
      current = Object.freeze({ revision: snapshot.revision, names: Object.freeze({ ...names }),
        recovery_notice: snapshot.recovery_notice || current?.recovery_notice || '' });
      minimumRevision = Math.max(minimumRevision, snapshot.revision);
      available = true;
      return true;
    },
  };
}

export function projectNicknames(data, state) {
  const saved = state.value;
  if (!saved || !Array.isArray(data.devices)) return data;
  // Even a delayed full-report read must use the newest adopted nickname snapshot.
  data.nickname_revision = state.available ? saved.revision : undefined;
  data.user_nicknames = saved.names;
  data.nickname_recovery_notice = saved.recovery_notice;
  data.devices = data.devices.map(device => ({ ...device, user_nickname: saved.names[device.device_id] }));
  return data;
}
