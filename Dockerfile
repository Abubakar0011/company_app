FROM ghcr.io/astral-sh/uv@sha256:bda40d0b4bab80ba4f41dda73cd3ef2f07c9a24b0f9709372fcfbb9683ab5a3c

# Set working directory in the container
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    poppler-utils \
&& rm -rf /var/lib/apt/lists/*

# Copy the pyproject.toml and uv.lock files to the container (for dependencies)
COPY pyproject.toml uv.lock ./ 

# Install project dependencies using uv (without dev or editable packages)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-editable

# Copy the rest of the application code to the container
COPY . .

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose ports for both Streamlit (8501) and FastAPI (8000)
EXPOSE 8501 8000

# Default command runs Streamlit frontend using uv run
# Override with: docker run -p 8000:8000 <image> uv run uvicorn api.main:app --host 0.0.0.0
CMD ["uv", "run", "streamlit", "run", "frontend/app.py", "--server.address", "0.0.0.0"]
