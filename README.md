# 🛒 AI Shopping Assistant

A production-grade conversational AI shopping agent powered by **GPT-4o** and **LangChain**. Users find and order products through natural language or by uploading a product photo. Built with a full DevOps stack: Docker, GitHub Actions CI/CD, AWS EC2, and Supabase PostgreSQL.

🔴 **Live Demo (Streamlit Cloud):** https://ai-shopping-agent-ql2vcdmjectqdwdcvonli2.streamlit.app
☁️ **Live Demo (AWS EC2):** http://13.42.21.134:8501
📦 **Docker:** `docker run -e OPENAI_API_KEY=sk-... yashparekh14/ai-shopping-agent`

---

## Demo

```
User: I want organic honey under $20 with a 4.5+ rating

Agent: Here are some organic honey options under $20 with a rating of 4.5 or higher:

#1. Organic Acacia Honey (ID:7) — $17.99 ★4.75 — organic
#2. Organic Raw Honey (ID:1) — $14.99 ★4.63 — organic
#3. Organic Buckwheat Honey (ID:5) — $18.99 ★4.63 — organic

Would you like to order one? Just say yes or give me the number.

User: Order number 1

Agent: Order #1 confirmed! 'Organic Acacia Honey' has been successfully
ordered for $17.99. Your order will arrive in 3-5 business days.
```

---

## Features

- **Natural language shopping** — filter by price, rating, organic status, category
- **Image search** — upload a product photo → GPT-4o vision identifies it → catalog search
- **Single-call search** — ratings joined at SQL level, no N+1 queries or extra LLM round-trips
- **Guarded checkout** — orders validated in code, never placed without explicit user confirmation
- **Dual database** — SQLite for local dev (zero setup), PostgreSQL/Supabase for production
- **Full observability** — LangSmith traces every agent run, tool call, token count, and cost
- **15 unit tests** and **15 behavioural eval scenarios** with pass-rate tracking

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User (Browser)                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Streamlit UI (app.py)                           │
│         Text chat + Image upload sidebar                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│           Agent — Manual ReAct Tool-Call Loop                │
│              GPT-4o via langchain-openai                     │
│                                                              │
│  ┌─────────────────┐  ┌──────────┐  ┌────────────────────┐  │
│  │ search_products │  │ checkout │  │describe_product    │  │
│  │ (with ratings   │  │ (guarded │  │image (GPT-4o       │  │
│  │  SQL JOIN)      │  │  in code)│  │ vision)            │  │
│  └────────┬────────┘  └────┬─────┘  └────────────────────┘  │
└───────────┼───────────────┼─────────────────────────────────┘
            │               │
            ▼               ▼
┌───────────────────────────────────────────────────────────┐
│                    catalog.py / db.py                      │
│         SQLite (local) ←→ Supabase PostgreSQL (prod)       │
└───────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────┐
│                  LangSmith (Observability)                  │
│     Every tool call · Token count · Latency · Cost         │
└───────────────────────────────────────────────────────────┘
```

### CI/CD Pipeline

```
git push to main
      │
      ▼
GitHub Actions
      │
      ├── 1. Run 15 unit tests (pytest)
      │         └── if pass ↓
      ├── 2. Build Docker image
      │         └── push to Docker Hub
      │                   └── and ↓
      └── 3. SSH into AWS EC2
                └── pull new image
                └── restart container
                └── app live in < 3 minutes
```

### File Structure

| File | Responsibility |
|------|----------------|
| `config.py` | All settings from env vars — models, DB, LangSmith |
| `db.py` | Connection context manager — SQLite or PostgreSQL |
| `catalog.py` | Product search (ratings JOIN), order creation |
| `reviews_api.py` | Rating aggregation — single and batch |
| `shopping_agent.py` | LangChain tools + manual ReAct agent loop |
| `app.py` | Streamlit chat UI — text and image search |
| `setup_db.py` | Creates tables and seeds data (SQLite and PostgreSQL) |
| `tests/` | 15 unit tests — no LLM or API key needed |
| `eval/` | 15 behavioural scenarios + pass-rate JSON logging |
| `Dockerfile` | Production container with health check |
| `.github/workflows/ci.yml` | CI/CD — test → build → push → deploy |

---

## Quick Start

### Option 1 — Docker (recommended, one command)

```bash
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=sk-your-key \
  yashparekh14/ai-shopping-agent:latest
```

Open http://localhost:8501 — uses local SQLite, no other setup needed.

### Option 2 — Local development

```bash
# 1. Clone
git clone https://github.com/YashParekh14/AI-shopping-agent.git
cd AI-shopping-agent

# 2. Install
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env — set OPENAI_API_KEY at minimum

# 4. Build database
python setup_db.py

# 5. Run
streamlit run app.py
```

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional — Supabase PostgreSQL (uses SQLite if not set)
DATABASE_URL=postgresql://user:password@host:6543/postgres

# Optional — LangSmith observability
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_PROJECT=shopping-agent
```

