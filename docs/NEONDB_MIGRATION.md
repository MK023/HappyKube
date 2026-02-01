# Migrazione da Render DB a NeonDB

**Deadline:** ~23 Gennaio 2026 (7-8 giorni da oggi)
**Motivo:** Render rende il PostgreSQL a pagamento

## 📋 Checklist Pre-Migrazione

- [ ] Verificare dati importanti esistenti su Render DB
- [ ] Backup completo del database Render
- [ ] Testare NeonDB in locale (già fatto ✅)
- [ ] Preparare DATABASE_URL per Doppler/Render
- [ ] Schedulare finestra di migrazione

---

## 🗄️ NeonDB - Configurazione

### Connection String (Pooler)
```
postgresql://neondb_owner:npg_VtgGS1rI8PmW@ep-misty-star-abzkkcf9-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require
```

**⚠️ IMPORTANTE:** Salvare questa connection string in Doppler (encrypted), mai committarla su Git!

### Caratteristiche
- **Region:** EU-West-2 (London)
- **Database:** neondb
- **Pooling:** Attivo (-pooler endpoint)
- **SSL:** Richiesto
- **Schema:** Completamente migrato (3 migrations applicate)

---

## 📦 Step 1: Backup Dati da Render

**Prima della scadenza, esportare tutti i dati importanti!**

### Opzione A: Export completo (pg_dump)

```bash
# Get Render DB URL dal dashboard
export RENDER_DB_URL="postgresql://..."

# Export completo
pg_dump "$RENDER_DB_URL" > render_backup_$(date +%Y%m%d).sql

# Verifica dimensione backup
ls -lh render_backup_*.sql
```

### Opzione B: Export selettivo (solo dati)

```bash
# Export solo dati utenti ed emozioni (no schema)
pg_dump "$RENDER_DB_URL" \
  --data-only \
  --table=users \
  --table=emotions \
  --table=api_keys \
  --table=audit_log \
  > render_data_only_$(date +%Y%m%d).sql
```

### Opzione C: Export CSV per analisi

```bash
# Export emotions in CSV
psql "$RENDER_DB_URL" -c "\COPY emotions TO 'emotions_export.csv' CSV HEADER"

# Export users in CSV
psql "$RENDER_DB_URL" -c "\COPY users TO 'users_export.csv' CSV HEADER"
```

---

## 🚀 Step 2: Importare Dati su NeonDB

### Se hai fatto export completo (pg_dump)

```bash
export NEON_DB_URL="postgresql://neondb_owner:npg_VtgGS1rI8PmW@ep-misty-star-abzkkcf9-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require"

# Import su NeonDB
psql "$NEON_DB_URL" < render_backup_20260116.sql
```

### Se hai fatto export solo dati

NeonDB ha già lo schema (migrations già eseguite), quindi:

```bash
# Import solo i dati
psql "$NEON_DB_URL" < render_data_only_20260116.sql
```

### Verifica Import

```bash
# Conta records importati
psql "$NEON_DB_URL" -c "SELECT
  (SELECT COUNT(*) FROM users) as users,
  (SELECT COUNT(*) FROM emotions) as emotions,
  (SELECT COUNT(*) FROM api_keys) as api_keys,
  (SELECT COUNT(*) FROM audit_log) as audit_log;"
```

---

## 🔄 Step 3: Switch Database su Render

### ⚠️ IMPORTANTE: Deploy del render.yaml aggiornato

Prima di configurare DATABASE_URL, assicurati di aver fatto il deploy del `render.yaml` aggiornato che:
- Rimuove `healthCheckPath: /ping` (risparmia ore di utilizzo!)
- Configura DATABASE_URL come variabile manuale

### Metodo: Tramite Render Dashboard (raccomandato)

1. Vai su https://dashboard.render.com
2. Apri service **happykube**
3. **Environment** → **Environment Variables**
4. Trova `DATABASE_URL` (o creala se non esiste)
5. Click **Edit** (o **Add Environment Variable**)
6. Incolla la NeonDB connection string:
   ```
   postgresql://neondb_owner:npg_VtgGS1rI8PmW@ep-misty-star-abzkkcf9-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require
   ```
7. **Save** (trigger auto-redeploy)

**📝 Nota:** Dopo il deploy, Render userà l'endpoint `/` come health check invece di `/ping`, riducendo drasticamente il consumo di ore.

### Verifica Deploy

Controlla i log su Render:
```
✅ Running database migrations...
INFO  [alembic.runtime.migration] Running upgrade  -> 001, Initial schema
INFO  [alembic.runtime.migration] Running upgrade 001 -> 7cb92b21caa4
INFO  [alembic.runtime.migration] Running upgrade 7cb92b21caa4 -> 6aeaf4a488e7
✅ All migrations completed
✅ Services started successfully
```

