// Stable result triggers and one shared detail panel; no persistence or requests.
export function findingDeviceOptions(findings, devices, label) {
  const counts = new Map();
  for (const finding of findings) counts.set(finding.device_id, (counts.get(finding.device_id) || 0) + 1);
  return [...counts].map(([id, count]) => {
    const device = devices.find(item => item.device_id === id);
    return { id, count, label: device ? `${label(device)} · ${device.ip}` : 'Observed device' };
  });
}

export function repeatedUnknownReplies(findings, services) {
  const counts = new Map();
  for (const finding of findings) {
    if (finding.rule_id !== 'R07' || finding.severity !== 'informational') continue;
    const service = services.find(item => item.service_id === finding.service_id);
    if (service?.state !== 'open' || service.name !== 'tcpwrapped' || service.detection_method !== 'probed' || !(service.nmap_confidence >= 7)) continue;
    counts.set(finding.device_id, (counts.get(finding.device_id) || 0) + 1);
  }
  return [...counts.values()].filter(count => count > 1).reduce((total, count) => total + count, 0);
}

export function renderFindingList({ document, container, layout, panel, findings,
  selectedId, compact, describe, onSelect }) {
  const focused = document.activeElement;
  const existing = new Map([...container.querySelectorAll('.finding-card')]
    .map(button => [button.dataset.findingId, button]));
  const wanted = [];
  const text = (tag, value, className) => {
    const node = document.createElement(tag);
    node.textContent = value;
    if (className) node.className = className;
    return node;
  };
  for (const finding of findings) {
    let button = existing.get(finding.finding_id);
    if (!button) {
      button = document.createElement('button');
      button.type = 'button';
      button.dataset.findingId = finding.finding_id;
      button.addEventListener('click', () => onSelect(finding.finding_id, button));
    }
    const value = describe(finding);
    const signature = JSON.stringify(value);
    if (button.renderSignature !== signature) {
      const bar = text('span', '', 'severity-bar');
      const main = text('span', '', 'finding-main');
      const meta = text('span', '', 'finding-meta');
      meta.append(text('span', value.priority, 'severity-badge'), text('span', value.device, 'device-name'));
      main.append(meta, text('span', value.title, 'finding-title'), text('span', value.feature, 'finding-feature'));
      const chevron = text('span', '›', 'chevron');
      chevron.setAttribute('aria-hidden', 'true');
      button.replaceChildren(bar, main, chevron);
      button.style.setProperty('--severity-color', value.color);
      button.renderSignature = signature;
    }
    const selected = finding.finding_id === selectedId;
    button.className = `finding-card${selected ? ' selected' : ''}`;
    button.setAttribute('aria-pressed', String(selected));
    button.setAttribute('aria-controls', panel.id);
    button.setAttribute('aria-expanded', String(selected));
    wanted.push(button);
    if (compact && selected) wanted.push(panel);
  }
  if (!compact && panel.parentElement !== layout) layout.append(panel);
  // Don't remove/reinsert nodes already in the right place: keyboard focus survives.
  wanted.forEach((node, index) => {
    if (container.children[index] !== node) container.insertBefore(node, container.children[index] || null);
  });
  for (const node of [...container.children]) if (!wanted.includes(node)) node.remove();
  if (focused?.isConnected && document.activeElement === document.body) focused.focus({ preventScroll: true });
}
