# Code organisation and live verification - 21 October 2026

Requested follow-up to [the four fixes](issue-fixes-20261021.md).

Plan / acceptance:

1. Make a small behaviour-preserving organisation change: move pure scan-start
   operation/generation ownership and bounded recovery-read state into a dedicated
   module. Keep DOM, storage, timers and requests in the dashboard. Protect all
   late-response/refresh behaviours with the existing acceptance tests.
2. Check source/asset reachability, imports, tests and package contents. Delete no
   file merely because its purpose is unfamiliar; preserve existing working-tree
   changes, historical evidence and household JSON.
3. Freeze source and confirm the current default-route network/this-PC address
   still match the authorised home scope before traffic. Use a new private data
   folder and owned backend, with Pi-hole disabled. Do not stop the normal server.
4. Run one Light/home scan and one Deep/this-PC scan. Verify saved coverage/errors,
   local AI wording against evidence, refresh, automatic report opening, mobile/
   desktop layout, exports and inventory. Do not conceal incomplete coverage or
   silently resubmit failed jobs.
5. Replay completed raw evidence/AI validation, confirm normal files unchanged and
   owned test-process cleanup. Record live, synthetic and hosted limits separately.

Organisation implemented: `static/js/start-state.mjs` now owns only operation,
generation, read ownership and the ten-read budget. It has no DOM/storage/network/
timer/authorisation effects. Dashboard orchestration delegates to it. Four added
pure-state cases and all 57 existing dashboard cases passed; the eleven source/
asset/API layout checks passed. No unused application files required deletion.

Full gates and live results are pending; final outcomes will be recorded here.
