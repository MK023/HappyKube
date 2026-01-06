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

### 3. Configuration Management
- [ ] **Centralizzare month names** (attualmente duplicati in 2 file)
  - Create `src/domain/constants.py` con `ITALIAN_MONTHS`
  - Rimuovere hardcoded dictionaries
  - Benefits: DRY, facilita i18n futuro

### 4. Error Handling
- [ ] **Custom exception hierarchy**
  - `EmotionNotFoundException` invece di generic `ValueError`
  - `InvalidMonthFormatException`
  - Better error messages per debugging

### 5. Type Safety
- [ ] **Strict typing** dove manca
  - Rivedere `str | None` → usare `Optional[str]` esplicitamente
  - Add `-> NoReturn` where appropriate
  - Benefits: mypy compliance, IDE support

## 📊 Performance Optimizations

### 6. Caching Strategy
- [ ] **Review cache TTLs**
  - Monthly stats: 30min → valutare se troppo aggressivo
  - Emotion analysis: 2h → OK

### 7. Database Queries
- [ ] **Add indexes** se mancano su:
  - `emotions.user_id + created_at` (monthly queries)
  - Review query plans con EXPLAIN

## 🧪 Testing

### 8. Unit Tests
- [ ] Aggiungere test per utility functions (quando separate)
- [ ] Test per error cases (404, timeout, etc.)

## 🔒 Security

### 9. API Key Management
- [ ] Valutare rotazione automatica API keys
- [ ] Add expiration alerts

## 📝 Notes
- **Priority**: 1 (webhook) > 2 (static methods) > rest
- **Estimated effort**: ~2-3 giorni (non consecutivi)
- **No breaking changes**: tutto backward compatible
