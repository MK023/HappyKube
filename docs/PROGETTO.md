# HappyKube v3.0 - Documentazione Progetto

## Panoramica

HappyKube è un bot Telegram con intelligenza artificiale per l'analisi emotiva del testo. L'utente invia un messaggio di testo e il bot risponde con l'emozione rilevata, il sentimento e un punteggio di confidenza. I risultati vengono salvati in un database PostgreSQL e sono consultabili tramite API REST per statistiche e report mensili.

Il sistema supporta italiano e inglese e rileva 7 emozioni: rabbia, gioia, tristezza, paura, amore, sorpresa, neutro. Classifica anche il sentimento come positivo, negativo o neutro.

---

## Stack Tecnologico

| Componente | Tecnologia | Motivazione |
|---|---|---|
| **Linguaggio** | Python 3.12 | Ecosistema AI/ML maturo, typing moderno con StrEnum, async nativo |
| **Web Framework** | FastAPI + Uvicorn | Framework ASGI async ad alte prestazioni, documentazione OpenAPI automatica, validazione Pydantic integrata |
| **AI / LLM** | Groq API (Llama 3.3 70B) | Inferenza ultra-veloce gratuita, modello 70B per alta qualità di analisi, nessun costo operativo |
| **Database** | PostgreSQL (NeonDB Serverless) | Serverless = nessun costo a riposo, JSONB per metadati flessibili, SSL nativo, region EU (London) |
| **Cache** | Redis (Redis Cloud) | Riduce chiamate API ripetute, TTL 1h per risultati stabili, connection pooling, region EU (Stockholm) |
| **Bot** | python-telegram-bot 21.7 | Libreria ufficiale, supporto webhook nativo, gestione errori robusta |
| **ORM** | SQLAlchemy 2.0 | mapped_column moderno, type-safe, DeclarativeBase, supporto async |
| **Migrazioni** | Alembic | Standard per SQLAlchemy, migrazioni versionabili e reversibili |
| **Deployment** | Fly.io (Frankfurt) | Free tier generoso, auto-stop/start, vicino ai servizi EU, deploy via Dockerfile |
| **Process Manager** | Supervisord | Gestione processo singolo nel container, restart automatico, logging stdout |
| **Sicurezza** | bcrypt + Fernet AES + JWT | API key hashate, testo utente crittografato a riposo, audit log completo |
| **Monitoring** | Sentry + Prometheus + structlog | Error tracking in produzione, metriche esportabili, logging strutturato JSON |
| **CI/CD** | GitHub Actions | Test automatici + linting su ogni push, integrato con repo pubblica |
| **Linting** | Ruff + Black | Ruff ultra-veloce con regole Bandit (sicurezza), Black per formatting consistente |
| **HTTP Client** | httpx con HTTP/2 | Connection pooling, multiplexing HTTP/2, timeout granulari |

---

## Architettura

### Pattern: Monolite con Clean Architecture (DDD-inspired)

L'applicazione segue i principi della Clean Architecture con separazione netta dei layer:

```
src/
  presentation/    <- API routes + Bot handlers + Middleware
  application/     <- Services + DTOs + Interfacce Repository
  domain/          <- Entities + Value Objects + Enums (puro Python, zero dipendenze)
  infrastructure/  <- Database + Cache + ML Client + Auth + Repository concreti
  config/          <- Settings + Logging + Sentry
```

### Perché Clean Architecture?

1. **Testabilità**: il domain layer è puro Python, testabile senza database o servizi esterni
2. **Sostituibilità**: cambiare Groq con OpenAI richiede solo un nuovo analyzer nell'infrastructure layer
3. **Manutenibilità**: ogni layer ha responsabilità chiare e ben definite
4. **Scalabilità**: se necessario, i layer possono essere estratti in microservizi

### Diagramma

Il file `docs/architettura.drawio` contiene il diagramma completo apribile con draw.io o diagrams.net.

---

## Flusso delle Richieste

### Flusso Telegram (Webhook)

