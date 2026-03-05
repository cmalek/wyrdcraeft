.. _runbook__old_english_ocr_pipeline:

Old English OCR Pipeline
========================

This runbook documents the current OCR architecture in ``wyrdcraeft``:

- ``olmocr`` pipeline execution for page OCR
- managed local OpenAI-compatible proxy in ``wyrdcraeft.services.ocr_proxy``
- local ``llama-server`` upstream (Apple Metal / llama.cpp path)

The primary objective is lower OCR page latency with explicit quality gates.

Current Architecture
--------------------

End-to-end flow for one source PDF:

1. ``wyrdcraeft ocr old-english`` starts a managed local proxy subprocess.
2. ``olmocr.pipeline`` is launched with proxy URL forced as ``--server``.
3. Proxy forwards to local upstream server (typically ``http://127.0.0.1:8080/v1``).
4. ``olmocr`` writes markdown outputs into ``olmocr_workspace/markdown``.
5. ``wyrdcraeft`` collects markdown, writes:

   - ``02_raw.txt``
   - ``03_normalized.txt``
   - ``04_unknown_tokens.tsv``

The ``--pages`` option is intentionally unsupported in the olmocr-backed path.

Core Commands
-------------

Run OCR pipeline:

.. code-block:: shell

    .venv/bin/python -m wyrdcraeft.main ocr old-english \
      --input-pdf tests/fixtures/ocr/wright1.pdf

Run standalone proxy:

.. code-block:: shell

    .venv/bin/python -m wyrdcraeft.main ocr proxy

Compatibility script shim:

.. code-block:: shell

    .venv/bin/python scripts/ocr/old_english_ocr_pipeline.py \
      --input-pdf tests/fixtures/ocr/wright1.pdf

llama.cpp Profiles
------------------

The Makefile includes dedicated targets:

- ``make llama``
- ``make llama-test``
- ``make llama-test-latency`` (forces ``LLAMA_PARALLEL=1``)
- ``make llama-test-throughput`` (forces ``LLAMA_PARALLEL=2``)

Important knobs for vision-model throughput/latency:

- ``LLAMA_IMAGE_MIN_TOKENS``
- ``LLAMA_IMAGE_MAX_TOKENS``
- ``LLAMA_BATCH``
- ``LLAMA_UBATCH``
- ``LLAMA_THREADS``
- ``LLAMA_THREADS_BATCH``
- ``LLAMA_THREADS_HTTP``
- ``LLAMA_PARALLEL``
- ``LLAMA_CONT_BATCHING``
- ``LLAMA_SEED``

The test profile keeps ``--flash-attn on``, ``--mmproj-offload``, and
``--n-gpu-layers -1`` enabled by default.

Live Integration Tests
----------------------

Live OCR integration tests are additive and opt-in.

Marker and flag:

- marker: ``ocr_integration``
- flag: ``--run-ocr-integration``

Command:

.. code-block:: shell

    .venv/bin/pytest -m ocr_integration --run-ocr-integration

The integration fixture behavior:

1. Probe ``http://127.0.0.1:8080/v1/models``.
2. Reuse existing healthy server.
3. Else start ``make llama-test``.
4. Poll readiness every 250ms up to 120s.
5. Teardown only if fixture started the server.

Accuracy Metrics
----------------

Live OCR comparisons use ``tests/fixtures/ocr/wright*.md`` as expected text and
generated ``02_raw.txt`` as observed text.

Preprocessing before scoring:

- Unicode NFKC normalization
- ``\\r\\n`` normalized to ``\\n``
- trailing whitespace stripped per line
- runs of 3+ blank lines collapsed to 2

Metrics:

- CER (character error rate)
- WER (word error rate)
- thorn/eth metrics:

  - ``thorn_expected``
  - ``thorn_preserved``
  - ``thorn_to_p_rate``

- macron metrics:

  - ``macron_expected``
  - ``macron_preserved``
  - ``macron_recall``

Thresholds are defined in ``tests/fixtures/ocr/wright_quality_thresholds.json``
and are intentionally coarse to catch only clear quality collapse in live runs.

Known OCR Caveats
-----------------

- ``þ``/``ð`` can be under-detected in difficult scans and may appear as ``p``.
- Macronized vowels can be dropped in noisy lines.
- Treat per-run quality metrics as the source of truth during tuning.

Benchmark Protocol
------------------

Use:

.. code-block:: shell

    .venv/bin/python scripts/ocr/benchmark_wright_live.py

Protocol defaults:

- warmup: 1 run (excluded)
- measured: 3 runs per fixture
- fixtures: ``wright1``..``wright5``

Reported fields:

- mean sec/page
- p95 sec/page
- stddev sec/page
- pages/minute
- retries/page
- CER/WER + thorn/macron aggregates

The script performs staged tuning sweeps:

1. image token budget
2. batch/ubatch
3. thread settings
4. proxy token cap

Selection rule:

- choose the lowest mean sec/page candidate that passes quality thresholds.

Default-Change Policy
---------------------

Do not auto-change global defaults from one benchmark run.

Instead:

1. emit recommended environment overrides from the benchmark report
2. validate across repeated local runs
3. promote defaults only after stable repeatability
