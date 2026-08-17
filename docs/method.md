# Method

Replication-gated broadcast topology. Consensus is not a debate or a vote. A candidate thesis is kept only if agents who originally **disagreed** can independently reproduce that sub-claim after seeing its reasoning (not the author’s identity).

This targets two failure modes from *Multi-Agent Teams Hold Experts Back*:

- **Tyranny of majority** — weaker agents agree and outweigh the expert
- **Compromise / semantic averaging** — deliberation dilutes the best member

The paper found the bottleneck is **leveraging** expertise, not identifying it. This pipeline never tells the team who the expert is (`decision_mode: expert_not_mentioned`).

## Stages

```
query + per-agent hidden info
        │
        ▼
1 Isolated drafts      no communication
        │
        ▼
2 Sub-claim grouping   exact discrete match, not embeddings
        │
        ▼
3 Complement exam      inject thesis into agents who disagreed
        │
        ▼
4 Topology rewrite     verified authors become broadcast hubs
        │
        ▼
5 Synthesis            assemble verified claims; hubs only if needed
```

Each stage is a class with `name` and `run(context, state) -> state`. The orchestrator runs `config.stages` in order. Ablations drop or replace entries in that list.

### 1. Isolated drafts

Every agent gets the task prompt plus only its own hidden expert info. Completions run in parallel. No other draft is in context.

Each draft is parsed into a ranking and scored with L1 against ground truth. Those scores **are** the best-individual and member-average baselines.

### 2. Sub-claim quotient grouping

Outputs are split into discrete sub-claims (default: one claim per ranked item, choice = integer rank). Agents are grouped **only** if their choice for that claim is identical. No similarity threshold.

Each coalition picks one representative rationale (`thesis_selector`). Default: item-specific span, then shortest complete trace. Logprobs are optional (Azure often has none).

### 3. Out-network cross-examination

For every non-unanimous coalition:

- Complement = agents who did not make that choice
- Each complement agent re-solves the **original** problem with the candidate rationale injected
- Author id is not shown
- Success = their extracted choice on **that claim** matches (full ranking need not match)
- `replication_rate = n_replicated / |complement|`

Unanimous claims skip the LLM call and get rate `1.0`. This stage is the cost center.

### 4. Topological reconstruction

Programmatic. No LLM manager (that would reintroduce averaging).

Default (`max_replication`): per claim, promote the thesis with the highest complement replication. That author becomes a hub for the claim. Ties become co-hubs. One agent can hub several claims. Everyone else has speaking authority `0`.

### 5. Final synthesis

Verified `(claim, choice, rationale, hub)` records are compiled.

1. If they form a valid permutation, that **is** the answer (no extra generation).
2. Otherwise only hubs generate, all seeing the same constraint packet. If hubs still disagree, pick by how many verified claims are preserved, then by replication — not by vote.

## What we reuse from the paper

| Reused | Not used |
| --- | --- |
| NASA / Lost at Sea / SBP prompts | `Task.execute()` discussion |
| Hidden-info splits (`none`, `full`, `single_expert`, `distributed`) | Reveal-expert prompts |
| Ranking parsers and L1 | Majority vote of post-discussion answers |

## Built-in comparisons

Same harness, different YAML:

- Full method — `configs/replication_broadcast.yaml`
- CoT + majority vote — `configs/majority_drafts.yaml`
- Oracle best draft — `configs/isolated_best.yaml` (uses ground truth; diagnostic only)
- Majority tyranny — `configs/majority_tyranny.yaml`
- Single global expert hub — `configs/global_winner.yaml`
