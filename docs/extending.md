# Extending

The rule: **register a new class, then point YAML at its name.** Do not add `if method == ...` inside existing stages.

Typical edit order:

1. Implement the class in the matching package
2. Add it to the registry dict (`STAGE_CLASSES`, `SCHEMAS`, `POLICIES`, `SELECTORS`, or `create_backend`)
3. Add a YAML file under `configs/` (or a CLI flag if operators need it)
4. Add a mock test in `tests/`
5. Run `pytest`

---

## Add or skip a stage

Stages live in `expert_choice/stages/`. Contract:

```python
class MyStage:
    name = "my_stage"

    def run(self, context, state: PipelineState) -> PipelineState:
        # read state / context, write fields, return state
        return state
```

`context` is a [`RunContext`](../expert_choice/pipeline/orchestrator.py): `adapter`, `backend`, `schema`, `thesis_selector`, `topology_policy`, `config`, `system_prompt`.

Register in [`expert_choice/stages/__init__.py`](../expert_choice/stages/__init__.py):

```python
from expert_choice.stages.my_stage import MyStage

STAGE_CLASSES = {
    # ...
    "my_stage": MyStage,
}
```

Enable it only through YAML:

```yaml
stages:
  - isolated_drafts
  - grouping
  - my_stage
  - reconstruct
  - synthesize
```

To ablate Stage 3, delete `cross_examine` from that list (see `configs/majority_tyranny.yaml`). Do not comment out code inside `CrossExamineStage`.

Baseline stages already registered:

- `majority_aggregate` — mode ranks, then a valid permutation
- `isolated_best_select` — lowest Stage-1 L1 (oracle)

If a stage needs a new config field, add it to `PipelineConfig` in [`pipeline/config.py`](../expert_choice/pipeline/config.py) with a default so old YAML still loads.

---

## Add a claim schema

Used whenever the “unit of agreement” changes (per item, pairwise, buckets, whole ranking, later: math sub-steps).

Subclass [`BaseClaimSchema`](../expert_choice/claims/base.py) in `expert_choice/claims/` (new file or `ranking.py`):

```python
class MySchema(BaseClaimSchema):
    name = "my_schema"

    def claim_ids(self, items: list[str]) -> list[str]:
        ...

    def extract(self, ranking: dict[str, int], items: list[str]) -> dict[str, str]:
        """claim_id -> discrete choice string. Grouping is exact string match."""
        ...

    def assemble(self, verified, items) -> dict[str, int] | None:
        """Return a ranking if verified claims uniquely determine one; else None."""
        ...

    def describe_claim(self, claim_id: str, choice: str) -> str:
        """Text injected into complement agents. Do not mention author identity."""
        ...
```

Register in `SCHEMAS` inside [`claims/ranking.py`](../expert_choice/claims/ranking.py):

```python
SCHEMAS = {
    "per_item_rank": PerItemRankSchema,
    "my_schema": MySchema,
}
```

Then:

```yaml
claim_schema: my_schema
```

Choices **must** be discrete strings. Do not cluster embeddings.

`assemble()` returning `None` is correct when the schema cannot form a permutation; Stage 5 will ask hubs to synthesize under constraints.

---

## Add a thesis selector

[`expert_choice/claims/selectors.py`](../expert_choice/claims/selectors.py):

```python
class MySelector:
    name = "my_selector"

    def select(self, drafts, agent_ids, claim_id, schema) -> Thesis:
        ...
```

Add to `SELECTORS`, then `thesis_selector: my_selector`.

---

## Add a topology policy

[`expert_choice/topology/policies.py`](../expert_choice/topology/policies.py). Input: coalitions + replication results. Output: a `Topology` (speaking rights, hubs per claim, verified claims, edges).

```python
class MyPolicy:
    name = "my_policy"

    def build(self, agent_ids, coalitions, replications) -> Topology:
        ...
```

Register in `POLICIES` and `get_topology_policy()`. Extra hyperparameters belong on `PipelineConfig` (see `replication_k`).

Keep this programmatic. An LLM “manager” reintroduces averaging.

---

## Add an LLM backend

1. Subclass [`BaseChatBackend`](../expert_choice/backends/base.py) and implement `complete()`.
2. Branch in [`create_backend()`](../expert_choice/backends/__init__.py).
3. Document env vars in `.env.example` and [getting started](getting-started.md).

