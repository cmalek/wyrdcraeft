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

.PHONY: docs release compile dist clean list
list:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$' | xargs
