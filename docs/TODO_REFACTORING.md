# TODO: Refactoring & Best Practices

## 🔧 Code Quality Improvements

### 1. Bot Architecture - Webhook Migration
- [ ] **Migrate from polling to webhooks** (tecnologia vecchia → moderna)
  - Setup webhook endpoint in FastAPI
  - Configure Telegram webhook URL
  - Remove polling loop
  - Benefits: meno risorse, più veloce, scalabile

### 2. Remove Static Methods Anti-Pattern
- [ ] **Create utility modules** invece di `@staticmethod`
  - `src/presentation/bot/utils/formatters.py` → `get_month_name()`, `get_emotion_emoji()`
  - `src/application/utils/date_helpers.py` → funzioni date/time
  - Remove duplicated `_get_month_name()` (attualmente in service + handler)
  - Benefits: testabilità, riusabilità, SRP

### 3. Settings Architecture - Split Configuration
- [ ] **Dividere `settings.py` monolitico** (~250 righe, viola SRP)
  - Struttura proposta:
    ```
    config/
    ├── base.py          # app_name, version, env, debug
    ├── database.py      # PostgreSQL settings
    ├── api.py           # FastAPI, CORS, rate limiting
    ├── bot.py           # Telegram bot settings
    ├── external.py      # Groq, Sentry, Redis
    └── security.py      # JWT, encryption
    ```
  - Benefits: SRP, testabilità, manutenibilità, chiara separazione

### 4. Configuration Management
- [ ] **Centralizzare month names** (attualmente duplicati in 2 file)
  - Create `src/domain/constants.py` con `ITALIAN_MONTHS`
  - Rimuovere hardcoded dictionaries
  - Benefits: DRY, facilita i18n futuro

### 5. Error Handling
- [ ] **Custom exception hierarchy**
  - `EmotionNotFoundException` invece di generic `ValueError`
  - `InvalidMonthFormatException`
  - Better error messages per debugging

### 6. Type Safety
- [ ] **Strict typing** dove manca
  - Rivedere `str | None` → usare `Optional[str]` esplicitamente
  - Add `-> NoReturn` where appropriate
  - Benefits: mypy compliance, IDE support

## 🔄 CI/CD Infrastructure

### 7. GitHub Actions CI Pipeline
- [ ] **Fix failing CI pipelines** (falliscono continuamente)
  - Review workflow configuration
  - Fix test failures
  - Update dependencies in CI
  - Add proper error handling
  - Benefits: reliable deployments, catch bugs early

### 8. Dockerfile Security - Non-root User
- [ ] **Fix pip root user warning** in Dockerfile build
  - Attualmente: `WARNING: Running pip as the 'root' user...`
  - Soluzione: Creare utente non-privilegiato nel Dockerfile
  - Esempio:
    ```dockerfile
    RUN adduser --disabled-password --gecos '' appuser
    USER appuser
    ```
  - Benefits: security best practice, evita permission issues

## 📊 Performance Optimizations

### 9. Caching Strategy
- [ ] **Review cache TTLs**
  - Monthly stats: 30min → valutare se troppo aggressivo
  - Emotion analysis: 2h → OK

### 10. Database Queries
- [ ] **Add indexes** se mancano su:
  - `emotions.user_id + created_at` (monthly queries)
  - Review query plans con EXPLAIN

## 🧪 Testing

### 11. Unit Tests
- [ ] Aggiungere test per utility functions (quando separate)
- [ ] Test per error cases (404, timeout, etc.)

## 🔒 Security

### 12. API Key Management
- [ ] Valutare rotazione automatica API keys
- [ ] Add expiration alerts

## 📝 Notes
- **Priority**:
  1. Webhook migration (riduce costi Render)
  2. Fix CI pipelines (blocca development workflow)
  3. Settings split (facilita manutenzione)
  4. Static methods removal > rest
- **Estimated effort**: ~3-4 giorni (non consecutivi)
- **No breaking changes**: tutto backward compatible
