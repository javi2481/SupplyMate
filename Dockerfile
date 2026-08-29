FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app
COPY data ./data

RUN pip install --no-cache-dir .

ENV SUPPLYMATE_DATA_DIR=/app/data
EXPOSE 8000

CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
