# Follow-up execution plan — 5 October 2026

Preserve existing changes, original scan evidence and normal app storage. Do not
rescan devices or replace incomplete coverage with success as part of UI repairs.

1. Fix the narrow-screen percentage: prevent percentage text from shrinking or
   wrapping, allow the neighbouring description to wrap. Test 0%, 90% and 100%
   at phone widths and enlarged text in Chromium, Firefox and WebKit.
2. Simplify live progress: distinguish app contact, running checks and waiting;
   replace lifecycle jargon with last check started/returned wording. Do not
   imply a device replied, or invent an estimated completion time. Test missing
   timestamps, multiple checks and analysis-phase wording.
3. Add saved device-role context to the first action and grouped next actions.
   Reuse the existing evidence-based role helper; never infer a gateway from an
   address suffix or replace a real name/nickname. Test missing context and roles.
4. Investigate the Windows socket-reset cleanup path against installed/upstream
   Python. Keep diagnostics and the reproducer. Apply only a supported, verified
   fix; do not suppress errors, monkeypatch private runtime methods or switch to
   an event loop that breaks scanner subprocesses. If no verified fix exists,
   record the remaining dependency issue explicitly rather than claim completion.
5. Run the complete isolated regression/browser suite, document results and update
   the current status. The unreachable host from the last live test is a coverage
   limitation with bounded retry already implemented, not an application crash.

## Execution results

Steps 1–3 implemented. Percentage text cannot shrink/wrap; neighbouring text can.
Progress explains check starts/ends in seconds-to-minutes language without claiming
the device answered. Missing/unknown timestamps add no invented timing. Suggested
actions retain names/nicknames and add only roles recorded in the saved snapshot.
Updated asset versions prevent old JavaScript being reused under the previous URL.

Step 4 investigated; runtime fix remains open. The application uses Python 3.14.2.
Its socket-close code calls shutdown before close, with no reset guard. The current
[upstream Python 3.14 implementation](https://github.com/python/cpython/blob/3.14/Lib/asyncio/proactor_events.py)
has the same sequence (inspected 5 October). No verified supported replacement was
identified in this review. Existing diagnostic delegation and deterministic reset
reproducer remain enabled; no error suppression, private-runtime patch or global
Python upgrade was made. Next action: evaluate a confirmed upstream fix in a new
isolated environment, including scanner subprocess and abrupt-disconnect tests,
before changing the normal installation. This issue is not marked fixed.

Step 5 completed: **442 Python tests passed**, one real-provider test deselected,
**56 JavaScript tests passed**, Chromium/Firefox/WebKit, lint/format (123 Python
files) and nine JavaScript syntax checks passed. No warnings were reported.
Artifacts: `.test-artifacts/checks-0b105ed580/`. Browser assertions cover 0%, 90%
and 100% at eight viewport sizes and 100%/200% text sizes, plus role context in
the first action and grouped next steps. Existing runtime diagnostic tests passed.
The first suite attempt caught a line-length error in the new browser test; corrected
before restarting the suite. The next run passed 441 Python tests including the
three-browser matrix; one integration assertion still expected the old dashboard
asset version. Updated that assertion; the final full rerun passed.
No new live scan is needed to verify these display-only
changes; the prior live evidence is retained unchanged.

## Additional runtime investigation

Added `scripts/check_windows_disconnects.py`: a bounded loopback-only diagnostic
using a temporary echo listener, orderly/abrupt client disconnects and concurrent
subprocesses. It delegates event-loop errors through the existing observer; it
does not patch or suppress them. Run with the project's Python interpreter.

Executed on Python 3.14.2 / ProactorEventLoop: 11 orderly disconnects, 10 abrupt
disconnects and 20 subprocesses passed. The listener remained responsive and zero
event-loop errors were reported. This did **not** reproduce the intermittent reset
and therefore does not establish a fix. The deterministic mocked shutdown-reset
test remains the evidence for the cleanup vulnerability; a real triggering sequence
or verified upstream repair is still needed. No normal backend was restarted and
no application evidence was changed.
All 15 focused runtime/subprocess regression tests passed, as did lint, formatting
and diff-whitespace checks for this addition. The full-suite counts above refer to
the preceding UI verification, not a new full-suite run for this diagnostic.
