FROM python:3.11-slim

WORKDIR /app

COPY requirements /app/requirements
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements/backend.txt -r /app/requirements/ml.txt

COPY . /app

EXPOSE 8000
CMD ["uvicorn", "apps.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
