from __future__ import annotations

import streamlit as st

from evaluation_deepeval.runner import run_deepeval_evaluation


def render_deepeval_tab() -> None:
    st.subheader("DeepEval (mocked)")
    if st.button("Run DeepEval", key="deepeval_run"):
        try:
            report = run_deepeval_evaluation()
            st.json(report)
        except Exception as exc:
            st.error(str(exc))
