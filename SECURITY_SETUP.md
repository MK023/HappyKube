# 🔒 Security Setup - CRITICAL

## ⚠️ IMPORTANTE: Configurare SUBITO dopo il deploy

L'API è attualmente **PUBBLICA** e deve essere protetta con API Key.

## 🚀 Setup Rapido (5 minuti)

### 1. Genera API Key

La tua API key sicura è già generata:

```
HK_L_Ln0elQ0R1CN_z83Xpd2HpbhbWTgt53zWMKEhZmgxY
```

**⚠️ CONSERVALA IN MODO SICURO - è come una password!**

### 2. Configura su Render

#### A. Aggiungi API Key al servizio Web (API)

1. Vai su https://dashboard.render.com/web/srv-d59fttbuibrs73b9ndc0
2. Clicca "Environment"
3. Aggiungi variabile:
   - **Key**: `API_KEYS`
   - **Value**: `HK_L_Ln0elQ0R1CN_z83Xpd2HpbhbWTgt53zWMKEhZmgxY`
4. Clicca "Save Changes"

#### B. Il bot Telegram usa l'API internamente (stesso container)

Il bot e l'API girano nello stesso container Docker, quindi **NON serve configurare nulla** per il bot - condividono le stesse variabili d'ambiente.

### 3. Verifica Sicurezza

Dopo il deploy, testa:

```bash
# ❌ Deve fallire (senza API key)
curl https://happykube-d884.onrender.com/api/v1/emotion/analyze

# ✅ Deve funzionare (con API key)
curl -H "X-API-Key: HK_L_Ln0elQ0R1CN_z83Xpd2HpbhbWTgt53zWMKEhZmgxY" \
     https://happykube-d884.onrender.com/api/v1/emotion/analyze

# ✅ Health check sempre pubblico
curl https://happykube-d884.onrender.com/ping
```

## 🛡️ Protezioni Implementate

### 1. **API Key Authentication** ⭐ PRINCIPALE
- Header `X-API-Key` richiesto per tutti gli endpoint
- Constant-time comparison (anti timing-attack)
- Solo `/healthz`, `/ping`, `/readyz`, `/metrics` sono pubblici

### 2. **Security Headers**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security` (HSTS)
- `Content-Security-Policy` (production)

### 3. **Request Size Limits**
- Max 1MB per request
- Protezione contro payload attacks

### 4. **Rate Limiting**
- 100 requests/minute per IP
- Anti-DoS protection

### 5. **Audit Logging**
- Tutti gli accessi loggati in DB
- IP, user-agent, endpoint tracciati

## 🔑 Come Usare l'API (per sviluppo futuro)

Se in futuro vuoi chiamare l'API da un client esterno:

```python
import httpx

API_KEY = "HK_L_Ln0elQ0R1CN_z83Xpd2HpbhbWTgt53zWMKEhZmgxY"

async with httpx.AsyncClient() as client:
    response = await client.post(
        "https://happykube-d884.onrender.com/api/v1/emotion/analyze",
        headers={"X-API-Key": API_KEY},
        json={"text": "Mi sento felice oggi!"}
    )
    print(response.json())
```

## 🔄 Rotazione API Key

Se devi cambiare la chiave:

```bash
# Genera nuova key
python3 -c "import secrets; print('HK_' + secrets.token_urlsafe(32))"

# Aggiorna su Render
# 1. Aggiungi nuova key: API_KEYS=old_key,new_key
# 2. Deploy
# 3. Aggiorna tutti i client
# 4. Rimuovi old_key: API_KEYS=new_key
```

## ⚠️ IMPORTANTE

- **MAI commitare API_KEYS in Git** - usa solo .env locale
- **Solo su Render dashboard** - configurazione manuale
- **Il bot Telegram funziona automaticamente** - stesso container
- **Endpoints pubblici**: solo health checks e metrics

## 📊 Monitoring

Controlla tentativi non autorizzati:

```sql
-- Audit log su PostgreSQL
SELECT * FROM audit_log
WHERE endpoint NOT IN ('/healthz', '/ping', '/readyz', '/metrics')
ORDER BY created_at DESC
LIMIT 100;
```
