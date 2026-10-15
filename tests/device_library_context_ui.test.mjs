import test from 'node:test';
import assert from 'node:assert/strict';
import { createDeviceContext } from '../app/static/js/device-library-context.mjs';

const instant = 1800000000000;
const value = { search: 'Living room', view: 'review', page: 2, y: 850,
  focusKey: `d-${'a'.repeat(64)}` };
function setup(initial = null, now = () => instant) {
  let raw = initial;
  const storage = { getItem: () => raw, setItem: (_, next) => { raw = next; } };
  return { context: createDeviceContext(() => storage, now), raw: () => raw };
}

test('only applied browsing context is saved; drafts and scan authority are excluded', () => {
  const app = setup();
  assert.equal(app.context.save({ ...value, drafts: ['private'], recognised: true,
    authorised: true, token: 'private', hosts: ['192.168.56.5'] }), true);
  assert.deepEqual(Object.keys(JSON.parse(app.raw())).sort(),
    ['version','search','view','page','y','focusKey','savedAt'].sort());
  assert.deepEqual(app.context.load(), { version: 1, ...value, savedAt: instant });
});

test('blocked or missing browser storage cannot prevent reading the device page', () => {
  for (const getter of [() => null, () => { throw new Error('blocked'); },
    () => ({ getItem() { throw new Error('blocked'); }, setItem() { throw new Error('full'); } })]) {
    const context = createDeviceContext(getter, () => instant);
    assert.equal(context.load(), null);
    assert.equal(context.save(value), false);
  }
});

test('malformed, oversized, future and expired context is ignored', () => {
  for (const raw of ['{broken', 'x'.repeat(2001), JSON.stringify({ version: 1, ...value, savedAt: instant + 1 }),
    JSON.stringify({ version: 1, ...value, savedAt: instant - 86400001 })]) {
    assert.equal(setup(raw).context.load(), null);
  }
});

test('invalid filters, pages, positions and card references cannot be restored', () => {
  for (const change of [{ view:'intruders' }, { page:0 }, { page:1.5 }, { page:1000001 },
    { y:-1 }, { y:10000001 }, { search:'x'.repeat(121) }, { search:'two\nlines' },
    { focusKey:'javascript:alert(1)' }, { focusKey:{} }, { version:2 }]) {
    const raw = JSON.stringify({ version: 1, ...value, savedAt: instant, ...change });
    assert.equal(setup(raw).context.load(), null);
  }
  assert.equal(setup(null, () => NaN).context.save(value), false);
});

test('explicit reset replaces old context and null focus restores no device identity', () => {
  const app = setup(); app.context.save(value);
  const reset = { search:'', view:'all', page:1, y:0, focusKey:null };
  assert.equal(app.context.save(reset), true);
  assert.deepEqual(app.context.load(), { version:1, ...reset, savedAt:instant });
});
