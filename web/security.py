"""Sifreleme (Fernet) + imzali oturum cerezi.

MASTER_KEY .env'deki WEB_MASTER_KEY'den gelir; yoksa uretilip .env'e eklenir.
"""
import base64
import hashlib
import hmac
import json
import os
import time

from cryptography.fernet import Fernet

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")


def _load_or_create_master() -> bytes:
    from dotenv import dotenv_values
    key = (dotenv_values(ENV_PATH).get("WEB_MASTER_KEY") or "").strip()
    if not key:
        key = Fernet.generate_key().decode()
        with open(ENV_PATH, "a", encoding="utf-8") as f:
            f.write(f"WEB_MASTER_KEY={key}\n")
    return key.encode()


_MASTER = _load_or_create_master()
_fernet = Fernet(_MASTER)
_session_secret = hashlib.sha256(b"session:" + _MASTER).digest()

SESSION_TTL = 7 * 86400


def encrypt(data: str) -> bytes:
    return _fernet.encrypt(data.encode())


def decrypt(blob: bytes) -> str:
    return _fernet.decrypt(blob).decode()


def make_session(user_id: int) -> str:
    payload = json.dumps({"u": user_id, "e": int(time.time()) + SESSION_TTL},
                         separators=(",", ":")).encode()
    sig = hmac.new(_session_secret, payload, hashlib.sha256).digest()
    return (base64.urlsafe_b64encode(payload).decode().rstrip("=") + "." +
            base64.urlsafe_b64encode(sig).decode().rstrip("="))


def read_session(token: str) -> int | None:
    try:
        p64, s64 = token.split(".")
        pad = lambda s: s + "=" * (-len(s) % 4)
        payload = base64.urlsafe_b64decode(pad(p64))
        sig = base64.urlsafe_b64decode(pad(s64))
        if not hmac.compare_digest(
                hmac.new(_session_secret, payload, hashlib.sha256).digest(), sig):
            return None
        data = json.loads(payload)
        if data.get("e", 0) < time.time():
            return None
        return int(data["u"])
    except Exception:
        return None
