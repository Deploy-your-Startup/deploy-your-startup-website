# Actions usage

Release polling runs every six hours instead of every ten minutes. Automatic installer updates can therefore arrive later; workflow_dispatch remains available for an immediate check. Pull requests have separate concurrency groups and superseded runs are cancelled; production runs remain serialized and are not interrupted. Browser and macOS installer checks still gate deployment.

The deployment gates, lint, integration coverage and browser scenarios remain enabled.

Local regression check:

```sh
python3 tests/test_release_gate_integration.py
```

The local regression executes the actual release-selection shell for eight event/update combinations.
GitHub PR checks must verify the complete suites before merge. Compare rounded job
minutes for representative successful runs before claiming a percentage saving.
