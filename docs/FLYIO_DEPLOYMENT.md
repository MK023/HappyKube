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
- ✅ **NeonDB** - PostgreSQL serverless (EU-West-2 London)
- ✅ **Redis Cloud** - Cache (EU-North-1 Stockholm)
- ✅ **Doppler** - Secrets management
- ✅ **Groq API** - Emotion analysis
- ✅ **Telegram Bot** - Interfaccia utente

---

## 🏗️ Architettura

```
┌─────────────┐
│   Doppler   │  ← Secrets centrali
│   (Secrets) │
└──────┬──────┘
       │ sync
       ▼
┌──────────────────────┐
│   Fly.io VM (fra)    │  ← 1 VM da 256MB
│   API + Bot          │
│   (Supervisor)       │
└───────┬──────────────┘
        │
        ├─→ NeonDB (external)
        ├─→ Redis Cloud (external)
        └─→ Groq API (external)
```

**Free Tier Usage:**
- 1 VM su 3 disponibili (256MB RAM, 1 vCPU)
- Database e Redis esterni (zero consumo Fly.io)
- Auto-stop quando idle (risparmio risorse)

---

## 🔐 Step 1: Sincronizza Secrets da Doppler

### Opzione A: Script Automatico
```bash
# Esegui lo script di sync
chmod +x /tmp/sync-doppler-to-fly.sh
/tmp/sync-doppler-to-fly.sh
```

### Opzione B: Manuale
```bash
# Database e Cache
fly secrets set \
  DATABASE_URL="$(doppler secrets get DATABASE_URL -p happykube -c dev --plain)" \
  REDIS_URL="$(doppler secrets get REDIS_URL -p happykube -c dev --plain)" \
  --app happykube

# Security
fly secrets set \
  ENCRYPTION_KEY="$(doppler secrets get ENCRYPTION_KEY -p happykube -c dev --plain)" \
  API_KEYS="$(doppler secrets get API_KEYS -p happykube -c dev --plain)" \
  INTERNAL_API_KEY="$(doppler secrets get INTERNAL_API_KEY -p happykube -c dev --plain)" \
  --app happykube

# Bot e AI
fly secrets set \
  TELEGRAM_BOT_TOKEN="$(doppler secrets get TELEGRAM_BOT_TOKEN -p happykube -c dev --plain)" \
  GROQ_API_KEY="$(doppler secrets get GROQ_API_KEY -p happykube -c dev --plain)" \
  --app happykube

# Optional: Monitoring
fly secrets set \
  SENTRY_DSN="$(doppler secrets get SENTRY_DSN -p happykube -c dev --plain)" \
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
1. **Build Docker** - Compila l'immagine (multi-stage)
2. **Push Registry** - Carica su Fly.io registry
3. **Run Migrations** - Applica migrazioni Alembic su NeonDB
4. **Start Services** - Avvia API (uvicorn) e Bot (Telegram)
5. **Health Checks** - Verifica `/healthz`

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
# Connetti a NeonDB e verifica dati
psql "postgresql://neondb_owner:...@ep-misty-star-abzkkcf9-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require"

# Query verifica
SELECT COUNT(*) FROM emotions;
SELECT * FROM emotions ORDER BY created_at DESC LIMIT 5;
```

### Verifica Redis
```bash
# Connetti a Redis Cloud
redis-cli -u "redis://neon:...@redis-18844.crce175.eu-north-1-1.ec2.cloud.redislabs.com:18844"

# Verifica chiavi
DBSIZE
KEYS emotion:*
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
**Causa:** TELEGRAM_BOT_TOKEN errato o bot process crashed
**Soluzione:**
```bash
# Verifica logs bot
fly logs --app happykube | grep "bot"

# Controlla supervisor
fly ssh console --app happykube
supervisorctl restart bot
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

# Sync da Doppler
/tmp/sync-doppler-to-fly.sh
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
- **VM:** 1/3 usate (256MB × 1)
- **Storage:** 3GB disponibili (usando ~500MB)
- **Bandwidth:** 160GB/mese (usando ~5GB)
- **Costo:** $0/mese ✅

### Limiti Free Tier
- 3 VM con 256MB ciascuna
- 3GB persistent volumes
- 160GB outbound bandwidth/mese

**Nota:** Database (NeonDB) e Redis (Redis Cloud) sono esterni, non consumano risorse Fly.io.

---

## 📚 Risorse

- [Fly.io Docs](https://fly.io/docs/)
- [Fly.io Django/FastAPI Guide](https://fly.io/docs/python/)
- [Fly.io Secrets Management](https://fly.io/docs/reference/secrets/)
- [NeonDB Documentation](https://neon.tech/docs)
- [Redis Cloud Docs](https://redis.com/cloud/)
- [Doppler CLI](https://docs.doppler.com/docs/cli)

---

**Ultima modifica:** 1 Febbraio 2026
**Autore:** Claude Code
**Status:** ✅ Ready for production
