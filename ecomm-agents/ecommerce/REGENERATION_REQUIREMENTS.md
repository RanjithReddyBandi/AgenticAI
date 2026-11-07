# Smart Shopping Agent and Streamlit Requirements

This document describes the requirements for recreating the shopping assistant
and its Streamlit interface. It is a behavioral specification; implementation
details may change as long as the requirements below remain satisfied.

## 1. Project overview

Build a shopping assistant that accepts a free-form product request, searches a
local ecommerce API, checks price, stock, and review summaries for relevant
products, and returns validated JSON recommendations. Provide both a command
line interface and a Streamlit chat interface.

Use LangChain's agent/tool-calling flow with a Groq-hosted model through the
OpenAI-compatible Chat Completions API.

## 2. Configuration

Load configuration variables from `ecomm-agents/.env` without printing
secrets. Use `../.agenticai` as the Python virtual environment; `.env` remains
the separate configuration file and is not the virtual environment.

Required:

```dotenv
GROQ_API_KEY=your_groq_api_key
```

Optional settings and defaults:

```dotenv
GROQ_MODEL=qwen/qwen3.8-27b
ECOMM_API_BASE_URL=http://127.0.0.1:8000
ECOMM_MOCK_DATA=default
```

`ECOMM_MOCK_DATA` accepts `default` or `edge`. The API selects the dataset at
process startup, so restart the API after changing this setting. Reject unknown
dataset names with a clear error.

## 3. Ecommerce API and tools

The assistant uses these API endpoints:

| Endpoint | Purpose |
| --- | --- |
| `GET /products` | Product ID, name, category, and description |
| `GET /price/{product_id}` | Price and currency |
| `GET /availability/{product_id}` | In-stock flag and quantity |
| `GET /reviews/{product_id}` | Review comments and average rating |

Expose the API through four LangChain tools:

1. **CatalogSearch**: accepts one `query: str` field. Search product names,
   categories, and descriptions. Return matching product records; do not return
   unrelated products when the query has terms but no matches. Product records
   have only ID, name, category, and description.
2. **PricingAPI**: accepts one `product_id: str` field. Return the observed
   price and explicitly report `"No discount"` because the mock API has no
   discount information.
3. **InventoryAPI**: accepts one `product_id: str` field. Return stock status
   and quantity.
4. **ReviewAPI**: accepts one `product_id: str` field. Return average rating,
   review count, and a concise sentiment summary. Do not send all review
   comments to the model unless a feature specifically needs them.

Keep tool argument schemas minimal and descriptions concise. Surface API errors
instead of turning failures into success-shaped empty results.

## 4. Agent behavior

- Search the catalogue first.
- For each reasonable candidate, use price, availability, and reviews to
  support the recommendation.
- Apply any explicit budget to the observed price. A product at the exact
  budget is within budget; a product above it is not.
- Do not treat color, material, size, or other attributes as confirmed unless
  catalogue text supports them. The API has no structured fields for these
  attributes.
- Do not invent product attributes, discounts, review evidence, or stock
  status.
- If no product meets the request, return no recommendations and explain which
  criteria were unsupported or unmatched.
- Include out-of-stock products only when relevant, mark them unavailable, and
  make that status clear.
- When multiple products are reasonable candidates, provide evidence-based
  comparisons with pros and cons.
- Explain the user-facing criteria and evidence concisely. Do not reveal hidden
  chain-of-thought or private free-form reasoning.

Use structured output validation (for example, LangChain `ToolStrategy` with a
Pydantic response model) rather than relying on a prompt to produce parseable
JSON. Fail clearly if a valid structured response is not returned.

## 5. Output schema

The final response must validate against this shape:

```json
{
  "recommendations": [
    {
      "product_id": "string",
      "name": "string",
      "price": "string including currency",
      "discount": "string",
      "stock": true,
      "reviews": "concise rating and sentiment summary"
    }
  ],
  "comparisons": [
    {
      "product_id": "string",
      "pros": ["string"],
      "cons": ["string"]
    }
  ],
  "explanation": "concise user-facing explanation"
}
```

