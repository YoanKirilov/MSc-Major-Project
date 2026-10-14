# Saved reports interaction follow-up - 14 October 2026

The recommended design is a complete, ordinary list of at most 24 report summaries
per page, with explicit numbered pagination. Use viewport observation only for an
optional entrance effect; it must never decide whether a report exists, can be
read or can receive focus. This is simpler and more dependable for this bounded
library than appending one cached row whenever a gesture is recognised.

This document is research and source review only. It implements no application or
test changes and supplies no live/browser result. Its source inventory describes
the snapshot inspected before concurrent follow-up implementation. The user's
new viewport-based request supersedes the earlier one-row-per-gesture policy;
the 24-report cap, safe deletion and recovery remain requirements.

## What already exists, and what this request changes

The inspected History source already has 24-item API requests, numbered pages,
whole-library submitted filters, stale-response rejection and page correction.
Selection is bounded to eligible rows in the displayed page, deletion uses named
confirmation and revision tokens, and destructive requests are not automatically
repeated after an uncertain response. These are existing behaviours to preserve,
not new recommendations.

The newer source also has a recovery-copy browser, separate active/recovery size
feedback, UTC filter-date explanations, distinct report identities and per-tab
search/page context. See `app/static/js/recovery.mjs`, `history-context.mjs` and
`app/templates/history.html`. Earlier recommendations about the absence of those
features should not be treated as a current missing-feature list. Source presence
does not prove they are loaded by the running backend or tested in this follow-up.

The remaining gesture-based behaviour is visible in
`app/static/js/history.js`, from the comment beginning "A wheel burst..." through
the wheel/touch/keydown/scroll listeners. `history-feed.mjs` requests all 24
summaries but `loadPage()` initially exposes one, and `reveal()` exposes one more.
The controller consumes a gesture token even though the reader may already be at
the list edge. The empty-stage CSS also imposes a viewport-height gap. These are
source observations; this agent did not reproduce the reported bug in a browser.

The new request also removes the separate **Display preferences** header shortcut
while keeping display options in Settings, and removes the Pi-hole UI option.
Both controls were still in the inspected shared header/Settings source; they
are requested changes, not established usability-standard violations.

## Comparing the loading models

| Model | Benefit | Cost or limitation | Recommendation for this app |
| --- | --- | --- | --- |
| Complete 24-summary page; optional viewport entrance effect | Every row is available to normal reading, Tab, browser Find and scrollbar jumps; page changes have clear boundaries. | All summaries for the selected page are rendered, including offscreen rows. | Preferred. A cap of 24 lightweight summaries makes this bounded and straightforward. |
| IntersectionObserver progressively appends cached rows within one page | Can reduce initial DOM work and fill content as the viewport approaches it. | Needs initial viewport filling, post-append rechecks, resize handling and a reliable AT/keyboard path to unrendered rows. Selection scope changes as rows arrive. | Secondary option only if measurement shows a useful benefit. Never append another numbered page automatically. |
| Explicit pagination without animation | Familiar, stable retrieval and management; the whole current page is available. | Less visual movement; still requires selecting the next page. | Strong fallback and default when motion is reduced or observation is unavailable. |
| Virtualized/windowed list | Keeps DOM size small for genuinely large lists. | Offscreen rows can leave the DOM, complicating focus, browser Find, AT navigation, variable heights and selection. | Unnecessary for 24 summaries; do not add a virtualization library without measured need. |
| Infinite scrolling across pages | Keeps appending content during browsing. | Loses bounded page position and makes reaching controls/footer and managing scope harder. | Do not substitute for the retained numbered-page contract. |

