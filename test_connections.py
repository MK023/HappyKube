#!/usr/bin/env python3
"""Test script for Redis and PostgreSQL connections."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_redis():
    """Test Redis connection."""
    print("🔄 Testing Redis connection...")
    try:
        import redis

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        print(f"   Connecting to: {redis_url}")

        client = redis.from_url(redis_url, decode_responses=True)

        # Test ping
        response = client.ping()
        if response:
            print("✅ Redis connection successful!")

            # Test set/get
            client.set("test_key", "test_value", ex=10)
            value = client.get("test_key")

            if value == "test_value":
                print("✅ Redis read/write test successful!")
                client.delete("test_key")
                return True
            else:
                print("❌ Redis read/write test failed")
                return False
        else:
            print("❌ Redis ping failed")
            return False

    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False


def test_postgresql():
    """Test PostgreSQL connection."""
    print("\n🔄 Testing PostgreSQL connection...")
    try:
        from sqlalchemy import create_engine, text

        db_url = os.getenv(
            "DATABASE_URL",
            "postgresql://happykube:happykube@localhost:5432/happykube"
        )
        print(f"   Connecting to: {db_url.replace(db_url.split('@')[0].split('://')[1], '***:***')}")

        engine = create_engine(db_url)

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL connection successful!")
            print(f"   Version: {version[:50]}...")

            # Test simple query
            result = conn.execute(text("SELECT 1 as test;"))
            test_value = result.fetchone()[0]

            if test_value == 1:
                print("✅ PostgreSQL query test successful!")
                return True
            else:
                print("❌ PostgreSQL query test failed")
                return False

    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False


def main():
    """Run all connection tests."""
    print("=" * 60)
    print("HappyKube v2 - Connection Tests")
    print("=" * 60)

    redis_ok = test_redis()
    postgres_ok = test_postgresql()

    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"  Redis:      {'✅ PASS' if redis_ok else '❌ FAIL'}")
    print(f"  PostgreSQL: {'✅ PASS' if postgres_ok else '❌ FAIL'}")
    print("=" * 60)

    if redis_ok and postgres_ok:
        print("\n🎉 All connection tests passed!")
        return 0
    else:
        print("\n⚠️  Some connection tests failed.")
        print("\n💡 Make sure services are running:")
        print("   - Redis:      docker run -d -p 6379:6379 redis:7-alpine")
        print("   - PostgreSQL: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=happykube \\")
        print("                 -e POSTGRES_USER=happykube -e POSTGRES_DB=happykube postgres:16-alpine")
        return 1


if __name__ == "__main__":
    sys.exit(main())
