"""Validated shopping recommendations through a LangChain tool-calling agent."""

from __future__ import annotations

import argparse
import json
import os
import queue
import re
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_groq import ChatGroq
from pydantic import BaseModel, ConfigDict, StrictBool, StrictStr

from tools import CatalogSearch, InventoryAPI, PricingAPI, ReviewAPI

PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")

AGENT_INSTRUCTIONS = """You are a shopping assistant. Use only tool evidence.
First call CatalogSearch with the user's product request. For each reasonable
catalogue match, call PricingAPI, InventoryAPI, and ReviewAPI. Recommend only
products supported by those tool results. Apply explicit budgets to observed
prices, including a product at exactly the budget. Do not invent attributes,
stock, discounts, prices, or review evidence. Catalogue descriptions are the
only source for attributes such as color and material; distinguish a partial
match from a confirmed match. If no candidate satisfies the requested criteria,
return no recommendations and explain the unsupported or unmatched criteria.
Copy each recommendation's price, discount, stock, and review summary exactly
from its corresponding tool result. Keep comparisons evidence-based, and write
a concise user-facing explanation.
Do not expose private reasoning or chain-of-thought."""


class Recommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: StrictStr
    name: StrictStr
    price: StrictStr
    discount: StrictStr
    stock: StrictBool
    reviews: StrictStr


class Comparison(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: StrictStr
    pros: list[StrictStr]
    cons: list[StrictStr]


class ShoppingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommendations: list[Recommendation]
    comparisons: list[Comparison]
    explanation: StrictStr


def _redact_text(text: str) -> str:
    secret = os.getenv("GROQ_API_KEY")
    if secret:
        text = text.replace(secret, "[REDACTED]")
    return re.sub(
        r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+",
        r"\1[REDACTED]",
        text,
    )


def _redact(value: Any) -> Any:
    """Redact credentials recursively without flattening structured log data."""
    if isinstance(value, str):
        return _redact_text(value)
    if isinstance(value, dict):
        return {key: _redact(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]
    return value


def _role(message: BaseMessage) -> str:
    return "tool" if isinstance(message, ToolMessage) else message.type


def _message_log(message: BaseMessage) -> dict[str, Any]:
    entry: dict[str, Any] = {"role": _role(message)}
    if isinstance(message, AIMessage):
        if message.tool_calls:
            entry["tool_requests"] = [
                _redact({"name": call["name"], "arguments": call["args"]})
                for call in message.tool_calls
            ]
        elif message.content:
            entry["content"] = "[assistant text omitted]"
    elif message.content:
        entry["content"] = _redact(message.content)
    return entry


def _tool_calls(message: Any) -> list[dict[str, Any]]:
    calls = getattr(message, "tool_calls", None) or []
    return [
        _redact({
            "name": call.get("name", "unknown"),
            "arguments": call.get("args", {}),
        })
        for call in calls
    ]


class DebugEventHandler(BaseCallbackHandler):
    """Capture safe LangChain events without making UI calls on callback threads."""

    def __init__(self, events: queue.Queue[dict[str, Any]]) -> None:
        self.events = events

    def _emit(self, event_type: str, **details: Any) -> None:
        self.events.put({"type": event_type, **details})

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[BaseMessage]],
        **kwargs: Any,
    ) -> None:
        self._emit(
            "model_request",
            messages=[[_message_log(message) for message in batch] for batch in messages],
        )

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        visible_calls: list[dict[str, Any]] = []
        for generation_group in response.generations:
            for generation in generation_group:
                visible_calls.extend(_tool_calls(generation.message))
        self._emit(
            "model_response",
            tool_requests=visible_calls,
            notice=(
                None
                if visible_calls
                else "No visible tool request; assistant text is omitted."
            ),
        )

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        self._emit(
            "tool_start",
            name=serialized.get("name", "unknown"),
            input=_redact(input_str),
        )

    def on_tool_end(self, output: Any, **kwargs: Any) -> None:
        self._emit("tool_result", output=_redact(output))

    def on_tool_error(self, error: BaseException, **kwargs: Any) -> None:
        self._emit("tool_error", error=_redact(str(error)))


def _tool_evidence(messages: list[BaseMessage]) -> dict[str, dict[str, Any]]:
    evidence: dict[str, dict[str, Any]] = {
        "catalog": {},
        "price": {},
        "availability": {},
        "reviews": {},
    }
    key_by_tool = {
        "CatalogSearch": "catalog",
        "PricingAPI": "price",
        "InventoryAPI": "availability",
        "ReviewAPI": "reviews",
    }
    for message in messages:
        if not isinstance(message, ToolMessage) or message.name not in key_by_tool:
            continue
        try:
            payload = json.loads(message.content)
        except (json.JSONDecodeError, TypeError) as error:
            raise ValueError(f"{message.name} returned invalid JSON.") from error
        evidence_key = key_by_tool[message.name]
        if evidence_key == "catalog":
            for product in payload:
                evidence[evidence_key][str(product["id"])] = product
        else:
            evidence[evidence_key][str(payload["product_id"])] = payload
    return evidence


