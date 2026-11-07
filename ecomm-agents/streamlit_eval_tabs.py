"""Utility module for Streamlit UI that runs the three evaluation suites.

The original repository ships a deterministic evaluator (pure Python) and
a stubbed DeepEval runner.  A hard‑coded reference evaluator does not exist,
so the UI simply informs the user that it is unavailable.

The module deliberately performs imports lazily—only when the user selects a
particular evaluation—to keep the Streamlit app start‑up fast.  For the
deterministic path we create a minimal *mock* response because the real
shopping request would require a running LLM.  This is sufficient for a UI demo.
"""

from __future__ import annotations

import json
import streamlit as st
from pathlib import Path


def _load_cases(dataset_path: str) -> list[dict]:
    """Read a JSONL dataset and return a list of dicts.

    The function is tolerant of malformed lines—it simply skips them—so the
    UI never crashes because of a single bad entry.
    """
    cases: list[dict] = []
    # Ensure the directory exists (the tests expect the file to be present)
    Path(dataset_path).parent.mkdir(parents=True, exist_ok=True)
    with open(dataset_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                cases.append(json.loads(line))
            except Exception:
                # Silently ignore malformed JSON lines – they are not critical
                continue
    return cases


def render_evaluation_tab() -> None:
    """Render a Streamlit tab that lets a user run any of the three evaluations.

    * **Deterministic** – uses ``evaluation.metrics.deterministic`` and runs
      the metric functions against a mocked response.

    * **DeepEval** – calls the stub ``evaluation_deepeval.runner`` which
      returns a static mock report.

    * **Hardcoded Reference** – not implemented in this repository; the UI
      will display an informational message.
    """
    st.subheader("🧪 Run Evaluations")
    choice = st.radio(
        "Select evaluation",
        ["Deterministic", "DeepEval", "Hardcoded Reference"],
    )

    # Resolve the dataset path relative to this file so it works regardless of
    # the current working directory when Streamlit runs.
    dataset_path = str(Path(__file__).parent / "evaluation" / "datasets" / "smoke.jsonl")

    if choice == "Deterministic":
        try:
            from evaluation.models import EvaluationCase
            from evaluation.metrics.deterministic import evaluate_deterministic
        except Exception as exc:
            st.error(f"Could not import deterministic evaluator: {exc}")
            return

        cases_json = _load_cases(dataset_path)
        st.write(f"Loaded {len(cases_json)} cases.")
        for idx, case_dict in enumerate(cases_json):
            case = EvaluationCase(**case_dict)
            mock_response = {
                "recommendations": [],
                "comparisons": [],
                "explanation": "[Mocked response]",
            }
            mock_events: list = []
            results = evaluate_deterministic(case, mock_response, mock_events)
            st.markdown(f"**Case {idx + 1}: {case.id}**")
            st.json({res.metric_id: res.score for res in results})

    elif choice == "DeepEval":
        try:
            from evaluation_deepeval.runner import run_deepeval_evaluation
        except Exception as exc:
            st.error(f"Could not import DeepEval runner: {exc}")
            return

        with st.spinner("Running DeepEval …"):
            try:
                report = run_deepeval_evaluation(dataset_path=dataset_path)
                st.json(report)
            except Exception as exc:
                st.error(f"DeepEval evaluation failed: {exc}")

    else:  # Hardcoded Reference – not available in this repo
        st.info("Hard‑coded reference evaluation is not available in this repository.")