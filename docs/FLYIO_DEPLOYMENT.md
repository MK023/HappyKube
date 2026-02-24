# 🚀 HappyKube Deployment su Fly.io

**Data:** 1 Febbraio 2026
**Status:** ✅ Pronto per deploy

---

## 📋 Prerequisiti

### 1. Account e CLI
```bash
# Installa flyctl via Homebrew
brew install flyctl

# Login
flyctl auth login

# Verifica
flyctl version
```

### 2. Servizi Esterni Configurati
- ✅ **Fly.io PostgreSQL** - Database managed (Frankfurt)
- ✅ **Redis Cloud** - Cache (EU-North-1 Stockholm)
- ✅ **Groq API** - Emotion analysis (Llama 3.3 70B)
- ✅ **Telegram Bot** - Interfaccia utente
- ✅ **Sentry** - Error tracking

---

## 🏗️ Architettura

```
┌──────────────────────┐
│   Fly.io VM (fra)    │  ← 1 VM da 512MB
│   API + Bot Webhook  │
│   (Supervisor)       │
└───────┬──────────────┘
        │
        ├─→ Fly.io PostgreSQL (internal, fra)
        ├─→ Redis Cloud (external, Stockholm)
        └─→ Groq API (external)
```

**Free Tier Usage:**
- 1 VM (512MB RAM, 1 shared vCPU)
- PostgreSQL interno Fly.io (stesso datacenter)
- Redis Cloud esterno (30MB free tier)
- Auto-stop quando idle (risparmio risorse)

---

## 🔐 Step 1: Configura Secrets

### Database
```bash
# Crea PostgreSQL su Fly.io (se non esiste)
fly postgres create --name happykube-db --region fra

# Collega al app (imposta DATABASE_URL automaticamente)
fly postgres attach happykube-db --app happykube
```

### Secrets manuali
```bash
# Cache
fly secrets set \
  REDIS_URL="rediss://default:password@host:port" \
  --app happykube

# Security
fly secrets set \
  ENCRYPTION_KEY="<fernet-key>" \
  API_KEYS="<api-key>" \
  INTERNAL_API_KEY="<internal-key>" \
  TELEGRAM_WEBHOOK_SECRET="<webhook-secret>" \
  --app happykube

# Bot e AI
fly secrets set \
  TELEGRAM_BOT_TOKEN="<from-botfather>" \
  GROQ_API_KEY="<from-groq-console>" \
  --app happykube

# Optional: Monitoring
fly secrets set \
  SENTRY_DSN="<sentry-dsn>" \
  --app happykube
```

---

## 🚀 Step 2: Deploy

```bash
# Prima build e deploy
fly deploy --app happykube --ha=false

# Attendi completamento (5-10 minuti)
```

### Cosa Succede Durante il Deploy
1. **Build Docker** - Compila l'immagine (multi-stage, ~87MB)
2. **Push Registry** - Carica su Fly.io registry
3. **Run Migrations** - Applica migrazioni Alembic su PostgreSQL
4. **Bootstrap API Keys** - Crea chiavi API se necessario
5. **Start Services** - Avvia API (uvicorn via Supervisor)
6. **Health Checks** - Verifica `/healthz`

---

## ✅ Step 3: Verifica Deploy

### Health Checks
```bash
# Info app
curl https://happykube.fly.dev/

# Liveness probe
curl https://happykube.fly.dev/healthz

# Database check
curl https://happykube.fly.dev/healthz/db

# Redis check
curl https://happykube.fly.dev/healthz/redis

# Readiness probe (tutti i check)
curl https://happykube.fly.dev/readyz
```

### Logs
```bash
# Logs in tempo reale
fly logs --app happykube

# Logs API
fly logs --app happykube | grep "program:api"

# Logs Bot
fly logs --app happykube | grep "program:bot"
```

### Status App
```bash
# Status generale
fly status --app happykube

# Dettagli VM
fly vm status --app happykube

# Secrets configurati
fly secrets list --app happykube
```

---

