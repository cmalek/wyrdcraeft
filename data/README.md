# any-llm + Qwen (Ollama) extraction bundle

## Install
```bash
pip install pydantic pytest "any-llm-sdk[ollama]"
```

## Pull Qwen + run live regression
```bash
ollama pull qwen2.5:14b-instruct
RUN_LIVE_LLM=1 pytest -k live_qwen
```

Optional:
- `ANYLLM_MODEL=qwen2.5:7b-instruct` (faster)
- `ANYLLM_TEMPERATURE=0.0` (recommended)

## Refresh goldens
```bash
python tools/refresh_goldens.py
```