```
Utente Telegram
    |
    v
Telegram API
    |  POST /telegram/webhook
    v
FastAPI (Presentation Layer)
    |  Middleware: SecurityHeaders -> APIKeyAuth -> RequestSizeLimit -> AuditLog
    v
telegram_webhook.py
    |  Valida secret token Telegram
    v
CommandHandlers / MessageHandlers
    |
    v
EmotionService.analyze_emotion()  (Application Layer)
    |
    |---> Redis Cache (check hit)
    |       |
    |       v  cache miss
    |---> GroqAnalyzer.analyze_emotion()   (parallelo)
    |---> GroqAnalyzer.analyze_sentiment() (parallelo)
    |       |
    |       v  asyncio.gather()
    |---> EmotionRepository.save()
    |---> Redis Cache (set, TTL 3600s)
    |
    v
Risposta formattata -> Telegram API -> Utente
```

### Flusso API REST

```
Client HTTP
    |  POST /api/v1/emotion (Header: X-API-Key)
    v
FastAPI + Middleware (rate limit 100/min)
    |
    v
EmotionService.analyze_emotion()
    |  (stesso flusso di sopra)
    v
JSON Response
```

---

## Schema Database

### Tabella `users`
| Colonna | Tipo | Note |
|---|---|---|
| `id` | UUID (PK) | Generato automaticamente |
| `telegram_id_hash` | VARCHAR(64) | SHA-256 dell'ID Telegram (privacy) |
| `created_at` | TIMESTAMPTZ | Registrazione |
| `last_seen_at` | TIMESTAMPTZ | Ultima interazione |
| `is_active` | BOOLEAN | Stato account |

### Tabella `emotions`
| Colonna | Tipo | Note |
|---|---|---|
| `id` | UUID (PK) | Generato automaticamente |
| `user_id` | UUID (FK -> users) | Riferimento utente |
| `text_encrypted` | BYTEA | Testo crittografato con Fernet AES-256 |
| `emotion` | VARCHAR(50) | Emozione rilevata |
| `score` | FLOAT | Confidenza (0.0 - 1.0) |
| `model_type` | VARCHAR(20) | Modello usato |
| `sentiment` | VARCHAR(20) | Sentimento (pos/neg/neutral) |
| `extra_data` | JSONB | Metadati aggiuntivi |
| `created_at` | TIMESTAMPTZ | Timestamp analisi |

### Tabella `api_keys`
| Colonna | Tipo | Note |
|---|---|---|
| `id` | UUID (PK) | Generato automaticamente |
| `key_hash` | VARCHAR(64) | Hash bcrypt della chiave |
| `name` | VARCHAR(100) | Nome/descrizione |
| `is_active` | BOOLEAN | Stato chiave |
| `rate_limit_per_minute` | INTEGER | Limite richieste/minuto |
| `expires_at` | TIMESTAMPTZ | Scadenza (opzionale) |
| `last_used_at` | TIMESTAMPTZ | Ultimo utilizzo |

### Tabella `audit_log`
| Colonna | Tipo | Note |
|---|---|---|
| `id` | UUID (PK) | Generato automaticamente |
| `user_id` | UUID (FK nullable) | Utente autenticato |
| `action` | VARCHAR(50) | Azione eseguita |
| `endpoint` | VARCHAR(100) | Endpoint chiamato |
| `ip_address` | VARCHAR(45) | IP client (supporta IPv6) |
| `user_agent` | TEXT | User agent |
| `created_at` | TIMESTAMPTZ | Timestamp |

---

## Sicurezza

### Misure Implementate (OWASP Top 10)

| Minaccia | Protezione |
|---|---|
| **A01 - Broken Access Control** | API key con bcrypt (cost 12), middleware di autenticazione globale |
| **A02 - Cryptographic Failures** | Fernet AES-256 per PII, SHA-256 per ID Telegram, bcrypt per API key |
| **A03 - Injection** | Pydantic validation, SQLAlchemy parametrized queries |
| **A04 - Insecure Design** | Clean Architecture, separation of concerns, principle of least privilege |
| **A05 - Security Misconfiguration** | Security headers (X-Frame-Options, X-Content-Type-Options, etc.), debug disabilitato in produzione |
| **A06 - Vulnerable Components** | Ruff con regole Bandit (S prefix), dependency scanning con Safety |
| **A07 - Authentication Failures** | Rate limiting (slowapi), bcrypt con cost 12, chiavi con scadenza |
| **A08 - Software Integrity** | Docker multi-stage build, non-root user (appuser), .dockerignore rigoroso |
| **A09 - Security Logging** | Audit log completo, Sentry error tracking, structlog JSON |
| **A10 - SSRF** | Nessun input utente usato per URL, timeout espliciti su tutte le chiamate HTTP |

