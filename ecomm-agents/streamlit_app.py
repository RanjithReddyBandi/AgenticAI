"""Streamlit chat interface for the smart shopping assistant."""

from __future__ import annotations

import queue
import threading
import time
from typing import Any
from streamlit_eval_tabs import render_evaluation_tab

import streamlit as st

from smart_shopping_agent import _redact, run_shopping_request


def _safe_error(error: Exception) -> str:
    return str(_redact(str(error)))


def _render_response(response: dict[str, Any]) -> None:
    st.markdown(response["explanation"])
    for recommendation in response["recommendations"]:
        with st.container(border=True):
            st.subheader(recommendation["name"])
            st.caption(f"Product ID: {recommendation['product_id']}")
            st.write(f"**Price:** {recommendation['price']}")
            st.write(f"**Discount:** {recommendation['discount']}")
            st.write(
                "**Availability:** "
                + ("In stock" if recommendation["stock"] else "Out of stock")
            )
            st.write(f"**Reviews:** {recommendation['reviews']}")

    if response["comparisons"]:
        st.subheader("Comparisons")
        for comparison in response["comparisons"]:
            with st.expander(f"Product {comparison['product_id']}"):
                left, right = st.columns(2)
                left.markdown("**Pros**")
                for pro in comparison["pros"]:
                    left.markdown(f"- {pro}")
                right.markdown("**Cons**")
                for con in comparison["cons"]:
                    right.markdown(f"- {con}")

    with st.expander("Validated JSON response"):
        st.json(response)


def _render_debug_log(
    placeholder: Any,
    request_log: dict[str, Any],
    current: bool,
) -> None:
    with placeholder.container():
        st.subheader("LLM Debug Log")
        if current:
            st.caption(f"Request: {request_log['query']} (running)")
        else:
            st.caption(f"Request: {request_log['query']}")
        st.json(request_log["events"])
        if request_log.get("error"):
            st.error(request_log["error"])
        elif request_log.get("response") is not None:
            st.json({"structured_final_response": request_log["response"]})


st.set_page_config(
    page_title="Smart Shopping Assistant",
    page_icon=":material/shopping_bag:",
)
st.title("Smart Shopping Assistant")
st.caption("Ask for products, budgets, or comparisons.")

# session state initialization
if "shopping_messages" not in st.session_state:
    st.session_state.shopping_messages = []
if "shopping_debug_logs" not in st.session_state:
    st.session_state.shopping_debug_logs = []

with st.sidebar:
    st.title("LLM Debug Log")
    debug_placeholder = st.empty()
    if st.session_state.shopping_debug_logs:
        for log in reversed(st.session_state.shopping_debug_logs):
            with st.expander(log["query"], expanded=False):
                st.json(log["events"])
                if log.get("error"):
                    st.error(log["error"])
                elif log.get("response") is not None:
                    st.json({"structured_final_response": log["response"]})
    else:
        st.caption("Request details will appear here.")

# Two main tabs: Chat and Evaluation
chat_tab, eval_tab = st.tabs(["Chat", "Evaluation"])

# ---- Chat tab -------------------------------------------
with chat_tab:
    for turn in st.session_state.shopping_messages:
        with st.chat_message(turn["role"]):
            if turn["role"] == "user":
                st.markdown(turn["content"])
            elif turn.get("error"):
                st.error(turn["error"])
            elif turn.get("response") is not None:
                _render_response(turn["response"])

    query = st.chat_input("What product are you looking for?")
    if query:
        st.session_state.shopping_messages.append({"role": "user", "content": query})

        request_events: queue.Queue[dict[str, Any]] = queue.Queue()
        request_log: dict[str, Any] = {
            "query": _redact(query),
            "events": [],
            "response": None,
            "error": None,
        }
        st.session_state.shopping_debug_logs.append(request_log)

        result: dict[str, Any] = {}
        failure: list[Exception] = []

        def run_request() -> None:
            try:
                result["response"] = run_shopping_request(query, request_events)
            except Exception as error:
                failure.append(error)

        worker = threading.Thread(target=run_request, daemon=True)
        worker.start()
        _render_debug_log(debug_placeholder, request_log, current=True)

        with st.chat_message("assistant"):
            progress = st.empty()
            progress.info("Searching the catalogue and checking product details…")
            while worker.is_alive() or not request_events.empty():
                try:
                    request_log["events"].append(request_events.get(timeout=0.1))
                except queue.Empty:
                    pass
                _render_debug_log(debug_placeholder, request_log, current=True)
                time.sleep(0.05)
            worker.join()
            while not request_events.empty():
                request_log["events"].append(request_events.get_nowait())

            if failure:
                error_message = _safe_error(failure[0])
                request_log["error"] = error_message
                progress.empty()
                st.error(f"Shopping request failed: {error_message}")
                st.session_state.shopping_messages.append(
                    {"role": "assistant", "error": error_message}
                )
            else:
                response = result["response"]
                request_log["response"] = _redact(response)
                progress.empty()
                _render_response(response)
                st.session_state.shopping_messages.append(
                    {"role": "assistant", "response": response}
                )
            _render_debug_log(debug_placeholder, request_log, current=False)
# ---- Evaluation tab ---------------------------------------------
with eval_tab:
    render_evaluation_tab()