VERSION = 1.1.0

PACKAGE = wyrdcraeft

# llama-server tuning defaults for local olmOCR usage on macOS/Metal.
# Override any of these on the command line, e.g.:
# make llama LLAMA_THREADS=12 LLAMA_BATCH=1536
LLAMA_MODEL ?= ./data/models/allenai_olmOCR-2-7B-1025-Q5_K_M.gguf
LLAMA_MMPROJ ?= ./data/models/mmproj-olmOCR-2-7B-1025-vision.gguf
LLAMA_HOST ?= 127.0.0.1
LLAMA_PORT ?= 8080
LLAMA_CTX ?= 16384
LLAMA_THREADS ?= $(shell sysctl -n hw.ncpu 2>/dev/null || echo 8)
LLAMA_THREADS_BATCH ?= $(LLAMA_THREADS)
LLAMA_THREADS_HTTP ?= 2
LLAMA_BATCH ?= 1024
LLAMA_UBATCH ?= 512
LLAMA_PARALLEL ?= 1
LLAMA_IMAGE_MIN_TOKENS ?= 512
LLAMA_IMAGE_MAX_TOKENS ?= 2048
LLAMA_CACHE_TYPE_K ?= q8_0
LLAMA_CACHE_TYPE_V ?= q8_0

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

ocr-old-english-help:
	@.venv/bin/python scripts/ocr/old_english_ocr_pipeline.py --help

download-models-macos:
	mkdir -p ./data/models
	hf download bartowski/allenai_olmOCR-2-7B-1025-GGUF --include "olmOCR-2-7B-1025-Q5_K_M.gguf" --local-dir ./data/models
	hf download richardyoung/olmOCR-2-7B-1025-GGUF mmproj-olmOCR-2-7B-1025-vision.gguf --local-dir ./data/models

llama:
	llama-server \
		-m $(LLAMA_MODEL) \
		--mmproj $(LLAMA_MMPROJ) \
		-c $(LLAMA_CTX) \
		--host $(LLAMA_HOST) --port $(LLAMA_PORT) \
		--threads $(LLAMA_THREADS) \
		--threads-batch $(LLAMA_THREADS_BATCH) \
		--threads-http $(LLAMA_THREADS_HTTP) \
		--parallel $(LLAMA_PARALLEL) \
		--batch-size $(LLAMA_BATCH) \
		--ubatch-size $(LLAMA_UBATCH) \
		--cache-type-k $(LLAMA_CACHE_TYPE_K) \
		--cache-type-v $(LLAMA_CACHE_TYPE_V) \
		--n-gpu-layers -1 \
		--flash-attn on \
		--no-webui \
		--reasoning-budget 0 \
		--image-min-tokens $(LLAMA_IMAGE_MIN_TOKENS) \
		--image-max-tokens $(LLAMA_IMAGE_MAX_TOKENS)

.PHONY: docs release compile dist clean list morphology-guardrails napoleon-gate napoleon-gate-strict napoleon-gate-baseline ocr-old-english-help download-models-macos llama
list:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$' | xargs
