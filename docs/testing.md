# Testing status

Verified in the current Windows development environment:

```text
python -m pytest tests/unit/test_models.py tests/unit/test_storage.py tests/unit/test_config.py -q
29 passed

python -m app --help
python -m app doctor
completed successfully
```

The full specification acceptance command is not yet passing. Supervisor discovery/deadline/recovery integration, complete protected session workflow, browser tests, AI explanation service, recovery fault tests, evaluation harness, and packaging handover remain to be implemented. Nmap is unavailable and no OpenAI API key is configured in this environment.
