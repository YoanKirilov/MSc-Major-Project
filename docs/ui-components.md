# Small UI/state contract

Keep native HTML and the existing CSS tokens; no additional UI framework is needed.

| Component | Contract |
| --- | --- |
| Shared navigation | Same Home, Saved reports and Settings links; display choices remain in Settings, not a duplicate global shortcut. Current page, visible keyboard focus and skip link reaching main content. |
| Primary/secondary/danger actions | One clear main task per group; wrap with spacing on phones; product target 44 CSS pixels high. Danger does not rely on red alone. |
| Feedback | Loading, empty, unavailable, success and unsaved states have plain text. Routine changes use status regions, actionable failures link to inputs. Do not move focus on every poll. |
| Dialog | Native modal, named heading, safe default focus, Escape/cancel return focus; pending operations cannot submit twice. Deletion identifies the exact saved records. |
| Scan overview | Stable job-ID rows/actions; status text updates in place. Pending cancellation remains pending. Disappearance moves focus only if that job held it. |
| History | A complete native list of up to 24 summaries loads for the selected numbered page. No gesture gate or infinite growth. Observation decorates only; absent observer cannot hide content. Select this page includes eligible offscreen rows, never another page. Restore search/page context, never destructive selection. |
| Dates | Saved UTC timestamps remain unchanged; visible timestamps include zone. UTC date filters are inclusive and each report exposes its matching filter date. |
| Recovery | Explicit authenticated listing, bounded pages, revision-safe Restore, no purge; unknown POST outcomes are reconciled by reload, not automatically repeated. |
| Wording | Short truthful source label; factual limitations stay visible. AI wording is not a second security test and Checked is not verified fixed. |
| Appearance | Explicit Dark/Light persist; device theme is opt-in and follows system changes only when selected. Device reduced motion always wins. Storage failures do not block reading. |

Verify these in both themes, forced colours, reduced motion and enlarged/text-spaced
views. Chromium/Firefox automation is evidence for those scenarios, not proof of
physical-phone operation, assistive-technology speech or complete WCAG conformance.

## Pending formative tasks (UX-01/07/10)

Use synthetic private-safe reports with consented novice readers and actual
NVDA/Firefox or Chromium and VoiceOver/Safari users. Ask them to choose scan scope,
interpret an unnamed/unanswered device, read a priority item, mark Need help,
find same-title reports by date, reach 24 rows/pagination, cancel deletion, leave
and recover a report. Test keyboard, touch, browse-mode/virtual-cursor, voice/switch,
physical landscape phones, 200/400% zoom, text spacing and high contrast.

Record correct target/report selection, comprehension of uncertainty, assistance,
recovery and focus/speech outcomes. Do not equate fewer clicks, all Checked or
shorter time with device safety. Add resume cues/onboarding only when actual task
evidence warrants them. This protocol is prepared, not a completed human study.
