# Retail AI Assistant

FastAPI and CLI implementation for the simulation-based retail AI assignment.

## What This Project Does

- Uses one tool-calling agent for shopping and support use cases
- Reads product, order, and policy data from local files
- Exposes a FastAPI `POST /chat` endpoint
- Includes a simple CLI for demos
- Keeps return reasoning deterministic inside `evaluate_return(order_id)`

## Project Data Files

The assignment data files are stored inside the project:

- `Retail AI Assistant\data\product_inventory.csv`
- `Retail AI Assistant\data\orders.csv`
- `Retail AI Assistant\data\policy.txt`

You can still override them with environment variables if needed:

- `PRODUCTS_CSV_PATH`
- `ORDERS_CSV_PATH`
- `POLICY_PATH`

## Setup

This project is currently set up with a local `.venv` folder. The available interpreter on this machine is Python 3.8, so `requirements.txt` includes a small compatibility package for the newer type annotations used by the app.

Create and activate the project-local virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies inside the activated virtual environment:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The `.venv` folder is local to this project and keeps installed packages isolated from your global Python environment.

## Environment Variables

The app loads environment variables from a local `.env` file. A starter `.env` file is included with placeholder values:

```bash
HUGGINGFACE_API_KEY=replace_with_your_huggingface_token
HUGGINGFACE_MODEL=openai/gpt-oss-120b:fastest
HUGGINGFACE_BASE_URL=https://router.huggingface.co/v1
```

Replace `replace_with_your_huggingface_token` with your Hugging Face token before running the API or CLI.

Recommended Hugging Face model:

- `openai/gpt-oss-120b:fastest` is the default because Hugging Face lists `openai/gpt-oss-120b` as a strong chat model with tool-calling capability, which this project needs for `search_products`, `get_product`, `get_order`, and `evaluate_return`. The `:fastest` suffix lets Hugging Face choose an available fast provider automatically.

Alternative models to try if the default is unavailable or too costly:

- `Qwen/Qwen2.5-7B-Instruct-1M` for a smaller long-context instruction model.
- `Qwen/Qwen3-4B-Thinking-2507` for a smaller reasoning-focused model.

This project does require a Hugging Face API key for the assistant features. The `POST /chat` endpoint and `cli.py` call Hugging Face through its OpenAI-compatible chat endpoint. The deterministic repository/tool tests can run without an LLM key.

If Hugging Face is unavailable, `/chat` returns a fallback JSON response with an explanatory `answer` and a `tool_trace` entry describing the provider error.

## Run The API

```bash
uvicorn main:app --reload
```

Swagger UI:

- `http://127.0.0.1:8000/docs`

## Run The CLI

Single prompt:

```bash
python cli.py "I need a modest evening gown under 300 dollars in size 8 and I prefer sale items."
```

Interactive mode:

```bash
python cli.py
```

Show tool activity:

```bash
python cli.py --show-tools
```

## Run Tests

```bash
pytest
```

## Key Assignment Features

- Required tools are implemented:
  - `search_products(filters)`
  - `get_product(product_id)`
  - `get_order(order_id)`
  - `evaluate_return(order_id)`
- Shopping recommendations consider:
  - price
  - tags
  - requested size
  - stock for that size
  - sale status
  - bestseller score
- Return decisions use:
  - order data
  - product attributes
  - policy text
- The agent refuses missing orders or products instead of guessing

## Notes

- The CSV and policy parsers are intentionally flexible because real classroom data files often vary in formatting.
- `evaluate_return` is deterministic so the model does not hallucinate policy decisions.
