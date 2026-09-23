import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

for (const name of ['dashboard', 'scan']) {
  test(`${name}: static preview opens the backend, backend page does not loop`, () => {
    const html = readFileSync(new URL(`../app/templates/${name}.html`, import.meta.url), 'utf8');
    const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
    const redirects = [];
    const window = { location: { replace(url) { redirects.push(url); } } };
    vm.runInNewContext(script, { window });
    assert.deepEqual(redirects, ['http://127.0.0.1:8765/']);
    redirects.length = 0;
    vm.runInNewContext(script.replace('{{ "backend" }}', 'backend'), { window });
    assert.deepEqual(redirects, []);
  });
}
