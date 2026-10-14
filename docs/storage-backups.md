# Private JSON backups and recovery

Stop the app before export, restore, audit or retention preview. Run these commands
from the project using its Python environment. Replace the example paths with your
actual data folder (shown by `python -m app doctor`) and **new** destination folders.

```powershell
python -m app storage export --data-dir "C:\path\app-data" --destination "C:\path\private-backup"
python -m app storage restore --data-dir "C:\path\private-backup" --destination "C:\path\restored-data"
python -m app storage audit --data-dir "C:\path\restored-data"
python -m app storage retention --data-dir "C:\path\app-data" --older-than-days 90
```

Exports include managed live-report JSON, raw XML, guidance archives, annotations,
nicknames, settings and managed `.trash` recovery evidence/receipts, with a SHA-256 manifest. Locks, session credentials and demo
runs are excluded. They are ordinary private folders, not encrypted archives.
Restore verifies checksums before creating the destination and will not overwrite an
existing folder. It copies data; it does not migrate unknown schemas or establish
that the original evidence is authentic. Audit the restored copy before use.

To inspect the restored copy, set `APP_DATA_DIR` to that folder before starting the
app. Never start two instances against the same folder. Old network scope settings
are preserved: reconfirm your current network before any new scan.

Retention remains a **preview**, not deletion. Export and verify first; decide which
reports to retain for the study. Nothing is deleted automatically. If a copy fails,
the source is preserved and any partial destination remains for inspection; retry
with another new destination. History offers an on-demand usage check and warns at
250 MiB. Current bounded transfer limits: 20 MiB/file, 20,000 files, 3 GiB total.
Linked paths are rejected before traversal. Managed recovery evidence is included
in the same checksum policy, not silently omitted. Unknown files are not exported.

On Saved reports, **Recover deleted reports → Reload recovery copies** lists up
to 24 copies per page and can restore a report after navigation/reload. Restore
rechecks evidence and note revisions and refuses to overwrite an existing report.
Unreadable or unsafe copies are preserved, not automatically repaired or purged.
The size check separates active managed data from recovery data and shows the
2 GiB recovery capacity; removal does not immediately free space. Backups contain
private device details, including those from deleted reports.
