# HappyKube v3.0 🤖😊

AI-powered emotion analysis Telegram bot with webhook architecture and enterprise security.

[![CI/CD Pipeline](https://github.com/MK023/HappyKube/actions/workflows/ci.yml/badge.svg)](https://github.com/MK023/HappyKube/actions/workflows/ci.yml)
[![CodeQL](https://img.shields.io/badge/CodeQL-enabled-brightgreen?logo=github)](https://github.com/MK023/HappyKube/security/code-scanning)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)
![Fly.io](https://img.shields.io/badge/Fly.io-Frankfurt-7B3FE4?logo=flydotio&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Webhook-26A5E4?logo=telegram&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-F55036)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**[Live bot](https://t.me/happykube_bot)** | **[API health](https://happykube.fly.dev/healthz)** | **[Security policy](SECURITY.md)**

## 🎯 Why

Built to learn three things at the same time, on a real product I would actually use:

1. **Clean Architecture in Python** — strict 4-layer separation (domain / infrastructure / application / presentation) with zero framework leakage into the core. The same pattern used in Java/.NET enterprise systems, applied to a Python async stack.
2. **Production-grade security on a hobby budget** — Fernet encryption for PII, prompt-injection prevention in the LLM pipeline, cache-poisoning resistance, full OWASP Top 10 coverage, SAST in CI. The bot processes user emotional data; the security bar matches what that responsibility demands.
3. **Free-tier production deployment** — Fly.io + Postgres + Redis Cloud all on free tiers, running ~$0/month, but designed so that *every architectural decision still holds* if it had to scale 100x tomorrow. No "I'll fix it when we have users" code.

The bot itself (emotion analysis via Groq LLaMA 3.3 70B) is the product; the architecture is the portfolio.

## 💰 Operating cost

Production deployment runs at **~$0/month** on free tiers:

| Component | Cost | Notes |
|---|---|---|
| Fly.io app (Frankfurt, 256 MB RAM) | Free | 3 shared-cpu-1x VMs free with auto-stop/start |
| Fly.io internal PostgreSQL | Free | Managed, Frankfurt region |
| Redis Cloud (Stockholm, 30 MB) | Free | 24h TTL for analyses, 1h for statistics |
| Groq API (LLaMA 3.3 70B) | Free | 14,400 req/day free tier |
| Telegram Bot API | Free | Unlimited messages |
| Sentry | Free | Free tier with sampling |

Auto-stop/start on Fly.io means the bot consumes **zero CPU when idle**. With light traffic, the entire stack genuinely costs nothing — but uses the same architectural patterns I'd use at scale.

## 🌟 Features

- 🤖 **AI-Powered Analysis**: Groq LLaMA 3.3 70B for multilingual emotion detection
- 🇮🇹 Italian emotion detection (7 emotions + neutral)
- 🇬🇧 English emotion detection (7 emotions + neutral)
- 📊 Advanced sentiment analysis with confidence scores
- 🔐 Enterprise security: Fernet encryption (AES-128 CBC), API key auth, rate limiting, prompt injection prevention
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

# Install pre-commit hooks
pre-commit install

# Configure
cp .env.example .env
# Edit .env with your values

# Run locally
uvicorn wsgi:app --host 0.0.0.0 --port 5000 --reload

# Run tests
pytest tests/ -v
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full development workflow.

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
# Format + Lint (ruff replaces black + flake8)
ruff format src/ tests/
ruff check src/ tests/ --fix

# Type check
mypy src/ --ignore-missing-imports

# Security scan
bandit -r src/ -x tests/ -s B101,B104

# Run all checks via pre-commit
pre-commit run --all-files
```

## 🛡️ Security

- **OWASP Top 10**: Full coverage — see [SECURITY.md](SECURITY.md)
- **Encryption**: Fernet (AES-128 CBC + HMAC) for user messages, bcrypt for API keys, SHA-256 for user IDs
- **Prompt Injection Prevention**: System/user message separation in LLM prompts
- **Cache Poisoning Prevention**: UNKNOWN results are never cached
- **Input Validation**: Multi-layer (Pydantic DTOs + service validation + SQL parametrization)
- **Secret Detection**: Pre-commit hooks (detect-secrets + gitleaks)
- **CI/CD Security**: CodeQL SAST, Trivy container scan, Hadolint, dependency review, Bandit, Safety

## 📝 Notes

- **Architecture**: Clean Architecture (DDD-inspired) with 4 layers
- **AI Model**: Groq LLaMA 3.3 70B (fast, accurate, free tier: 14,400 req/day)
- **Database**: Fly.io internal PostgreSQL (managed, Frankfurt region)
- **Cache**: Redis Cloud (30MB free tier, 24h TTL for analysis, 1h for stats)
- **Memory**: 512MB RAM on Fly.io free tier with auto-stop/start
- **Region**: Frankfurt (Fly.io + PostgreSQL), Stockholm (Redis Cloud)

## 📄 License

[MIT License](LICENSE)

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## 🙏 Acknowledgments

- [Groq](https://groq.com/) for ultra-fast LLM inference
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for the Telegram bot framework
- [FastAPI](https://fastapi.tiangolo.com/) for high-performance async API

---

**Built with Clean Architecture and Domain-Driven Design**
