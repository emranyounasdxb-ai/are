FROM python:3.13.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY pyproject.toml README.md ./
RUN python -m pip install --no-cache-dir --upgrade pip==26.1.2 \
    && python -m pip install --no-cache-dir ".[dev]"

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
