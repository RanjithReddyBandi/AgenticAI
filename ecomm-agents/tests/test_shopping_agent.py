"""Offline acceptance checks for agent schemas, filtering, and fixtures."""

import json
import os
import queue
import subprocess
import sys
import unittest
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch

import tools
from ecommerce import data
from langchain_core.messages import AIMessage, HumanMessage
from streamlit.testing.v1 import AppTest
from smart_shopping_agent import (
    Comparison,
    DebugEventHandler,
    Recommendation,
    ShoppingResponse,
    _apply_budget,
    _redact,
)

PROJECT_DIR = Path(__file__).resolve().parents[1]


class ShoppingAgentTests(unittest.TestCase):
    def test_streamlit_chat_page_renders_without_errors(self) -> None:
        app = AppTest.from_file(str(PROJECT_DIR / "streamlit_app.py")).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.title[0].value, "Smart Shopping Assistant")
        self.assertEqual(len(app.chat_input), 1)

    def test_debug_events_omit_assistant_text_and_redact_credentials(self) -> None:
        events: queue.Queue[dict[str, object]] = queue.Queue()
        handler = DebugEventHandler(events)
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-secret"}):
            handler.on_chat_model_start(
                {},
                [[
                    HumanMessage(content="search for this test-secret"),
                    AIMessage(content="private chain reasoning"),
                ]],
                run_id=uuid4(),
            )
            logged = events.get_nowait()
            message_log = logged["messages"][0]
            self.assertEqual(message_log[0]["content"], "search for this [REDACTED]")
            self.assertEqual(
                message_log[1]["content"],
                "[assistant text omitted]",
            )
            self.assertEqual(_redact({"response": "test-secret"}), {
                "response": "[REDACTED]"
            })

    def test_tool_schemas_have_one_required_input_each(self) -> None:
        expected = [
            (tools.CatalogSearch, {"query"}),
            (tools.PricingAPI, {"product_id"}),
            (tools.InventoryAPI, {"product_id"}),
            (tools.ReviewAPI, {"product_id"}),
        ]
        for agent_tool, fields in expected:
            with self.subTest(tool=agent_tool.name):
                self.assertEqual(set(agent_tool.args), fields)

    def test_catalog_search_does_not_fall_back_to_unrelated_products(self) -> None:
        products = [
            {"id": 1, "name": "black leather jacket", "category": "apparel", "description": "Black leather."},
            {"id": 2, "name": "silk scarf", "category": "accessories", "description": "Purple silk."},
        ]
        with patch.object(tools, "_request_json", return_value=products):
            result = json.loads(tools.CatalogSearch.invoke({"query": "purple silk hat"}))
            unmatched = json.loads(
                tools.CatalogSearch.invoke({"query": "find 12345"})
            )
        self.assertEqual([product["id"] for product in result], [2])
        self.assertEqual(unmatched, [])

    def test_edge_fixture_ids_are_consistent_and_reviews_are_nonempty(self) -> None:
        products = {product["id"] for product in data.EDGE_DATA["products"]}
        self.assertEqual(products, set(data.EDGE_DATA["prices"]))
        self.assertEqual(products, set(data.EDGE_DATA["availability"]))
        self.assertEqual(products, set(data.EDGE_DATA["reviews"]))
        self.assertTrue(all(data.EDGE_DATA["reviews"][product_id]["reviews"] for product_id in products))

    def test_edge_dataset_is_selected_at_process_startup(self) -> None:
        env = os.environ.copy()
        env["ECOMM_MOCK_DATA"] = "edge"
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from ecommerce.data import DATASET_NAME, PRODUCTS; "
                "print(DATASET_NAME, len(PRODUCTS))",
            ],
            cwd=PROJECT_DIR,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(result.stdout.strip(), "edge 10")

    def test_edge_api_serves_related_records_for_every_product(self) -> None:
        env = os.environ.copy()
        env["ECOMM_MOCK_DATA"] = "edge"
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from fastapi.testclient import TestClient; "
                "from ecommerce.main import app; "
                "client = TestClient(app); "
                "products = client.get('/products').json(); "
                "assert len(products) == 10; "
                "assert all(client.get(f\"/price/{p['id']}\").status_code == 200 "
                "and client.get(f\"/availability/{p['id']}\").status_code == 200 "
                "and client.get(f\"/reviews/{p['id']}\").status_code == 200 "
                "for p in products); "
                "print('all edge endpoints passed')",
            ],
            cwd=PROJECT_DIR,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("all edge endpoints passed", result.stdout)

    def test_unknown_dataset_fails_with_supported_values(self) -> None:
        env = os.environ.copy()
        env["ECOMM_MOCK_DATA"] = "missing"
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import ecommerce.data",
            ],
            cwd=PROJECT_DIR,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("choose 'default' or 'edge'", result.stderr)

    def test_output_schema_and_budget_equality(self) -> None:
        response = ShoppingResponse(
            recommendations=[
                Recommendation(
                    product_id="101",
                    name="black leather jacket",
                    price="100.00 USD",
                    discount="No discount",
                    stock=True,
                    reviews="4.5/5 average; positive sentiment",
                ),
                Recommendation(
                    product_id="102",
                    name="brown leather jacket",
                    price="100.01 USD",
                    discount="No discount",
                    stock=False,
                    reviews="1.5/5 average; negative sentiment",
                ),
            ],
            comparisons=[
                Comparison(product_id="101", pros=["Within budget"], cons=[]),
                Comparison(product_id="102", pros=[], cons=["Over budget"]),
            ],
            explanation="Evidence-based options.",
        )
        filtered = _apply_budget(response, "jacket under $100")
        self.assertEqual(
            [recommendation.product_id for recommendation in filtered.recommendations],
            ["101"],
        )
        self.assertEqual(
            [comparison.product_id for comparison in filtered.comparisons],
            ["101"],
        )
        self.assertIn("at or below $100.00", filtered.explanation)


if __name__ == "__main__":
    unittest.main()