---

## 🧪 Step 4: Test Post-Migrazione

### Test API Health

```bash
curl https://happykube.onrender.com/ping
# Expected: {"status": "ok"}

curl https://happykube.onrender.com/health
# Expected: {"status": "healthy", "database": "connected", ...}
```

### Test Bot

1. Apri Telegram
2. Invia messaggio al bot
3. Verifica risposta
4. Controlla che l'analisi emotiva funzioni

### Verifica Database

```bash
# Connetti a NeonDB e verifica ultimi record
psql "$NEON_DB_URL" -c "SELECT COUNT(*) FROM emotions;"
psql "$NEON_DB_URL" -c "SELECT * FROM emotions ORDER BY created_at DESC LIMIT 5;"
```

---

## 📊 Architettura Finale

```
                    ┌─────────────┐
                    │   Doppler   │
                    │   (Secrets) │
                    └──────┬──────┘
                           │
                           ▼
┌──────────────────────────────────────┐
│      Render Web Service              │
│   (API + Bot + Supervisor)           │
│      Region: Frankfurt               │
└───────┬──────────┬──────────┬────────┘
        │          │          │
        ▼          ▼          ▼
   ┌────────┐ ┌────────┐ ┌──────────┐
   │ NeonDB │ │ Redis  │ │  Groq    │
   │ (NEW)  │ │ Cloud  │ │   API    │
   │EU-West2│ │EU-North│ │          │
   └────────┘ └────────┘ └──────────┘
```

**Componenti:**
- **Render:** Hosting API + Bot (Frankfurt)
- **Doppler:** Gestione secrets e config
- **NeonDB:** PostgreSQL serverless (London)
- **Redis Cloud:** Cache distribuita (EU-North-1)
- **Groq API:** LLM per analisi emozioni

---

## 🔧 Troubleshooting

### Problema: Migration fallisce su NeonDB

**Soluzione:** Le migrations sono idempotenti, ri-esegui:
```bash
alembic upgrade head
```

### Problema: Errore "statement_timeout not supported"

**Soluzione:** Il codice già gestisce questo caso automaticamente. Verifica che stai usando l'URL con `-pooler`.

### Problema: Dati non visibili dopo import

**Causa:** Probabilmente conflitto con sequence/ID.

**Soluzione:**
```sql
-- Reset sequences dopo import
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));
SELECT setval('emotions_id_seq', (SELECT MAX(id) FROM emotions));
```

### Problema: Connection timeout

**Causa:** SSL o network issue.

**Soluzione:** Verifica che l'URL contenga `?sslmode=require`

---

## ⚠️ Note Importanti

1. **Password in Chiaro:** La connection string contiene password. Usare sempre Doppler/secrets manager, mai committare su Git.

2. **Backup Prima di Tutto:** Render cancellerà i dati dopo la scadenza. Backup PRIMA di qualsiasi operazione.

3. **Redis Rimane su Render:** Non toccare REDIS_URL, rimane invariato.

4. **Downtime Minimo:** Se fai import dati durante la migrazione, il downtime è ~2-5 minuti.

5. **Rollback Plan:** Se qualcosa va storto, puoi tornare temporaneamente a Render DB (se ancora disponibile).

---

## 📅 Timeline Consigliata

**Oggi (16 Gennaio):**
- ✅ NeonDB configurato e testato
- ✅ Codice compatibile pushato

**Tra 2-3 giorni (18-19 Gennaio):**
- [ ] Backup completo Render DB
- [ ] Test import su NeonDB
- [ ] Verifica che i dati siano corretti

**Giorno della Scadenza (~23 Gennaio):**
- [ ] Ultimo backup Render DB
- [ ] Import finale su NeonDB
- [ ] Switch DATABASE_URL su Render
- [ ] Verifica tutto funziona
- [ ] Monitor logs per 24h

---

## 🎁 Bonus: NeonDB Features

### Database Branching

Crea branch del database per test:
```bash
# Via NeonDB CLI
neonctl branches create --name test-migration

# Usa il branch URL per test isolati
```

### Autoscaling

NeonDB scala automaticamente in base al carico:
- **Compute:** 0.25 - 4 vCPU (free tier)
- **Storage:** 0.5 GB (free tier)
- **Scale-to-zero:** Risparmio quando inattivo

### Monitoring

Dashboard NeonDB: https://console.neon.tech/
- Query performance
- Connection stats
- Storage usage

---

## 📞 Supporto

- **NeonDB Docs:** https://neon.tech/docs
- **NeonDB Discord:** https://discord.gg/neon
- **Render Support:** https://render.com/docs/troubleshooting-deploys

---

**Ultima modifica:** 16 Gennaio 2026
**Status:** ✅ Pronto per migrazione
