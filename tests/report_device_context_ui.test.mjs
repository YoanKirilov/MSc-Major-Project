import test from 'node:test';
import assert from 'node:assert/strict';
import { validReportDeviceId, readReportDeviceContext, resolveReportDeviceContext, resumeReportDeviceContext } from '../app/static/js/report-device-context.mjs';

test('exact context supports bounded saved legacy identifiers without accepting invisible formatting', () => {
  for (const value of ['11111111-2222-5333-8444-555555555555', 'synthetic-device', 'Saved device', '室内-device', 'x'.repeat(200)]) {
    assert.equal(validReportDeviceId(value), true);
  }
  for (const value of [null, 5, '', ' x', 'x ', 'x'.repeat(201), 'x\n', 'x\u0000y', 'x\u00ady', 'x\u2028y', 'x\u2029y', 'x\u202ey', 'x\u200by']) {
    assert.equal(validReportDeviceId(value), false);
  }
});

test('query context is bounded, single-valued and reading-only', () => {
  assert.deepEqual(readReportDeviceContext(''), { status: 'none' });
  assert.deepEqual(readReportDeviceContext('?profile=deep&authorised=true'), { status: 'none' });
  assert.deepEqual(readReportDeviceContext('?device=Saved+device&authorised=true&hosts=192.168.0.1'),
    { status: 'requested', deviceId: 'Saved device' });
  for (const value of ['?device=', '?device=x&device=x', '?device=x&device=y', '?device=%E2%80%AEabc', '?device=' + 'a'.repeat(201), 'a'.repeat(4097)]) {
    assert.deepEqual(readReportDeviceContext(value), { status: 'invalid' });
  }
});

test('only one exact saved device is selected; names, addresses and partial identifiers cannot substitute', () => {
  const data = { devices: [{ device_id: 'exact', hostname: 'wanted', ip: '192.168.56.10' },
    { device_id: 'exact-more', hostname: 'exact', ip: '192.168.56.11' }] };
  const before = JSON.stringify(data);
  const context = readReportDeviceContext('?device=exact');
  const selected = resolveReportDeviceContext(data, context);
  assert.equal(selected.status, 'available');
  assert.equal(selected.device, data.devices[0]);
  for (const id of ['wanted', '192.168.56.10', 'exac', 'EXACT']) {
    assert.equal(resolveReportDeviceContext(data, readReportDeviceContext('?device=' + id)).status, 'missing');
  }
  assert.equal(resolveReportDeviceContext({ devices: [data.devices[0], data.devices[0]] }, context).status, 'ambiguous');
  assert.equal(resolveReportDeviceContext({ devices: Array(4097).fill(data.devices[0]) }, context).status, 'unavailable');
  assert.equal(resolveReportDeviceContext(data, { status: 'invalid' }).status, 'invalid');
  assert.deepEqual(resolveReportDeviceContext(data, { status: 'none' }), { status: 'none', message: '' });
  assert.equal(JSON.stringify(data), before);
});

test('reload and Back restore later reading context only for the same explicit device', () => {
  const request = readReportDeviceContext('?device=one');
  for (const navigation of ['reload', 'back_forward']) {
    assert.equal(resumeReportDeviceContext(request, { contextDeviceId: 'one' }, navigation), true);
  }
  assert.equal(resumeReportDeviceContext(request, { contextDeviceId: 'two' }, 'reload'), false);
  assert.equal(resumeReportDeviceContext(request, { contextDeviceId: 'one' }, 'navigate'), false);
  assert.equal(resumeReportDeviceContext({ status: 'none' }, { contextDeviceId: 'one' }, 'reload'), false);
  assert.equal(resumeReportDeviceContext(request, null, 'back_forward'), false);
});
