install:
	uv sync

dev:
	uv run --active flask --debug --app page_analyzer:app run

PORT ?= 8000
start:
	uv run --active gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

render-start:
	gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

build:
	@if [ "$$SKIP_DB" = "true" ]; then \
		echo "Skipping DB initialization (SKIP_DB=true)"; \
	else \
		echo "Initializing DB..."; \
		psql $$DATABASE_URL -f database.sql; \
	fi

init-db:
	psql $$DATABASE_URL -f database.sql

lint:
	flake8 page_analyzer

test:
	pytest
