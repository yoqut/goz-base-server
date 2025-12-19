FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/home/app/.local/bin:$PATH"

# Tizim kutubxonalari
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    python3-dev \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# User yaratish
RUN useradd -m -u 1000 app
USER app

WORKDIR /app

# Virtual environment
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Requirements
COPY --chown=app:app requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Project fayllari
COPY --chown=app:app . .

# Entrypoint
COPY --chown=app:app entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]