# 🔐 Doppler Setup Guide for HappyKube

## Why Doppler?

- ✅ **Centralized secrets management** - All secrets in one place
- ✅ **Environment-based configs** - dev, staging, production
- ✅ **Auto-sync to Render** - No manual env var updates
- ✅ **Encryption at rest** - AES-256 encryption
- ✅ **Audit logs** - Track who changed what
- ✅ **Version control** - Rollback capability

---

## Step 1: Install Doppler CLI

### macOS (Homebrew)
```bash
# Fix Homebrew permissions first
sudo chown -R $(whoami) /usr/local/Homebrew

# Install Doppler
brew install dopplerhq/cli/doppler
```

### Alternative: Direct Script
```bash
curl -Ls --tlsv1.2 --proto "=https" --retry 3 https://cli.doppler.com/install.sh | sudo sh
```

### Verify Installation
```bash
doppler --version
```

---

## Step 2: Login to Doppler

```bash
# This will open browser for authentication
doppler login
```

---

## Step 3: Setup Project

```bash
cd /Users/marcobellingeri/Documents/GitHub/HappyKube

# Initialize Doppler in your project
doppler setup

# You'll be prompted to:
# 1. Select/create project: HappyKube
# 2. Select config: dev (for local development)
```

This creates a `doppler.yaml` file (don't commit it):
```yaml
setup:
  project: happykube
  config: dev
```

---

## Step 4: Create Environments

Doppler usa 3 ambienti standard:

### Development (dev)
Local development - usa questo per testare in locale

### Staging (stg)
Pre-production testing

### Production (prd)
Produzione su Render

```bash
# Switch tra ambienti
doppler setup --config dev
doppler setup --config prd
```

---

## Step 5: Add Secrets to Doppler

### Via Dashboard (Consigliato)
1. Vai su https://dashboard.doppler.com
2. Seleziona progetto `HappyKube`
3. Seleziona config `prd` (production)
4. Aggiungi le secrets:

#### Required Secrets
```
DATABASE_URL=<NeonDB PostgreSQL URL>
REDIS_URL=<Render Redis URL>
TELEGRAM_BOT_TOKEN=<Your Telegram Bot Token>
GROQ_API_KEY=<Your Groq API Key>
JWT_SECRET_KEY=<Random secure string>
ENCRYPTION_KEY=<Fernet key for PII encryption>
```

#### Optional Secrets
```
APP_ENV=production
LOG_LEVEL=INFO
SENTRY_DSN=<Your Sentry DSN>
API_KEYS=<Comma-separated API keys>
```

### Via CLI (Alternativa)
```bash
# Switch to production config
doppler setup --config prd

# Add secrets one by one
doppler secrets set DATABASE_URL="postgresql://..."
doppler secrets set REDIS_URL="rediss://..."
doppler secrets set TELEGRAM_BOT_TOKEN="<token>"
doppler secrets set GROQ_API_KEY="<key>"
doppler secrets set JWT_SECRET_KEY="$(openssl rand -hex 32)"
doppler secrets set ENCRYPTION_KEY="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
```

---

## Step 6: Integrate with Render

### Option A: Render Integration (Automated Sync)

1. **In Doppler Dashboard:**
   - Go to Integrations → Render
   - Click "Connect Render"
   - Authorize Doppler to access Render
   - Select your Render service: `HappyKube`
   - Map Doppler config `prd` → Render service

2. **Auto-sync enabled!** 🎉
   - Changes in Doppler → Auto-deploy on Render
   - No more manual env var updates

### Option B: Service Token (Manual)

If you prefer manual control:

```bash
# Generate a service token for production
doppler configs tokens create prd-render --config prd

# Copy the token (starts with dp.st.prd_...)
```

Then in Render Dashboard:
- Add env var: `DOPPLER_TOKEN=dp.st.prd_...`
- Update Start Command:
  ```bash
  doppler run -- python -m src.presentation.bot.telegram_bot &
  doppler run -- python -m uvicorn src.presentation.api.app:app --host 0.0.0.0 --port $PORT
  ```

---

## Step 7: Local Development

### Run Locally with Doppler
```bash
# Development environment
doppler setup --config dev

# Run your app with Doppler injecting secrets
doppler run -- python -m src.presentation.bot.telegram_bot

# Or run tests
doppler run -- pytest

# Or open a shell with secrets loaded
doppler run -- bash
```

### VS Code Integration

Add to `.vscode/settings.json`:
```json
{
  "python.terminal.activateEnvironment": false,
  "python.envFile": "${workspaceFolder}/.env"
}
```

Then create a script `run_with_doppler.sh`:
```bash
#!/bin/bash
doppler run --config dev -- "$@"
```

---

## Step 8: CI/CD Integration

### GitHub Actions

Add Doppler token to GitHub Secrets:
1. Generate service token: `doppler configs tokens create ci-token --config dev`
2. Add to GitHub: Settings → Secrets → `DOPPLER_TOKEN`

Update `.github/workflows/ci.yml`:
```yaml
- name: Inject secrets with Doppler
  uses: dopplerhq/cli-action@v3
  with:
    doppler-token: ${{ secrets.DOPPLER_TOKEN }}

- name: Run tests
  run: doppler run -- pytest
```

---

## Step 9: Security Best Practices

### 1. Add to .gitignore
```bash
echo "doppler.yaml" >> .gitignore
echo ".env.doppler" >> .gitignore
```

### 2. Use Branch-specific Configs
```bash
# Create config per branch
doppler configs create dev/feature-x --from dev
doppler setup --config dev/feature-x
```

### 3. Enable Audit Logging
- Dashboard → Settings → Audit Log
- Review who accessed/changed secrets

### 4. Rotate Secrets Regularly
```bash
# Rotate JWT secret
doppler secrets set JWT_SECRET_KEY="$(openssl rand -hex 32)"

# Auto-redeploy on Render if integration enabled
```

---

## Step 10: Migrate Existing .env

Se hai già un `.env` file:

```bash
# Import all secrets from .env
doppler secrets upload .env

# Verify
doppler secrets
```

---

## Common Commands Cheat Sheet

```bash
# View all secrets (redacted)
doppler secrets

# View specific secret (unredacted)
doppler secrets get DATABASE_URL --plain

# Download secrets to file
doppler secrets download --no-file --format env > .env.local

# Compare configs
doppler secrets diff dev prd

# Rollback to previous version
doppler configs rollback prd

# View audit log
doppler activity
```

---

## Troubleshooting

### "Command not found: doppler"
```bash
# Reinstall Doppler
brew reinstall dopplerhq/cli/doppler
```

### "Not logged in"
```bash
doppler login
```

### "Config not found"
```bash
# List available configs
doppler configs

# Setup correct config
doppler setup --config prd
```

---

## Migration Path

### Current State
- Manual env vars in Render Dashboard
- Secrets scattered across different places

### With Doppler
1. **Week 1**: Setup Doppler, import existing secrets
2. **Week 2**: Test with dev environment
3. **Week 3**: Enable Render integration for auto-sync
4. **Week 4**: Remove manual env vars from Render

---

## Cost

- **Free Tier**:
  - 5 users
  - Unlimited projects
  - Unlimited secrets
  - 14-day audit log

Perfect for your personal bot! 🎯

---

## Next Steps

1. ✅ Install Doppler CLI
2. ✅ Login and create project
3. ✅ Add production secrets
4. ✅ Setup Render integration
5. ✅ Test locally with `doppler run`
6. ✅ Deploy to production

---

## Support

- Docs: https://docs.doppler.com
- Support: support@doppler.com
- Status: https://status.doppler.com
