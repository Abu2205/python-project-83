PORT ?= 8000

install:
	pip install -r requirements.txt

dev:
	uv run flask --debug --app page_analyzer:app run

start:
	gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

render-start:
	gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

build:
	./build.sh

init-db:
	psql $$DATABASE_URL -f database.sql

lint:
	flake8 page_analyzer

test:
	pytest