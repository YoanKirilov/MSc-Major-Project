# Experience and discovery implementation plan

30 September 2026. Preserve existing changes, JSON storage, five-job admission and
bounded scanner/AI resources. Do not run a live network scan during implementation.

## Ordered work and acceptance criteria

1. Unified report search: all words match across nicknames, detected names, addresses,
   vendor/category, plain service labels and explanations. Filter device cards as well
   as findings, retain devices without findings, show counts and provide Clear search.
2. Deep picker: offer recent Light observations from saved reports in the current
   authorised scope. Display source date/address and uncertainty; selection only fills
   setup and never submits a scan. Keep manual address entry.
3. Running overview: authenticated per-job profile, target, start time and saved stage,
   progress/report links and explicit cancel. Poll without duplicating jobs or stealing
   the current tab's selected scan. Do not invent precise time estimates.
4. History: server-side filtering before pagination by text, profile, state and date;
   search every saved report, including device nicknames. Optional report titles live
   separately from factual scan evidence. Preserve unreadable-file notices.
5. Nickname updates: poll a small revision/view endpoint on finished visible reports;
   update labels while retaining selected finding/search and without rewriting evidence.
   Preserve revision conflicts and device-matching safeguards.
6. Identification refresh: explicit authorised, bounded name-only lookup for one saved
   device. Revalidate current scope/interface, limit concurrent lookups, record source,
   time and unavailable/unknown results separately from original scan evidence. No wider
   port scan, packet capture, automatic probing or invented identity. Cover transports
   with mocks, not real network requests.
7. Comparison panel: surface existing history observations and their limits; do not call
   absent/incomplete observations resolved or silently compare incompatible profiles.

## Verification and handover

- Isolated temporary JSON fixtures; no edits to normal saved scans or credentials.
- Focused Python/JavaScript tests for search, pagination, scope, annotations and concurrency.
- Synthetic browser workflow: direct pages, picker, search, nickname refresh, running jobs,
  report titles and history filters. Extend existing responsive matrix to new controls.
- Full offline/browser suites; package verification if routes/assets change.
- Record completed steps, artifact paths, counts and genuinely unverified external work
  in testing/status docs. Keep failures and residual limitations explicit.

Status: all seven steps implemented. See [verification evidence](testing.md) and
[architecture](architecture.md) for the implementation boundaries. Synthetic tests do
not establish real-network name discovery, Pi-hole operation, human readability or
large-archive performance; those evaluations remain separate follow-up work.
