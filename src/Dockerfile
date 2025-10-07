FROM python:3.11-alpine

# Installa tool base (alpine style)
RUN apk update && apk add --no-cache \
    bash \    
    build-base \
    curl \
    net-tools

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

CMD ["python", "app.py"]