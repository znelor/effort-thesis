#!/usr/bin/env bash
# Make all figures and the supervisor PDF. PYTHON=... to choose the interpreter.
set -euo pipefail
cd "$(dirname "$0")"; PY="${PYTHON:-.venv/bin/python}"
for f in figures/*/make_figure.py; do echo "== $f"; "$PY" "$f"; done
"$PY" docs/build_pdf.py
