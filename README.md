# Retail AI Assistant

A simulation-based agentic AI project for retail shopping and customer support workflows.

The assistant acts as a single intelligent agent with two business roles:

- Personal Shopper: recommends products using price, size, stock, tags, sale status, and bestseller score.
- Customer Support Assistant: evaluates orders against return policy rules and explains return eligibility.

The project uses local CSV/text files for product, order, and policy data. No external store integration is required.

## Why Hugging Face

This project uses the Hugging Face Inference Router for LLM calls because it is practical for development and testing without requiring OpenAI API billing. Hugging Face provides an OpenAI-compatible chat endpoint, so the project can use tool/function calling while keeping development cost low.

The app uses:

```text
https://router.huggingface.co/v1
```

Default model:

```text
openai/gpt-oss-120b:fastest
```

The `:fastest` suffix lets Hugging Face choose an available fast provider automatically.

## Features

- Single agent for shopping and support use cases
- Structured tool/function calling
- Product recommendations based on multiple business constraints
- Deterministic return evaluation through Python code
- Local project data files in `data/`
- FastAPI chat endpoint
- CLI mode for quick demos
- Fallback JSON response when the Hugging Face provider is unavailable
- Test coverage for tools, return engine, and chat API behavior

## Required Tools

The model dynamically chooses from these structured tools:

```text
search_products(filters)
get_product(product_id)
get_order(order_id)
evaluate_return(order_id)
```

Tool implementations are registered in:

```text
app/tools/registry.py
```

## Project Structure

```text
Retail AI Assistant/
|-- app/
|   |-- agent/
|   |   |-- orchestrator.py      # LLM agent loop and tool-calling flow
|   |   `-- prompts.py           # System prompt and behavior rules
|   |-- api/
|   |   `-- routes/
|   |       `-- chat.py          # FastAPI /chat and /health routes
|   |-- repositories/
|   |   |-- product_repository.py
|   |   |-- order_repository.py
|   |   `-- policy_repository.py
|   |-- schemas/
|   |   |-- chat.py              # API request/response schemas
|   |   |-- domain.py            # Product, order, and result models
|   |   `-- tools.py             # Tool argument schemas
|   |-- services/
|   |   `-- return_engine.py     # Deterministic return-policy logic
|   |-- tools/
|   |   |-- product_tools.py     # Product search and lookup tools
|   |   |-- order_tools.py       # Order lookup and return tools
|   |   `-- registry.py          # Tool definitions exposed to the model
|   |-- utils/
|   |   `-- parsers.py           # CSV and policy parsing helpers
|   |-- config.py                # Environment and data-path settings
|   |-- container.py             # Application dependency container
|   `-- main.py                  # FastAPI app factory
|-- data/
|   |-- product_inventory.csv    # Product inventory data
|   |-- orders.csv               # Customer order data
|   |-- policy.txt               # Return policy text
|   `-- README.txt
|-- docs/
|   `-- architecture.md          # Architecture explanation
|-- tests/
|   |-- test_chat_api.py
|   |-- test_product_tools.py
|   `-- test_return_engine.py
|-- cli.py                       # CLI entrypoint
|-- main.py                      # Uvicorn import target
|-- requirements.txt
`-- README.md
```

## Data Files

The assignment data is stored inside the project:

```text
data/product_inventory.csv
data/orders.csv
data/policy.txt
```

You can override these paths with environment variables if needed:

```text
PRODUCTS_CSV_PATH
ORDERS_CSV_PATH
POLICY_PATH
```

## Setup

From PowerShell:

```powershell
cd "c:\python_projects\Retail AI Assistant"
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The `.venv` folder keeps dependencies isolated from the global Python installation.

## Environment Variables

Create or update `.env` in the project root:

```env
HUGGINGFACE_API_KEY=replace_with_your_huggingface_token
HUGGINGFACE_MODEL=openai/gpt-oss-120b:fastest
HUGGINGFACE_BASE_URL=https://router.huggingface.co/v1
```

Replace `replace_with_your_huggingface_token` with your real Hugging Face access token.

The deterministic tests can run without a Hugging Face token. The CLI and `/chat` endpoint require the token because they call the LLM.

## Run the API

