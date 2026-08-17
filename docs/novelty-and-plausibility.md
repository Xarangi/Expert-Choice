# Novelty and plausibility analysis

**Method:** Replication-Gated Broadcast Topology (this repo’s “Expert Choice” pipeline).  
**Stated purpose:** Close the *strong-synergy gap* documented in Pappu et al., [Multi-Agent Teams Hold Experts Back](https://arxiv.org/abs/2602.01011) (arXiv:2602.01011, 2026): LLM teams underperform their best member because of **tyranny of the majority** and **integrative compromise**, not because they fail to notice who the expert is.  
**Research date:** 17 August 2026. Sources are public papers and code; this is not a claim of an exhaustive literature review, and it is not empirical proof that the method works.

**Verdict in one paragraph.** The *composition* is novel enough to be a paper: turn consensus into a **demonstrability test** (can originally-disagreeing agents independently reproduce a sub-claim from a thesis that hides author identity?), then **rewrite speaking rights** into a multi-hub broadcast graph, then **assemble** verified sub-claims without a team vote. No single prior system was found that uses complement-pool *re-solving* (as opposed to judging, voting, or debating) as the gate for *per-claim hub promotion*. The *parts* are not new. Plausibility is mixed and **load-bearing assumptions may fail on the exact tasks this repo implements first** (NASA / Lost at Sea / Student Body President). The most serious risks are (1) the Stage-3 test collapsing into **consultancy/sycophancy** rather than verification, (2) **weak demonstrability** of survival rankings, and (3) **persuasive adversaries** being *promoted* rather than diluted. Those are falsifiable; they should be treated as the experimental core, not as footnotes.

---

## 1. What the idea is actually claiming

The pipeline is not “better debate.” It is a **protocol change**:

1. **Isolate** so early fluency cannot infect the team (Stage 1).
2. **Partition** answers into discrete sub-claims and form coalitions by **exact choice match**, not embedding similarity (Stage 2).
3. **Test** each coalition’s thesis on the **complement** — agents who did *not* make that choice — by injecting the rationale (not the author) and asking them to re-solve. Replication rate is the expertise signal (Stage 3).
4. **Reconfigure** the communication graph: high-replication authors become **broadcast hubs**; everyone else loses speaking rights (Stage 4). Multiple hubs, not one global winner.
5. **Synthesize** from verified sub-claims by deterministic assembly when possible; otherwise only hubs generate under shared constraints (Stage 5). No majority vote among muted nodes.

The intended scientific contribution is therefore:

> Expertise should be *demonstrated* to outsiders by independent reproduction of a conclusion, not *negotiated* in a conversation and not *counted* by coalition size.

That is a direct operationalization of Laughlin’s **demonstrability** conditions (below) plus a rejection of the paper’s observed **epistemic-flexibility / integrative-compromise** loop.

---

## 2. How novelty is scored here

A method can be:

| Grade | Meaning |
| --- | --- |
| **Primitive novelty** | A new mechanism not previously used in LLM MAS |
| **Composition novelty** | Known pieces, previously unused combination and purpose |
| **Application novelty** | Known method, new evaluation setting (Pappu tasks / synergy gap) |
| **Incremental** | Small variant of an existing protocol |

This write-up treats **composition + application** as enough for a research contribution if (a) the combination is not already published, (b) it is *aimed at a documented failure mode rather than “add agents, hope,”* and (c) it makes a prediction that existing methods get wrong. Primitive novelty is **not** claimed for isolated drafts, discrete grouping, topology graphs, or “verify the CoT.”

---

## 3. Related-work map

Six families matter. Distances are relative to *this* method, not to MAS in general.

### 3.1 Debate, vote, and “society of minds”

These are the protocols the idea refuses.

- **Du et al. (2023/2024),** [Improving Factuality and Reasoning through Multiagent Debate](https://arxiv.org/abs/2305.14325). Symmetric agents propose, see each other, revise, often majority-vote. This *is* integrative compromise with extra steps.
- **Liang et al. (2023/2024),** [MAD — tit-for-tat debate + judge](https://arxiv.org/abs/2305.19118) ([arXiv:2305.19118](https://arxiv.org/abs/2305.19118)). Explicit disagreement plus an LLM judge. Still conversational; the judge is an averaging/authority node.
- **Chen, Saha, Bansal (2024),** [ReConcile](https://arxiv.org/abs/2309.13007) ([ACL](https://aclanthology.org/2024.acl-long.381/)). Round-table discussion; agents try to **convince** each other; **confidence-weighted vote**. Closest “don’t treat agents equally” cousin — but the weight is *self-reported confidence*, which is exactly the kind of semantic signal this method wants to abandon, and the channel is still discussion.
- **Wang et al. (2024),** [Mixture-of-Agents](https://arxiv.org/abs/2406.04692) ([arXiv:2406.04692](https://arxiv.org/abs/2406.04692)). Layered proposers + aggregator LLM. Aggregation, not demonstrability; the aggregator can reintroduce averaging.
- **Wang et al. (2022),** [Self-Consistency](https://arxiv.org/abs/2203.11171) ([arXiv:2203.11171](https://arxiv.org/abs/2203.11171)). Sample many CoTs, **majority-vote the answer**. Stage 1 + majority_drafts in this repo *is* self-consistency across agents. The whole point of Stages 3–4 is to **not** do this when the majority is wrong.
- **Choi et al. (2025),** [Debate or Vote](https://arxiv.org/html/2508.17536v1) ([arXiv:2508.17536](https://arxiv.org/abs/2508.17536)). Majority voting accounts for most MAD gains; debate itself is a martingale on beliefs. Directly supports the claim that “more talking” is the wrong fix for Pappu’s gap.
- **Elumar / “Beyond Majority Voting” (2025),** [higher-order aggregation](https://arxiv.org/html/2510.01499v1) ([arXiv:2510.01499](https://arxiv.org/abs/2510.01499)). Uses accuracy and correlation, not replication of reasoning.
- **Gao et al. (2026),** [LMAD — Where Reasoning Diverges](https://arxiv.org/abs/2608.01463). Parses traces into nodes, debates only the **earliest local conflict**, commits resolved claims to shared state. Closest *sub-claim localization* cousin; still conversational MAD, not complement re-solve or hub mute.

**Distance:** far on protocol (they talk or vote). Near on *diagnosis* (Choi, Pappu): deliberation is not where the gains are.

### 3.2 Learned or dynamic topology

These rewrite graphs. They do **not** gate edges on complement replication.

- **Zhuge et al. (2024),** [GPTSwarm](https://proceedings.mlr.press/v235/zhuge24a.html). Agents as graphs; optimize prompts and edges (typically toward task reward / search). Topology is an *optimization object*, not a verification certificate.
- **Liu et al. (DyLAN, 2023/2024),** [Dynamic LLM-Agent Network](https://arxiv.org/abs/2310.02170) ([HTML](https://arxiv.org/html/2310.02170v2), [code](https://github.com/SALT-NLP/DyLAN)). Temporal FFN; **Agent Importance Score** from message passing; drop low contributors. Importance ≠ “outsiders can reproduce your sub-claim.”
- **Qian et al. (2024),** [MacNet](https://arxiv.org/abs/2406.07155) ([arXiv:2406.07155](https://arxiv.org/abs/2406.07155)). DAG of actors (nodes) and critics (edges); scale to many agents; logistic “collaborative scaling.” Critics refine artifacts along edges; they do not run a complement-pool re-solve. Pappu’s *dilution with team size* sits in tension with MacNet’s “more agents help then saturate” — different tasks, but a reminder that topology papers often *want* more voices.
- **Zhang et al. (2024/2025),** [G-Designer](https://arxiv.org/abs/2410.11782) ([arXiv:2410.11782](https://arxiv.org/abs/2410.11782)). VGAE decodes a **task-adaptive** communication graph; sparsity and adversarial robustness. Input-dependent topology, but the decoder is a GNN, not a replication statistic. They report **adversarial robustness via topology** — Pappu reports robustness via *compromise*. Different mechanisms, same symptom (mute the weirdo).
- **Yang et al. (2025),** [AgentNet](https://arxiv.org/html/2504.00587v2) ([arXiv:2504.00587](https://arxiv.org/abs/2504.00587)). Decentralized evolving DAG, RAG memory, routing by success. Online specialization, not per-query sub-claim hubs.
- **AFlow / AgentSquare / Magentic-One / AutoGen.** Workflow search or a **central orchestrator** (Magentic-One’s Task/Progress ledgers). This method’s Stage 4 is deliberately *not* an LLM manager, because a manager would re-average.

**Distance:** same *noun* (topology). Different *verb* (optimize/route/orchestrate vs certify-then-broadcast). Closest structural rhyme is DyLAN’s “deactivate low-importance agents,” still a different score.

### 3.3 Verifiers, judges, debate-as-oversight

This is the family Stage 3 actually lives in.

- **Lightman et al. (2023/2024),** [Let’s Verify Step by Step](https://arxiv.org/abs/2305.20050). Trained **process reward models** score math steps. Human labels, MATH, not a team topology. Same *spirit* (process over outcome); different *machinery*.
- **Zheng et al. (2023),** [Judging LLM-as-a-Judge](https://arxiv.org/abs/2306.05685). A model *grades* quality. Stage 3 does not ask “is this good?”; it asks “if you re-solve, do you land on the same discrete choice?”
- **Dhuliawala et al. (2024),** [Chain-of-Verification (CoVe)](https://aclanthology.org/2024.findings-acl.212/). Draft → plan check questions → **answer checks independently** → rewrite. Independent answering to avoid self-bias is the same *hygiene* as complement re-solving. CoVe is intra-model fact-checking, not inter-agent hub election.
- **Irving, Christiano, Amodei (2018),** [AI safety via debate](https://arxiv.org/abs/1805.00899). Two agents argue; a weaker judge picks. Complexity-theoretic motivation: truth is easier to verify than to find.
- **Khan et al. (2024),** [Debating with More Persuasive LLMs](https://arxiv.org/abs/2402.06782) ([PMLR](https://proceedings.mlr.press/v235/khan24a.html)). Weak judges (and humans) supervising strong experts with **information asymmetry**. **Debate beats consultancy.** Consultancy = one expert’s argument injected into a non-expert — structurally the **closest published analogue of Stage 3**, and it is the *weaker* protocol in their results. Judges show **sycophancy** (crediting unverified quotes).
- **Kenton et al. (2024),** [On scalable oversight with weak LLMs judging strong LLMs](https://arxiv.org/abs/2407.04622) ([arXiv:2407.04622](https://arxiv.org/abs/2407.04622)). Multi-task: debate > consultancy especially when the consultant is *wrong*. Open consultancy: judges are **equally convinced** whether the consultant is correct or not.
- **Cohen et al. (2023),** [LM vs LM: Detecting Factual Errors via Cross-Examination](https://aclanthology.org/2023.emnlp-main.778/). Examiner LM interrogates an examinee’s claim. Cross-examination as *inconsistency detection*, not independent reproduction of a discrete sub-claim, and no topology rewrite.
- **AgentAuditor (2026),** [Auditing Multi-Agent LLM Reasoning Trees](https://arxiv.org/abs/2602.09341). Replaces majority vote with path search over a **Reasoning Tree**; localized audits at Critical Divergence Points; trains an adjudicator with Anti-Consensus Preference Optimization (ACPO) on majority-failure cases. Recovers minority-correct answers where voting gets 0%. Closest *anti-majority aggregation* system found in this search. Still an LLM adjudicator over traces, not complement-pool re-solve, not identity-blind replication, not speaking-authority rewrite.

**Distance:** Stage 3 is **open consultancy without an opposing debater**, then used as a **graph rewrite**, not as a judge’s final pick. That is a sharp novelty claim *and* a sharp plausibility warning: the literature’s best evidence says single-thesis persuasion is a bad truth serum. AgentAuditor shows you *can* beat vote without replication-gated hubs — so it is a required baseline, not a proof that this protocol is unnecessary.

### 3.4 Claim decomposition

- **Min et al. (2023),** [FActScore](https://arxiv.org/abs/2305.14251). Atomic facts vs Wikipedia.
- **Song et al. (2024),** [VERISCORE](https://arxiv.org/abs/2406.19276). Verifiable claims + retrieval.
- **Wanner et al. (2024),** [Decomposition Dilemmas](https://arxiv.org/abs/2411.02400). Decomposition can *hurt* strong verifiers.

Stage 2’s “sub-claims” look similar but are **not** fact-checking against a corpus. They are **quotient sets of the team’s own discrete outputs** (item rank, pairwise order, bucket). No retrieval. Exact string/rank match, not NLI.

**Distance:** shared “don’t treat the whole answer as one blob.” Different verification oracle (world knowledge vs other agents’ re-solves).

### 3.5 Organizational psychology (the actual theoretical parent)

Pappu et al. already cite this; the method is trying to *implement* it.

- **Laughlin & Ellis (1986); Laughlin (2011).** Intellective vs judgmental tasks. Demonstrability needs four conditions: shared conceptual system; sufficient information; **incorrect members can recognize a correct solution**; correct members can demonstrate it.
- **Social decision schemes:** “truth wins” vs “truth-supported wins.” One correct member is often *not* enough; conformity can crush a singleton expert (Laughlin et al. on intellective tasks).
- **Bonner et al. (2002); Yetton & Bottger.** Humans defer when expertise is revealed — the behavior LLM teams lack.
- **Stasser et al. (1995).** Hidden profiles: shared information dominates unique information. SBP in this repo *is* that paradigm.
- **Li et al. (2025),** [HiddenBench](https://arxiv.org/abs/2505.11556): 65 hidden-profile tasks; MAS ~30% vs ~81% with full information. Frontier LLMs fail to pool distributed information (human-like).

**Distance:** conceptually the nearest ancestor. The method’s bet is that **replication-by-complement is a machine-checkable stand-in for “recognize a demonstrated solution.”** Whether NASA-style rankings *are* demonstrable enough is a plausibility question, not a novelty one.

### 3.6 The failure this method exists to fix

- **Pappu et al. (2026),** [arXiv:2602.01011](https://arxiv.org/abs/2602.01011). Synergy gaps 6–41%; leveraging not identification; integrative compromise correlates with error; larger teams worse; **adversarial robustness as the flip side of dilution**. Reveal-Expert GEPA prompts that say “copy the expert” still do not match the individual expert without *killing* discussion. No published *fix* in that paper — only a harness.
- **Davidson et al. (2025),** [The Collaboration Gap](https://arxiv.org/abs/2511.02687) (also discussed in [Horvitz’s summary](https://www.linkedin.com/posts/erichorvitz_discovery-of-an-ai-agent-collaboration-gap-activity-7391881948748632065-Dvcc)). Different setting (partial observability / maze grounding). Same slogan: agents that work alone fail together.
- Searches in August 2026 did **not** surface a follow-up paper that already “solves Pappu” with replication-gated hubs. AgentAuditor (same month as Pappu) attacks **majority vote on traces**, not the psychology ranking / synergy-gap harness. If a later paper combines exact-match quotient grouping, identity-blind complement replication, *and* multi-hub broadcast authority, this novelty grade drops to application-only.

---

## 4. Component-by-component novelty

| Component | Prior art | Novelty |
| --- | --- | --- |
| Isolated drafts | Universal (self-consistency, debate round 0, Pappu individual phase) | None |
| Exact-match coalitions | Self-consistency answer clustering; majority vote | Low. “Quotient grouping” is a naming of a standard partition. Avoiding embedding thresholds is good engineering, not a new theory. |
| Representative thesis per coalition | Best-of-N / shortest-complete CoT / logprob | Low |
| Complement-pool **re-solve** with identity hidden | Consultancy (Khan, Kenton); CoVe independent checks; LM-vs-LM cross-exam; AgentAuditor localized audit; “second LLM, given this reasoning, is the answer right?” (common production pattern, not a MAS selector) | **High as a *selection statistic* for teammates who originally disagreed.** Medium as a *verification idea*. |
| Hide author identity | Standard anti-authority control; opposite of Reveal Expert | Low as a trick; important as an *ablation against Pappu* |
| Promote hubs by max replication, mute the rest | DyLAN importance dropout; G-Designer sparsity; star topologies in MacNet | **Medium.** Score is new; “mute non-hubs” is old. |
| Multi-hub overlay (per-claim experts) | MoE routing; distributed expertise in Pappu; not usually a *runtime graph of verified sub-claims* | **Medium–high** as an alternative to global winner / single aggregator |
| Deterministic assembly of sub-claims | Ranking aggregation (Kemeny, Borda) — which this method *rejects* as averaging; constraint solving | Medium. Assembly without vote is the point; collisions will still force a synthesis LLM. |
| Programmatic manager (no LLM orchestrator) | Contrast Magentic-One / AutoGen | Low as an idea (“rules not vibes”); high as a *design constraint consistent with the diagnosis* |

**Overall novelty grade: composition novelty + application novelty. Not primitive novelty.** That is still publishable if experiments show strong synergy where debate/vote/Reveal-Expert fail.

The sentence that should appear in a related-work section:

> We do not optimize a communication graph (GPTSwarm, G-Designer, AgentNet), we do not debate-then-vote (Du, MAD, ReConcile, LMAD), and we do not train an anti-majority adjudicator over a reasoning tree (AgentAuditor). We treat a thesis as expert only if agents who *rejected* it can **independently reproduce its discrete conclusion** after seeing the reasoning without author identity, then we **broadcast only those nodes**.

If a reviewer can name a paper that does exactly that, the novelty claim is overstated. None of the sources above do.

---

## 5. Closest neighbors (ranked)

1. **Khan et al. 2024 / Kenton et al. 2024 consultancy.** Same information-flow sketch: expert-like argument → non-expert re-decision. They conclude **add an opposing debater**; this method **does not**. A reviewer will say: “You reinvented the protocol they showed is the *worse* half of debate.” The rebuttal has to be empirical: replication-as-gate + mute + multi-hub + no identity ≠ judge-picks-a-winner, and ranking/hidden-profile ≠ QuALITY. Until that experiment exists, this is the most dangerous *protocol* citation.
2. **AgentAuditor (2026).** Closest *anti-majority system*: localized audits at divergence points, ACPO against confabulation consensus, recovers minority-correct cases. Differs: trained LLM adjudicator over a reasoning tree, not identity-blind complement re-solve, not exact-match quotient coalitions, not speaking-authority rewrite. Required empirical neighbor, not a duplicate.
3. **LMAD (Gao et al. 2026).** Closest *sub-claim localization*: earliest conflict only, then commit. Differs: still debate plus a controller that judges the resolved claim; no replication rate; no hub overlay.
4. **Laughlin demonstrability / truth-supported-wins.** Theoretical parent. Humans needed *recognition* of a proof, often *two* correct members. This method asks the entire complement to reproduce — stricter than truth-wins, different from truth-supported-wins (which is a vote count among people who already believe).
5. **Irving debate / Cohen LM-vs-LM.** Cross-examination as verification. Differs: adversarial Q&A or a weak judge, not independent re-derivation of a discrete choice by originally-disagreeing teammates.
6. **DyLAN / G-Designer.** Mute or rewire agents using a score. Different score, often trained or conversational.
7. **CoVe.** Independent verification questions. Same anti-contamination instinct; no team graph.
8. **Self-consistency / CoT+MV.** The baseline this method must beat, not a cousin.

---

## 6. What looks unoccupied

Unoccupied (as of this search):

- **Complement-conditioned replication rate** as the *definition* of expertise in a heterogeneous LLM team.
- **Per-sub-claim hub overlay** constructed from that rate, with **speaking authority zero** for unverified nodes, without a learned GNN or LLM orchestrator.
- **Explicit anti-Pappu protocol**: never reveal the expert; never vote; evaluate on NASA / Lost at Sea / SBP *and* the synergy gap (team vs best member), not only vs ground truth.
- Using **failure of replication** as a hallucination filter for *other agents’* traces, then compiling a **constraint set** for a final pass.

Occupied, do not market as new:

- “Topology matters.”
- “Verify the reasoning.”
- “Decompose into claims.”
- “Don’t let everyone talk.”
- “Isolated first drafts.”
- “Audit traces instead of voting” (AgentAuditor).
- “Debate only the local conflict” (LMAD).

Honest framing: **a demonstrability protocol for LLM teams**, not “a new kind of neural graph.”

---

## 7. Plausibility analysis

Plausibility here means: *should this close the synergy gap on the intended tasks, given what we already know about LLMs?* Not: *is the code well structured?*

### 7.1 Load-bearing assumptions

The method works only if most of these are true:

| # | Assumption | If false |
| --- | --- | --- |
| A1 | A **correct** thesis is more replicable by originally-wrong agents than an **incorrect** majority thesis. | Max-replication promotes the majority (tyranny, just with extra LLM calls). |
| A2 | Listeners **condition on the logic**, not on fluency, length, or the leaked conclusion line. | Measures persuasion / sycophancy (Turpin, Sharma, Perez, Khan). |
| A3 | Hidden author identity removes authority bias without removing the only cue that would have helped. | May not matter; Pappu already found identification isn’t the bottleneck. |
| A4 | The task is **demonstrable**: outsiders can recognize a right ranking from a write-up without already holding the facts. | Expert theses **fail** to replicate (hidden facts aren’t checkable); or they replicate only by **copying leaked facts** (information pooling, not proof). |
| A5 | Per-item (or pairwise) sub-claims are the right atoms; independently verified ranks form a usable global ranking. | Assembly collisions → hub LLM synthesis → compromise among hubs, weaker version of the original bug. |
| A6 | Unanimous coalitions deserve rate 1.0 without a test. | Shared hallucinations auto-promote (especially `none` / pretraining-aligned wrong ranks). |
| A7 | Muting non-hubs does not discard unique hidden-profile facts that never became a “winning thesis.” | SBP distributed mode: four candidate-experts; if only some claims replicate, unique negative info about A/B may drop. |
| A8 | Extra Stage-3 compute is worth it vs CoT+MV (Choi). | Correct but too expensive; reviewers will demand a cost–quality Pareto. |

### 7.2 Evidence that it *could* work

- **Pappu’s own coding:** Epistemic deference correlates with *better* team L1; integrative compromise with *worse*. A protocol that *forbids* compromise channels is aimed at the measured mechanism, not a vague “alignment bad” story.
- **Reveal Expert failed.** So “just tell them who to copy” is not a solution. A non-conversational gate is a reasonable next experiment.
- **Laughlin:** On highly demonstrable intellective tasks, groups *do* match experts when a proof can be shown. If a sub-claim is closer to “compass is useless because the Moon’s field isn’t polarized” *and* listeners can evaluate that sentence, replication is the right test.
- **CoVe / independent answering:** Isolating the check from the draft reduces self-justification. Complement agents never produced the thesis, which is stronger isolation than self-CoVe.
- **Khan (debate, not consultancy):** Non-experts *can* extract truth from expert arguments **when two sides compete** and (in their setup) quotes can be verified. So “weak agents using expert text” is not hopeless; the **protocol details** matter.
- **Hidden-profile mechanics:** If the thesis *contains* the unique facts, Stage 3 is a way to **move private information into other contexts** without a free-for-all discussion that drowns it. That may close SBP’s gap *even if* the philosophical story is “verification.” Call that **replication-as-pooling**. It is still a contribution if it works; it is a different paper than “we test proofs.”

### 7.3 Evidence that it may *not* work

**Sycophancy and unfaithful CoT (high severity).**  
Turpin et al. ([arXiv:2305.04388](https://arxiv.org/abs/2305.04388)): models rationalize biased answers and omit the bias. Sharma / Perez: RLHF assistants agree with the user. Injecting a confident thesis is a **suggested answer**. Turpin’s “Suggested Answer” bias dropped accuracy by large margins. Stage 3 currently also states the candidate *conclusion* in the prompt (`describe_claim`), which makes agreement even cheaper than following the reasoning. Replication then tracks **compliance**, not demonstrability.

**Consultancy is the wrong cousin (high severity).**  
Kenton et al.: a single consultant convinces the judge **whether or not they are correct**. That is A1 failing. Debate was the mitigation (opposing thesis). This method’s Stage 3 has **no opposing thesis in the same context**. A cheap, theoretically motivated variant is **pairwise replication**: inject thesis A *and* thesis B, ask the complement to re-solve — still no conversation, still identity-free, much closer to Irving/Khan.

**Demonstrability of the first eval slice (high severity for NASA / Lost at Sea / SBP).**  
Survival ranking is only **weakly intellective**. Ground truth is an expert key (NASA / Coast Guard), not a derivation in a shared formal system. Laughlin’s condition (c) — incorrect members can *recognize* correctness — is shaky for “parachute silk vs heating unit.” Humans needed **revealed expertise** (Bonner). If LLMs cannot recognize a correct ranking from a paragraph, expert theses will not replicate unless listeners **trust the prose**. Then you have reimplemented Reveal Expert with extra tokens, except you hid the name so they trust *style* instead of identity.

**Pretraining leakage (medium–high).**  
Pappu notes models already have non-trivial NASA/Lost-at-Sea priors. Then “concentrated expertise” is a *nudge*, not exclusive knowledge. Complements may already rank oxygen first; replication of the expert looks successful for the wrong reason. Control: `expert_info_mode=none` vs `single_expert`, and check whether replication *selects the designated expert* or just the culturally default ranking.

**Hidden profiles vs proofs (high for SBP).**  
Optimal SBP ranking needs **unshared** valences. A true demonstration *must transmit those facts*. Then Stage 3 is communication of evidence, and “independent reproduction” is “I adopted your private data.” That can still beat discussion (which fails to surface unique info — Stasser, Li 2025). It does **not** validate the “hallucination vs proof” slogan. Analysis should log whether replicated theses contain the unique strings.

**Majority stability and confabulation consensus (medium–high).**  
Self-consistency works because **correct** answers are more stable under resampling *on math-like tasks*. On judgmental or prior-dominated tasks, the **modal wrong answer** is the stable one. Complements of a majority are small (often one expert). One non-replication against a majority thesis gives rate 0; the expert needs **many** listeners to flip. Variance is asymmetric and can structurally favor large coalitions unless you **normalize by complement size carefully** (you already divide by `|complement|`, which *helps* minorities — good — but a 1-person complement makes majority rate a Bernoulli with n=1). Unanimous wrong answers skip the test (A6). AgentAuditor names the correlated-error version of this: **confabulation consensus** — agents share biases and confirm the same wrong rationale. Complement replication among same-family models can *certify* that failure instead of catching it.

**Unfaithful traces as the injected object (medium).**  
Lanham et al., [Measuring Faithfulness in CoT](https://arxiv.org/abs/2307.13702): models often do not condition on their own CoT. Then “can you follow this proof?” is ill-posed: there is no proof, only a post-hoc story. VeryTrace / FACT-E (2026) try formal/causal checks because NL traces are not certificates. Ranking rationales (“oxygen is important”) are especially generic.

**Assembly (medium).**  
Independent per-item ranks will collide. Hub synthesis with “preserve as many verified placements as possible” can become **Kemeny-like averaging among hubs**. If hubs are all true experts (full-info control in Pappu almost matched the individual expert), this is fine. If hubs are a mix of lucky replicators, you are back to compromise with a smaller committee — maybe better, not the claimed qualitative shift.

**Adversarial tradeoff (medium, theoretically important).**  
Pappu: dilution **protects** against a saboteur with the worst ranking. This method **promotes** high-replication theses. A fluent adversary (their `with_ground_truth` imposter) is optimized to *sound* reasonable while pushing a bad ranking. If A2 fails, the adversary becomes a hub. Any paper must run Pappu’s adversarial condition; **improvement on synergy with a collapse on sabotage is a real tradeoff**, not a bug to hide. Possible mitigation: require replication **and** disagreement with a held-out isolated majority — still not debate, but two-sided.

**Cost (medium for adoption, high for ML-bench follow-up).**  
Stage 3 is O(claims × coalitions × complement). NASA × 4 agents × full complement is many times a 4-round debate. Pappu already subsampled ML benches because discussion is expensive. Choi implies you must beat **cheap** CoT+MV, not only expensive debate. `top2_coalitions` is an ablation of the method, not the method.

**LLM-as-judge unreliability (medium if you ever swap re-solve for “does this logic hold?”).**  
Zheng et al.; 2026 “reliability without validity” judges. The current design’s use of **parsed discrete match** is strictly better than Likert “sounds right.” Keep that. Do not “improve” Stage 3 into a judge prompt.

### 7.4 Task-wise plausibility (v1 slice)

**NASA Moon Survival / Lost at Sea (concentrated).**  
Best case: expert-only facts (compass, matches, heating unit) appear in the thesis; listeners **update those item ranks** because the mechanism is stated, and those items are the ones majority gets wrong. Then L1 can drop without full permutation assembly working.  
Worst case: listeners already know oxygen > matches; they “replicate” the easy items; they **do not** move compass; hubs look expert-like on the obvious and majority-like on the actual expertise. Synergy gap barely moves.  
Prior: mixed. Run item-level: replication rate vs |rank − ground truth| per item.

**Same tasks, distributed.**  
Multi-hub is *more* plausible: each agent is expert on a subset of items; per-claim hubs match the generative process. This is the setting where “not a global winner” is actually load-bearing. Prior: **better than concentrated**, if A4 holds per item.

**Student Body President.**  
If theses quote unique valences, Stage 3 is **information pooling by quotation**. That is a reasonable attack on hidden profiles (Li 2025 / Stasser). If the prompt forbids treating injected text as new evidence, the expert cannot demonstrate. The current prompt says listeners *may* use the analysis if convincing — i.e. pooling is allowed. Prior: **plausible as pooling, weak as pure verification.** Report both mechanisms.

**Later ML benches (GPQA, HLE, MATH).**  
Math: A1 is most plausible (demonstrable, self-consistency literature). GPQA/HLE: expert changes per item; multi-hub is the right picture; A2/A4 still bind. Do not claim v1 results generalize here.

### 7.5 Predicted outcomes (pre-registered style)

These are guesses to make the analysis falsifiable:

1. vs `majority_drafts`: small gain on NASA concentrated, larger on SBP distributed **if** unique facts appear in theses.
2. vs `isolated_best` (oracle): still a gap; the method has no access to L1 at selection time.
3. vs `majority_tyranny`: this is the real test of A1. If RGBT ≈ majority_tyranny, replication is not adding information.
4. vs `global_winner`: distributed SBP should prefer multi-hub; concentrated NASA might not care.
5. Adversarial `with_ground_truth`: **RGBT worse than debate** if sycophancy dominates.
6. Ablation: hide the conclusion sentence in Stage 3 (rationale only). If rates stay high, listeners are following logic or leaking from the rationale’s last line; if rates collapse, they were matching `describe_claim`.
7. Ablation: two-thesis injection (A vs B). If this beats single-thesis, Kenton/Khan apply and the current Stage 3 should change.

---

## 8. What would make this a strong paper vs a clever workflow

**Strong paper**

- Beats CoT+MV and Pappu discussion on **relative synergy gap**, not only raw L1, with the same models/seeds/info modes. Compare also to an AgentAuditor-style localized-audit / anti-majority judge if that protocol can be run on the psychology ranking traces.
- Shows **hub set recovers designated experts** *and* that this recovery **causes** the L1 drop (mediation / counterfactual mute).
- Shows replication rate **correlates with item-level correctness** and **anti-correlates with coalition size** when the majority is wrong (A1).
- Survives or honestly maps the **adversarial tradeoff**.
- Cost table: tokens vs debate vs vote.
- Mechanism section: pooling vs proof (string overlap of unique info in replicated theses).

**Incremental workflow**

- Only beats noisy debate, not majority of drafts.
- Hubs are just the majority.
- Gains vanish when the conclusion is not printed in the Stage-3 prompt.
- Only works in `full` information (four experts) — then you have Pappu’s Appendix D result (discussion among experts is fine) with more steps.

---

## 9. Recommended falsification experiments (cheap first)

Already partly encoded as YAML; worth treating as a **claim checklist**, not a backlog dump:

1. `majority_tyranny` vs full method (A1).
2. Stage-3 prompt without `describe_claim` (A2).
3. Pairwise thesis injection (consultancy vs debate).
4. Correlate replication with ground-truth item error; report singleton-expert Bernoulli variance.
5. SBP: fraction of unique-info strings in winning theses.
6. Pappu adversarial agent.
7. `cross_examine: top2` Pareto.
8. Human check: do replicators’ new rationales **reuse** the injected argument or **regenerate** it? Regeneration is closer to “understood”; copy-paste of ranks with a new story is sycophancy.

---

## 10. Conclusion

**Novelty.** Legitimate **composition**: demonstrability-as-replication-rate × identity-free complement test × multi-hub mute × no terminal vote, aimed at a 2026 result that existing MAS topologies and debate protocols do not address. Do not claim to have invented verification, topology, or claim decomposition. Closest *systems* are **AgentAuditor** and **LMAD**; the dangerous *protocol* neighbor is still **scalable-oversight consultancy**, not GPTSwarm.

**Plausibility.** The *purpose* (stop averaging experts away) is well supported by Pappu, Choi, Laughlin, and hidden-profile work. The *instrument* (single-thesis re-solve) is **the protocol the oversight literature found easiest to fool**. On NASA-like rankings, demonstrability is historically weak, so the first eval slice is a **harsh** test — which is good science if you report failures, and a trap if you only ship happy seeds.

**Practical stance for this repo.** Keep the modular ablations; they *are* the novelty/plausibility experiment. The highest-leverage design change suggested by outside work is to make Stage 3 **two-sided** (competing theses, still no conversation, still no names) before investing in ML-bench scale. Treat sycophancy, unanimous auto-pass, and adversarial hubs as first-class metrics beside L1.

### Key URLs

- Pappu et al.: https://arxiv.org/abs/2602.01011  
- AgentAuditor: https://arxiv.org/abs/2602.09341  
- LMAD: https://arxiv.org/abs/2608.01463  
- Du debate: https://arxiv.org/abs/2305.14325  
- Choi debate vs vote: https://arxiv.org/abs/2508.17536  
- Khan persuasive debate: https://arxiv.org/abs/2402.06782  
- Kenton scalable oversight: https://arxiv.org/abs/2407.04622  
- Irving debate: https://arxiv.org/abs/1805.00899  
- Cohen LM vs LM: https://aclanthology.org/2023.emnlp-main.778/  
- ReConcile: https://arxiv.org/abs/2309.13007  
- Mixture-of-Agents: https://arxiv.org/abs/2406.04692  
- Self-consistency: https://arxiv.org/abs/2203.11171  
- DyLAN: https://arxiv.org/abs/2310.02170  
- GPTSwarm: https://proceedings.mlr.press/v235/zhuge24a.html  
- G-Designer: https://arxiv.org/abs/2410.11782  
- AgentNet: https://arxiv.org/abs/2504.00587  
- MacNet: https://arxiv.org/abs/2406.07155  
- Lightman PRM: https://arxiv.org/abs/2305.20050  
- CoVe: https://aclanthology.org/2024.findings-acl.212/  
- Turpin unfaithful CoT: https://arxiv.org/abs/2305.04388  
- Sharma sycophancy: https://arxiv.org/abs/2310.13548  
- FActScore: https://arxiv.org/abs/2305.14251  
- Lanham CoT faithfulness: https://arxiv.org/abs/2307.13702  
- MAD: https://arxiv.org/abs/2305.19118  
- HiddenBench: https://arxiv.org/abs/2505.11556  
- Collaboration Gap: https://arxiv.org/abs/2511.02687  
