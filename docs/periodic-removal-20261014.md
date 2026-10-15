# Periodic-check and movement-control removal — 14 October 2026

The user requested a simpler Settings page and complete removal of periodic
checks, not just hiding the opt-in form. This supersedes the periodic feature
described in earlier dated implementation and verification records.

## Implemented

- Removed the periodic API router, scheduler service, storage model and browser
  controller/model, together with the Settings form and feature-only tests.
- Removed scheduling-only `approved_context` and `require_idle` admission hooks.
  The shared admission mutex, parallel capacity, duplicate-job protection,
  standalone AI admission and report Delete/Restore safeguards are retained.
- Startup and shutdown no longer create or start a scheduling service. There is
  no `/api/monitoring` route and no scheduler module in the installed package.
- Preserved existing `monitor.json` and `monitor.previous.json` files as inert
  archival bytes. They are never read for execution or deleted. Private verified
  backup/restore retains them so removal cannot silently lose previous data.
- Removed the separate Movement on screen control from Settings and report
  accessibility preferences. Theme and text-size choices still apply immediately
  and persist independently of scan evidence. Motion follows
  `prefers-reduced-motion` automatically, including changes while a page is open.
  Legacy browser motion values are ignored without losing theme/text size.

The regular backend must be restarted after active jobs finish to unload the old
Python scheduler/routes. Reload open browser pages afterwards. This change does
not stop or mutate a currently running normal app instance.

## Verification

- 11 appearance JavaScript cases passed, including ignored legacy movement values,
  automatic OS motion changes, storage failure and preserved theme/text size.
- 25 isolated Python cases passed: complete periodic removal, no new schedule
  files, unchanged legacy bytes, private archival backup/restore, instance locking,
  supervisor admission/shutdown and packaged-check tooling.
- The initial sandboxed pytest attempt failed because Windows denied access to
  its temporary directory. The approved rerun used a new isolated artifact folder
  and passed all 25 cases. No network scan or normal saved-report access was used.
- 14 focused browser cases passed: seven in Chromium (60.65 seconds) and seven in
  Firefox (106.60 seconds), with no errors, failures or skips. They exercised
  appearance persistence across pages, the new report information dialog,
  retained theme/text-size controls, automatic OS reduced motion, ignored legacy
  motion settings, blocked storage, unavailable app settings, narrow/wide larger
  text, actual report text/focus contrast and saved report profile colours.
- Ruff checks, formatting checks and the scoped Git whitespace check passed.

Artifacts: `.test-artifacts/periodic-removal-unit-20261014-approved`.
Browser result files: `.test-artifacts/appearance-simplification-browser-20261014.xml`
and `.test-artifacts/appearance-simplification-firefox-20261014.xml`. The first run
selected only Chromium because the shared fixture reads `RESPONSIVE_BROWSERS`;
the explicit Firefox run completed the second engine. Full integrated/package
verification is recorded separately in the parent UI-simplification execution
record. These browser regressions are not physical-device or assistive-technology
certification, and no live scan was run for this removal work.
