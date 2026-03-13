.PHONY: install setup dev shutdown lint refresh clean help

# Default target
all: help

install: ## Install Python dependencies with uv
	uv sync

setup: install ## First-time setup: install deps + seed database
	uv run python -c "from src.quick_trip_planner.db import init_db; init_db()"
	uv run python -c "from src.quick_trip_planner.db import get_db; from src.quick_trip_planner.data_provider import refresh_data; refresh_data(get_db())"
	@echo "✅ Setup complete. Database seeded at data/trips.db"

dev: ## Run the development server (port 8000, auto-reload)
	uv run uvicorn src.quick_trip_planner.main:app --reload --port 8000

shutdown: ## Kill the dev server on port 8000
	@-fuser -k 8000/tcp 2>/dev/null || true
	@echo "✅ Server stopped, port 8000 freed."

lint: ## Lint backend code with ruff
	uvx ruff check src/
	uvx ruff format --check src/

format: ## Auto-format backend code with ruff
	uvx ruff format src/
	uvx ruff check --fix src/

refresh: ## Refresh airport and route data via the API
	@curl -s -X POST http://localhost:8000/api/data/refresh | python3 -m json.tool

clean: ## Remove database and Python caches
	rm -f data/trips.db
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned."

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
