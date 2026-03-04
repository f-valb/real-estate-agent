# Real Estate Agent

A full-stack **hybrid AI + microservices** proof-of-concept for real estate — deterministic CRUD services for reliable data operations, combined with LLM-powered agents for reasoning tasks. Fully local, zero API cost.

![Architecture](https://img.shields.io/badge/architecture-hybrid%20AI%20%2B%20microservices-6366f1) ![Python](https://img.shields.io/badge/python-3.12-blue) ![Next.js](https://img.shields.io/badge/next.js-15-black) ![License](https://img.shields.io/badge/license-MIT-green)

---

## Architecture

```
Browser (Next.js 15)
    └── API Gateway :8090
            ├── property-listing  :8000   → PostgreSQL db_listings
            ├── crm-contact       :8001   → PostgreSQL db_crm
            ├── market-data       :8002   → PostgreSQL db_market
            ├── pricing-strategy  :8010   ─┐
            ├── lead-intelligence :8011   ─┼─→ LiteLLM :4000 → Ollama :11434 (Qwen2.5:14b)
            └── home-finder       :8012   ─┘
                     │
                  Kafka (events) ──→ all services
                  Redis (rate limiting)
```

**Key design principle:** Agents are microservices that call deterministic services as tools. The LLM only handles reasoning; data operations stay in typed, tested Python code.

---

## Services

### Microservices (deterministic)

| Service | Port | Description |
|---------|------|-------------|
| `property-listing` | 8000 | Property CRUD, status workflow, MLS numbers, Kafka events |
| `crm-contact` | 8001 | Contact pipeline, interactions log, tags, preferences |
| `market-data` | 8002 | Sales history ingestion, comps finder, market stats by ZIP |
| `gateway` | 8090 | Reverse proxy, Redis rate limiting, unified API surface |

### AI Agents (LLM-powered)

| Agent | Port | What it does |
|-------|------|--------------|
| `pricing-strategy` | 8010 | Comparative market analysis → recommended price + range + confidence |
| `lead-intelligence` | 8011 | Lead scoring 0–100, hot/warm/cold qualification, recommended next actions |
| `home-finder` | 8012 | Natural language buyer search → extracts criteria, searches listings, ranks + explains results |

All agents use the **OpenAI SDK → LiteLLM proxy → Ollama/Qwen2.5:14b** chain. Swapping to any other model (GPT-4o, Claude, Mistral) only requires a LiteLLM config change — agent code is unchanged. Each agent has a heuristic fallback so the UI stays functional when the LLM is warming up.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend services | Python 3.12, FastAPI, SQLAlchemy 2.0 async, asyncpg |
| Messaging | Apache Kafka (Confluent 7.6) + Zookeeper |
| Caching | Redis 7 |
| Database | PostgreSQL 16 (separate DB per service) |
| AI inference | Ollama + Qwen2.5:14b (local, no API key needed) |
| LLM proxy | LiteLLM (OpenAI-compatible API, model routing) |
| Frontend | Next.js 15, React 19, Tailwind CSS, TanStack Query |
| Orchestration | Docker Compose |

---

## Frontend Pages

| Page | Description |
|------|-------------|
| `/` | Dashboard — listing counts, active listings, hot leads |
| `/listings` | Property grid with status badges and price |
| `/listings/[id]` | Property detail + **AI Pricing Analysis** panel |
| `/contacts` | Contact pipeline with type and stage badges |
| `/contacts/[id]` | Contact detail + **AI Lead Scoring** panel |
| `/find` | **Natural language home search** — describe your dream home, AI matches listings and explains reasoning |

---

## Quick Start

### Prerequisites
- Docker + Docker Compose
- 8 GB RAM free (Qwen2.5:14b needs ~6 GB)

### 1. Start all services

```bash
docker compose up -d
```

First run pulls images and builds containers (~5 min). Ollama will download Qwen2.5:14b on first agent call (~9 GB, one-time).

### 2. Wait for everything to be healthy

```bash
docker compose ps
```

All 12 containers should show `healthy` or `running`.

### 3. Seed data

```bash
make seed
# Seeds: 50 properties, 100 contacts, 500 market sales records
```

### 4. Open the frontend

```bash
cd frontend && npm install && npm run dev
```

Visit **http://localhost:3000**

---

## API Examples

```bash
# List properties
curl http://localhost:8090/api/v1/listings?status=active&limit=10

# Get a contact
curl http://localhost:8090/api/v1/contacts/<uuid>

# AI pricing analysis
curl -X POST http://localhost:8090/api/v1/agents/pricing/analyze \
  -H "Content-Type: application/json" \
  -d '{"property_id": "<uuid>"}'

# AI lead scoring
curl -X POST http://localhost:8090/api/v1/agents/leads/score \
  -H "Content-Type: application/json" \
  -d '{"contact_id": "<uuid>"}'

# Natural language home search
curl -X POST http://localhost:8090/api/v1/agents/home-finder/search \
  -H "Content-Type: application/json" \
  -d '{"description": "3-bed family home near good schools in Austin, yard, around $500k"}'
```

---

## Project Structure

```
real-estate-agent/
├── docker-compose.yml          # Full stack — 12 containers
├── Makefile                    # up / down / seed / test
├── shared/                     # Shared Python library (Pydantic schemas, Kafka, SQLAlchemy)
├── services/
│   ├── property-listing/       # Listings CRUD + Kafka producer
│   ├── crm-contact/            # Contacts + interactions + tags
│   └── market-data/            # Sales history + market stats
├── agents/
│   ├── pricing-strategy/       # CMA pricing agent
│   ├── lead-intelligence/      # Lead scoring agent
│   └── home-finder/            # Natural language search agent
├── gateway/                    # API Gateway (FastAPI reverse proxy)
├── frontend/                   # Next.js 15 dashboard
├── seed/                       # Faker-based data seeding scripts
├── tests/                      # Integration tests (pytest-asyncio)
└── infra/
    ├── postgres/               # DB initialisation script
    ├── litellm/                # LiteLLM model routing config
    └── kafka/                  # Topic creation script
```

---

## Running Tests

```bash
# Requires all services running
make test

# Or directly
cd tests && pip3 install -r requirements.txt && pytest -v
```

16 integration tests covering CRUD operations and agent endpoints.

---

## How the Agents Work

Each agent follows a **ReAct loop**:

1. **System prompt** defines the task and available tools
2. **LLM call** — model decides whether to call a tool or produce final output
3. **Tool execution** — agent calls real microservice APIs (property search, CRM lookup, market comps)
4. **Loop** up to N iterations until the model produces a valid JSON response
5. **Guardrails** — Pydantic validates the output; retries or fallback on failure
6. **Heuristic fallback** — regex/rule-based logic runs if LLM is unavailable, so the API always returns a response

```
User request
    → LLM: "I need to call search_listings(city=Austin, max_price=500000)"
    → Tool: GET /api/v1/listings?city=Austin&max_price=500000&status=active
    → LLM: "Here are the top matches and my reasoning..."
    → Guardrails: validate schema
    → Response to client
```
