PYTHON ?= python

.PHONY: test smoke capabilities validate release-check

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

smoke:
	PYTHONPATH=src $(PYTHON) -m dpawb.cli assess --profile fixtures/profiles/synthetic_evolution_latest.yaml

capabilities:
	PYTHONPATH=src $(PYTHON) -m dpawb.cli capabilities

validate:
	./scripts/validate-local.sh

release-check:
	./scripts/release-check-local.sh
