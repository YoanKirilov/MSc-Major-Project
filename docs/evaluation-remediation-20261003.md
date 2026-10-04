# Remaining evaluation gates

Software implementation cannot substitute for human participants or unavailable lab
devices. These gates remain pending until real sessions produce evidence.

1. Use the existing evaluation-session.md tasks and results CSV. Prepare matched,
   identifier-free saved scenarios for fixed reviewed wording versus accepted local
   AI wording. Counterbalance order; measure understanding of open services, priority,
   incomplete checks, CVE candidates and next actions, plus time and help requested.
   Preserve which fields were actually AI-selected; do not label fallbacks as AI.
2. On physical Android/iOS devices, verify portrait/landscape reflow, zoom, readable
   touch targets, collapsed technical details and CVE links. Add keyboard-only and
   screen-reader checks on desktop. Browser viewport checks are a separate gate.
3. On the authorised Ubuntu VM lab, install the built wheel, Nmap and local Ollama.
   Record adapter/capability setup, exact versions and service ground truth before
   Light/Deep. Compare expected versus observed TCP/UDP services and rule findings;
   count false positives/negatives and explicitly distinguish UDP ambiguity.
4. Exercise five jobs synthetically, then a bounded authorised Light and Sony-only
   Deep run. Test cancellation/refresh/suspend/network change synthetically before
   considering controlled physical interruption. Never move a running scan onto a
   shared network as an experiment.
5. Record pass/fail separately for unit, browser, provider, home-network, Ubuntu and
   participant tests. No participant or physical-device result may be fabricated.
