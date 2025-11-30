FROM python:3.13-slim-bullseye AS builder

# Set working directory
WORKDIR /app

# Install system dependencies (if needed for packages like psycopg2 or others)
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    build-essential \
    libmagic-mgc \
    libmagic1 \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY ./requirements.txt /app/requirements.txt
COPY ./pyproject.toml /app/pyproject.toml

# Install Python dependencies in a virtual env (but for Docker, we use --user for isolation)
RUN pip install --no-cache-dir -r requirements.txt

FROM builder AS runner

# Copy source code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Environment variables for Streamlit (can be overridden at runtime)
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV PYTHONPATH=/app
ENV PATH=/root/.local/bin:$PATH

# Run the Streamlit app
CMD ["streamlit", "run", "app/main.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]