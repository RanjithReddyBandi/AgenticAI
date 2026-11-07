"""LLM judge metric wrappers (Groq-backed, optional)."""

from __future__ import annotations

import os
from typing import Any

from evaluation.models import (
    EvaluationCase,
    LLM_JUDGE_METRICS,
    MetricResult,
    ToolEvent,
    normalize_judge_score,
    pass_state,
)

JUDGE_METRIC_IDS = LLM_JUDGE_METRICS


def _build_prompt(case, response, events, metric_id):
    tools = ", ".join(event.name for event in events if event.error is None) or "none"
    return (
        "You are an evaluator. Score the shopping assistant response for metric "
        f"{metric_id} on a 1-5 scale.\n"
        f"Query: {case.query}\n"
        f"Checks: {case.checks}\n"
        f"Tools called: {tools}\n"
        f"Response: {response}\n"
        "Reply with a single integer from 1 to 5 and a one-sentence rationale."
    )


def _parse_response(text):
    for token in text.split():
        cleaned = token.strip(".,;:()")
        if cleaned.isdigit() and 1 <= int(cleaned) <= 5:
            return float(cleaned), text.strip()
    raise ValueError(f"Could not parse judge score from: {text!r}")


def evaluate_judge(metric_id, case, response, events, client=None):
    if metric_id not in JUDGE_METRIC_IDS:
        return MetricResult(
            metric_id=metric_id,
            evaluator="llm_judge",
            score=None,
            passed=None,
            rationale="",
            error=f"Unknown judge metric: {metric_id}",
        )
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        return MetricResult(
            metric_id=metric_id,
            evaluator="llm_judge",
            score=None,
            passed=None,
            rationale="",
            error="GROQ_API_KEY is not configured.",
        )
    if client is None:
        from langchain_groq import ChatGroq

        client = ChatGroq(
            model=os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"),
            temperature=0,
            max_tokens=200,
            api_key=api_key,
        )
    prompt = _build_prompt(case, response, events, metric_id)
    message = client.invoke(prompt)
    raw_score, rationale = _parse_response(getattr(message, "content", str(message)))
    score = normalize_judge_score(raw_score)
    return MetricResult(
        metric_id=metric_id,
        evaluator="llm_judge",
        score=score,
        passed=pass_state(score),
        rationale=rationale,
    )