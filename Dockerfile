FROM python:3.10-slim

# Installa tool di base
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    bash \
    build-essential \
    curl \
    net-tools \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copia TUTTI i file Python dalla src/ nella root di /app
COPY src/ .

# Il comando di default viene sovrascritto dal deployment YAML (Gunicorn o bot)
CMD ["python", "app.py"]