This comparison is an app-specific inference, not a measured popularity ranking.
GOV.UK recommends pagination when it improves performance/usability and warns
against infinite scrolling because of keyboard problems. It also advises applying
filtering and sorting across the entire result list, not merely the current page.
[GOV.UK pagination guidance](https://design-system.service.gov.uk/components/pagination/).

Google's web.dev explains virtualization as rendering only a small window from a
large list. It supplies a performance technique, not an accessibility guarantee
or a reason to use React in this application.
[Virtualize large lists](https://web.dev/articles/virtualize-long-lists-react-window).

## Preferred viewport behaviour

Use two independent responsibilities:

1. A bounded page controller fetches and renders up to 24 native list rows for the
   explicitly selected page. Search, page change, Retry, Refresh and successful
   management actions use the same stale-response and state safeguards.
2. A small optional IntersectionObserver watches rendered rows entering the
   viewport and applies one short entrance effect once. Row content is visible by
   default, remains in the DOM and does not become hidden when it leaves view.

This keeps the viewport effect from becoming an access requirement. Focus and
browser Find must expose content immediately, even before an observer callback
runs. Do not use `hidden`, `inert`, `aria-hidden`, `display:none` or permanently
zero opacity to conceal offscreen report controls. A focused row must never wait
for a timed reveal or be animated away from the reader's current position.

Avoid an artificial blank stage. A loading message can reserve a modest amount
of space; the whole result region should not need an extra screen of scrolling
before its first useful row appears. If the result area is already visible on a
tall screen, initial loading is expected under the revised design. Tests enforcing
the superseded zero-request/one-row contract should be rewritten around the new
bounded-list behaviour, not retained by manufacturing empty space.

If initial page fetching is deferred until the report region enters the viewport,
do it once for the selected page; explicit Search/page activation should load the
requested results without waiting for a physical scroll. Prefer a complete page
once fetched. A read-only report-summary fetch does not start a scan.

The API observes intersections asynchronously; a callback is not evidence of a
specific user gesture. Feature-detect it, disconnect after a one-time effect and
retain functional plain rows when it is absent or fails. The published W3C
Intersection Observer document is a **Working Draft** describing an API, not an
endorsement of any particular UI loading design.
[W3C Intersection Observer](https://www.w3.org/TR/intersection-observer/).

For practical API usage, an observer can notify on first observation as well as
threshold crossings, and `rootMargin` changes the area considered intersecting.
Use a simple viewport root and a small number of targets/thresholds; complex
pixel-level tracking is unnecessary for this effect.
[MDN Intersection Observer API](https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API).

## If progressive cached append is retained instead

This alternative must use geometry, not wheel bursts, touch contacts, key-repeat
rules or gesture expiry. On intersection, add enough cached summaries to move the
sentinel outside the viewport plus a small prefetch margin, or stop at the page
end. Recheck after rendering/layout settles and on viewport resizing; appending
one short row can leave the sentinel intersecting without another threshold
crossing. That is why replacing the gesture listener with a single callback that
still calls `reveal()` once can reproduce a stuck list.

Bound the top-up loop by remaining rows and permit only one page request in flight.
Stop on error, management/dialog activity, page end or a superseding generation.
Do not automatically retry failed requests from a still-visible sentinel. Do not
fetch page 2 when page 1 runs out. Keep appended nodes rather than removing rows
above the viewport. An ordinary named way to expose the complete current page
must remain usable by readers whose navigation does not move the visual viewport.

Do not add `role="feed"` as a decorative accessibility fix. WAI's feed pattern is
a particular interoperability contract involving article focus, reader navigation
and dynamic loading. A bounded report-management `<ul>` with native links,
checkboxes and buttons does not automatically implement that contract.
[WAI APG feed pattern](https://www.w3.org/WAI/ARIA/apg/patterns/feed/).

## Concrete acceptance checks

These are proposed checks, not results of this review. Use synthetic records for
Delete/Restore scenarios and instrument requests to distinguish summary reads
from scan, provider and management operations.

| Area | Scenario | Required outcome |
| --- | --- | --- |
| Bounded content | Libraries with 0, 1, 23, 24, 25 and many reports | Current page has at most 24 summaries; correct total and page count; no automatic request for another page. |
| Initial geometry | Short laptop, tall monitor, 320 CSS-pixel width, larger text | First useful rows appear without an artificial full-screen gap or special gesture sequence. |
| Scroll/input | Wheel, continuous touch, dragged scrollbar, Page Down, End, browser Find | The complete selected page remains reachable; no one-row-per-input stall or unexpected page advance. |
| Observer absence | Delete/replace IntersectionObserver in a fixture | All rows, links and management controls still work; only the optional effect is lost. |
| Focus before callback | Tab to an offscreen row before observer work completes | The browser can scroll it into view and its label/control is immediately visible. |
| Assistive technology | Screen-reader reading mode, headings/links/buttons navigation, keyboard-only | Reach every current-page report, distinguish its identity and leave the list without custom timing. Validate actual announcements. |
| Animation | Device reduced motion, app reduction, unchanged preference | Reduction disables the entrance effect; reading/focus/selection behaviour is identical. |
| Resizing/zoom | Resize after first render; 200%/400% zoom; text spacing overrides | Rows reflow, action labels remain available, current focus and selection survive layout changes. |
| Request races | Rapid Search/page changes and delayed earlier responses | Only the latest requested state is adopted; no duplicate request for the current generation; older responses never replace current results. |
| Page context | Open report and return; reload; session storage blocked; disappeared last page | Valid page/filter context resumes with safe fallback/correction; no hidden destructive selection carries across pages. |
| Empty library | No reports at all | Clear no-reports message and route to set up a scan; no spinner, false error or repeated background request. |
| No matches | Valid filters return zero | Explain that filters matched nothing and offer Clear filters; distinguish this from an empty library. |
| Read errors | Corrupt/unreadable entries; unavailable backend; list request failure | Preserve available entries, show useful warning/retry state and retain evidence; avoid endless sentinel retry. |
| Selection | 24 rows including busy/unreadable entries | Label current-page scope; select only eligible current-page rows; count and mixed checkbox state are correct. |
| Delete | Same titles; mixed eligibility; Escape; stale revisions; lost connection | Confirm distinct identities; safe Cancel; truthful per-report outcome; no automatic destructive retry. |
| Restore | Undo; reload recovery list after navigation; existing target; mixed failures | Recovery remains available; refuse overwrite; show outcome with meaningful focus; correct recovery pagination after changes. |
| Footer/recovery access | Last report visible; End; keyboard exits list | Footer, recovery and bottom pages stay reachable; the page does not continuously grow. |
| Performance | Synthetic long library but 24-summary page | Request/DOM size remain page-bounded; no continuous geometry polling, leaking observers or redundant rerenders. Record actual timings rather than inventing a pass threshold. |

Relevant accessibility references include
[keyboard operation](https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html),
[status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html),
[reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html)
and [focus not obscured](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html).
Use 44-pixel hit areas as a comfortable product target if retained; WCAG 2.2 AA
SC 2.5.8 uses 24 by 24 CSS pixels with exceptions/spacing alternatives, not a
universal 44-pixel minimum.
[Target-size guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).
Animation from interactions is Level AAA; respecting reduced motion should
continue but must not be described as a separate AA certification.
[Animation guidance](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html).

## Requested UI simplification

Remove the duplicate header Display preferences shortcut from
`app/templates/includes/shared-header.html`. Keep colour theme, device-theme
choice, text size and reduced motion in Settings, with existing browser-local
application/persistence feedback. Shared navigation becomes Scan, Saved reports
and Settings; all pages should retain their current-page indication and skip link.
A contextual link from a report to the Settings section is compatible with this
arrangement if needed; it need not become another global navigation item.

Remove the Pi-hole fieldset/control from `app/templates/settings.html` and its
frontend bindings/error-field references. `settings.js` currently dereferences
`#pihole-enabled`, reads `.checked` and includes it in payload/dirty-state logic.
Deleting markup alone will therefore leave invalid assumptions. Verify initial
loading, save, discard, conflict and availability handling without that input.

UI removal should have an explicit backend-setting policy: do not silently
replace a saved setting with a guessed value merely because its input disappeared.
If the request removes only the UI, preserve/omit the backend field deliberately;
if the product is also retiring the service, make that separately requested
behaviour explicit. Retain the provenance of already saved observations rather
than rewriting historical evidence. No Pi-hole request or settings write is made
by this research document.

## Additional useful improvements after the interaction fix

| Priority | Improvement | Existing source / reason | Suggested check |
| --- | --- | --- | --- |
| Next | Update copy to the full-page model | History still says one report per scroll gesture and gives special key instructions. | No wording promises staged reveal when all current-page summaries are available; count reports on page and across matches. |
| Next | Use readable applied-filter values | `history.js` currently prints values such as `deep-tcp-v1` and `completed` in its applied-filter description. | Applied filters say Deep/Finished, matching their controls; search/date text remains accurate. |
| Next | Label selection as current-page scope | With all 24 rendered, an offscreen row is still part of the displayed page. | Readers understand Select reports on this page means eligible current-page records, never every search match. |
| Next | Give pagination meaningful orientation | Numbered controls already exist; current template title remains generic. | Announce Page 2 of 4 once after explicit navigation; retain visible current page and an informative document title. |
| Later | Keep identities distinct without excessive technical prose | `reportIdentity()` includes a full UUID; recovery puts the whole identity in a visible heading. | Distinct titles/type/date/target remain easy to read; optional reference details retain exact disambiguation. |
| Later | Use compact durable management feedback | Immediate Undo and persistent recovery already exist. | Result stays perceivable after mutation; a concise message names the outcome and points to the actual recovery action. |

These are practical patterns in maintained design guidance, not findings that
popular interfaces universally use them. GOV.UK's pagination guidance supports
clear current-page orientation; checkbox guidance supports explicit selection
instructions; notification guidance distinguishes feedback from field errors.
[Pagination](https://design-system.service.gov.uk/components/pagination/),
[checkboxes](https://design-system.service.gov.uk/components/checkboxes/)
and [notification banners](https://design-system.service.gov.uk/components/notification-banner/).
Do not import another system's full styling or move action success into a
short-lived toast solely because those patterns are common.

The first implementation priority is the complete bounded list and removal of
gesture gating/empty-stage assumptions, followed by the requested navigation and
Pi-hole UI simplification. Optional entrance effects and smaller copy refinements
must not delay a usable list. Performance optimisations beyond that should follow
measurement rather than a generic preference for lazy rendering.

## Evidence limits

All external references were browsed on 14 October 2026. No browser, screen reader,
physical phone, scanner, provider or participant was used by this agent. The
acceptance matrix is a plan for verification; it does not establish WCAG
conformance or prove human comprehension. Live findings and implementation/test
results belong in the main agent's separate execution record. Only this new
follow-up document was written; the earlier recommendations remain a dated review
whose implemented gaps are explicitly identified above.
