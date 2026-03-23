#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
set +e
pytest tests/integration/test_worker_postgres_lock.py
rc=$?
set -e
if [ "$rc" -eq 5 ]; then
  echo "No tests collected for postgres lane; treating as soft-skip."
  exit 0
fi
exit "$rc"
