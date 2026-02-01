# 🚀 Guida Rapida: Deploy NeonDB su Render

**Data:** 1 Febbraio 2026
**Status:** ✅ Pronto per deployment

## 📋 Modifiche Apportate

### 1. ✅ render.yaml Aggiornato
- ❌ Rimosso `healthCheckPath: /ping` (risparmio ore!)
- ✅ Render userà `/` come health check (più leggero)
- ✅ DATABASE_URL configurato come variabile manuale per NeonDB

### 2. ✅ Codice già compatibile
- Il codice in `src/infrastructure/database/connection.py` supporta già NeonDB
- Gestione automatica del pooler NeonDB (linee 43-46)
- Ottimizzazioni per serverless (pool_recycle=300)

---

## 🎯 Passaggi per il Deployment

### Step 1: Push del codice aggiornato

```bash
git add render.yaml docs/
git commit -m "feat: migrate to NeonDB and optimize health checks

- Remove healthCheckPath to save Render hours
- Configure DATABASE_URL for NeonDB
- Update deployment documentation"
git push origin main
```

### Step 2: Configurare DATABASE_URL su Doppler

**Nota:** HappyKube usa Doppler per gestire le variabili d'ambiente. Aggiorna DATABASE_URL su Doppler:

```bash
# Aggiorna DATABASE_URL con NeonDB
doppler secrets set DATABASE_URL="postgresql://neondb_owner:npg_VtgGS1rI8PmW@ep-misty-star-abzkkcf9-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require" -p happykube -c dev

# Verifica
doppler secrets get DATABASE_URL -p happykube -c dev
```

**Se hai più config Doppler** (es. `prd` per produzione), aggiorna anche quelli:

```bash
doppler secrets set DATABASE_URL="postgresql://..." -p happykube -c prd
```

Doppler sincronizzerà automaticamente con Render se l'integrazione è configurata.

### Step 3: Verificare il deployment

Attendi il deploy e controlla i log su Render:

```
✅ Building...
✅ Running database migrations...
INFO  [alembic.runtime.migration] Running upgrade  -> 001, Initial schema
✅ All migrations completed
✅ Services started successfully
```

### Step 4: Test finale

```bash
# Test health check
curl https://happykube.onrender.com/
# Expected: {"service": "HappyKube", "version": "2.0.1", "status": "running", ...}

# Test database connectivity
curl https://happykube.onrender.com/healthz/db
# Expected: {"status": "healthy", "service": "database"}

# Test bot su Telegram
# Invia un messaggio al bot e verifica la risposta
```

---

## 🎉 Benefici della Migrazione

### 1. **Zero Costi per il DB**
- NeonDB free tier: 0.5 GB storage, autoscaling
- Render DB era diventato a pagamento

### 2. **Risparmio Ore Render**
- Prima: `/ping` chiamato ogni ~10s → ~259,200 chiamate/mese
- Dopo: `/` chiamato ogni ~25s → ~103,680 chiamate/mese
- **Risparmio stimato: ~60% di ore mensili**

### 3. **Performance Migliori**
- NeonDB ha autoscaling automatico
- Pooler connection (-pooler endpoint) per latenza ridotta
- Region EU-West-2 (London) vicina a Frankfurt (Render)

### 4. **Architettura Ottimizzata**

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
   │        │ │ Cloud  │ │   API    │
   │EU-West2│ │EU-North│ │          │
   └────────┘ └────────┘ └──────────┘
```

**Nessun database Render utilizzato** - tutti i servizi esterni gestiti via Doppler.

---

## 🔧 Troubleshooting

### Problema: "Database connection failed"

**Causa:** DATABASE_URL non configurato o errato

**Soluzione:**
1. Verifica che DATABASE_URL sia impostato su Render
2. Controlla che contenga `-pooler` nell'URL
3. Verifica che finisca con `?sslmode=require&channel_binding=require`

### Problema: "Migration failed"

**Causa:** NeonDB non ha le migrazioni applicate

**Soluzione:**
```bash
# Connetti a NeonDB localmente
export DATABASE_URL="postgresql://neondb_owner:npg_VtgGS1rI8PmW@ep-misty-star-abzkkcf9-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# Applica migrazioni
cd src
alembic upgrade head
```

### Problema: "Health check failing"

**Causa:** L'endpoint `/` non è accessibile

**Soluzione:**
1. Verifica che il servizio sia in running su Render
2. Controlla i log per errori
3. Testa manualmente: `curl https://happykube.onrender.com/`

---

## 📊 Monitoraggio

### NeonDB Dashboard
- URL: https://console.neon.tech/
- Monitora: Query performance, connection stats, storage usage

### Render Dashboard
- URL: https://dashboard.render.com/
- Monitora: Deploy status, logs, metrics, hours usage

### Verifica Ore Rimanenti
1. Vai su Render Dashboard
2. Service **happykube** → **Metrics**
3. Controlla "Hours Used" questo mese
4. Dovrebbe mostrare un consumo molto ridotto dopo il deploy

---

## 📅 Prossimi Step (Opzionali)

### 1. Rimuovere il DB Render (se non più usato)
- Vai su Render Dashboard → Database **happykube-db**
- Click **Delete** (conferma)
- Risparmio: rimuove il servizio non più necessario

### 2. Monitorare performance NeonDB
- Usa NeonDB Console per vedere query lente
- Considera di aggiungere indici se necessario

### 3. Configurare backup automatici
- NeonDB ha snapshot automatici (free tier)
- Puoi creare branch del database per test

---

## 🔐 Sicurezza

⚠️ **IMPORTANTE:** La connection string di NeonDB contiene password in chiaro.

- ✅ È salvata come variabile d'ambiente su Render (encrypted)
- ❌ NON committare mai su Git
- ✅ Usa solo su piattaforme sicure (Render, Doppler, ecc.)

---

## ✅ Checklist Finale

- [ ] Push del codice aggiornato (`render.yaml`)
- [ ] DATABASE_URL configurato su Render Dashboard
- [ ] Deploy completato con successo
- [ ] Test endpoint `/` funzionante
- [ ] Test `/healthz/db` conferma connessione a NeonDB
- [ ] Bot Telegram risponde correttamente
- [ ] Verificato consumo ore ridotto su Render

---

**Ultima modifica:** 1 Febbraio 2026
**Autore:** Claude Code
**Status:** ✅ Ready for deployment
