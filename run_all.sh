#!/usr/bin/env bash
# Run all analyses. Figures go to output/, model results to figures/*/out/results.json.
set -euo pipefail
cd "$(dirname "$0")"; PY="${PYTHON:-.venv/bin/python}"
for f in figures/*/make_figure.py; do echo "== $f"; "$PY" "$f"; done