```powershell
cd "c:\python_projects\Retail AI Assistant"
.\.venv\Scripts\activate
uvicorn main:app --reload
```

Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
GET http://127.0.0.1:8000/health
```

Chat endpoint:

```text
POST http://127.0.0.1:8000/chat
```

Example request:

```json
{
  "message": "I need a modest evening gown under $300 in size 8. I prefer something on sale."
}
```

## Run the CLI

Interactive mode:

```powershell
python cli.py
```

Single prompt:

```powershell
python cli.py "I need a modest evening gown under $300 in size 8. I prefer something on sale."
```

Show tool activity:

```powershell
python cli.py --show-tools
```

## Example Questions

Product recommendation:

```text
Can you help me find a modest size 8 evening dress under $300, preferably one that is currently discounted?
```

Product lookup:

```text
Show me product P0001.
```

Order lookup:

```text
Get order O0005.
```

Return decision:

```text
Order O0005 does not fit. Can I return it?
```

Missing order:

```text
Can I return order O9999?
```

## Expected Demo Outputs

Exact wording may vary because the final answer is generated by the LLM, but the response should include the same facts and tool-driven reasoning.

### Shopping Scenario 1

Request:

```json
{
  "message": "Can you help me find a modest size 8 evening dress under $300, preferably one that is currently discounted?"
}
```

Expected behavior:

- Calls `search_products(filters)`
- Filters products under `$300`
- Checks `modest` and `evening` tags when available
- Checks size `8` availability and stock
- Prioritizes sale items and strong `bestseller_score`

Expected style of response:

```text
I found a good match: Lumiere Style 4. It is under $300 at $120.00, is currently on sale, matches the modest requirement, and size 8 has stock available. It also has a strong bestseller score, so it is a strong recommendation for your constraints.
```

### Shopping Scenario 2

Request:

```json
{
  "message": "Show me a sale dress for a cocktail event in size 10 with a good bestseller score."
}
```

Expected behavior:

- Calls `search_products(filters)`
- Filters for `cocktail`
- Checks sale status
- Checks size `10` stock
- Uses `bestseller_score` in ranking

Expected style of response:

```text
I found sale options for a cocktail event in size 10. The recommendation should mention the product title, price, stock for size 10, sale status, matched tags, and bestseller score.
```

### Support Scenario 1

Request:

```json
{
  "message": "Order O0005 does not fit. Can I return it?"
}
```

Expected behavior:

- Calls `get_order(order_id)`
- Calls `evaluate_return(order_id)`
- Checks the linked product
- Applies `policy.txt`
- Gives a clear approved, denied, or manual review decision

Expected style of response:

```text
I found order O0005 and evaluated it against the return policy. The answer should explain whether the order is inside the allowed return window, mention the applied policy rules, and avoid guessing beyond the available data.
```

### Support Scenario 2

Request:

```json
{
  "message": "Can you check whether order O0002 is eligible for return?"
}
```

Expected behavior:

- Calls `get_order(order_id)`
- Calls `evaluate_return(order_id)`
- Applies sale, clearance, vendor, exchange, and normal return rules as relevant

Expected style of response:

```text
I checked order O0002 against the policy. The response should clearly say whether the return is approved, denied, or needs manual review, and should explain which policy rules affected the decision.
```

### Edge Case: Invalid Order

Request:

```json
{
  "message": "Can I return order O9999?"
}
```

Expected behavior:

- Calls `get_order(order_id)` or `evaluate_return(order_id)`
- Detects that the order does not exist
- Refuses to guess

Expected style of response:

```text
I could not find order O9999 in the order data, so I cannot evaluate a return for it.
```

### Test Output

Command:

```powershell
python -m pytest
```

Expected output:

```text
6 passed
```

## Run Tests

```powershell
cd "c:\python_projects\Retail AI Assistant"
.\.venv\Scripts\activate
python -m pytest
```

Expected result:

```text
6 passed
```

Run with verbose output:

```powershell
python -m pytest -v
```

## How Hallucination Is Minimized

- The model must use tools for product, order, stock, and policy facts.
- Product and order data is read from local files, not invented by the model.
- Return decisions are made by `evaluate_return(order_id)` using deterministic Python logic.
- Missing products and orders return structured not-found responses.
- The API response includes `tool_trace`, so tool activity can be inspected.

## Fallback Behavior

If Hugging Face is unavailable, `/chat` returns a normal JSON response instead of crashing:

```json
{
  "answer": "I cannot complete this chat request right now because the Hugging Face LLM provider is unavailable...",
  "tool_trace": [
    {
      "tool_name": "fallback",
      "arguments": {},
      "result": {
        "provider": "huggingface",
        "error_type": "...",
        "detail": "..."
      }
    }
  ]
}
```

## Architecture Document

See:

```text
docs/architecture.md
```

It explains:

- why the agent is structured this way
- how hallucination is minimized
- how tools are selected dynamically

## Demo Video Guide

Use this file to prepare the required project walkthrough video:

```text
docs/demo_script.md
```

It includes the recording flow, exact prompts, talking points, expected behavior, and the required edge case.
