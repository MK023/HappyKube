# Axiom Setup & Dashboard Guide

Guida completa per configurare Axiom logging e creare dashboard personalizzate.

---

## 📋 Prerequisiti

1. Account Axiom: https://app.axiom.co/
2. API Token generato
3. Organization ID

---

## 🔧 Configurazione Environment Variables

### Su Render Dashboard

1. Vai su https://dashboard.render.com
2. Apri service **happykube**
3. **Environment** → **Environment Variables**
4. Aggiungi/verifica:

```bash
# Axiom Configuration
AXIOM_API_TOKEN=xaat-your-token-here
AXIOM_ORG_ID=your-org-id-here
AXIOM_DATASET=happykube

# IMPORTANTE: Deve essere production!
APP_ENV=production
```

### Su Doppler (se usi)

```bash
doppler secrets set AXIOM_API_TOKEN="xaat-..." -p happykube -c prd
doppler secrets set AXIOM_ORG_ID="..." -p happykube -c prd
doppler secrets set AXIOM_DATASET="happykube" -p happykube -c prd
doppler secrets set APP_ENV="production" -p happykube -c prd
```

---

## ✅ Verifica Configurazione

### Metodo 1: Check Logs di Startup

Dopo deploy, cerca nei logs:

```
✅ "Axiom initialized" dataset=happykube environment=production
✅ "Axiom logging processor enabled"
```

❌ **Se vedi:**
```
"Axiom not configured (AXIOM_API_TOKEN missing)"
```
→ AXIOM_API_TOKEN non è settato correttamente

❌ **Se vedi:**
```
"Axiom disabled in development environment"
```
→ APP_ENV è "development" invece di "production"

### Metodo 2: Test Manuale

```bash
# In locale con env vars di produzione
export AXIOM_API_TOKEN="xaat-..."
export AXIOM_ORG_ID="..."
export APP_ENV="production"

python3 << 'EOF'
import sys
sys.path.insert(0, 'src')

from config import init_axiom, setup_logging, get_logger

# Initialize
init_axiom()
setup_logging(service_name="test", axiom_enabled=True)

# Test logging
logger = get_logger(__name__)
logger.info("Test log to Axiom", test=True, timestamp="now")
logger.error("Test error log", error_code=500)

print("✅ Logs sent to Axiom! Check dashboard in 5-10 seconds.")
EOF
```

### Metodo 3: Query Axiom API

```bash
# Check dataset exists
curl -H "Authorization: Bearer $AXIOM_API_TOKEN" \
  "https://api.axiom.co/v1/datasets/happykube"

# Query recent logs
curl -H "Authorization: Bearer $AXIOM_API_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  "https://api.axiom.co/v1/datasets/happykube/query" \
  -d '{
    "startTime": "'$(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ)'",
    "endTime": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "aggregations": [{"op": "count"}]
  }'
```

---

## 📊 Creare Dashboard su Axiom

### Dashboard 1: Overview Sistema

**Cosa monitorare:**
- Request rate (API)
- Error rate
- Response time (p50, p95, p99)
- Active users
- Bot messages processed

**Step by step:**

1. **Vai su Axiom Dashboard**
   - https://app.axiom.co/
   - Click **Dashboards** → **New Dashboard**
   - Nome: "HappyKube - System Overview"

2. **Chart 1: Total Requests (Time Series)**
   ```apl
   ['happykube']
   | where ['service'] == 'api'
   | where ['level'] == 'info'
   | where contains(['message'], 'Request')
   | summarize count() by bin(_time, 5m)
   ```

3. **Chart 2: Error Rate (Time Series)**
   ```apl
   ['happykube']
   | where ['level'] == 'error'
   | summarize errors=count() by bin(_time, 5m)
   ```

4. **Chart 3: Response Time (Percentiles)**
   ```apl
   ['happykube']
   | where ['service'] == 'api'
   | where isnotnull(['duration_ms'])
   | summarize
       p50=percentile(['duration_ms'], 50),
       p95=percentile(['duration_ms'], 95),
       p99=percentile(['duration_ms'], 99)
     by bin(_time, 5m)
   ```

5. **Chart 4: Top Errors (Table)**
   ```apl
   ['happykube']
   | where ['level'] == 'error'
   | summarize count() by ['error']
   | sort by count_
   | limit 10
   ```

6. **Chart 5: Active Services (Stat)**
   ```apl
   ['happykube']
   | where _time > ago(5m)
   | summarize dcount(['service'])
   ```

### Dashboard 2: Bot Analytics

**Queries utili:**

1. **Messages Per Hour**
   ```apl
   ['happykube']
   | where ['service'] == 'bot'
   | where contains(['message'], 'emotion')
   | summarize count() by bin(_time, 1h)
   ```

2. **Top Emotions Detected**
   ```apl
   ['happykube']
   | where ['service'] == 'bot'
   | where isnotnull(['emotion'])
   | summarize count() by ['emotion']
   | sort by count_
   ```

3. **Bot Response Time**
   ```apl
   ['happykube']
   | where ['service'] == 'bot'
   | where isnotnull(['duration_ms'])
   | summarize
       avg_ms=avg(['duration_ms']),
       max_ms=max(['duration_ms'])
     by bin(_time, 10m)
   ```

4. **Error Messages**
   ```apl
   ['happykube']
   | where ['service'] == 'bot'
   | where ['level'] == 'error'
   | project _time, ['message'], ['error']
   | sort by _time desc
   | limit 50
   ```

