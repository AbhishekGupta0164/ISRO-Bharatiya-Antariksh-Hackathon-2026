FROM python:3.11-slim

# Set up a new user named "user" with UID 1000
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Copy requirements and install
# We combine all requirements for the combined HF app
COPY --chown=user requirements /app/requirements
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements/backend.txt -r requirements/ml.txt

# Copy application code
COPY --chown=user . /app

# Build frontend if needed (though main.py mounts it as static)
# If the frontend is static HTML/JS/CSS, it just needs to be there.
# If it needs a build step, we'd add it here.

EXPOSE 7860
ENV PORT 7860

# Run the FastAPI app on the port HF expects
CMD ["uvicorn", "apps.backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