`comparisons` may be an empty list when comparison is unnecessary.

## 6. Streamlit interface

- Provide a chat-style input for free-form shopping requests and retain the
  conversation/results for the current Streamlit session.
- Render recommendations as readable product cards, comparisons as pros/cons,
  and the explanation as normal user-facing text. Make the validated JSON
  available for inspection.
- Show a dedicated sidebar **LLM Debug Log** for each request. During execution,
  update the log as events arrive; retain completed request logs for the session.
- For every model call, log the messages sent to the model and the model's
  observable response:
  - requested tool names and arguments;
  - structured final-response tool arguments/result;
  - concise indication when there is no visible tool request.
- For each tool call, log its name, input, returned output, and any error.
- Do not display hidden chain-of-thought. Free-form intermediate assistant
  text should be omitted or replaced with an explicit notice; display the
  structured final response and user-facing explanation.
- Never invoke Streamlit APIs from LangChain callback/worker threads. Callbacks
  should capture events in a thread-safe queue; the Streamlit session thread
  drains the queue and renders events while the agent executes.
- Display actionable error messages in the UI without silently substituting
  empty responses.

## 7. Command line interface

Retain a command line path in the shopping-agent module:

- An optional query argument runs one request and prints formatted validated
  JSON.
- With no query argument, prompt repeatedly until the user enters `quit` or
  `exit`.
- Keep the Streamlit app as a separate entry point.

## 8. Edge-case fixtures and test queries

Support a selectable edge dataset separate from the default mock data. It
should include:

- Similar products with ambiguous names/descriptions.
- Attributes explicitly supported by some descriptions and absent from others.
- Prices exactly at and just above common budget thresholds.
- In-stock and out-of-stock products, including low positive stock.
- Reviews spanning negative, mixed, and positive average ratings.
- Consistent product IDs across catalogue, prices, availability, and reviews.
- Non-empty, valid review lists so average-rating calculation is defined.

Useful manual queries include:

1. `Find a black leather jacket under $100.`
2. `Find a black leather belt under $50.`
3. `Find a wallet under $40, and tell me which options are in stock.`
4. `Find a brown leather jacket; compare the availability and reviews.`
5. `Find a purple silk hat under $100.`

Inspect the debug log as well as the final response. Catalogue search may return
partial/ambiguous matches; the agent must not claim every requested criterion
is satisfied unless tool evidence supports it.

## 9. Setup and run

From the `ecomm-agents` directory, using the project virtual environment:

```powershell
# Select the edge fixtures before starting the API.
$env:ECOMM_MOCK_DATA = "edge"
..\.agenticai\Scripts\python.exe -m uvicorn ecommerce.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
..\.agenticai\Scripts\python.exe -m streamlit run streamlit_app.py
```

Alternatively, set `ECOMM_MOCK_DATA=edge` in `.env` before starting the API.
Use `default` or omit the setting for the normal fixture. The API and Streamlit
agent must point at the same running API via `ECOMM_API_BASE_URL`.

Command line examples:

```powershell
..\.agenticai\Scripts\python.exe smart_shopping_agent.py "black leather jacket under $100"
..\.agenticai\Scripts\python.exe smart_shopping_agent.py
```

## 10. Acceptance checks

- Both datasets can be selected, and all API endpoints serve the selected
  dataset after API restart.
- Each tool schema contains only its required input field.
- Budget equality and over-budget cases are handled correctly.
- Unknown attributes and no-match requests are explained without fabricated
  claims.
- Ratings/sentiment and stock values agree with API tool results.
- Structured output conforms to the response schema.
- Streamlit starts, shows results and the live sidebar log, and retains prior
  requests for the session.
- Callback events can arrive from worker threads without calling Streamlit
  outside the Streamlit session thread.
- Logs show the model's observable inputs, tool requests, tool results, and
  structured final response without exposing hidden chain-of-thought or
  credentials.