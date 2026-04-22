#!/usr/bin/env bash
set -eu

export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}src"

python -m compileall src tests
python -m unittest discover -s tests -v
python -m dpawb.cli capabilities >/dev/null
python -m dpawb.cli assess --profile fixtures/profiles/synthetic_evolution_latest.yaml >/dev/null
python -m dpawb.cli coverage \
  --profile fixtures/profiles/synthetic_evolution_latest.yaml \
  --use-case fixtures/use_cases/product_identity_lookup.yaml >/dev/null