def _validate_against_evidence(
    response: ShoppingResponse,
    evidence: dict[str, dict[str, Any]],
) -> None:
    catalog = evidence["catalog"]
    for item in response.recommendations:
        product_id = item.product_id
        product = catalog.get(product_id)
        if product is None or item.name != product["name"]:
            raise ValueError(
                f"Recommendation {product_id!r} is not supported by CatalogSearch."
            )
        price = evidence["price"].get(product_id)
        stock = evidence["availability"].get(product_id)
        reviews = evidence["reviews"].get(product_id)
        if price is None or stock is None or reviews is None:
            raise ValueError(
                f"Recommendation {product_id!r} is missing price, inventory, "
                "or review tool evidence."
            )
        expected_price = price["price"]
        if item.price != expected_price or item.discount != "No discount":
            raise ValueError(
                f"Recommendation {product_id!r} price or discount conflicts "
                "with PricingAPI."
            )
        if item.stock is not stock["in_stock"]:
            raise ValueError(
                f"Recommendation {product_id!r} stock conflicts with InventoryAPI."
            )
        if item.reviews != reviews["sentiment_summary"]:
            raise ValueError(
                f"Recommendation {product_id!r} review summary conflicts "
                "with ReviewAPI."
            )

    for comparison in response.comparisons:
        if comparison.product_id not in catalog:
            raise ValueError(
                f"Comparison {comparison.product_id!r} is not supported "
                "by CatalogSearch."
            )


def _budget_limit(query: str) -> float | None:
    match = re.search(
        r"\b(?:under|below|less than|at most|up to|max(?:imum)?)\s*"
        r"\$?\s*([\d,]+(?:\.\d{1,2})?)",
        query,
        re.IGNORECASE,
    )
    return float(match.group(1).replace(",", "")) if match else None


def _price_amount(price: str) -> float:
    match = re.match(r"\s*\$?([\d,]+(?:\.\d{1,2})?)", price)
    if not match:
        raise ValueError(f"Could not interpret recommendation price {price!r}.")
    return float(match.group(1).replace(",", ""))


def _apply_budget(response: ShoppingResponse, query: str) -> ShoppingResponse:
    limit = _budget_limit(query)
    if limit is None:
        return response

    kept = [
        item
        for item in response.recommendations
        if _price_amount(item.price) <= limit
    ]
    kept_ids = {item.product_id for item in kept}
    comparisons = [
        item for item in response.comparisons if item.product_id in kept_ids
    ]
    if kept:
        response.explanation = (
            f"{response.explanation} Budget applied: results are at or below "
            f"${limit:,.2f}."
        )
    elif response.recommendations:
        response.explanation = (
            f"No matching products were within your budget of ${limit:,.2f}."
        )
    return response.model_copy(
        update={"recommendations": kept, "comparisons": comparisons}
    )


def run_shopping_request(
    query: str,
    events: queue.Queue[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run one shopping request and return evidence-checked structured data."""
    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("Enter a product request before searching.")

    load_dotenv(PROJECT_DIR / ".env")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add your Groq API key to ecomm-agents/.env."
        )

    model = ChatGroq(
        model=os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"),
        temperature=0,
        max_tokens=1200,
        api_key=api_key,
    )
    agent = create_agent(
        model=model,
        tools=[CatalogSearch, PricingAPI, InventoryAPI, ReviewAPI],
        system_prompt=AGENT_INSTRUCTIONS,
        response_format=ToolStrategy(ShoppingResponse, handle_errors=False),
    )
    config: dict[str, Any] = {}
    if events is not None:
        config["callbacks"] = [DebugEventHandler(events)]

    result = agent.invoke(
        {"messages": [{"role": "user", "content": cleaned_query}]},
        config=config,
    )
    structured = result.get("structured_response")
    if not isinstance(structured, ShoppingResponse):
        raise ValueError("The model did not return a valid structured response.")
    messages = result.get("messages", [])
    _validate_against_evidence(structured, _tool_evidence(messages))
    final_response = _apply_budget(structured, cleaned_query)
    response_data = final_response.model_dump(mode="json")
    if events is not None:
        events.put({"type": "final_response", "response": _redact(response_data)})
    return response_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Smart shopping assistant")
    parser.add_argument(
        "query",
        nargs="*",
        help="Natural-language shopping request. Omit to use interactive mode.",
    )
    args = parser.parse_args()

    if args.query:
        try:
            response = run_shopping_request(" ".join(args.query))
        except Exception as error:
            parser.exit(1, f"Shopping request failed: {_redact(str(error))}\n")
        print(json.dumps(response, indent=2))
        return

    while True:
        try:
            query = input("What are you shopping for? (type quit to stop): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if query.lower() in {"quit", "exit"}:
            return
        if not query:
            continue
        try:
            print(json.dumps(run_shopping_request(query), indent=2))
        except Exception as error:
            print(f"Shopping request failed: {_redact(str(error))}", file=sys.stderr)


if __name__ == "__main__":
    main()
