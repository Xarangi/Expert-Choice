# Evaluation

Scoring matches the paper’s psychology tasks: **L1 distance** between a ranking and ground truth (lower is better).

For item `i`, L1 adds `|model_rank(item_i) - expert_rank(item_i)|`. NASA / Lost at Sea use 15 items; Student Body President uses 4 candidates.

## Metrics on every run

Written to `outputs/summaries/*.json` and into the JSONL trace (`state.metrics`).

| Key | Meaning |
| --- | --- |
| `team_l1` | Final team ranking error |
| `best_individual_l1` | Min Stage-1 L1 (best member on this seed) |
| `member_average_l1` | Mean Stage-1 L1 |
| `individual_l1` | Per-agent Stage-1 scores |
| `relative_synergy_gap` | `(team - expert) / expert`. `0` matches the expert; positive means the team is worse |
| `strong_synergy` | `team_l1 <= best_individual_l1` |
| `weak_synergy` | `team_l1 <= member_average_l1` |
| `n_hubs` / `hub_ids` | Speaking agents after reconstruction |
| `hub_expert_jaccard` | Overlap of hubs with `designated_expert_ids` (diagnostic only, not a training signal) |
| `stage3_llm_calls` | Complement-exam completions |
| `llm_calls`, `input_tokens`, `output_tokens` | Usage |

`isolated_best` as a pipeline uses ground truth to pick the winner. Report it as an oracle ceiling, not as a deployable method.

## Traces

Each run appends one JSON object:

```text
outputs/traces/<task>_<method>_<seed>_<utc>.jsonl
outputs/summaries/<task>_<method>_<seed>_<utc>.json
```

The JSONL record is a full `PipelineState`: drafts, coalitions, replication attempts (including complement raw text), topology, final ranking. Use it to debug “did the minority thesis actually replicate?” without rerunning.

Helpers: [`expert_choice/eval/logging.py`](../expert_choice/eval/logging.py).

## Suggested comparison grid

Hold `seed`, `task`, `n_agents`, `expert_info_mode`, and backend fixed. Swap only the config file:

| Condition | Config |
| --- | --- |
| Method | `replication_broadcast.yaml` |
| Majority of drafts | `majority_drafts.yaml` |
| Oracle individual | `isolated_best.yaml` |
| Majority coalitions as hubs | `majority_tyranny.yaml` |
| One global hub | `global_winner.yaml` |

Expertise splits worth reporting (paper):

- `single_expert` — one agent gets all specialized facts
- `distributed` — facts partitioned across agents
- `full` / `none` — communication-noise and prior-knowledge controls

Keep `decision_mode: expert_not_mentioned` unless you are explicitly replicating the paper’s Reveal Expert condition (not required for this method).

## Interpreting gaps

- `relative_synergy_gap > 0` — team worse than its best member (the paper’s main finding)
- `weak_synergy` true, `strong_synergy` false — typical deliberative teams in the paper
- Hubs that do not include `designated_expert_ids` — identification failure; still possible for a thesis to be right
- `synthesis_mode` in metadata: `deterministic_assembly` vs `constraint_preserving_hubs` vs baseline names
