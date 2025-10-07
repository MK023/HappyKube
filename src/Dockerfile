FROM python:3.10-slim

# Aggiorna e installa tool base (stile Debian)
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

COPY app.py .

CMD ["python", "app.py"]