## 🤖 Step 4: Test Bot Telegram

1. Apri Telegram
2. Cerca `@HappyKube_bot`
3. Invia messaggio: `/start`
4. Invia messaggio emotivo: "Oggi sono felice!"
5. Verifica risposta con analisi emotiva

### Verifica Database
```bash
# Connetti via Fly.io proxy
fly postgres connect --app happykube-db

# Query verifica
SELECT COUNT(*) FROM emotions;
SELECT * FROM emotions ORDER BY created_at DESC LIMIT 5;
```

### Verifica Redis
```bash
# Connetti a Redis Cloud
redis-cli -u "rediss://default:...@host:port"

# Verifica chiavi
DBSIZE
KEYS emo:*
```

---

## 📊 Monitoring e Manutenzione

### Auto-Scaling
Fly.io scala automaticamente:
- **Idle → Stop** - VM si ferma dopo 5 min inattività
- **Request → Start** - VM si riavvia in ~5s
- **Free tier friendly** - Risparmia ore mensili

### Resource Usage
```bash
# CPU e memoria
fly vm status --app happykube

# Bandwidth
fly dashboard --app happykube
```

### Restart Manuale
```bash
# Restart app (utile dopo config change)
fly apps restart happykube
```

---

## 🔧 Troubleshooting

### Problema: Deploy fallisce con "build failed"
**Causa:** Errore Docker build
**Soluzione:**
```bash
# Test build locale
docker build -t happykube .

# Se fallisce, verifica logs Docker
```

### Problema: Health check failing
**Causa:** API non risponde su porta 5000
**Soluzione:**
```bash
# Verifica logs
fly logs --app happykube | grep "ERROR"

# Controlla supervisor
fly ssh console --app happykube
supervisorctl status
```

### Problema: Database connection failed
**Causa:** DATABASE_URL non configurato o errato
**Soluzione:**
```bash
# Verifica secret
fly secrets list --app happykube | grep DATABASE_URL

# Testa connessione manuale
psql "$DATABASE_URL"
```

### Problema: Bot non risponde
**Causa:** TELEGRAM_BOT_TOKEN errato o webhook non configurato
**Soluzione:**
```bash
# Verifica logs
fly logs --app happykube | grep "webhook"

# Verifica webhook Telegram
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"

# Ri-configura webhook
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://happykube.fly.dev/telegram/webhook", "secret_token": "<SECRET>"}'
```

---

## 🔄 Update e Redeploy

### Deploy Nuova Versione
```bash
# Dopo modifiche al codice
git add .
git commit -m "feat: nuova funzionalità"
git push origin main

# Deploy su Fly.io
fly deploy --app happykube
```

### Update Secrets
```bash
# Singolo secret
fly secrets set GROQ_API_KEY="nuovo_valore" --app happykube

# Verifica secrets configurati
fly secrets list --app happykube
```

### Rollback
```bash
# Lista releases
fly releases --app happykube

# Rollback a versione precedente
fly releases rollback <version> --app happykube
```

---

## 💰 Costi

### Free Tier (attuale)
- **VM:** 1 app (512MB RAM)
- **PostgreSQL:** Fly.io internal (stesso datacenter)
- **Redis:** Redis Cloud 30MB free tier
- **Bandwidth:** 160GB/mese
- **Costo:** $0/mese ✅

### Limiti
- Fly.io free tier: 3 shared VMs, 3GB volumes
- Redis Cloud free tier: 30MB
- Groq free tier: 14.400 req/giorno

---

## 📚 Risorse

- [Fly.io Docs](https://fly.io/docs/)
- [Fly.io PostgreSQL](https://fly.io/docs/postgres/)
- [Fly.io Secrets Management](https://fly.io/docs/reference/secrets/)
- [Redis Cloud Docs](https://redis.com/cloud/)
- [Groq Console](https://console.groq.com/)

---

**Ultima modifica:** 24 Febbraio 2026
**Autore:** Claude Code
**Status:** ✅ Production (deployed)
