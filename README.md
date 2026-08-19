# Expert Choice

Replication-gated broadcast topology for multi-agent LLM teams. Isolated drafts, exact-match sub-claim coalitions, complement-pool replication tests, and a multi-hub overlay replace conversational voting.

Psychology ranking scenarios (NASA Moon Survival, Lost at Sea, Student Body President) come from [Multi-Agent Teams Hold Experts Back](https://github.com/apappu97/multi-agent-teams-hold-experts-back) via `third_party/teamwork`. That library supplies prompts, hidden-info splits, parsers, and L1 scoring. Its discussion `execute()` loop is never called.

## Documentation

Start here: **[docs/index.md](docs/index.md)**

| Guide | Topic |
| --- | --- |
| [Getting started](docs/getting-started.md) | Install, keys, first run, tests |
| [Method](docs/method.md) | Five stages and failure modes |
| [Configuration](docs/configuration.md) | YAML, CLI, bundled ablations |
| [Architecture](docs/architecture.md) | Package layout and data flow |
| [Extending](docs/extending.md) | Add stages, schemas, backends, tasks |
| [Evaluation](docs/evaluation.md) | L1, synergy gap, traces |
| [Novelty and plausibility](docs/novelty-and-plausibility.md) | Related work and whether the method should work |
| [Troubleshooting](docs/troubleshooting.md) | Submodule, Azure, parse errors |

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
python -m expert_choice.experiments.run_psychology --config configs/replication_broadcast.yaml
```

Defaults to Azure Foundry + `DeepSeek-V4-Flash`. Official OpenAI: `--backend openai --model gpt-4o-mini`.

```bash
pytest
```

## Ablations (YAML only)

| Config | What it measures |
| --- | --- |
| `configs/replication_broadcast.yaml` | Full method |
| `configs/majority_drafts.yaml` | CoT + majority vote |
| `configs/isolated_best.yaml` | Oracle best Stage-1 draft |
| `configs/majority_tyranny.yaml` | Largest coalitions, no replication |
| `configs/global_winner.yaml` | Single global expert hub |
