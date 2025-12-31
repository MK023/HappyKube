# API Key Management System

Sistema di gestione delle API key basato su database con bcrypt hashing e controllo delle scadenze.

## 🔐 Caratteristiche di Sicurezza

- **Bcrypt Hashing**: Le chiavi sono hashate con bcrypt (no plaintext storage)
- **Scadenza**: Supporto per chiavi con data di scadenza
- **Rate Limiting**: Limite di richieste per minuto configurabile per ogni chiave
- **Tracking**: Timestamp di ultimo utilizzo per ogni chiave
- **Constant-Time Comparison**: Previene timing attacks durante la validazione

## 📋 CLI Tool - Gestione Chiavi

### Installazione

```bash
# Installa dipendenze
pip install -e .

# Oppure solo click se già installato il progetto
pip install click
```

### Creazione Nuova API Key

```bash
# Sintassi base
python src/scripts/manage_api_keys.py create "Nome Key"

# Con rate limit personalizzato
python src/scripts/manage_api_keys.py create "Production Bot" --rate-limit 200

# Con scadenza
python src/scripts/manage_api_keys.py create "Test Key" --rate-limit 50 --expires 2026-12-31

# Esempio completo
python src/scripts/manage_api_keys.py create "HappyKube Production API" --rate-limit 300
```

**Output Esempio:**
```
✅ API key created successfully!

ID:         550e8400-e29b-41d4-a716-446655440000
Name:       Production Bot
Rate Limit: 200 req/min
Expires:    Never

🔑 API Key (COPY THIS NOW - won't be shown again):
    HK_P_abc123def456ghi789jkl012mno345pqr678

💡 Add this to your .env or Render environment:
    API_KEYS="HK_P_abc123def456ghi789jkl012mno345pqr678"
```

⚠️ **IMPORTANTE**: Salva la chiave immediatamente! Non verrà più mostrata.

### Elenco Chiavi

```bash
# Mostra solo chiavi attive
python src/scripts/manage_api_keys.py list

# Mostra anche chiavi disattivate
python src/scripts/manage_api_keys.py list --include-inactive
```

**Output Esempio:**
```
📋 API Keys (2 total):

ID:         550e8400-e29b-41d4-a716-446655440000
Name:       Production Bot
Status:     ✅ Active
Rate Limit: 200 req/min
Created:    2025-12-30
Expires:    Never
Last Used:  2025-12-31 10:30
--------------------------------------------------
```

### Disattivazione Chiave

```bash
# Usa l'ID UUID della chiave
python src/scripts/manage_api_keys.py deactivate 550e8400-e29b-41d4-a716-446655440000
```

## 🚀 Deployment su Render

### 1. Creazione Prima API Key (Locale)

```bash
# Crea la chiave in locale (connesso al DB di produzione)
python src/scripts/manage_api_keys.py create "Render Production" --rate-limit 300

# Output:
# 🔑 API Key: HK_P_xyz789abc...
```

### 2. Configurazione Environment Variable su Render

```bash
# Vai su Render Dashboard → Service → Environment
# Aggiungi/Aggiorna:
API_KEYS="HK_P_xyz789abc..."  # La chiave generata al punto 1
```

### 3. Migrazione Database (Automatica)

Il sistema esegue automaticamente le migration all'avvio del container tramite `entrypoint.sh`:

```bash
#!/bin/bash
# Run Alembic migrations
cd src && alembic upgrade head
```

La migration `20251226_0100_001_initial_schema.py` crea la tabella `api_keys` se non esiste.

## 🔧 Come Funziona

### 1. Middleware Security (Validazione)

Il middleware `APIKeyMiddleware` in [src/presentation/api/middleware/security.py](../src/presentation/api/middleware/security.py):

1. Estrae `X-API-Key` header dalla richiesta
2. Chiama `APIKeyRepository.validate_key()` per validazione
3. Verifica con bcrypt (`bcrypt.checkpw()`) - constant-time comparison
4. Controlla scadenza (`expires_at < now()`)
5. Aggiorna `last_used_at` timestamp
6. Salva `api_key_id` e `rate_limit` in `request.state` per audit logging

### 2. Repository (Database Operations)

Il repository `APIKeyRepository` in [src/infrastructure/repositories/api_key_repository.py](../src/infrastructure/repositories/api_key_repository.py):

**Metodi:**
- `validate_key(api_key: str)` → `(is_valid, api_key_id, rate_limit)`
- `create_key(api_key, name, rate_limit, expires_at)` → `APIKeyModel`
- `deactivate_key(key_id: UUID)` → `bool`
- `list_keys(include_inactive: bool)` → `list[APIKeyModel]`

### 3. Generazione Chiavi Sicure

Formato: `HK_<env>_<40 random chars>`

```python
import secrets

def generate_secure_api_key() -> str:
    prefix = "HK_P_"  # HappyKube Production
    random_part = secrets.token_urlsafe(30)  # ~40 chars base64
    return f"{prefix}{random_part}"
```

**Esempio**: `HK_P_L_Ln0elQ0R1CN_z83Xpd2HpbhbWTgt53zWMKEhZmgxY`

