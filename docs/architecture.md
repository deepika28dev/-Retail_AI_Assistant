# Retail AI Assistant Architecture

## 1. Why The Agent Is Structured This Way

This project uses one intelligent agent with four structured tools instead of mixing data access and reasoning together. The goal is to keep the model responsible for language understanding and response writing, while the code remains responsible for facts and rules.

The architecture has four clear layers:

1. FastAPI and CLI entrypoints receive user input.
2. The agent decides which tool to call based on the user request.
3. Tools fetch structured data or run deterministic policy logic.
4. Repositories read products, orders, and policy content from local files.

This split keeps the code understandable because each layer has a single job:

- repositories load data
- tools expose assignment-required operations
- the return engine applies policy rules
- the agent explains results in natural language

## 2. How Hallucination Is Minimized

The design reduces hallucination in three ways.

First, the model is instructed to use tools for all product, order, stock, and return facts. It is not allowed to invent catalog details or return outcomes.

Second, the important business decision for returns is handled inside `evaluate_return(order_id)`. That function reads the order, the linked product, and relevant policy clauses, then makes the final decision in Python code. This means the LLM is not guessing about policy.

Third, not-found cases are handled explicitly. If an order ID or product ID is missing, the tools return a structured not-found response and the agent is instructed to refuse rather than continue with assumptions.

The project also keeps a tool trace in both the API response and CLI output, which makes it easier to prove that the answer came from real tool calls.

## 3. How Tools Are Selected

The single agent receives the user message and chooses tools dynamically through function calling.

For shopping requests, the model should usually call `search_products(filters)` first. That tool applies hard filters for price, tags, vendor, size availability, and actual stock for the requested size. It also ranks results using sale preference and `bestseller_score`, so the returned products are already business-aware.

For support requests, the model should first call `get_order(order_id)`. If the order exists, it then calls `evaluate_return(order_id)`. If more context is helpful for the final explanation, it can call `get_product(product_id)` as well.

This approach separates retrieval from reasoning:

- tools retrieve or compute facts
- the model explains those facts to the user

## 4. Why The Data Layer Uses CSV And Text Files

The assignment provides CSV files and a text policy file, so using a database would add complexity without improving the solution. The repositories load the input files directly and normalize common formatting differences such as:

- comma-separated or pipe-separated tags
- JSON-like size or stock fields
- different date formats

This keeps the project simple, transparent, and easy to grade.

## 5. Limitations And Future Improvements

The current policy parser is rule-based and works best when the policy text contains clear keywords such as `sale`, `clearance`, `exchange`, vendor names, and day counts. If the policy becomes much more complex, a future version could add a stricter policy parser that extracts sections more formally while still keeping the final decision deterministic.

Another future improvement would be a small conversation memory layer so the assistant can handle follow-up questions like “show me two cheaper options” without repeating the full search.
