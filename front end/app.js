const findings = [
  {
    id: 1,
    severity: "critical",
    title: "Router still uses a default administrator password",
    device: "Living room router",
    address: "192.168.1.1 · Web administration",
    summary: "Anyone connected to the Wi-Fi may be able to take control of the router.",
    explanation: "The router appears to accept a commonly used factory login. If another person joins the network, they could change DNS settings, expose devices, or lock the owner out.",
    impact: "A compromised router can redirect browsing, weaken Wi-Fi security, and give an attacker a useful position from which to target other devices.",
    actions: ["Open the router settings using its official app or local address.", "Set a unique administrator passphrase that is not the Wi-Fi password.", "Disable remote administration unless it is genuinely required."],
    confidence: "High confidence",
    confidenceLevel: 3
  },
  {
    id: 2,
    severity: "critical",
    title: "Outdated SMBv1 file-sharing service is enabled",
    device: "Family desktop",
    address: "192.168.1.24 · TCP port 445",
    summary: "An old file-sharing protocol could allow rapid malware spread inside the home.",
    explanation: "SMBv1 is an obsolete version of Windows file sharing. It lacks modern safeguards and has been associated with serious malware outbreaks.",
    impact: "If one device becomes infected, the outdated service may help malware reach shared files or other computers on the same network.",
    actions: ["Confirm that no old printer or storage device depends on SMBv1.", "Turn off the SMB 1.0/CIFS feature in Windows Features.", "Restart the computer and confirm normal file sharing still works."],
    confidence: "High confidence",
    confidenceLevel: 3
  },
  {
    id: 3,
    severity: "high",
    title: "Router management page uses unencrypted HTTP",
    device: "Living room router",
    address: "192.168.1.1 · TCP port 80",
    summary: "Login details may be visible to another device on the local network.",
    explanation: "The administration page is using HTTP rather than HTTPS. Information exchanged with that page is not protected in transit.",
    impact: "Someone already on the network could potentially observe a router login or alter unprotected management traffic.",
    actions: ["Enable HTTPS administration in the router security settings.", "Bookmark the HTTPS address and stop using the HTTP page.", "If HTTPS is unavailable, check for an official firmware update."],
    confidence: "High confidence",
    confidenceLevel: 3
  },
  {
    id: 4,
    severity: "high",
    title: "Security updates are missing",
    device: "Upstairs laptop",
    address: "192.168.1.37 · Windows device",
    summary: "The device may not contain recent fixes for known security weaknesses.",
    explanation: "The sample device reports an operating-system build that is behind the current update level used by this demonstration dataset.",
    impact: "Known weaknesses are easier to exploit because attackers can study public details and reusable attack methods.",
    actions: ["Save open work and connect the laptop to power.", "Open Windows Update and install all security and cumulative updates.", "Restart, then check again until no security updates remain."],
    confidence: "Medium confidence",
    confidenceLevel: 2
  },
  {
    id: 5,
    severity: "medium",
    title: "Smart camera is reachable from other home devices",
    device: "Hallway camera",
    address: "192.168.1.62 · IoT device",
    summary: "The camera shares the same network as laptops and phones.",
    explanation: "The camera is shown on the main home network. Smart devices usually need internet access, but rarely need direct access to personal computers.",
    impact: "If the camera is compromised, network separation can limit what an attacker is able to reach next.",
    actions: ["Create a guest or IoT Wi-Fi network in the router settings.", "Move the camera and other smart devices to that network.", "Turn on client isolation if the router offers it."],
    confidence: "Medium confidence",
    confidenceLevel: 2
  },
  {
    id: 6,
    severity: "medium",
    title: "UPnP is enabled on the router",
    device: "Living room router",
    address: "192.168.1.1 · Network service",
    summary: "Apps and devices may open incoming network ports automatically.",
    explanation: "Universal Plug and Play can make gaming and video calls easier, but it also lets local apps request changes to the router firewall without manual approval.",
    impact: "A malicious or compromised device could expose a service to the internet, increasing the routes into the home network.",
    actions: ["Review the router's current port-forwarding rules.", "Disable UPnP if games or calls continue to work without it.", "Create only the specific manual rules that trusted services need."],
    confidence: "High confidence",
    confidenceLevel: 3
  },
  {
    id: 7,
    severity: "medium",
    title: "Printer exposes its settings without authentication",
    device: "Office printer",
    address: "192.168.1.48 · TCP port 80",
    summary: "Any connected guest may be able to view or change printer settings.",
    explanation: "The printer's sample web console opens without requesting a password. Administrative pages can reveal network details or allow configuration changes.",
    impact: "A local visitor or compromised device might change settings, interrupt printing, or use exposed information for further attacks.",
    actions: ["Open the printer's administration page from a trusted device.", "Set a unique administrator password or PIN.", "Install the latest firmware supplied by the printer manufacturer."],
    confidence: "Medium confidence",
    confidenceLevel: 2
  },
  {
    id: 8,
    severity: "low",
    title: "Device name reveals personal information",
    device: "Yoan-Laptop",
    address: "192.168.1.19 · Device hostname",
    summary: "The laptop name may reveal the owner's identity to network visitors.",
    explanation: "Device names are often visible to other users of the same Wi-Fi. This example includes a first name, which is unnecessary for identifying the laptop.",
    impact: "This is mainly a privacy concern, but small identifying details can help make social-engineering attempts more convincing.",
    actions: ["Rename the laptop using a neutral label such as Personal-Laptop.", "Restart it so the new name appears across the network.", "Avoid including a full name, address, or room number."],
    confidence: "High confidence",
    confidenceLevel: 3
  }
];

