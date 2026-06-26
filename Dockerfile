# ── Stage 1: base image ───────────────────────────────────────────────────────
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ── Stage 2: install Python dependencies ──────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 3: copy application code ────────────────────────────────────────────
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check — ensures container is ready before traffic is sent
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# ── Startup ───────────────────────────────────────────────────────────────────
# --server.address=0.0.0.0 is required for Docker (default is localhost only)
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
