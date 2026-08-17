# Architecture

The repo has two layers:

1. **`expert_choice/`** — the method, backends, eval, experiment runner
2. **`third_party/teamwork/`** — paper scenarios, parsers, L1, hidden-info assignment

Do not implement features inside the paper package. Wrap it.

## Layout

```text
Expert-Choice/
  configs/                         YAML pipelines (ablations live here)
  docs/                            this documentation
  expert_choice/
    adapters/                      RankingTaskAdapter + TeamworkRankingAdapter
    backends/                      OpenAI, Azure, Mock
    claims/                        sub-claim schemas + thesis selectors
    core/types.py                  PipelineState and related models
    core/protocols.py              structural typing (Stage, ChatBackend, …)
    eval/                          L1 synergy metrics + JSONL traces
    experiments/run_psychology.py  CLI
    pipeline/                      config, factory, orchestrator
    stages/                        one module per stage
    topology/                      hub promotion policies
  tests/                           mock pipeline + adapter tests
  third_party/teamwork/            git submodule
  outputs/                         gitignored run artifacts
```

## Run graph

```text
CLI / YAML
    │
    ▼
PipelineConfig
    │
    ▼
build_orchestrator()
    ├─ TeamworkRankingAdapter   (or a test fake)
    ├─ ChatBackend
    ├─ ClaimSchema
    ├─ ThesisSelector
    ├─ TopologyPolicy
    └─ RunContext
            │
            ▼
      Orchestrator.run()
            │  for stage in config.stages
            ▼
      PipelineState  (mutated in order)
            │
            ▼
      JSONL trace + JSON summary
```

`Orchestrator` does not contain method logic. If a stage is missing from `config.stages`, it does not run.

## Shared state

[`expert_choice/core/types.py`](../expert_choice/core/types.py) — Pydantic models:

| Object | Produced by | Consumed by |
| --- | --- | --- |
| `Draft` | isolated drafts | grouping, metrics, baselines |
| `Coalition` / `Thesis` | grouping | cross-examine, reconstruct |
| `ReplicationResult` | cross-examine | reconstruct |
| `Topology` / `VerifiedClaim` | reconstruct | synthesize |
| `final_ranking` / `final_solution` | synthesize or baseline stages | eval, traces |
| `metrics` / `usage` | drafts + synthesize | summaries |

Stages must be readable in isolation: they only read fields earlier stages are documented to fill.

## Context vs state

- **`RunContext`** — adapter, backend, schema, selector, policy, config, system prompt. Built once.
- **`PipelineState`** — everything that changes during a run.

## Paper boundary

[`TeamworkRankingAdapter`](../expert_choice/adapters/teamwork.py) calls:

- `get_task_description`
- `_assign_expert_information` (via dummy agents)
- `_parse_ranking`
- `ground_truth_ranking` for L1
- `get_hidden_info`

It never constructs paper `TeamAgent` backends or calls `execute()`. Dummy objects only exist so assignment can read `profile.agent_id`.

## Backends

[`ChatBackend.complete(messages, agent_id=...)`](../expert_choice/backends/base.py) is the only LLM interface. `complete_many` parallelizes with a thread pool. Cross-examination uses opaque request keys and `route_agent_id` so per-agent deployments still resolve to the real agent.

New providers belong in `backends/` plus a branch in `create_backend()`. Stages must not import `openai` directly.

## Tests

| File | What it locks in |
| --- | --- |
| `tests/test_grouping.py` | exact-match coalitions, not similarity |
| `tests/test_topology.py` | replicable minority beats majority; tyranny control |
| `tests/test_assembly.py` | permutation vs collision vs pairwise sort |
| `tests/test_pipeline_mock.py` | full method on a 4-item fake task |
| `tests/test_adapter.py` | paper parsers and hidden-info concentration |
| `tests/test_metrics.py` | relative synergy gap |
| `tests/fakes.py` | `FakeRankingAdapter` — no API, no submodule behavior |

Use the fake adapter for method tests. Use `TeamworkRankingAdapter` only when you are testing paper wiring.
