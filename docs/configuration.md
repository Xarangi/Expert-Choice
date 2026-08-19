# Configuration

All method knobs live in YAML under `configs/`. CLI flags override YAML for one run. Do not hardcode ablations inside stage files.

## Load path

```text
configs/*.yaml  →  PipelineConfig  →  CLI overrides  →  build_orchestrator()
```

Defined in [`expert_choice/pipeline/config.py`](../expert_choice/pipeline/config.py). Runner: [`expert_choice/experiments/run_psychology.py`](../expert_choice/experiments/run_psychology.py).

## Example

```yaml
method: replication_broadcast
task: moon_survival
n_agents: 4
seed: 0
expert_info_mode: single_expert
decision_mode: expert_not_mentioned
claim_schema: per_item_rank
thesis_selector: rationale_span
topology_policy: max_replication
replication_k: 0.5
synthesis: assemble_then_hubs
cross_examine: full_complement
stages:
  - isolated_drafts
  - grouping
  - cross_examine
  - reconstruct
  - synthesize
backend:
  provider: azure           # azure | azure_openai | foundry | openai | mock
  model: DeepSeek-V4-Flash  # Azure deployment name (or OpenAI model id)
  # temperature: 0.7        # omit unless you need to override the model default
  max_workers: 8            # parallel LLM calls in complete_many
  agent_models: {}          # optional {"0": "deploy-a", "1": "deploy-b"}
output_dir: outputs
```

Copy an existing file in `configs/` rather than inventing a schema. Unknown keys fail Pydantic validation.

## Field reference

| Field | Allowed values | Role |
| --- | --- | --- |
| `task` | `moon_survival`, `lost_at_sea`, `student_body_president` (aliases: `nasa`, `sbp`) | Paper scenario |
| `n_agents` | int, default 4 | Team size. SBP distributed mode expects 4 |
| `seed` | int | Item shuffle + expert assignment |
| `expert_info_mode` | `none`, `full`, `single_expert`, `distributed` | How ground-truth facts are split |
| `decision_mode` | keep `expert_not_mentioned` | Paper reveal modes exist on the task object; this method should not use them |
| `claim_schema` | `per_item_rank`, `pairwise_order`, `rank_buckets`, `global_ranking` | Sub-claim definition |
| `thesis_selector` | `rationale_span`, `logprob` | Coalition representative |
| `topology_policy` | `max_replication`, `majority_size`, `replication_at_least_k`, `global_winner` | Who becomes a hub |
| `replication_k` | float, default `0.5` | Only for `replication_at_least_k` |
| `cross_examine` | `full_complement`, `top2_coalitions`, `skip` | Stage 3 budget |
| `synthesis` | `assemble_then_hubs`, `assemble_only` | Stage 5 fallback |
| `stages` | list of registered stage names | Ablation surface |
| `backend.provider` | `azure`, `openai`, `mock` | LLM client (`azure` / `foundry` use the OpenAI SDK) |
| `backend.model` | string | Azure deployment name (default `DeepSeek-V4-Flash`) or OpenAI model id |
| `backend.temperature` | float or omit | Only sent if set. Omit to use the model's default (many reasoning models reject `0`) |
| `backend.max_workers` | int, default 8 | Cap on parallel `complete_many` threads (isolated drafts, replication tests) |
| `backend.agent_models` | map agent id → model | Heterogeneous teams |
| `output_dir` | path | Traces and summaries |
| `system_prompt` | optional string | Overrides default isolated-draft system prompt |

## CLI overrides

```bash
python -m expert_choice.experiments.run_psychology --help
```

| Flag | Overrides |
| --- | --- |
| `--config` | YAML path (default `configs/replication_broadcast.yaml`) |
| `--task` | `task` |
| `--seed` | `seed` |
| `--n-agents` | `n_agents` |
| `--expert-info-mode` | `expert_info_mode` |
| `--backend` | `backend.provider` |
| `--model` | `backend.model` |
| `--output-dir` | `output_dir` |
| `--claim-schema` | `claim_schema` |
| `--topology-policy` | `topology_policy` |
| `--cross-examine` | `cross_examine` |

Example:

```bash
python -m expert_choice.experiments.run_psychology ^
  --config configs/replication_broadcast.yaml ^
  --task lost_at_sea ^
  --expert-info-mode distributed ^
  --seed 3 ^
  --backend azure ^
  --model DeepSeek-V4-Flash
```

## Bundled configs

| File | Stages | Intent |
| --- | --- | --- |
| `configs/replication_broadcast.yaml` | drafts → group → exam → reconstruct → synthesize | Full method |
| `configs/majority_drafts.yaml` | drafts → majority_aggregate | CoT + majority (tyranny control) |
| `configs/isolated_best.yaml` | drafts → isolated_best_select | Oracle best individual |
| `configs/majority_tyranny.yaml` | drafts → group → reconstruct → synthesize; `topology_policy: majority_size`; `cross_examine: skip` | Promote largest coalitions |
| `configs/global_winner.yaml` | full pipeline; `claim_schema: global_ranking`; `topology_policy: global_winner` | Single hub, original global-expert idea |

## Claim schemas

- `per_item_rank` — one claim per item, choice is rank. Default. Assembly succeeds only if verified ranks are a permutation.
- `pairwise_order` — claim is “A before B”. More Stage 3 calls; assembly is a topological sort.
- `rank_buckets` — top / mid / bottom. Cannot uniquely assemble; always needs hub synthesis.
- `global_ranking` — one claim for the whole list. Recovers “pick a global winner”.

## Topology policies

- `max_replication` — highest complement replication per claim (default, no threshold)
- `majority_size` — largest coalition (negative control)
- `replication_at_least_k` — keep theses with rate ≥ `replication_k`; a claim may have no hub
- `global_winner` — collapse to one speaking agent

## Cost knobs

Stage 3 dominates token use. For cheaper debugging:

```yaml
cross_examine: top2_coalitions   # only the two largest coalitions per claim
n_agents: 2
task: student_body_president     # 4 items instead of 15
```

`cross_examine: skip` with `topology_policy: max_replication` is not a meaningful ablation; pair skip with `majority_size`.

## Heterogeneous models

```yaml
backend:
  provider: azure
  model: DeepSeek-V4-Flash
  agent_models:
    "0": DeepSeek-V4-Flash
    "1": cheap-deploy
    "2": cheap-deploy
    "3": cheap-deploy
```

Agent ids are strings `"0"` … `"n-1"`.