```python
class WhateverBackend(BaseChatBackend):
    def complete(self, messages: list[Message], *, agent_id: str) -> Completion:
        model = self.agent_models.get(agent_id, self.model)
        ...
        return Completion(text=..., input_tokens=..., output_tokens=...)
```

Stages already call `context.backend.complete_many(...)`. You get parallelism for free.

`MockBackend` takes `handler(agent_id, messages) -> str` or a per-agent reply queue. Use it in tests instead of hitting a provider.

To support a new provider name in YAML (`backend.provider: whatever`), only `create_backend` needs to know about it.

---

## Add a ranking task from the paper submodule

[`TeamworkRankingAdapter._build_teamwork_task`](../expert_choice/adapters/teamwork.py) is the task switch. For another ranking class already in `third_party/teamwork`:

```python
if task_name in {"my_task"}:
    from teamwork.tasks.my_task import MyTask
    return MyTask(**kwargs)
```

Allow the name in the CLI help string in `run_psychology.py`. No stage changes if it still emits `MY RANKING:` lists.

Do not call `task.execute()`. If assignment of expert info is custom, the paper class should override `_assign_expert_information` (SBP already does).

---

## Add a ranking task that is not in the paper repo

Implement [`RankingTaskAdapter`](../expert_choice/adapters/base.py):

```python
class MyAdapter(RankingTaskAdapter):
    name = "my_task"
    items = [...]
    agent_ids = ["0", "1", "2", "3"]
    designated_expert_ids = ["0"]

    def prepare(self) -> None: ...
    def prompt_for(self, agent_id: str) -> str: ...
    def parse_ranking(self, text: str) -> dict[str, int]: ...
    def score(self, ranking: dict[str, int]) -> float: ...
```

Wire it in [`build_orchestrator`](../expert_choice/pipeline/factory.py) (today it always builds `TeamworkRankingAdapter` unless the caller passes `adapter=`). Options:

- Pass `adapter=MyAdapter(...)` from a new experiment module
- Or extend the factory with `if config.task == "my_task"`

Keep factory branching small. New experiment scripts are fine (`expert_choice/experiments/run_my_task.py`).

See `tests/fakes.py` for a minimal adapter used by unit tests.

---

## Add a non-ranking task (MCQ, short answer, later ML benches)

v1 schemas assume `ranking: dict[str, int]`. For GPQA-style answers:

1. Generalize `Draft` (e.g. `solution: dict[str, str]` or a small union type) in `core/types.py`
2. New adapter protocol methods: `parse_solution`, `score(solution)`
3. New claim schema whose `extract()` returns discrete choices (letter, number, span)
4. New assemble/synthesis that does not require a permutation
5. Leave existing ranking stages working — either keep ranking-specific stages or make them call adapter hooks

Do not overload NASA ranking parsers for multiple choice.

---

## Add an experiment runner

`run_psychology.py` is a thin CLI: load YAML, override flags, `build_orchestrator`, dump traces.

For a sweep, write a script that loops `PipelineConfig` / seeds and calls `build_orchestrator(config).run()`. Prefer that over Hydra until you need it.

---

## Change prompts

- Per-agent task text: paper `get_task_description` / adapter `prompt_for`
- Isolated-draft system prompt: `system_prompt` in YAML or `DEFAULT_SYSTEM_PROMPT`
- Replication injection: `_replication_prompt` in [`stages/cross_examine.py`](../expert_choice/stages/cross_examine.py)
- Hub synthesis: [`stages/synthesize.py`](../expert_choice/stages/synthesize.py)

Keep author identity out of Stage 3 prompts. That is load-bearing: it is how we avoid the paper’s Reveal Expert condition.

---

## Change metrics

[`expert_choice/eval/metrics.py`](../expert_choice/eval/metrics.py):

- `draft_baselines` after Stage 1
- `finalize_team_metrics` after a final ranking exists
- Relative synergy gap for error tasks: `(team_l1 - best_individual_l1) / best_individual_l1`

Add fields onto `state.metrics`. Summaries dump the whole dict.

---

## Tests for an extension

Minimum:

1. Pure function / policy test with no backend
2. Mock pipeline test if the change affects Stage 3+ (see `tests/test_pipeline_mock.py`)

Do not require `EXPERT_CHOICE_LIVE=1` for default `pytest`.