### Crittografia dei Dati

- **A riposo**: il testo dell'utente viene crittografato con Fernet (AES-128-CBC + HMAC-SHA256) prima di essere salvato nel database
- **In transito**: tutte le connessioni usano SSL/TLS (NeonDB richiede `sslmode=require`, Redis usa `rediss://`)
- **ID utente**: l'ID Telegram viene hashato con SHA-256 e solo l'hash viene salvato (privacy by design)

---

## Perché Queste Scelte?

### Groq invece di OpenAI/Anthropic
- **Gratuito**: 14.400 richieste/giorno senza costi
- **Ultra-veloce**: inferenza hardware specializzata, risposte in <1s
- **Llama 3.3 70B**: modello open-source di alta qualità, multilinguaggio
- **Nessun vendor lock-in**: il GroqAnalyzer è isolato nell'infrastructure layer

### NeonDB invece di PostgreSQL self-hosted
- **Serverless**: scala a zero, nessun costo quando inattivo
- **Compatibile PostgreSQL**: nessuna modifica al codice
- **Region EU**: London (eu-west-2) per conformità GDPR
- **Branching**: possibilità di creare branch del database per test

### Redis Cloud invece di Redis self-hosted
- **Free tier**: 30MB sufficienti per cache emotiva
- **Region EU**: Stockholm (eu-north-1)
- **Managed**: backup, monitoring, SSL inclusi

### Fly.io invece di AWS/GCP
- **Free tier generoso**: 3 shared-cpu-1x VMs gratuite
- **Auto-stop/start**: nessun costo quando il bot non è in uso
- **Deploy semplice**: `fly deploy` da Dockerfile
- **Region Frankfurt**: bassa latenza verso NeonDB e Redis Cloud

### Webhook invece di Polling
- **Efficienza**: nessuna richiesta polling continua, risorse usate solo quando necessario
- **Scalabilità**: compatibile con auto-stop di Fly.io (il bot si sveglia al primo messaggio)
- **Processo singolo**: API e bot nello stesso processo, zero overhead

### Clean Architecture invece di MVC semplice
- **Progetto educativo**: dimostra best practice professionali
- **Estensibilità**: aggiungere un nuovo analyzer (es. OpenAI) richiede solo una nuova classe
- **Testing**: il domain layer è testabile in isolamento completo
- **Manutenzione**: struttura chiara per chi contribuisce al progetto

---

## Endpoint API

| Metodo | Path | Descrizione | Auth |
|---|---|---|---|
| `GET` | `/` | Informazioni API | No |
| `GET` | `/healthz` | Liveness probe | No |
| `GET` | `/healthz/db` | Health check database | No |
| `GET` | `/healthz/redis` | Health check Redis | No |
| `GET` | `/ping` | Ping leggero | No |
| `GET` | `/readyz` | Readiness probe (DB + Redis + Groq) | No |
| `POST` | `/api/v1/emotion` | Analisi emotiva | X-API-Key |
| `GET` | `/api/v1/report` | Report emozioni | X-API-Key |
| `GET` | `/reports/monthly/{telegram_id}/{month}` | Statistiche mensili | X-API-Key |
| `POST` | `/telegram/webhook` | Webhook Telegram | Secret Token |
| `GET` | `/metrics` | Metriche Prometheus | No |

---

## Comandi Bot Telegram

| Comando | Descrizione |
|---|---|
| `/start` | Benvenuto e registrazione utente |
| `/help` | Guida ai comandi disponibili |
| `/ask` | Richiesta di analisi emotiva |
| `/monthly` | Report statistiche mensili |
| `/exit` | Chiusura sessione |
| *(testo libero)* | Analisi emotiva automatica del messaggio |

---

## Deployment

### Prerequisiti
- Account Fly.io
- NeonDB database (PostgreSQL serverless)
- Redis Cloud instance
- Groq API key (gratuita)
- Token bot Telegram (da @BotFather)