const severityConfig = {
  critical: { label: "Critical", color: "#ff626d" },
  high: { label: "High", color: "#ff9a52" },
  medium: { label: "Medium", color: "#f6ca61" },
  low: { label: "Low", color: "#63a9ff" }
};

let activeFilter = "all";
let activeFindingId = 1;
let searchTerm = "";

const list = document.querySelector("#findingsList");
const panel = document.querySelector("#detailPanel");
const summary = document.querySelector("#resultsSummary");
const chips = [...document.querySelectorAll(".filter-chip")];
const searchInput = document.querySelector("#searchInput");
const scoreDialog = document.querySelector("#scoreDialog");

function getVisibleFindings() {
  return findings.filter((finding) => {
    const matchesSeverity = activeFilter === "all" || finding.severity === activeFilter;
    const haystack = `${finding.title} ${finding.device} ${finding.summary} ${finding.address}`.toLowerCase();
    return matchesSeverity && haystack.includes(searchTerm);
  });
}

function findingCard(finding) {
  const config = severityConfig[finding.severity];
  const button = document.createElement("button");
  button.type = "button";
  button.className = `finding-card${activeFindingId === finding.id ? " selected" : ""}`;
  button.style.setProperty("--severity-color", config.color);
  button.setAttribute("aria-pressed", activeFindingId === finding.id ? "true" : "false");
  button.innerHTML = `
    <span class="severity-bar" aria-hidden="true"></span>
    <span class="finding-main">
      <span class="finding-meta">
        <span class="severity-badge">${config.label}</span>
        <span class="device-name">${finding.device}</span>
      </span>
      <h3>${finding.title}</h3>
      <p>${finding.summary}</p>
    </span>
    <svg class="chevron" viewBox="0 0 20 20" aria-hidden="true"><path d="m7 4 6 6-6 6" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  button.addEventListener("click", () => selectFinding(finding.id));
  return button;
}

function renderList() {
  const visible = getVisibleFindings();
  list.innerHTML = "";
  summary.textContent = visible.length === findings.length
    ? `Showing all ${findings.length} sample findings`
    : `Showing ${visible.length} of ${findings.length} sample findings`;

  if (!visible.length) {
    list.innerHTML = '<div class="empty-state"><strong>No matching findings</strong><p>Try another severity or search term.</p></div>';
    panel.innerHTML = '<div class="empty-state"><strong>Nothing selected</strong><p>Change the filters to explore a sample finding.</p></div>';
    return;
  }

  if (!visible.some((item) => item.id === activeFindingId)) activeFindingId = visible[0].id;
  visible.forEach((finding) => list.appendChild(findingCard(finding)));
  renderDetail(findings.find((finding) => finding.id === activeFindingId));
}

function renderDetail(finding) {
  const config = severityConfig[finding.severity];
  const confidenceDots = [1, 2, 3].map((level) => `<i class="${level > finding.confidenceLevel ? "dim" : ""}"></i>`).join("");
  panel.style.setProperty("--severity-color", config.color);
  panel.innerHTML = `
    <div class="detail-topline">
      <span class="severity-badge">${config.label} severity</span>
      <span class="confidence"><span class="confidence-dots" aria-hidden="true">${confidenceDots}</span>${finding.confidence}</span>
    </div>
    <h3>${finding.title}</h3>
    <p class="detail-location"><strong>${finding.device}</strong> · ${finding.address}</p>
    <div class="detail-block">
      <h4>What this means</h4>
      <p>${finding.explanation}</p>
    </div>
    <div class="detail-block">
      <h4>Why it matters</h4>
      <p>${finding.impact}</p>
    </div>
    <div class="detail-block recommendation">
      <h4>Suggested fix</h4>
      <ol class="remediation-list">${finding.actions.map((action) => `<li>${action}</li>`).join("")}</ol>
    </div>`;
}

function selectFinding(id, shouldScroll = false) {
  activeFindingId = id;
  renderList();
  if (shouldScroll) {
    document.querySelector("#findings").scrollIntoView({ behavior: "smooth", block: "start" });
    window.setTimeout(() => panel.setAttribute("tabindex", "-1") || panel.focus({ preventScroll: true }), 500);
  }
}

chips.forEach((chip) => {
  chip.addEventListener("click", () => {
    activeFilter = chip.dataset.filter;
    chips.forEach((item) => {
      const isActive = item === chip;
      item.classList.toggle("active", isActive);
      item.setAttribute("aria-pressed", String(isActive));
    });
    renderList();
  });
});

searchInput.addEventListener("input", (event) => {
  searchTerm = event.target.value.trim().toLowerCase();
  renderList();
});

document.querySelector("#walkthroughButton").addEventListener("click", () => {
  activeFilter = "critical";
  chips.forEach((item) => {
    const isActive = item.dataset.filter === "critical";
    item.classList.toggle("active", isActive);
    item.setAttribute("aria-pressed", String(isActive));
  });
  searchInput.value = "";
  searchTerm = "";
  selectFinding(1, true);
});

document.querySelector("#scoreInfoButton").addEventListener("click", () => scoreDialog.showModal());
scoreDialog.addEventListener("click", (event) => {
  if (event.target === scoreDialog) scoreDialog.close();
});

renderList();
