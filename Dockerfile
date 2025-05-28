FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN python3 -m venv venv
RUN . venv/bin/activate && pip install -r requirements.txt

EXPOSE 8000

CMD ["venv/bin/gunicorn", "-w", "4", "-b", "0.0.0.0:$PORT", "page_analyzer:app"]