### Variabili d'Ambiente Richieste

| Variabile | Descrizione | Obbligatoria |
|---|---|---|
| `DATABASE_URL` | URL PostgreSQL con `?sslmode=require` | Si |
| `REDIS_URL` | URL Redis con `rediss://` per SSL | Si |
| `ENCRYPTION_KEY` | Chiave Fernet 32 caratteri | Si (produzione) |
| `API_KEYS` | Chiavi API (formato HK_...) | Si |
| `INTERNAL_API_KEY` | Chiave interna per webhook | Si |
| `TELEGRAM_BOT_TOKEN` | Token da @BotFather | Si |
| `GROQ_API_KEY` | Chiave API Groq | Si |
| `SENTRY_DSN` | DSN Sentry per error tracking | No |

### Deploy su Fly.io

```bash
# Primo deploy
fly launch --name happykube --region fra

# Imposta secrets
fly secrets set DATABASE_URL="postgresql://..." REDIS_URL="rediss://..." ...

# Deploy successivi
fly deploy
```

---

## Struttura Directory

```
HappyKube/
  src/
    config/           # Settings (Pydantic), logging (structlog), Sentry
    domain/
      entities/       # EmotionRecord, User (puro Python)
      enums/          # EmotionType, SentimentType, ModelType (StrEnum)
      value_objects/  # EmotionScore, UserId (validazione + hashing)
    application/
      dto/            # Pydantic models per request/response
      interfaces/     # Interfacce astratte repository
      services/       # EmotionService (logica di business)
    infrastructure/
      auth/           # JWT utilities
      cache/          # Redis wrapper con TTL
      database/       # SQLAlchemy models, connection, encryption
      ml/             # GroqAnalyzer (httpx HTTP/2), ModelFactory
      repositories/   # Implementazioni concrete dei repository
    presentation/
      api/
        app.py        # FastAPI factory con lifespan
        middleware/    # Security, Auth, Audit, Rate limiting
        routes/       # Emotion, Health, Reports, Webhook, Metrics
      bot/
        handlers/     # CommandHandlers, MessageHandlers
    scripts/          # CLI per gestione API key (click)
  alembic/            # Migrazioni database
  docker/             # entrypoint.sh, supervisord.conf
  tests/              # Unit tests (pytest + pytest-asyncio)
  docs/               # Documentazione progetto
  Dockerfile          # Multi-stage build (builder + runtime)
  fly.toml            # Configurazione Fly.io
  pyproject.toml      # Dipendenze, linting, test config
  wsgi.py             # Entry point ASGI per Uvicorn
```

---

## Performance

### Ottimizzazioni Implementate

- **Connection pooling**: httpx (Groq), SQLAlchemy (DB pool_size=3), Redis (max_connections=10)
- **HTTP/2**: multiplexing per chiamate Groq, riduce latenza di connessione
- **Cache Redis**: risultati cachati per 1 ora, evita chiamate API ripetute per lo stesso testo
- **Analisi parallela**: emozione e sentimento analizzati in parallelo con `asyncio.gather()`
- **Lazy loading**: modelli ML caricati solo al primo utilizzo
- **Auto-stop Fly.io**: container spento quando inattivo (free tier optimization)
- **Docker multi-stage**: immagine runtime leggera senza tool di build

### Limiti Noti

- **Groq free tier**: 14.400 richieste/giorno (10/min media)
- **Fly.io free tier**: 512MB RAM, 1 shared vCPU
- **NeonDB free tier**: 0.5 GB storage, auto-suspend dopo 5 minuti inattività
- **Redis Cloud free tier**: 30MB storage

---

## Sviluppo Locale

```bash
# Clona il repository
git clone https://github.com/marcobellingeri/HappyKube.git
cd HappyKube

# Crea virtual environment
python -m venv .venv
source .venv/bin/activate

# Installa dipendenze (incluse dev)
pip install -e ".[dev]"

# Copia e configura variabili d'ambiente
cp .env.example .env
# Modifica .env con i tuoi valori

# Esegui i test
pytest tests/ -v

# Linting
ruff check src/ tests/
black --check src/ tests/

# Avvia l'applicazione
uvicorn wsgi:app --host 0.0.0.0 --port 5000 --reload
```
