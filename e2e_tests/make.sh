#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
case "${1:-}" in
  setup_local) npm ci; npx playwright install chromium ;;
  test_e2e) shift; npm test -- "$@" ;;
  ci_e2e)
    mkdir -p /reports
    status=0
    npm test -- --shard="${SHARD_INDEX:-1}/${SHARD_TOTAL:-1}" || status=$?
    for report in test-results playwright-report; do
      if [ -d "$report" ]; then cp -R "$report" /reports/; fi
    done
    exit "$status" ;;
  *) echo 'Usage: ./make.sh {setup_local|test_e2e|ci_e2e}' >&2; exit 2 ;;
esac
