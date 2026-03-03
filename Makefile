VERSION = 1.1.0

PACKAGE = wyrdcraeft

#======================================================================


clean:
	rm -rf *.tar.gz *.egg-info
	find . -path './.venv' -prune -o -name "__pycache__" -exec rm -rf '{}' ';'
	rm -rf .pytest_cache
	rm -rf build
	rm -rf dist

dist: clean
	@uv build --sdist --wheel

compile:
	@uv pip compile --group=docs pyproject.toml -o requirements.txt

release:
	@bin/release.sh

docs:
	@echo "Generating docs..."
	@cd doc && rm -rf build && make html
	@open doc/build/html/index.html

morphology-guardrails:
	@.venv/bin/python scripts/morphology/report_quality_guardrails.py

napoleon-gate:
	@python scripts/quality/check_napoleon_gate.py

napoleon-gate-strict:
	@python scripts/quality/check_napoleon_gate.py --strict

napoleon-gate-baseline:
	@python scripts/quality/check_napoleon_gate.py --write-baseline

.PHONY: docs release compile dist clean list morphology-guardrails napoleon-gate napoleon-gate-strict napoleon-gate-baseline
list:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$' | xargs
