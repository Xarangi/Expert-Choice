from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from expert_choice.eval.logging import write_summary, write_trace
from expert_choice.pipeline.config import PipelineConfig
from expert_choice.pipeline.factory import build_orchestrator


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run replication-gated broadcast topology on psychology ranking tasks."
    )
    parser.add_argument(
        "--config",
        default="configs/replication_broadcast.yaml",
        help="YAML pipeline config",
    )
    parser.add_argument("--task", help="moon_survival | lost_at_sea | student_body_president")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--n-agents", type=int)
    parser.add_argument("--expert-info-mode")
    parser.add_argument("--backend", help="openai | azure | mock")
    parser.add_argument("--model", help="OpenAI model or Azure deployment name")
    parser.add_argument("--output-dir")
    parser.add_argument(
        "--claim-schema",
        help="per_item_rank | pairwise_order | rank_buckets | global_ranking",
    )
    parser.add_argument("--topology-policy")
    parser.add_argument("--cross-examine")
    return parser.parse_args(argv)


def apply_overrides(config: PipelineConfig, args: argparse.Namespace) -> PipelineConfig:
    updates: dict = {}
    if args.task:
        updates["task"] = args.task
    if args.seed is not None:
        updates["seed"] = args.seed
    if args.n_agents is not None:
        updates["n_agents"] = args.n_agents
    if args.expert_info_mode:
        updates["expert_info_mode"] = args.expert_info_mode
    if args.output_dir:
        updates["output_dir"] = args.output_dir
    if args.claim_schema:
        updates["claim_schema"] = args.claim_schema
    if args.topology_policy:
        updates["topology_policy"] = args.topology_policy
    if args.cross_examine:
        updates["cross_examine"] = args.cross_examine
    backend = config.backend.model_copy()
    if args.backend:
        backend.provider = args.backend
    if args.model:
        backend.model = args.model
    updates["backend"] = backend
    return config.model_copy(update=updates)


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = parse_args(argv)
    config = apply_overrides(PipelineConfig.from_yaml(args.config), args)
    orchestrator = build_orchestrator(config)
    state = orchestrator.run()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(config.output_dir)
    trace_path = out_dir / "traces" / f"{config.task}_{config.method}_{config.seed}_{stamp}.jsonl"
    summary_path = out_dir / "summaries" / f"{config.task}_{config.method}_{config.seed}_{stamp}.json"
    write_trace(trace_path, state)
    write_summary(
        summary_path,
        {
            "task": config.task,
            "method": config.method,
            "seed": config.seed,
            "expert_info_mode": config.expert_info_mode,
            "backend": config.backend.model_dump(),
            "metrics": state.metrics,
            "metadata": state.metadata,
            "final_solution": state.final_solution,
            "trace": str(trace_path),
        },
    )
    print(f"task={config.task} method={config.method} seed={config.seed}")
    print(f"team_l1={state.metrics.get('team_l1')}")
    print(f"best_individual_l1={state.metrics.get('best_individual_l1')}")
    print(f"relative_synergy_gap={state.metrics.get('relative_synergy_gap')}")
    print(f"wrote {trace_path}")
    print(f"wrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
