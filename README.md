# HappyKube v3.0 🤖😊

AI-powered emotion analysis Telegram bot with webhook architecture and enterprise security.

## 🌟 Features

- 🤖 **AI-Powered Analysis**: Groq LLaMA 3.3 70B for multilingual emotion detection
- 🇮🇹 Italian emotion detection (7 emotions)
- 🇬🇧 English emotion detection (7 emotions)
- 📊 Advanced sentiment analysis with confidence scores
- 🔐 Enterprise security: AES-256 encryption, API key auth, rate limiting
- 🚀 Production-ready FastAPI with webhook architecture
- ⚡ Redis caching for optimal performance
- 📊 PostgreSQL database with Alembic migrations
- 🔄 Telegram webhook mode (no polling)

## 📁 Project Structure

```
happykube/
├── src/
│   ├── domain/              # Core business logic
│   ├── infrastructure/      # Database, cache, ML
│   ├── application/         # Services & DTOs
│   ├── presentation/        # API & Bot
│   ├── config/              # Settings
│   └── migrations/          # Alembic migrations
├── docker/                  # Dockerfiles
├── tests/                   # Test suite
└── fly.toml                 # Fly.io deployment config
```

## 🚀 Deploy to Fly.io

### 1. Prerequisites
- GitHub repository
- [Fly.io](https://fly.io) account
- Telegram Bot Token from [@BotFather](https://t.me/botfather)
- Groq API key from [Groq Console](https://console.groq.com)

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
```

### 3. Deploy

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   fly auth login
   ```

2. **Create App**
   ```bash
   fly launch --no-deploy
   # Follow prompts, select Frankfurt region (closest to NeonDB)
   ```

3. **Set Secrets**
   ```bash
   fly secrets set \
     ENCRYPTION_KEY="<generated-fernet-key>" \
     JWT_SECRET_KEY="<generated-jwt-secret>" \
     API_KEYS="<generated-api-key>" \
     INTERNAL_API_KEY="<generated-internal-key>" \
     TELEGRAM_BOT_TOKEN="<from-botfather>" \
     GROQ_API_KEY="<from-groq-console>" \
     DATABASE_URL="<neondb-connection-string>" \
     REDIS_URL="<redis-cloud-connection-string>"
   ```

4. **Deploy**
   ```bash
   fly deploy
   ```

5. **Setup Telegram Webhook**
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://your-app.fly.dev/telegram/webhook"}'
   ```

### 4. External Services

#### NeonDB (PostgreSQL)
1. Create account at [Neon](https://neon.tech)
2. Create project in EU-West-2 (London)
3. Get connection string with `-pooler` endpoint

#### Redis Cloud
1. Create account at [Redis Cloud](https://redis.com/try-free/)
2. Create database in EU-North-1 (Stockholm)
3. Get connection string

## 🔧 Local Development

```bash
# Setup
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your values

# Run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f api
docker-compose logs -f bot
```

## 📡 API Endpoints

- `GET /ping` - Basic health check
- `GET /healthz` - Liveness probe
- `GET /readyz` - Readiness probe (DB + Redis)
- `POST /api/v1/emotion/analyze` - Analyze emotion (requires API key)
- `GET /api/v1/reports/monthly/{telegram_id}/{month}` - Get monthly report
- `POST /telegram/webhook` - Telegram webhook endpoint (internal)
- `GET /metrics` - Prometheus metrics

### Example Request

```bash
curl -X POST https://your-app.fly.dev/api/v1/emotion/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"text": "Oggi mi sento felice!"}'
```

## 🤖 Telegram Bot Commands

- `/start` - Start conversation
- `/help` - Show help
- `/exit` - Exit current operation
- Just send a message - Get instant emotion analysis

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
| `DATABASE_URL` | PostgreSQL connection string (NeonDB) | Yes |
| `REDIS_URL` | Redis connection string (Redis Cloud) | Yes |
| `ENCRYPTION_KEY` | Fernet key for PII encryption | Yes |
| `JWT_SECRET_KEY` | JWT signing key | Yes |
| `API_KEYS` | Comma-separated API keys (HK_ prefix) | Yes |
| `INTERNAL_API_KEY` | Internal API key for Telegram webhook | Yes |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | Yes |
| `GROQ_API_KEY` | Groq API key for LLM analysis | Yes |
| `SENTRY_DSN` | Sentry error tracking DSN | No |
| `AXIOM_API_TOKEN` | Axiom logging token | No |

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

## 📝 Notes

- **Architecture**: Webhook-based (no polling) for better performance
- **Security**: API key authentication, rate limiting, audit logging
- **AI Model**: Groq LLaMA 3.3 70B (fast, accurate, free tier available)
- **Database**: NeonDB PostgreSQL serverless (0.5GB free tier)
- **Cache**: Redis Cloud (30MB free tier, sufficient for 2-hour TTL)
- **Memory**: 512MB RAM on Fly.io free tier
- **Region**: Frankfurt (Fly.io), London (NeonDB), Stockholm (Redis)

## 📄 License

MIT License

## 🙏 Acknowledgments

- [MilaNLProc](https://github.com/MilaNLProc) for Italian NLP models
- [Hugging Face](https://huggingface.co/) for transformers
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)

---

**Built with Clean Architecture and Domain-Driven Design**
