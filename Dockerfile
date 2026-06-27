# Stage 1: Build the frontend
FROM node:20-slim AS frontend-build
WORKDIR /app
COPY package*.json ./
COPY apps/frontend/package*.json ./apps/frontend/
RUN rm -rf package-lock.json
RUN npm install
COPY . .
WORKDIR /app/apps/frontend
RUN npx vite build

# Stage 2: Final image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv and requirements
RUN pip install --no-cache-dir uv
COPY requirements/ ./requirements/
COPY pyproject.toml uv.lock ./
RUN uv pip install --system --no-cache -r requirements/backend.txt -r requirements/ml.txt

# Copy everything
COPY . .

# Copy the bundled frontend from Stage 1
COPY --from=frontend-build /app/apps/frontend/dist /app/apps/frontend/dist

# Set up user for HF
RUN useradd -m -u 1000 user && \
    chown -R user:user /app
USER user
ENV PATH="/home/user/.local/bin:$PATH"

EXPOSE 7860

# Run the backend (which now serves the dist folder)
CMD ["uvicorn", "apps.backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
