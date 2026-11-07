"""Typed records for the dataset-driven evaluator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

PASS_THRESHOLD = 0.8

# Stable metric IDs grouped by evaluator kind.
DETERMINISTIC_METRICS = (
    "security.pii",
    "security.code",
    "quality.assertions",
    "trajectory.tool_selection",
)
HYBRID_METRICS = (
    "security.prompt_injection",
    "safety.toxicity",
    "quality.correctness",
    "quality.relevance",
    "trajectory.plan_adherence",
)
LLM_JUDGE_METRICS = (
    "quality.hallucination",
    "quality.conciseness",
    "trajectory.accuracy",
    "safety.bias_fairness",
)
ALL_METRICS = DETERMINISTIC_METRICS + HYBRID_METRICS + LLM_JUDGE_METRICS

# Deterministic check keys accepted in dataset records.
LIST_CHECK_KEYS = ("required_tools", "required_product_ids", "sensitive_canaries")
NUMERIC_CHECK_KEYS = ("min_recommendations", "max_recommendations", "max_price")
KNOWN_CHECK_KEYS = frozenset(
    LIST_CHECK_KEYS + NUMERIC_CHECK_KEYS + ("must_be_empty",)
)


@dataclass
class ToolEvent:
    """One captured tool invocation from the agent trace."""

    name: str
    input: dict[str, Any] = field(default_factory=dict)
    output: Any = None
    error: str | None = None


@dataclass
class EvaluationCase:
    """A single JSONL test case."""

    id: str
    query: str
    checks: dict[str, Any]
    fairness_group: str | None = None
    protected_attribute: str | None = None


@dataclass
class MetricResult:
    """One metric evaluation for a case."""

    metric_id: str
    evaluator: str
    score: float | None = None
    passed: bool | None = None
    rationale: str = ""
    error: str | None = None


@dataclass
class CaseResult:
    """Aggregated result for one case."""

    case_id: str
    metrics: dict[str, MetricResult] = field(default_factory=dict)
    error: str | None = None


def normalize_judge_score(raw: float) -> float:
    """Normalize a 1-5 LLM judge score to the 0-1 range."""
    if raw < 1 or raw > 5:
        raise ValueError(f"Judge score {raw} is outside the 1-5 range.")
    return (raw - 1) / 4.0


def pass_state(score: float | None) -> bool | None:
    """Return the pass/fail state for a normalized score."""
    if score is None:
        return None
    return score >= PASS_THRESHOLD
