from expert_choice.stages.baselines import IsolatedBestSelectStage, MajorityAggregateStage
from expert_choice.stages.cross_examine import CrossExamineStage
from expert_choice.stages.grouping import GroupingStage
from expert_choice.stages.isolated_drafts import IsolatedDraftsStage
from expert_choice.stages.reconstruct import ReconstructStage
from expert_choice.stages.synthesize import SynthesizeStage

STAGE_CLASSES = {
    "isolated_drafts": IsolatedDraftsStage,
    "grouping": GroupingStage,
    "cross_examine": CrossExamineStage,
    "reconstruct": ReconstructStage,
    "synthesize": SynthesizeStage,
    "majority_aggregate": MajorityAggregateStage,
    "isolated_best_select": IsolatedBestSelectStage,
}


def build_stage(name: str):
    try:
        return STAGE_CLASSES[name]()
    except KeyError as exc:
        raise ValueError(f"Unknown stage: {name}") from exc
