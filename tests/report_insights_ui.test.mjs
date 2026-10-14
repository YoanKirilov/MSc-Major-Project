import test from 'node:test';
import assert from 'node:assert/strict';
import { shortcutMatches, serviceGroups, comparisonEntries } from '../app/static/js/report-insights.mjs';

const device = { device_id: 'd', ip: '192.168.56.2' };
const data = { devices: [device], findings: [], services: [], coverage: { targets: [{ip: device.ip, service_status: 'completed'}] } };
test('shortcuts distinguish missing names, unfinished checks and review items without safety claims', () => {
  assert.equal(shortcutMatches(device, data, 'unnamed'), true);
  assert.equal(shortcutMatches({...device, user_nickname:'TV'}, data, 'unnamed'), false);
  assert.equal(shortcutMatches(device, data, 'unfinished'), false);
  assert.equal(shortcutMatches({ip:'192.168.56.3'}, data, 'unfinished'), true);
  assert.equal(shortcutMatches(device, {...data, findings:[{device_id:'d'}]}, 'review'), true);
});
test('features group answering services only, retaining inferred names and individual ports', () => {
  const values = serviceGroups({...data, services: [
    {device_id:'d',name:'http',port:80,state:'open',detection_method:'probed'},
    {device_id:'d',name:'http',port:8080,state:'open',detection_method:'table'},
    {device_id:'d',name:'http',port:443,state:'closed'},
    {device_id:'other',name:'ssh',port:22,state:'open'},
  ]});
  assert.equal(values.length, 2);
  assert.match(values[1][0], /type unconfirmed/);
  assert.deepEqual(values.map(([,entries])=>entries[0].service.port), [80,8080]);
});
test('older textual comparisons remain available but never become a zero-change verdict', () => {
  const values = comparisonEntries({...data, devices:[{...device, details:[{kind:'history',label:'Service comparison',value:'Newly observed open: TCP 80.'}]}]});
  assert.equal(values[0].status, 'not_compared');
  assert.match(values[0].reason, /text-only.*TCP 80/);
  assert.equal(values[0].added_count, undefined);
});
test('structured dates and exact totals survive the presentation projection', () => {
  const value = {status:'available',source_created_at:'2026-10-13T10:00:00Z',current_created_at:'2026-10-14T10:00:00Z',added:[],added_count:300,not_observed:[],not_observed_count:2};
  assert.deepEqual(comparisonEntries({...data,devices:[{...device,comparison:value}]}),[{device:{...device,comparison:value},...value}]);
});
