# Getting started

## Requirements

- Python 3.10+
- Git (the paper tasks are a submodule)
- An OpenAI key, **or** Azure AI Foundry / Azure OpenAI credentials

## Install

From the repo root:

```bash
git clone --recurse-submodules <this-repo>
cd Expert-Choice
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

If you already cloned without the submodule:

```bash
git submodule update --init --recursive
```

`pip install -e ".[dev]"` installs this package in editable mode plus `pytest`. The paper code is imported from `third_party/teamwork` via `sys.path`; you do not install that package separately.

## API keys

Edit `.env` (never commit it).

OpenAI:

```bash
OPENAI_API_KEY=sk-...
```

Azure AI Foundry / Azure OpenAI (GA **OpenAI v1** route — do **not** set a dated `api-version`):

```bash
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=<your-deployment-name>
```

The pipeline uses the standard `OpenAI` client with base URL `{endpoint}/openai/v1/` and the Azure `api-key` header. `backend.model` (or `--model`) is the **deployment name**, not a catalog id. A `*.services.ai.azure.com` resource host is rewritten to `*.openai.azure.com` automatically.

## First run

Paper default slice: NASA Moon Survival, 4 agents, concentrated expert info, expert identity **not** revealed.

```bash
python -m expert_choice.experiments.run_psychology --config configs/replication_broadcast.yaml
```

Azure:

```bash
python -m expert_choice.experiments.run_psychology --config configs/replication_broadcast.yaml --backend azure --model your-deployment
```

Other paper tasks:

```bash
python -m expert_choice.experiments.run_psychology --task lost_at_sea
python -m expert_choice.experiments.run_psychology --task student_body_president --expert-info-mode distributed
```

Traces: `outputs/traces/*.jsonl`. Summaries: `outputs/summaries/*.json`.

## Tests (no API)

```bash
pytest
```

Live two-agent NASA smoke (real calls, opt-in):

```bash
# Windows
set EXPERT_CHOICE_LIVE=1
pytest tests/test_live_smoke.py

# macOS / Linux
EXPERT_CHOICE_LIVE=1 pytest tests/test_live_smoke.py
```

## Next

- [Configuration](configuration.md) for YAML knobs and ablations
- [Extending](extending.md) to change the method
- [Architecture](architecture.md) for where code lives
