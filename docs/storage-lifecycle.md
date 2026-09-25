# Local JSON lifecycle

The current format remains schema version 1. New fields have defaults so existing
saved reports can be loaded. Reading history does not rewrite them. Unknown future
schema versions are rejected rather than guessed.

Each managed JSON file has a 20 MiB UTF-8 byte limit, enforced before writes and on
reads. Atomic replacement and the previous-revision backup remain in use. Oversized
updates leave the prior report and backup untouched. A scan that exceeds the evidence
limit reports incomplete coverage; it must not claim the unpersisted checks completed.

When a primary document has no room for final job status, a small `terminal.json` stores
only permitted status/coverage/error fields bound to its exact scan ID and revision.
Readers apply it without changing factual evidence. A subsequent successful primary
write absorbs that state and removes the redundant marker. `progress.json` is only a
rebuildable cache; polling falls back to the primary/terminal state when needed.

Guidance history keeps at most three snapshots inside a report. Older snapshots, or
snapshots that would push the report over its size limit, move to its `guidance/`
directory. `guidance_archives` stores their filenames. The report links to authenticated
JSON downloads. Archiving preserves all prior wording; these files count towards any
future retention policy. An interrupted write can leave an unreferenced archive,
which may be retained safely until a maintenance tool checks it.

## Offline audit and recovery

Stop the backend first: maintenance acquires the same application-instance lock.
Commands require an explicit existing data folder and do not start Nmap or Ollama.

```powershell
python -m app storage audit --data-dir "<data-dir>"
python -m app storage retention --data-dir "<data-dir>" --older-than-days 90
python -m app storage recover --data-dir "<data-dir>" --scan-id <uuid>
# Only after inspecting the preview:
python -m app storage recover --data-dir "<data-dir>" --scan-id <uuid> --apply
```

Audit validates report/backup JSON and referenced guidance. Retention lists only old,
readable, finished, completed reports; it cannot delete anything. Failed, incomplete and
unreadable reports are not candidates. Recovery validates `scan.previous.json`, creates
a **new report ID**, copies referenced guidance and records an older-checkpoint warning.
Original reports, backups and raw output remain in their original folder. Interrupted
backups become explicitly interrupted results, not resumed jobs. Recovery may lack later
observations and does not bypass schema/size limits. No automatic repair is performed.

## Retention plan

No automatic expiry is currently enabled. A future maintenance screen should show total
disk use and let the owner select an age/count policy, preview affected report IDs and
dates, export a backup, and move selected reports to recoverable trash. Keep active jobs
and their raw evidence, backups and guidance together. A later explicit action may
permanently empty trash. Do not delete reports just because they failed or are unreadable.

## Migration plan

For a future incompatible schema, implement a versioned converter and test it against
copies of old, corrupt and oversized reports. Validate each converted document before
atomic replacement, retain the original version in a dedicated migration backup, and
record the converter version and time. Support a preview mode and interruption/restart.
Never silently repair evidence, infer missing completed checks, or overwrite an unknown
schema. Reports already larger than the legacy read limit need a dedicated, bounded
recovery/import tool; raising the normal reader limit is not an automatic migration.
