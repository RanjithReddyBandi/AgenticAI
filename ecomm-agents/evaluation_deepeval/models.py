from __future__ import annotations
import os
from typing import Any, Dict, List

from evaluation.models import EvaluationCase, ToolEvent, MetricResult

class GroqDeepEvalModel:
    """A lightweight placeholder for the DeepEval integration.
    It does not require the real DeepEval package; it returns a static mock
    score for the requested metric.
    """
    def __init__(self, api_key: str | None = None, model_name: str | None = None):
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        if not self.api_key or self.api_key == 'your_groq_api_key_here':
            raise RuntimeError('GROQ_API_KEY is missing or invalid. DeepEval cannot run.')
        self.model_name = model_name or os.getenv('GROQ_MODEL', 'qwen/qwen3.8-27b')
        # Real DeepEval client would be instantiated here lazily.

    def evaluate(self, case: EvaluationCase, response: Dict[str, Any], events: List[ToolEvent], metric_name: str) -> MetricResult:
        """Return a static mocked metric score.
        In production this would invoke the Groq-backed DeepEval model.
        """
        # Simple deterministic mock: always return a high score.
        return MetricResult(
            metric_id=metric_name,
            evaluator='deepeval',
            score=0.9,
            passed=True,
            rationale='Mocked DeepEval score for demonstration.',
        )