---

## Testing

### Unit tests (no API key needed)

```bash
pytest
# 15 passed in 0.3s
```

Tests use an isolated in-memory SQLite database — never touches Supabase or store.db. Covers:
- Product search with all filter combinations
- Rating aggregation (single and batch)
- Order creation and validation
- Error handling for unknown products

### Behavioural eval (requires OPENAI_API_KEY)

```bash
python -m eval.run_eval

# Run a single scenario
python -m eval.run_eval --scenario browse_does_not_order
```

Results saved to `eval/results.json` for tracking pass rates across runs.

### Eval scenarios covered

| # | Scenario | What it verifies |
|---|----------|-----------------|
| 1 | browse_does_not_order | No checkout during browsing |
| 2 | confirmation_triggers_order | Checkout fires on explicit confirmation |
| 3 | price_filter_respected | All shown products within price limit |
| 4 | organic_filter_respected | Only organic products when requested |
| 5 | vague_greeting_does_not_order | Greeting never triggers tools |
| 6 | nonexistent_product_graceful | Missing category handled cleanly |
| 7 | no_order_on_ambiguous_response | Ambiguous reply never orders |
| 8 | rating_filter_respected | All shown products meet minimum rating |
| 9 | order_by_number | "Order #2" correctly triggers checkout |
| 10 | combined_price_organic_rating | All three filters applied together |
| 11 | prompt_injection_user_message | Injection attempt blocked |
| 12 | no_order_on_negative_response | "No thanks" never triggers checkout |
| 13 | dairy_alt_search | Plant-based milk search works |
| 14 | very_low_price_filter | Sub-$5 filter works correctly |
| 15 | followup_without_repeat | Multi-turn memory works |

---

## Deployment

### Streamlit Cloud

1. Fork this repo
2. Go to share.streamlit.io → Create app → select your fork
3. Add secrets in Advanced settings:

```toml
OPENAI_API_KEY = "sk-..."
DATABASE_URL = "postgresql://..."
LANGCHAIN_TRACING_V2 = "true"
LANGCHAIN_API_KEY = "ls__..."
LANGCHAIN_PROJECT = "shopping-agent"
```

### AWS EC2

```bash
# On EC2 instance (Amazon Linux 2023)
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Pull and run
docker pull yashparekh14/ai-shopping-agent:latest

docker run -d -p 8501:8501 \
  -e OPENAI_API_KEY="sk-..." \
  -e DATABASE_URL="postgresql://..." \
  -e LANGCHAIN_API_KEY="ls__..." \
  -e LANGCHAIN_TRACING_V2="true" \
  -e LANGCHAIN_PROJECT="shopping-agent" \
  --name shopping-agent \
  --restart unless-stopped \
  yashparekh14/ai-shopping-agent:latest
```

Open `http://YOUR_EC2_PUBLIC_IP:8501` (ensure port 8501 is open in security group).

---

## Design Decisions

**Why a manual ReAct loop instead of `create_agent`?**
LangChain's `create_agent` had version-specific issues where tool results were not fed back to GPT-4o correctly. The manual loop gives full control over the tool-call cycle and works reliably across all LangChain versions.

**Why join ratings in SQL instead of a separate tool call?**
Fetching ratings per-product in a loop is N+1 queries and N separate LLM round-trips. A single LEFT JOIN returns all products with ratings attached — one query, one tool call, faster and more reliable.

**Why SQLite for local dev and PostgreSQL for production?**
SQLite needs zero setup — anyone can clone and run in 2 minutes. The `db.py` context manager handles both backends; swapping is a single `DATABASE_URL` environment variable. No other file changes needed.

**Why guard checkout in code, not just the prompt?**
Prompt instructions alone can be bypassed. `create_order()` in `catalog.py` validates the product exists before any write — a hallucinated product ID cannot create an order.

**Why treat product descriptions as untrusted input?**
The system prompt explicitly instructs the agent to treat catalog content as data, not commands. This mitigates prompt injection attacks through product names or descriptions.

---

## Production Considerations

| Concern | Current (demo) | Production approach |
|---------|---------------|---------------------|
| Database | Supabase free tier | AWS RDS PostgreSQL in VPC |
| Deployment | EC2 t3.micro | ECS Fargate with auto-scaling |
| Container registry | Docker Hub | AWS ECR |
| Secrets | Environment variables | AWS Secrets Manager |
| Monitoring | LangSmith | LangSmith + CloudWatch |
| Auth | None | AWS Cognito / API key middleware |
| Rate limiting | None | API Gateway throttling |
| Cost control | Manual | AWS Budgets + OpenAI spend limits |
| Scale | Single instance | ECS auto-scaling on CPU/requests |

---

## Stack

Python · LangChain · OpenAI GPT-4o · Supabase PostgreSQL · SQLite ·
Streamlit · Docker · AWS EC2 · GitHub Actions · LangSmith · psycopg2 · pytest
