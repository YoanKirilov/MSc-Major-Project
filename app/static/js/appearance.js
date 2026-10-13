// Loaded before the stylesheet on every page. Appearance never changes scan data.
(function (window, document) {
  'use strict';
  const key = 'netguard-appearance-v1';
  const defaults = { theme: 'dark', textSize: 'standard', motion: 'device' };
  const choices = { theme: ['dark', 'light'], textSize: ['standard', 'larger'], motion: ['device', 'reduce'] };
  const controls = { theme: 'themePreference', textSize: 'textSizePreference', motion: 'motionPreference' };
  const listeners = new Set();
  const bound = new WeakSet();
  let storageAvailable = true;
  let deviceMotion;
  try { deviceMotion = window.matchMedia('(prefers-reduced-motion: reduce)'); } catch { /* Optional device preference. */ }

  function normalize(value) {
    return Object.fromEntries(Object.entries(choices).map(([name, allowed]) =>
      [name, allowed.includes(value?.[name]) ? value[name] : defaults[name]]));
  }
  function parse(raw) {
    if (!raw || raw.length > 1024) return null;
    try {
      const value = JSON.parse(raw);
      return value?.version === 1 ? normalize(value) : null;
    } catch { return null; }
  }
  let preferences = { ...defaults };
  try { preferences = parse(window.localStorage.getItem(key)) || preferences; }
  catch { storageAvailable = false; }

  function getAppearancePreferences() { return { ...preferences }; }
  function render() {
    const root = document.documentElement;
    root.dataset.theme = preferences.theme;
    root.dataset.textSize = preferences.textSize;
    root.dataset.reduceMotion = String(preferences.motion === 'reduce' || Boolean(deviceMotion?.matches));
    for (const [name, id] of Object.entries(controls)) {
      const control = document.getElementById(id);
      if (control) control.value = preferences[name];
    }
    const options = document.querySelector('.reading-options');
    if (options && !storageAvailable && !document.getElementById('appearance-storage-notice')) {
      const notice = document.createElement('p');
      notice.id = 'appearance-storage-notice';
      notice.className = 'status-message';
      notice.setAttribute('role', 'status');
      notice.textContent = 'Your display choices work on this page, but this browser could not remember them for later.';
      options.append(notice);
    }
  }
  function publish() {
    render();
    for (const listener of listeners) {
      try { listener(getAppearancePreferences()); } catch { /* A view cannot break display preferences. */ }
    }
  }
  function applyAppearancePreferences(patch = {}) {
    const next = normalize({ ...preferences, ...patch });
    if (Object.keys(defaults).some(name => next[name] !== preferences[name])) {
      preferences = next;
      try { window.localStorage.setItem(key, JSON.stringify({ version: 1, ...preferences })); }
      catch { storageAvailable = false; }
    }
    publish();
    return getAppearancePreferences();
  }
  function subscribeAppearancePreferences(listener) {
    if (typeof listener !== 'function') return () => {};
    listeners.add(listener);
    return () => listeners.delete(listener);
  }
  function bindAppearancePreferences() {
    for (const [name, id] of Object.entries(controls)) {
      const control = document.getElementById(id);
      if (!control || bound.has(control)) continue;
      bound.add(control);
      control.addEventListener('change', () => applyAppearancePreferences({ [name]: control.value }));
    }
    render();
  }
  window.NetGuardAppearance = Object.freeze({ getAppearancePreferences, applyAppearancePreferences,
    subscribeAppearancePreferences, bindAppearancePreferences });
  render();
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bindAppearancePreferences, { once: true });
  else bindAppearancePreferences();
  window.addEventListener('storage', event => {
    if (event.key !== key) return;
    const next = event.newValue === null ? { ...defaults } : parse(event.newValue);
    if (next) { preferences = next; publish(); }
  });
  if (deviceMotion?.addEventListener) deviceMotion.addEventListener('change', publish);
  else deviceMotion?.addListener?.(publish);
})(window, document);
