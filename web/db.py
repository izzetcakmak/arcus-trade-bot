"""SQLite veritabani — kullanicilar, cuzdanlar, bot ayarlari."""
import os
import sqlite3
import time

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arcusweb.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    google_sub TEXT,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS wallets (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    address TEXT UNIQUE NOT NULL,
    enc_wallet_key BLOB NOT NULL,     -- Fernet ile sifreli ETH private key
    enc_api_key BLOB NOT NULL,        -- Fernet ile sifreli Ed25519 private key
    api_pub TEXT NOT NULL,            -- Arcus apiKey (public)
    account_index INTEGER NOT NULL DEFAULT 0,
    revealed INTEGER NOT NULL DEFAULT 0,   -- key'ler kullaniciya gosterildi mi
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    bot_active INTEGER NOT NULL DEFAULT 0,
    symbols TEXT NOT NULL DEFAULT 'BTC-USD,ETH-USD,SOL-USD',
    leverage INTEGER NOT NULL DEFAULT 3,
    margin_usd REAL NOT NULL DEFAULT 100,
    sl_pct REAL NOT NULL DEFAULT 30,
    tp_pct REAL NOT NULL DEFAULT 60,
    max_daily_loss_pct REAL NOT NULL DEFAULT 5,
    adx_threshold REAL NOT NULL DEFAULT 20,
    telegram_chat_id TEXT,
    telegram_link_token TEXT
);
"""


def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


def init():
    with conn() as c:
        c.executescript(SCHEMA)


def get_or_create_user(email: str, name: str = "", google_sub: str = "") -> dict:
    with conn() as c:
        row = c.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if row is None:
            cur = c.execute(
                "INSERT INTO users (email, name, google_sub, created_at) VALUES (?,?,?,?)",
                (email, name, google_sub, time.time()))
            c.execute("INSERT INTO settings (user_id) VALUES (?)", (cur.lastrowid,))
            row = c.execute("SELECT * FROM users WHERE id=?", (cur.lastrowid,)).fetchone()
        elif google_sub and not row["google_sub"]:
            c.execute("UPDATE users SET google_sub=?, name=COALESCE(NULLIF(name,''),?) "
                      "WHERE id=?", (google_sub, name, row["id"]))
    return dict(row)


def get_user(user_id: int) -> dict | None:
    with conn() as c:
        row = c.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return dict(row) if row else None


def get_wallet(user_id: int) -> dict | None:
    with conn() as c:
        row = c.execute("SELECT * FROM wallets WHERE user_id=?", (user_id,)).fetchone()
    return dict(row) if row else None


def save_wallet(user_id, address, enc_wallet_key, enc_api_key, api_pub, account_index):
    with conn() as c:
        c.execute("INSERT INTO wallets (user_id, address, enc_wallet_key, enc_api_key,"
                  " api_pub, account_index, created_at) VALUES (?,?,?,?,?,?,?)",
                  (user_id, address, enc_wallet_key, enc_api_key, api_pub,
                   account_index, time.time()))


def mark_revealed(user_id):
    with conn() as c:
        c.execute("UPDATE wallets SET revealed=1 WHERE user_id=?", (user_id,))


def get_settings(user_id: int) -> dict | None:
    with conn() as c:
        row = c.execute("SELECT * FROM settings WHERE user_id=?", (user_id,)).fetchone()
    return dict(row) if row else None


def update_settings(user_id: int, **kw):
    if not kw:
        return
    cols = ", ".join(f"{k}=?" for k in kw)
    with conn() as c:
        c.execute(f"UPDATE settings SET {cols} WHERE user_id=?",
                  (*kw.values(), user_id))


def active_users_with_wallets() -> list[dict]:
    """Bot motoru icin: botu acik olan tum kullanicilar + cuzdan + ayarlar."""
    with conn() as c:
        rows = c.execute(
            "SELECT u.id, u.email, w.address, w.enc_api_key, w.account_index, s.* "
            "FROM users u JOIN wallets w ON w.user_id=u.id "
            "JOIN settings s ON s.user_id=u.id WHERE s.bot_active=1").fetchall()
    return [dict(r) for r in rows]


def get_user_by_link_token(token: str) -> dict | None:
    if not token:
        return None
    with conn() as c:
        row = c.execute(
            "SELECT u.* FROM users u JOIN settings s ON s.user_id=u.id "
            "WHERE s.telegram_link_token=?", (token,)).fetchone()
    return dict(row) if row else None
