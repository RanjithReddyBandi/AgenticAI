"""DeepEval runner stub for the ShoppingAssistant evaluation."""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import List, Dict, Any

from evaluation.models import EvaluationCase, MetricResult, pass_state
from evaluation_deepeval.models import GroqDeepEvalModel

def _load_cases(dataset_path: str) -> List[EvaluationCase]:
    cases: List[EvaluationCase] = []
    with open(dataset_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            cases.append(EvaluationCase(**json.loads(line)))
    return cases

def run_deepeval_evaluation(
    dataset_path: str = 'evaluation/datasets/smoke.jsonl',
    selected_metrics: List[str] | None = None,
) -> Dict[str, Any]:
    """Run a DeepEval-style evaluation.
    This stub does **not** invoke the real agent or external services; it returns
    static mocked scores via :class:GroqDeepEvalModel for the requested metric
    IDs.
    """
    if selected_metrics is None:
        # Use the three live metrics defined in the spec.
        selected_metrics = ['answer_relevancy', 'faithfulness', 'tool_correctness']
    # Load cases – we still need case IDs for the report.
    cases = _load_cases(dataset_path)
    model = GroqDeepEvalModel()
    report: Dict[str, Any] = {
        'case_count': len(cases),
        'metrics': selected_metrics,
        'results': [],
    }
    # Mock a generic response and empty events for each case.
    mock_response: Dict[str, Any] = {
        'recommendations': [],
        'comparisons': [],
        'explanation': 'Mocked response for DeepEval demo.',
    }
    mock_events: List[Any] = []
    for case in cases:
        case_entry: Dict[str, Any] = {'case_id': case.id, 'metrics': {}}
        for metric in selected_metrics:
            metric_res = model.evaluate(case, mock_response, mock_events, metric)
            case_entry['metrics'][metric] = {
                'score': metric_res.score,
                'passed': metric_res.passed,
                'rationale': metric_res.rationale,
            }
        report['results'].append(case_entry)
    return report