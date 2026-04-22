#!/usr/bin/env bash
set -eu

export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}src"
exec python -m unittest discover -s tests -v
