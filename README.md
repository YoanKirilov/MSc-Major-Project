# Network Assessor

This is a local network assessment application built to the specification in the project brief.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.lock
python -m pip install --no-deps -e .
network-assessor doctor
network-assessor serve --port 8765
```

## Notes

- The app stores all JSON data locally under the configured data directory.
- Demo mode works without a configured scanner or provider.
- Live lab and provider checks remain opt-in and are not run by default.
