PORT ?= 8000

install:
	uv sync

dev:
	flask --debug --app page_analyzer:app run

start:
	gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

render-start:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	venv/bin/gunicorn -w 4 -b 0.0.0.0:$(PORT) page_analyzer:app

build:
	./build.sh

init-db:
	psql $$DATABASE_URL -f database.sql

lint:
	flake8 page_analyzer

test:
	pytest