Usa `secrets.token_urlsafe()` per garantire crittograficamente sicurezza CSPRNG.

## 📊 Schema Database

Tabella: `api_keys`

```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY,
    key_hash VARCHAR(64) UNIQUE NOT NULL,  -- Bcrypt hash
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    rate_limit_per_minute INTEGER DEFAULT 100,
    created_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ
);

CREATE INDEX ix_api_keys_key_hash ON api_keys (key_hash);
```

## 🔄 Migration da Environment Variables

### Stato Attuale (Variabili d'Ambiente)

```bash
# render.yaml
API_KEYS: "HK_L_key1,HK_L_key2,HK_L_key3"
```

### Nuovo Sistema (Database)

1. **Crea chiavi nel database**:
```bash
python src/scripts/manage_api_keys.py create "Telegram Bot" --rate-limit 200
python src/scripts/manage_api_keys.py create "Web Dashboard" --rate-limit 100
```

2. **Aggiorna Render (opzionale - backward compatibility)**:
```bash
# Puoi mantenere API_KEYS per fallback, ma non sarà più usato
# Il middleware usa SOLO il database ora
```

3. **Rimuovi vecchie chiavi** (dopo verifica):
```bash
# In render.yaml, rimuovi o commenta:
# - key: API_KEYS
#   value: "..."
```

## 🛡️ Best Practices

### 1. Rotazione Chiavi

```bash
# 1. Crea nuova chiave
python src/scripts/manage_api_keys.py create "Production Bot v2" --rate-limit 200

# 2. Aggiorna client con nuova chiave
# (Telegram bot, dashboard, ecc.)

# 3. Disattiva vecchia chiave dopo 24h
python src/scripts/manage_api_keys.py deactivate <old_key_id>
```

### 2. Chiavi di Test con Scadenza

```bash
# Chiave temporanea per testing (scade dopo 7 giorni)
python src/scripts/manage_api_keys.py create "Test Key" \
    --rate-limit 50 \
    --expires 2026-01-07
```

### 3. Rate Limiting per Ambiente

- **Production Bot**: 300 req/min (alto traffico)
- **Dashboard Web**: 100 req/min (uso normale)
- **Testing**: 50 req/min (limitato)
- **Public API**: 30 req/min (utenti esterni)

### 4. Monitoring

```bash
# Controlla quando le chiavi sono state usate l'ultima volta
python src/scripts/manage_api_keys.py list

# Disattiva chiavi inutilizzate da >30 giorni
```

## 🔍 Troubleshooting

### Error: "Invalid API key"

1. **Verifica chiave nel database**:
```bash
python src/scripts/manage_api_keys.py list
```

2. **Controlla scadenza**:
   - Se `expires_at` è passato, la chiave è scaduta
   - Crea nuova chiave o rimuovi scadenza nel database

3. **Verifica header HTTP**:
```bash
curl -H "X-API-Key: HK_P_..." https://your-api.com/emotions/analyze
```

### Error: "Authentication service error"

- **Database non raggiungibile**: Controlla `DATABASE_URL`
- **Migration non eseguita**: Esegui `alembic upgrade head`
- **Tabella api_keys mancante**: Verifica migration 001

### Chiave non funziona dopo creazione

1. **Riavvia il servizio** (Render redeploy)
2. **Verifica bcrypt hash** nel database:
```sql
SELECT id, name, key_hash, is_active FROM api_keys WHERE is_active = true;
```

## 📝 Note Tecniche

### Bcrypt vs Plain Text

**Prima (insicuro)**:
```python
# settings.py
api_keys = ["HK_L_plaintext1", "HK_L_plaintext2"]

# Confronto diretto
if api_key in api_keys:
    # ✅ Valid
```

**Ora (sicuro)**:
```python
# Database (bcrypt hash)
key_hash: "$2b$12$abc123..."  # Bcrypt hash del plaintext

# Validazione
if bcrypt.checkpw(api_key.encode(), key_hash.encode()):
    # ✅ Valid (constant-time comparison)
```

### Performance

- **Bcrypt è lento**: ~100ms per verifica (di proposito per prevenire brute-force)
- **Caching**: Il middleware usa lazy-loading del repository
- **Connection Pooling**: SQLAlchemy riusa le connessioni al database

### Security Features

1. **Constant-Time Comparison**: `bcrypt.checkpw()` previene timing attacks
2. **Salt Automatico**: Bcrypt genera salt unico per ogni chiave
3. **Work Factor**: Bcrypt usa 12 rounds (configurable in `bcrypt.gensalt()`)
4. **No Rainbow Tables**: Salt rende impossibile pre-computare hash

## 🎯 Roadmap Future

- [ ] API REST per gestione chiavi (POST /admin/api-keys)
- [ ] Dashboard web per monitoring
- [ ] Alert su chiavi in scadenza (email/Telegram)
- [ ] Statistiche uso per chiave (richieste/giorno)
- [ ] IP whitelisting per chiave
- [ ] Revoca automatica dopo inattività (90 giorni)

## 📚 Riferimenti

- [Bcrypt Spec](https://en.wikipedia.org/wiki/Bcrypt)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [Python secrets module](https://docs.python.org/3/library/secrets.html)
