# Axiom Integration Setup Guide

## Overview
HappyKube integrates with Axiom for centralized logging across all services (API, Bot, Database queries).

## Prerequisites
- Axiom account (https://axiom.co)
- Doppler account for secrets management
- Render account for deployment

## Step 1: Create Axiom Dataset

1. Log into Axiom dashboard
2. Create a new dataset called `happykube`
3. Optionally create another dataset `happykube-ci` for CI/CD logs

## Step 2: Get Axiom Credentials

1. Go to Settings → API Tokens
2. Create a new API token with `ingest` permission
3. Note your Organization ID (in Settings → Profile)
4. Save these credentials:
   - `AXIOM_API_TOKEN`
   - `AXIOM_ORG_ID` (optional)
   - `AXIOM_DATASET` (default: "happykube")

## Step 3: Configure in Doppler

```bash
# Add Axiom credentials to Doppler
doppler secrets set AXIOM_API_TOKEN="xaat-xxx-xxx"
doppler secrets set AXIOM_DATASET="happykube"
doppler secrets set AXIOM_ORG_ID="your-org-id"  # optional
doppler secrets set AXIOM_URL="https://api.axiom.co"  # default, works globally

# Optional: Use edge deployment for better ingest performance
# EU: doppler secrets set AXIOM_URL="https://eu-central-1.aws.edge.axiom.co"
# US: doppler secrets set AXIOM_URL="https://us-east-1.aws.edge.axiom.co"
```

## Step 4: Configure in Render

### Option A: Using Doppler (Recommended)

1. Go to your Render service dashboard
2. Add Doppler integration if not already configured
3. Axiom credentials will sync automatically from Doppler

### Option B: Manual Configuration

1. Go to your Render service → Environment
2. Add environment variables:
   ```
   AXIOM_API_TOKEN=xaat-xxx-xxx
   AXIOM_DATASET=happykube
   AXIOM_ORG_ID=your-org-id
   AXIOM_URL=https://api.axiom.co
   ```
3. Redeploy the service

## Step 5: Configure Log Forwarding from Render (Optional)

For complete coverage, configure Render to forward all logs to Axiom:

1. Go to Render service → Logging
2. Enable "Log Streams" if available
3. Add Axiom as a destination:
   - Endpoint: `https://api.axiom.co/v1/datasets/{dataset}/ingest`
   - Headers: `Authorization: Bearer {AXIOM_API_TOKEN}`
   - Format: JSON

## Step 6: Verify Integration

### Local Testing

```bash
# Set environment variables
export AXIOM_API_TOKEN="xaat-xxx-xxx"
export AXIOM_DATASET="happykube"
export APP_ENV="production"

# Run the API
python -m uvicorn presentation.api.app:app --host 0.0.0.0 --port 5000

# Or run the bot
python -m presentation.bot.telegram_bot
```

Check Axiom dashboard for logs with `service=api` or `service=bot`.

### Production Testing

After deploying to Render:
1. Trigger some API requests
2. Send messages to the Telegram bot
3. Check Axiom dashboard for logs
4. Look for:
   - `service=api` - API request logs
   - `service=bot` - Bot interaction logs
   - `level=warning` - Slow database queries
   - `level=error` - Application errors

## Step 7: GitHub Actions (CI/CD Logs)

To send CI/CD logs to Axiom:

1. Add `AXIOM_TOKEN` to GitHub repository secrets
2. Logs from test and lint jobs will be sent to `happykube-ci` dataset
3. Note: This is optional and can be enabled when Axiom GitHub Action is stable

## Log Fields

All logs sent to Axiom include:

- `_time`: Timestamp (ISO 8601)
- `level`: Log level (debug, info, warning, error)
- `message`: Log message
- `service`: Service identifier (api, bot)
- Additional structured fields depending on context

### API Logs
- `method`: HTTP method
- `path`: Request path
- `status_code`: Response status
- `duration_ms`: Request duration

### Bot Logs
- `user_id`: Telegram user ID (hashed)
- `chat_id`: Chat ID (hashed)
- `command`: Command name
- `error_type`: Error type if applicable

### Database Logs
- `query_preview`: First 100-200 chars of query
- `duration_ms`: Query execution time
- `has_params`: Whether query had parameters

## Security Best Practices

✅ **DO:**
- Store Axiom token in Doppler/Render secrets
- Use production environment only
- Sanitize sensitive data before logging
- Review logs regularly for PII

❌ **DON'T:**
- Commit Axiom token to git
- Log passwords, API keys, or tokens
- Log full database queries with parameters
- Enable in development (logs to console)

## Troubleshooting

### Logs not appearing in Axiom

1. Check environment variables are set correctly
2. Verify `APP_ENV=production` (Axiom disabled in development)
3. Check Render logs for "Axiom initialized" message
4. Verify API token has `ingest` permission
5. Check dataset name matches

### Axiom errors in logs

```
Failed to send logs to Axiom: ...
```

This is non-fatal. The app continues working, logs go to stdout.
Check:
- API token validity
- Network connectivity
- Axiom service status

### High Axiom costs

- Reduce log level to `INFO` or `WARNING`
- Increase batch size in `axiom.py` (default: 50)
- Disable debug logs
- Filter out noisy libraries

## Monitoring Queries

Useful Axiom queries:

```apl
# API error rate
['service'] == "api" and ['level'] == "error"
| summarize count() by bin(_time, 5m)

# Slow database queries
['duration_ms'] > 1000
| project _time, query_preview, duration_ms
| order by duration_ms desc

# Bot interactions by user
['service'] == "bot"
| summarize count() by user_id, bin(_time, 1h)

# API response times by endpoint
['service'] == "api"
| summarize avg(duration_ms), max(duration_ms) by path
| order by avg_duration_ms desc
```

## Cost Optimization

Axiom pricing is based on:
- Ingestion volume (GB/month)
- Query compute (seconds)
- Retention period

To optimize:
1. Use appropriate log levels (INFO in prod, not DEBUG)
2. Batch logs (already configured: 50 logs/batch)
3. Set retention to 30 days for production
4. Use sampling for high-volume endpoints if needed

## Support

- Axiom Docs: https://axiom.co/docs
- HappyKube Issues: https://github.com/MK023/HappyKube/issues
