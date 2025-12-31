#!/usr/bin/env python3
"""
CLI tool for managing API keys in the database.

Usage:
    python src/scripts/manage_api_keys.py create <name> [--rate-limit 100] [--expires 2026-12-31]
    python src/scripts/manage_api_keys.py list
    python src/scripts/manage_api_keys.py deactivate <key_id>

Examples:
    # Create new API key
    python src/scripts/manage_api_keys.py create "Production Bot" --rate-limit 200

    # List all active keys
    python src/scripts/manage_api_keys.py list

    # Deactivate a key
    python src/scripts/manage_api_keys.py deactivate abc-123-def
"""

import secrets
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from infrastructure.database import get_engine
from infrastructure.repositories import APIKeyRepository


def generate_secure_api_key() -> str:
    """
    Generate a cryptographically secure API key.

    Format: HK_<environment>_<40 random chars>
    Example: HK_P_abc123def456...

    Returns:
        Secure API key string
    """
    prefix = "HK_P_"  # HappyKube Production
    random_part = secrets.token_urlsafe(30)  # ~40 chars base64
    return f"{prefix}{random_part}"


@click.group()
def cli():
    """API Key management CLI tool."""
    pass


@cli.command()
@click.argument("name")
@click.option("--rate-limit", default=100, type=int, help="Requests per minute limit")
@click.option("--expires", type=str, help="Expiration date (YYYY-MM-DD)")
def create(name: str, rate_limit: int, expires: str | None):
    """Create a new API key."""
    # Parse expiration date
    expires_at = None
    if expires:
        try:
            expires_at = datetime.strptime(expires, "%Y-%m-%d")
        except ValueError:
            click.echo(f"❌ Invalid date format: {expires}. Use YYYY-MM-DD", err=True)
            sys.exit(1)

    # Generate secure key
    api_key = generate_secure_api_key()

    # Store in database
    engine = get_engine()
    repo = APIKeyRepository(engine)

    try:
        model = repo.create_key(
            api_key=api_key,
            name=name,
            rate_limit_per_minute=rate_limit,
            expires_at=expires_at
        )

        click.echo("✅ API key created successfully!\n")
        click.echo(f"ID:         {model.id}")
        click.echo(f"Name:       {model.name}")
        click.echo(f"Rate Limit: {model.rate_limit_per_minute} req/min")
        click.echo(f"Expires:    {model.expires_at or 'Never'}")
        click.echo(f"\n🔑 API Key (COPY THIS NOW - won't be shown again):")
        click.echo(f"    {api_key}\n")

        click.echo("💡 Add this to your .env or Render environment:")
        click.echo(f'    API_KEYS="{api_key}"\n')

    except Exception as e:
        click.echo(f"❌ Error creating API key: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--include-inactive", is_flag=True, help="Show inactive keys")
def list(include_inactive: bool):
    """List all API keys."""
    engine = get_engine()
    repo = APIKeyRepository(engine)

    try:
        keys = repo.list_keys(include_inactive=include_inactive)

        if not keys:
            click.echo("No API keys found.")
            return

        click.echo(f"\n📋 API Keys ({len(keys)} total):\n")

        for key in keys:
            status = "✅ Active" if key.is_active else "❌ Inactive"
            expires = key.expires_at.strftime("%Y-%m-%d") if key.expires_at else "Never"
            last_used = key.last_used_at.strftime("%Y-%m-%d %H:%M") if key.last_used_at else "Never"

            click.echo(f"ID:         {key.id}")
            click.echo(f"Name:       {key.name}")
            click.echo(f"Status:     {status}")
            click.echo(f"Rate Limit: {key.rate_limit_per_minute} req/min")
            click.echo(f"Created:    {key.created_at.strftime('%Y-%m-%d')}")
            click.echo(f"Expires:    {expires}")
            click.echo(f"Last Used:  {last_used}")
            click.echo("-" * 50)

    except Exception as e:
        click.echo(f"❌ Error listing API keys: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("key_id")
def deactivate(key_id: str):
    """Deactivate an API key."""
    from uuid import UUID

    engine = get_engine()
    repo = APIKeyRepository(engine)

    try:
        # Convert string to UUID
        key_uuid = UUID(key_id)

        success = repo.deactivate_key(key_uuid)

        if success:
            click.echo(f"✅ API key {key_id} deactivated successfully!")
        else:
            click.echo(f"❌ API key {key_id} not found.", err=True)
            sys.exit(1)

    except ValueError:
        click.echo(f"❌ Invalid UUID format: {key_id}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error deactivating API key: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
