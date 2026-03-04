.PHONY: up down logs seed seed-properties seed-contacts seed-market test pull-model health

# ── Infrastructure ──────────────────────────────────────────────
up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

logs-%:
	docker compose logs -f $*

# ── Ollama model ────────────────────────────────────────────────
pull-model:
	docker compose exec ollama ollama pull qwen2.5:14b

# ── Seed data ───────────────────────────────────────────────────
seed: seed-properties seed-contacts seed-market

seed-properties:
	cd seed && pip3 install -q -r requirements.txt > /dev/null 2>&1 && python3 seed_properties.py

seed-contacts:
	cd seed && pip3 install -q -r requirements.txt > /dev/null 2>&1 && python3 seed_contacts.py

seed-market:
	cd seed && pip3 install -q -r requirements.txt > /dev/null 2>&1 && python3 seed_market_data.py

# ── Health checks ───────────────────────────────────────────────
health:
	@echo "Property Listing:"; curl -sf http://localhost:8000/health || echo "DOWN"
	@echo "CRM Contact:"; curl -sf http://localhost:8001/health || echo "DOWN"
	@echo "Market Data:"; curl -sf http://localhost:8002/health || echo "DOWN"
	@echo "Pricing Agent:"; curl -sf http://localhost:8010/health || echo "DOWN"
	@echo "Lead Agent:"; curl -sf http://localhost:8011/health || echo "DOWN"
	@echo "Gateway:"; curl -sf http://localhost:8090/health || echo "DOWN"
	@echo "Ollama:"; curl -sf http://localhost:11434/api/tags || echo "DOWN"
	@echo "LiteLLM:"; curl -sf http://localhost:4000/health/liveliness || echo "DOWN"

# ── Tests ───────────────────────────────────────────────────────
test:
	cd tests && pip install -q pytest pytest-asyncio httpx > /dev/null 2>&1 && python -m pytest -v
