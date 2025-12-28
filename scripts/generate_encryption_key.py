#!/usr/bin/env python3
"""Generate encryption key for HappyKube."""

from cryptography.fernet import Fernet

if __name__ == "__main__":
    key = Fernet.generate_key()
    print("Generated encryption key (store in secrets):")
    print(key.decode())
    print("\nAdd to your secrets.yaml:")
    print(f"encryption-key: \"{key.decode()}\"")
