# Troubleshooting

## Submodule / import errors

`ModuleNotFoundError: teamwork` or empty `third_party/teamwork`:

```bash
git submodule update --init --recursive
```

The adapter adds `third_party/teamwork` to `sys.path`. Importing a paper task also imports `teamwork.backends`, which needs the `openai` and `anthropic` packages from `pip install -e .`.

## Azure 401 / deployment not found

- Do **not** pass `AZURE_OPENAI_API_VERSION`. The client is `OpenAI(base_url="https://<resource>.openai.azure.com/openai/v1/")` with the Azure `api-key` header ([API version lifecycle](https://learn.microsoft.com/en-us/azure/foundry/openai/api-version-lifecycle)).
- `backend.model` (or `--model`) must be the **deployment name** in the Foundry portal.
- Default resource endpoint: `https://<resource>.openai.azure.com`. A `*.services.ai.azure.com` resource host is rewritten to `*.openai.azure.com`.
- Foundry **project** URLs (`.../api/projects/<project>`) are left on `services.ai.azure.com` and still get `/openai/v1/` appended.

`provider` accepts `azure`, `azure_openai`, and `foundry` (same client).

## OpenAI 401

`.env` not loaded, or a stale key. The runner calls `load_dotenv()` from the process working directory. Run from the repo root.

## Incomplete ranking / parse errors

Paper parsers require a `MY RANKING:` numbered list using item names close to the canonical strings. Failed parses get `worst_score` and are dropped from coalitions. Check `drafts.*.parse_error` in the JSONL trace.

If Stage 5 assembly fails, metadata `synthesis_mode` becomes `constraint_preserving_hubs` (or the run errors if `synthesis: assemble_only`).

## Stage 3 is slow or expensive

Expected: up to `(claims × coalitions × complement size)` completions. Mitigations:

```yaml
cross_examine: top2_coalitions
task: student_body_president
n_agents: 2
claim_schema: per_item_rank    # not pairwise_order
```

## `cross_examine: skip` did not change hubs

`max_replication` with no replication results cannot distinguish theses. Use `configs/majority_tyranny.yaml` (`topology_policy: majority_size`).

## Tests skipped or live smoke ran against a bad key

Default `pytest` skips live calls. Live smoke runs only if `EXPERT_CHOICE_LIVE=1`. A present-but-invalid `OPENAI_API_KEY` does not enable it.

Windows pytest `tmp_path` `Access is denied` is why pipeline tests write a local file under `tests/` and delete it.

## Editable install not picking up code

```bash
pip install -e ".[dev]"
python -c "import expert_choice; print(expert_choice.__file__)"
```

Confirm that path is this repo, not another copy.

## Do not

- Call `Task.execute()` on paper objects (that is the debate protocol)
- Reveal expert identity in Stage 3 prompts
- Cluster sub-claims with embeddings
- Put API keys in YAML or traces you share (traces include prompt text and may include hidden expert facts — treat `outputs/` as sensitive)
