# 🛒 AI Shopping Assistant

🔴 **Live demo:**  https://ai-shopping-agent-ql2vcdmjectqdwdcvonli2.streamlit.app/

A conversational shopping agent built with **LangChain** and a **Groq**-hosted LLM.
Users describe what they want in natural language (or upload a product photo) and the
agent searches a SQLite catalog, looks up customer ratings, filters by the user's
constraints, and places orders — only after explicit confirmation.

A Streamlit chat UI sits on top, including a "shop by image" flow that uses a vision
model to identify a product from a photo and search for similar items.

## Features

- **Natural-language browsing** — "organic honey under $20 with a 4.5+ rating"
- **Tool-using agent** — `search_products`, `get_rating`, `get_ratings` (batch),
  `checkout`, `describe_product_image`
- **Image search** — upload a photo → vision model extracts attributes → catalog search
- **Guarded checkout** — orders are validated in code and only placed on explicit user confirmation
- **Tested core logic** and a **behavioural eval harness** for the agent

## Architecture

The code separates *domain logic* from *LLM orchestration* so the business logic is
testable without spinning up a model.

| File | Responsibility |
|------|----------------|
| `config.py` | Central config (models, temperature, DB path, log level) from env vars |
| `db.py` | One connection context manager — commit/rollback/close handled safely |
| `catalog.py` | Pure product logic: `search_products`, `get_product`, `create_order` |
| `reviews_api.py` | Rating aggregation: single + batch (`get_ratings_for_products`) |
| `shopping_agent.py` | Thin `@tool` wrappers around the above + the LangChain agent definition |
| `app.py` | Streamlit chat UI (text + image search) |
| `setup_db.py` | Creates and seeds `store.db` (32 products, ~100 reviews) |
| `tests/` | Unit tests for catalog + reviews logic (no LLM needed) |
| `eval/` | Behavioural eval scenarios + runner for the live agent |

```
UI (app.py)
   │
   ▼
Agent (shopping_agent.py)  ──tools──►  catalog.py / reviews_api.py
   │                                          │
   ▼                                          ▼
 Groq LLM                                  db.py ──► store.db
```

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure your API key
cp .env.example .env
#   then edit .env and set GROQ_API_KEY  (https://console.groq.com)

# 3. Build the database (creates store.db)
python setup_db.py

# 4. Run the app
streamlit run app.py
```

## Testing

Unit tests cover search filters, ordering, and rating aggregation against an isolated
temp database (the real `store.db` is never touched):

```bash
pytest
```

## Evaluating the agent

The eval harness replays scripted conversations and checks behavioural properties from
the agent's tool-call trace — e.g. *it must not call `checkout` while only browsing*,
*it must call `checkout` after the user confirms*, and *every product it shows must
satisfy the price/rating filters*. Requires `GROQ_API_KEY`:

```bash
python -m eval.run_eval
```

Add new cases in `eval/scenarios.py`.

## Design decisions & notes

- **Domain logic is LLM-free.** `catalog.py` and `reviews_api.py` are plain functions,
  so they're fast and deterministic to unit-test. The agent tools are thin wrappers.
- **Batch ratings over N+1.** `get_ratings` fetches every candidate's rating in one query
  (and one tool call) instead of looping `get_rating` per product, which would be one LLM
  round-trip each.
- **Checkout is guarded in code, not just by the prompt.** `create_order` validates that
  the product exists before writing, so a hallucinated ID can't create a bad order. The
  system prompt also instructs the agent to treat product names/descriptions as untrusted
  data, mitigating prompt injection through catalog content.
- **Connections are managed.** A single `get_connection` context manager guarantees
  cleanup even on error, replacing the original manual `connect()/close()` pattern.
- **Config is centralised.** Model names and temperature live in `config.py`/env, not
  scattered across modules.

## Known limitations / next steps

- Checkout has no real auth or payment — it's a demo write to a local table.
- No request tracing yet; wiring in LangSmith would give per-run observability.
- The vision model's JSON output is parsed defensively but not schema-validated
  (a Pydantic model would tighten this).
- Conversation history grows unbounded in the UI; long sessions would need trimming
  or summarisation.


)
