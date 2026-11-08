#!/bin/bash
# Runs all checks: the catalog itself (tools/check.py), then the checker's
# own tests. Stops at the first failure. Run it before committing; CI runs
# the same script. Makes .venv with the pinned Python packages on first use.

set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -x .venv/bin/python ] || [ requirements.txt -nt .venv/.installed ]; then
  python3 -m venv .venv
  .venv/bin/pip install --quiet --disable-pip-version-check -r requirements.txt
  touch .venv/.installed
fi

echo "== The catalog"
.venv/bin/python tools/check.py

echo "== The checker's tests"
.venv/bin/python -m unittest discover -s tests -q

echo "== All checks passed"
