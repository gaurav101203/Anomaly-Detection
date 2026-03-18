FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --default-timeout=100 -r requirements.txt

COPY . .

CMD ["sh", "-c", "python wait-for-db.py && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
