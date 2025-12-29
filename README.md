# HappyKube v2.0 🤖😊

AI-powered emotion analysis Telegram bot with clean architecture.

## 🌟 Features

- 🇮🇹 Italian emotion detection (anger, joy, sadness, fear)
- 🇬🇧 English emotion detection (7 emotions)
- 📊 Sentiment analysis (positive, negative, neutral)
- 🔐 AES-256 encryption for PII
- 🚀 Production-ready Flask API
- ⚡ Redis caching
- 📊 PostgreSQL database with migrations

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
└── render.yaml              # Render.com config
```

## 🚀 Deploy to Render

### 1. Prerequisites
- GitHub repository
- [Render.com](https://render.com) account
- Telegram Bot Token from [@BotFather](https://t.me/botfather)

### 2. Generate Secrets

```bash
# Encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# JWT secret (any random string)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# API key (any random string)
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

### 3. Deploy

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Ready for Render"
   git push origin main
   ```

2. **Connect to Render**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Blueprint"
   - Connect your GitHub repo
   - Render will auto-detect `render.yaml`

3. **Set Secret Environment Variables**

   In Render dashboard, set these for BOTH services (api + bot):

   ```
   ENCRYPTION_KEY=<generated-fernet-key>
   JWT_SECRET_KEY=<generated-jwt-secret>
   API_KEYS=<generated-api-key>
   TELEGRAM_BOT_TOKEN=<from-botfather>
   ```

4. **Deploy!**
   - Click "Apply" in Render
   - Wait ~10-15 minutes for build (models download)
   - Check logs for errors

### 4. Setup UptimeRobot

Keep API alive on free tier:

1. Go to [UptimeRobot](https://uptimerobot.com)
2. Add new monitor:
   - Type: HTTP(s)
   - URL: `https://your-app.onrender.com/ping`
   - Interval: 5 minutes

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

- `GET /ping` - UptimeRobot health check
- `GET /healthz` - Liveness probe
- `GET /readyz` - Readiness probe (DB + Redis)
- `POST /api/v1/emotion` - Analyze emotion
- `GET /api/v1/report` - Get user report

### Example Request

```bash
curl -X POST https://your-app.onrender.com/api/v1/emotion \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"user_id": "123", "text": "Oggi mi sento felice!"}'
```

## 🤖 Telegram Bot Commands

- `/start` - Start conversation
- `/help` - Show help
- `/ask` - Analyze emotion

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
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `ENCRYPTION_KEY` | Fernet key for PII encryption | Yes |
| `JWT_SECRET_KEY` | JWT signing key | Yes |
| `API_KEYS` | Comma-separated API keys | Yes |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | Yes (bot only) |

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

- **Free tier limitations**: API sleeps after 15 min inactivity (use UptimeRobot)
- **Build time**: First deploy takes ~10-15 min (ML models download)
- **Memory**: Free tier has 512MB RAM, sufficient for this app
- **Database**: Free PostgreSQL has 1GB limit

## 📄 License

MIT License

## 🙏 Acknowledgments

- [MilaNLProc](https://github.com/MilaNLProc) for Italian NLP models
- [Hugging Face](https://huggingface.co/) for transformers
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)

---

**Built with Clean Architecture and Domain-Driven Design**
