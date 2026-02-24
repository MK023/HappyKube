# HappyKube v3.0 🤖😊

AI-powered emotion analysis Telegram bot with webhook architecture and enterprise security.

## 🌟 Features

- 🤖 **AI-Powered Analysis**: Groq LLaMA 3.3 70B for multilingual emotion detection
- 🇮🇹 Italian emotion detection (7 emotions + neutral)
- 🇬🇧 English emotion detection (7 emotions + neutral)
- 📊 Advanced sentiment analysis with confidence scores
- 🔐 Enterprise security: AES-256 encryption, API key auth, rate limiting, prompt injection prevention
- 🚀 Production-ready FastAPI with webhook architecture
- ⚡ Redis caching with intelligent TTL (24h analysis, 1h statistics)
- 📊 PostgreSQL database (Fly.io internal) with Alembic migrations
- 🔄 Telegram webhook mode (no polling, auto-stop/start)
- 🛡️ Hardened core pipeline: input validation, cache poisoning prevention, decrypt resilience

## 📁 Project Structure

```
happykube/
├── src/
│   ├── domain/              # Core business logic (pure Python, zero deps)
│   ├── infrastructure/      # Database, cache, ML, auth
│   ├── application/         # Services, DTOs, repository interfaces
│   ├── presentation/        # API routes, bot handlers, middleware
│   └── config/              # Settings, logging, Sentry
├── docker/                  # entrypoint.sh, supervisord.conf
├── tests/                   # Unit tests (pytest + pytest-asyncio)
├── alembic/                 # Database migrations
├── docs/                    # Project documentation
└── fly.toml                 # Fly.io deployment config
```

## 🚀 Deploy to Fly.io

### 1. Prerequisites
- GitHub repository
- [Fly.io](https://fly.io) account
- Telegram Bot Token from [@BotFather](https://t.me/botfather)
- Groq API key from [Groq Console](https://console.groq.com)
- Redis Cloud instance from [Redis Cloud](https://redis.com/try-free/)

### 2. Generate Secrets

```bash
# Encryption key (Fernet)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# API key
python -c "import secrets; print('HK_' + secrets.token_urlsafe(32))"

# Internal API key (for Telegram webhook)
python -c "import secrets; print('HK_' + secrets.token_urlsafe(32))"

# Telegram webhook secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Deploy

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   fly auth login
   ```

2. **Create App with Postgres**
   ```bash
   fly launch --no-deploy
   # Follow prompts, select Frankfurt region
   fly postgres create --name happykube-db --region fra
   fly postgres attach happykube-db --app happykube
   ```

3. **Set Secrets**
   ```bash
   fly secrets set \
     ENCRYPTION_KEY="<generated-fernet-key>" \
     JWT_SECRET_KEY="<generated-jwt-secret>" \
     API_KEYS="<generated-api-key>" \
     INTERNAL_API_KEY="<generated-internal-key>" \
     TELEGRAM_BOT_TOKEN="<from-botfather>" \
     TELEGRAM_WEBHOOK_SECRET="<generated-webhook-secret>" \
     GROQ_API_KEY="<from-groq-console>" \
     REDIS_URL="<redis-cloud-connection-string>"
   ```
   Note: `DATABASE_URL` is set automatically by `fly postgres attach`.

4. **Deploy**
   ```bash
   fly deploy --ha=false
   ```

5. **Setup Telegram Webhook**
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://happykube.fly.dev/telegram/webhook", "secret_token": "<TELEGRAM_WEBHOOK_SECRET>"}'
   ```

### 4. External Services

#### Redis Cloud
1. Create account at [Redis Cloud](https://redis.com/try-free/)
2. Create database in EU-North-1 (Stockholm)
3. Get connection string (`rediss://...` for TLS)

## 🔧 Local Development

```bash
# Setup
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your values

# Run locally
uvicorn wsgi:app --host 0.0.0.0 --port 5000 --reload

# Run tests
pytest tests/ -v
```

## 📡 API Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/ping` | Basic health check | No |
| `GET` | `/healthz` | Liveness probe | No |
| `GET` | `/readyz` | Readiness probe (DB + Redis + Groq) | No |
| `POST` | `/api/v1/emotion` | Analyze emotion | X-API-Key |
| `GET` | `/api/v1/report` | Get emotion report | X-API-Key |
| `GET` | `/reports/monthly/{telegram_id}/{month}` | Monthly statistics | X-API-Key |
| `POST` | `/telegram/webhook` | Telegram webhook | Secret Token |
| `GET` | `/metrics` | Prometheus metrics | No |

### Example Request

```bash
curl -X POST https://happykube.fly.dev/api/v1/emotion \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"text": "Oggi mi sento felice!"}'
```

## 🤖 Telegram Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Start conversation and register |
| `/help` | Show available commands |
| `/ask` | Request emotion analysis prompt |
| `/monthly` | View monthly statistics report |
| `/exit` | Exit current operation |
| *(free text)* | Instant emotion analysis |

## 📊 Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 🧪 Testing

```bash
pytest
pytest --cov=src --cov-report=html
```

## 🔐 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string (Fly.io internal) | Yes |
| `REDIS_URL` | Redis connection string (Redis Cloud, `rediss://`) | Yes |
| `ENCRYPTION_KEY` | Fernet key for PII encryption | Yes |
| `JWT_SECRET_KEY` | JWT signing key | Yes |
| `API_KEYS` | Comma-separated API keys (HK_ prefix) | Yes |
| `INTERNAL_API_KEY` | Internal API key for Telegram webhook | Yes |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | Yes |
| `TELEGRAM_WEBHOOK_SECRET` | Webhook secret token validation | Yes |
| `GROQ_API_KEY` | Groq API key for LLM analysis | Yes |
| `SENTRY_DSN` | Sentry error tracking DSN | No |

## 🛠️ Development Tools

```bash
# Format
black src/

# Lint
ruff check src/

# Type check
mypy src/

# Security scan
bandit -r src/
```

## 🛡️ Security Hardening

- **Prompt Injection Prevention**: LLM prompts use system/user message separation
- **Cache Poisoning Prevention**: UNKNOWN results are never cached
- **Input Validation**: Service-layer validation for all inputs (text length, empty checks)
- **Decrypt Resilience**: Bulk operations survive individual decrypt failures
- **Session Safety**: Rollback on all exception types, not just SQLAlchemy errors
- **Bot Singleton**: Shared Bot instance prevents resource leaks
- **Privacy**: User messages deleted after analysis, PII excluded from logs

See [SECURITY.md](SECURITY.md) for full OWASP Top 10 coverage.

## 📝 Notes

- **Architecture**: Clean Architecture (DDD-inspired) with 4 layers
- **Security**: API key auth (bcrypt), rate limiting, audit logging, prompt injection prevention
- **AI Model**: Groq LLaMA 3.3 70B (fast, accurate, free tier: 14,400 req/day)
- **Database**: Fly.io internal PostgreSQL (managed, Frankfurt region)
- **Cache**: Redis Cloud (30MB free tier, 24h TTL for analysis, 1h for stats)
- **Memory**: 512MB RAM on Fly.io free tier with auto-stop/start
- **Region**: Frankfurt (Fly.io + PostgreSQL), Stockholm (Redis Cloud)

## 📄 License

MIT License

## 🙏 Acknowledgments

- [Groq](https://groq.com/) for ultra-fast LLM inference
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) v22
- [FastAPI](https://fastapi.tiangolo.com/) for high-performance async API

---

**Built with Clean Architecture and Domain-Driven Design**
