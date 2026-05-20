FROM python:3.12-slim

WORKDIR /app

# System deps for psycopg2 and lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Copy project files needed for dependency resolution
COPY pyproject.toml ./

# Install deps (skip building the project itself — uv.package = false)
RUN uv sync --no-install-project || uv sync

# Copy the rest
COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
