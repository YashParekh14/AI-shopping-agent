# 🛒 AI Shopping Assistant

A production-ready conversational shopping agent powered by **GPT-4o** and **LangChain**.
Users find and order products through natural language or by uploading a product photo.

🔴 **Live demo:** https://your-app.streamlit.app *(update with your URL)*
📦 **Docker:** `docker run -e OPENAI_API_KEY=sk-... yashparekh14/ai-shopping-agent`

---

## Features

- **Natural language shopping** — "organic honey under $20 with 4.5+ rating"
- **Image search** — upload a photo → GPT-4o vision identifies it → catalog search
- **Single-call search** — ratings joined at SQL level, no separate LLM round-trips
- **Guarded checkout** — orders validated in code, never placed without explicit confirmation
- **Dual database** — SQLite for local dev, PostgreSQL/Supabase for production
- **Full observability** — LangSmith tracing for every agent run
- **15 unit tests** and **15 behavioural eval scenarios** with pass-rate tracking

---

## Architecture

```
User (Streamlit UI)
       │
       ▼
Agent (shopping_agent.py)          Manual ReAct tool-call loop
       │                           GPT-4o via langchain-openai
       ├── search_products ──────► catalog.py  ──► db.py ──► SQLite / PostgreSQL
       ├── checkout ─────────────► catalog.py  ──► orders table
       └── describe_product_image► GPT-4o vision (base64 image)

Observability: LangSmith traces every tool call, token count, and latency
CI/CD: GitHub Actions → pytest → Docker build → Docker Hub
```

| File | Responsibility |
|------|----------------|
| `config.py` | All settings from env vars (models, DB, LangSmith) |
| `db.py` | Connection context manager — SQLite or PostgreSQL |
| `catalog.py` | Product search (with ratings JOIN), order creation |
| `reviews_api.py` | Rating aggregation (single + batch) |
| `shopping_agent.py` | LangChain tools + manual agent loop |
| `app.py` | Streamlit chat UI |
| `setup_db.py` | Creates tables + seeds data (SQLite and PostgreSQL) |
| `tests/` | 15 unit tests — no LLM needed |
| `eval/` | 15 behavioural scenarios + pass-rate tracking |

---

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/YashParekh14/AI-shopping-agent.git
cd AI-shopping-agent
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env — set OPENAI_API_KEY at minimum

# 3. Build database (auto-runs on first app start too)
python setup_db.py

# 4. Run
streamlit run app.py
```

### With Docker (recommended)
```bash
docker build -t ai-shopping-agent .
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=sk-your-key \
  ai-shopping-agent
# Open http://localhost:8501
```

---

## Production Setup (Supabase + Streamlit Cloud)

1. Create a free project at [supabase.com](https://supabase.com)
2. Copy the **Transaction pooler** connection string
3. Add to Streamlit Cloud secrets:
```toml
OPENAI_API_KEY = "sk-..."
DATABASE_URL = "postgresql://postgres.xxx:password@aws-0-eu-west-2.pooler.supabase.com:6543/postgres"
LANGCHAIN_TRACING_V2 = "true"
LANGCHAIN_API_KEY = "ls-..."
LANGCHAIN_PROJECT = "shopping-agent"
```
4. Run `python setup_db.py` locally with `DATABASE_URL` set to seed Supabase

---

## Testing

```bash
# Unit tests (no API key needed — uses isolated temp database)
pytest

# Behavioural eval (requires OPENAI_API_KEY — runs real agent)
python -m eval.run_eval

# Single scenario
python -m eval.run_eval --scenario browse_does_not_order
```

### Eval scenarios covered
| # | Scenario | What it checks |
|---|----------|----------------|
| 1 | browse_does_not_order | No checkout during browsing |
| 2 | confirmation_triggers_order | Checkout fires on confirmation |
| 3 | price_filter_respected | All shown products within price |
| 4 | organic_filter_respected | Only organic products shown |
| 5 | vague_greeting_does_not_order | Greeting never triggers tools |
| 6 | nonexistent_product_graceful | Missing category handled cleanly |
| 7 | no_order_on_ambiguous_response | Ambiguous reply never orders |
| 8 | rating_filter_respected | All shown products meet rating |
| 9 | order_by_number | "Order #2" triggers checkout |
| 10 | combined_price_organic_rating | All three filters together |
| 11 | prompt_injection_user_message | Injection attempt blocked |
| 12 | no_order_on_negative_response | "No thanks" never orders |
| 13 | dairy_alt_search | Plant-based milk found |
| 14 | very_low_price_filter | Sub-$5 filter works |
| 15 | followup_without_repeat | Multi-turn memory works |

---

## CI/CD Pipeline

Every `git push` to `main`:
1. GitHub Actions installs dependencies
2. Runs all 15 unit tests
3. If tests pass → builds Docker image
4. Pushes to Docker Hub as `yashparekh14/ai-shopping-agent:latest`

---

## Design Decisions

**Why a manual tool-call loop instead of `create_agent`?**
LangChain's `create_agent` had version-specific issues where tool results
weren't fed back to GPT-4o correctly. The manual loop gives full control
over the ReAct cycle and works reliably across all LangChain versions.

**Why join ratings in SQL instead of a separate tool call?**
Fetching ratings per-product in a loop is N+1 queries and N separate
LLM round-trips. A single LEFT JOIN returns all products with ratings
attached — one query, one tool call, more reliable.

**Why SQLite for local dev and PostgreSQL for production?**
SQLite needs zero setup — anyone can clone and run in 2 minutes.
PostgreSQL (via Supabase or AWS RDS) is used in production for persistence
and concurrent writes. The `db.py` context manager handles both;
swapping is a single environment variable.

**Why guard checkout in code, not just the prompt?**
Prompt instructions alone can be bypassed by an adversarial user or a
confused model. `create_order()` in `catalog.py` validates the product
exists before any write — a hallucinated ID cannot create an order.

---

## Production Considerations

| Concern | Current (demo) | Production approach |
|---------|----------------|---------------------|
| Database | SQLite / Supabase | AWS RDS PostgreSQL in VPC |
| Deployment | Streamlit Cloud | AWS ECS + Application Load Balancer |
| Containerisation | Docker (local) | AWS ECR + ECS Fargate |
| Secrets | .env / Streamlit secrets | AWS Secrets Manager |
| Monitoring | LangSmith | LangSmith + CloudWatch |
| Scaling | Single instance | ECS auto-scaling on CPU/request count |
| Auth | None (demo) | AWS Cognito / API Gateway auth |
| Rate limiting | None | API Gateway throttling |
| Cost control | Manual | AWS Budgets alert + OpenAI spend limits |

---

## Stack

Python · LangChain · OpenAI GPT-4o · SQLite / PostgreSQL · Supabase ·
Streamlit · Docker · GitHub Actions · LangSmith · psycopg2 · pytest