### Dashboard 3: Database Monitoring

1. **Slow Queries (> 1 second)**
   ```apl
   ['happykube']
   | where contains(['message'], 'Slow query')
   | project _time, ['duration_ms'], ['query_preview']
   | sort by ['duration_ms'] desc
   ```

2. **Database Connections**
   ```apl
   ['happykube']
   | where contains(['message'], 'Database connection')
   | summarize count() by bin(_time, 5m), ['message']
   ```

3. **Query Performance Over Time**
   ```apl
   ['happykube']
   | where contains(['message'], 'Query completed')
   | summarize
       avg_ms=avg(['duration_ms']),
       p95_ms=percentile(['duration_ms'], 95)
     by bin(_time, 10m)
   ```

---

## 🔔 Alerts Setup

### Alert 1: High Error Rate

```apl
['happykube']
| where ['level'] == 'error'
| summarize error_count=count() by bin(_time, 5m)
| where error_count > 10
```

**Configurazione:**
- Threshold: > 10 errors in 5 minutes
- Notification: Email/Slack

### Alert 2: Slow Response Time

```apl
['happykube']
| where ['service'] == 'api'
| where ['duration_ms'] > 5000
| summarize slow_requests=count() by bin(_time, 5m)
| where slow_requests > 5
```

**Configurazione:**
- Threshold: > 5 requests taking > 5s in 5 minutes
- Notification: Email/Slack

### Alert 3: Service Down

```apl
['happykube']
| summarize last_log=max(_time)
| where last_log < ago(10m)
```

**Configurazione:**
- Threshold: No logs in 10 minutes
- Notification: Email/SMS/PagerDuty

---

## 🎨 Dashboard Layout Consigliato

```
┌─────────────────────────────────────────────────────┐
│             HappyKube - System Overview             │
├──────────────────┬──────────────────┬───────────────┤
│  Total Requests  │   Error Rate     │ Active Users  │
│   (Time Series)  │  (Time Series)   │    (Stat)     │
├──────────────────┴──────────────────┴───────────────┤
│            Response Time (Percentiles)              │
│              p50, p95, p99 (Line)                   │
├──────────────────┬──────────────────────────────────┤
│   Top Errors     │     Recent Error Logs            │
│    (Table)       │        (List)                    │
└──────────────────┴──────────────────────────────────┘
```

---

## 📝 Custom Queries Utili

### Debug: Trova Request Specifico

```apl
['happykube']
| where ['request_id'] == 'abc-123'
| project _time, ['service'], ['level'], ['message']
| sort by _time asc
```

### Performance: Query più lente oggi

```apl
['happykube']
| where _time > startofday(now())
| where isnotnull(['duration_ms'])
| sort by ['duration_ms'] desc
| limit 20
```

### Security: API Key Usage

```apl
['happykube']
| where contains(['message'], 'API key')
| summarize requests=count() by ['api_key_name']
```

### Users: Sentiment Analysis

```apl
['happykube']
| where ['service'] == 'bot'
| where isnotnull(['sentiment'])
| summarize count() by ['sentiment'], bin(_time, 1h)
```

---

## 🔍 Troubleshooting

### Problema: Nessun log visibile

**Causa 1: APP_ENV è development**
```bash
# Verifica su Render
echo $APP_ENV
# Deve essere: production
```

**Causa 2: Token invalido**
```bash
# Test token
curl -H "Authorization: Bearer $AXIOM_API_TOKEN" \
  https://api.axiom.co/v1/user
```

**Causa 3: Dataset non esiste**
```bash
# Crea dataset
curl -X POST \
  -H "Authorization: Bearer $AXIOM_API_TOKEN" \
  -H "Content-Type: application/json" \
  https://api.axiom.co/v1/datasets \
  -d '{"name": "happykube", "description": "HappyKube logs"}'
```

### Problema: Logs in ritardo

**Normale:** I logs vengono inviati in batch ogni 5 secondi.

**Se ritardo > 1 minuto:**
- Check network connectivity
- Check Axiom status: https://status.axiom.co/

### Problema: Logs duplicati

**Causa:** Multiple instances dello stesso service.

**Soluzione:** Aggiungere `instance_id` ai logs:
```python
import uuid
instance_id = str(uuid.uuid4())[:8]
structlog.contextvars.bind_contextvars(instance=instance_id)
```

---

## 📖 Risorse

- **Axiom Docs:** https://axiom.co/docs
- **APL Query Language:** https://axiom.co/docs/apl
- **Dashboard Examples:** https://axiom.co/docs/dashboards
- **Alerts Guide:** https://axiom.co/docs/monitor-data/monitors

---

## 🎯 Quick Start Checklist

- [ ] AXIOM_API_TOKEN settato su Render
- [ ] AXIOM_ORG_ID settato su Render
- [ ] APP_ENV=production (NON development!)
- [ ] Deploy effettuato
- [ ] Verificato logs di startup (vedi "Axiom initialized")
- [ ] Atteso 1-2 minuti per primi logs
- [ ] Aperto Axiom dashboard: https://app.axiom.co/
- [ ] Navigato su "happykube" dataset
- [ ] Visto i logs in arrivo
- [ ] Creato prima dashboard
- [ ] Settato primo alert

---

**Ultima modifica:** 16 Gennaio 2026
