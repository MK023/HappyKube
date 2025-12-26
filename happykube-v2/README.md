# HappyKube v2.0 🤖😊

Enterprise-grade emotion analysis Telegram bot with production-ready architecture.

## 🌟 Features

### v2.0 Improvements
- ✅ **Clean Architecture**: Domain-driven design with proper separation of concerns
- ✅ **Security**: AES-256 encryption for PII, API key authentication, rate limiting
- ✅ **Performance**: Redis caching, connection pooling, optimized Docker images
- ✅ **Scalability**: Kubernetes-native, horizontal pod autoscaling
- ✅ **Database**: SQLAlchemy 2.0 with Alembic migrations
- ✅ **Type Safety**: Full type hints with mypy validation
- ✅ **Testing**: Pytest framework (unit + integration tests)
- ✅ **Monitoring**: Structured logging, health checks, Prometheus-ready

### AI/ML Capabilities
- 🇮🇹 Italian emotion detection (anger, joy, sadness, fear)
- 🇬🇧 English emotion detection (7 emotions)
- 📊 Sentiment analysis (positive, negative, neutral)
- 🤖 Automatic language detection
- 💾 Encrypted emotion history storage

## 📁 Project Structure

```
happykube-v2/
├── src/
│   ├── domain/              # Core business logic
│   │   ├── entities/        # User, EmotionRecord
│   │   ├── value_objects/   # UserId, EmotionScore
│   │   └── enums/           # EmotionType, ModelType
│   ├── infrastructure/      # External dependencies
│   │   ├── database/        # SQLAlchemy models + encryption
│   │   ├── cache/           # Redis wrapper
│   │   ├── ml/              # ML analyzers + factory
│   │   └── repositories/    # Data persistence
│   ├── application/         # Use cases
│   │   ├── services/        # Business logic orchestration
│   │   ├── dto/             # Data transfer objects
│   │   └── interfaces/      # Repository interfaces
│   ├── presentation/        # API/Bot layer
│   │   ├── api/             # Flask REST API
│   │   └── bot/             # Telegram bot
│   ├── config/              # Settings + logging
│   └── migrations/          # Alembic migrations
├── tests/                   # Test suite
├── docker/                  # Dockerfiles
├── deployment/              # Kubernetes manifests
└── scripts/                 # Utility scripts
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Docker & Docker Compose
- Minikube (for K8s deployment)
- PostgreSQL database (or use Neon)
- Redis
- Telegram Bot Token ([get one from @BotFather](https://t.me/botfather))

### 1. Local Development

```bash
# Clone repository
cd happykube-v2

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements/dev.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env

# Generate encryption key
python scripts/generate_encryption_key.py

# Run database migrations
alembic upgrade head

# Migrate old data (optional)
python scripts/migrate_old_data.py

# Run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f api
docker-compose logs -f bot
```

### 2. Minikube Deployment

```bash
# Start Minikube
minikube start --cpus=4 --memory=8192

# Create secrets file
cp deployment/overlays/minikube/secrets.yaml.example deployment/overlays/minikube/secrets.yaml

# Edit secrets with your credentials
nano deployment/overlays/minikube/secrets.yaml

# Deploy to Minikube
chmod +x scripts/deploy_minikube.sh
./scripts/deploy_minikube.sh

# Port forward API (optional)
kubectl port-forward svc/happykube-api 5000:80 -n happykube

# Check bot logs
kubectl logs -f deployment/happykube-bot -n happykube
```

## 🔐 Security

### Secrets Management
Never commit secrets to git! Use:
- **Local dev**: `.env` file (gitignored)
- **Minikube**: `secrets.yaml` (gitignored, copy from `.example`)
- **Production**: Sealed Secrets or External Secrets Operator

### Generate Encryption Key
```python
python scripts/generate_encryption_key.py
```

### PII Protection
- User text is encrypted at rest (AES-256 Fernet)
- Telegram IDs are hashed (SHA-256)
- API requires authentication
- Rate limiting enabled

## 📊 Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# Check current version
alembic current
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_emotion_service.py

# Run with verbose output
pytest -v
```

## 🐳 Docker

### Build Images

```bash
# Build API
docker build -f docker/Dockerfile.api -t emmekappa23/happykube-api:v2.0.0 .

# Build Bot
docker build -f docker/Dockerfile.bot -t emmekappa23/happykube-bot:v2.0.0 .

# Push to registry (if needed)
docker push emmekappa23/happykube-api:v2.0.0
docker push emmekappa23/happykube-bot:v2.0.0
```

## 📡 API Endpoints

### Health Checks
- `GET /healthz` - Liveness probe
- `GET /readyz` - Readiness probe (checks DB + Redis)

### Emotion Analysis
```bash
# Analyze emotion
curl -X POST http://localhost:5000/api/v1/emotion \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-12345" \
  -d '{"user_id": "123456789", "text": "Oggi mi sento felice!"}'

# Get user report
curl -X GET "http://localhost:5000/api/v1/report?user_id=123456789&month=2025-12" \
  -H "X-API-Key: dev-key-12345"
```

## 🤖 Telegram Bot Commands

- `/start` - Start conversation
- `/help` - Show help message
- `/ask` - Prompt for emotion input

## 🔧 Configuration

See [.env.example](.env.example) for all available configuration options.

Key settings:
- `DB_*` - Database connection (Neon PostgreSQL)
- `REDIS_*` - Redis cache configuration
- `ENCRYPTION_KEY` - Fernet key for PII encryption
- `API_KEYS` - Comma-separated API keys
- `TELEGRAM_BOT_TOKEN` - Bot authentication

## 📈 Monitoring

### Logs
```bash
# Docker Compose
docker-compose logs -f api
docker-compose logs -f bot

# Kubernetes
kubectl logs -f deployment/happykube-api -n happykube
kubectl logs -f deployment/happykube-bot -n happykube
```

### Metrics
Prometheus metrics available at `/metrics` (if enabled).

## 🛠️ Development Tools

### Code Quality
```bash
# Format code
black src/

# Lint
ruff check src/

# Type checking
mypy src/

# Security scan
bandit -r src/
```

### Pre-commit Hooks
```bash
pre-commit install
pre-commit run --all-files
```

## 📝 Migration from v1

If you have data in the old HappyKube schema:

1. Rename old table: `ALTER TABLE emotions RENAME TO emotions_old;`
2. Run migrations: `alembic upgrade head`
3. Migrate data: `python scripts/migrate_old_data.py`
4. Verify data was migrated correctly
5. Archive old table: `ALTER TABLE emotions_old RENAME TO emotions_archive;`

## 🚀 Production Deployment

### AWS
Update image tags in `deployment/overlays/aws/` and apply:
```bash
kubectl apply -k deployment/overlays/aws/
```

### Oracle Cloud
Update configurations in `deployment/overlays/oracle/` and apply:
```bash
kubectl apply -k deployment/overlays/oracle/
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pytest`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open Pull Request

## 📄 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

- [MilaNLProc](https://github.com/MilaNLProc) for Italian NLP models
- [Hugging Face](https://huggingface.co/) for transformer models
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for Telegram API

## 📞 Support

- Issues: [GitHub Issues](https://github.com/MK023/HappyKube/issues)
- Email: marco@example.com

---

**Built with ❤️ using Clean Architecture and Domain-Driven Design**
