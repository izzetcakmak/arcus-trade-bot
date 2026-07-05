"""Veritabani katmani — DATABASE_URL varsa Postgres (Neon/Vercel), yoksa SQLite.

Ayni fonksiyon imzalari her iki backend'de calisir. Sorgular '?' yer tutucusuyla
yazilir; Postgres'te '%s'e cevrilir.
"""
import json
import os
import sqlite3
import time

from dotenv import dotenv_values

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arcusweb.db")

DATABASE_URL = (os.environ.get("DATABASE_URL")
                or dotenv_values(os.path.join(BASE_DIR, ".env")).get("DATABASE_URL")
                or "").strip()
IS_PG = bool(DATABASE_URL)

SCHEMA_SQLITE = """
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
    enc_wallet_key BLOB NOT NULL,
    enc_api_key BLOB NOT NULL,
    api_pub TEXT NOT NULL,
    account_index INTEGER NOT NULL DEFAULT 0,
    revealed INTEGER NOT NULL DEFAULT 0,
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
CREATE TABLE IF NOT EXISTS fund_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    amount_usd INTEGER NOT NULL,
    stage TEXT NOT NULL DEFAULT 'queued',
    error TEXT,
    done INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS bot_state (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    running INTEGER NOT NULL DEFAULT 0,
    snapshot TEXT,
    events TEXT,
    updated_at REAL NOT NULL
);
"""

SCHEMA_PG = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    google_sub TEXT,
    created_at DOUBLE PRECISION NOT NULL
);
CREATE TABLE IF NOT EXISTS wallets (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    address TEXT UNIQUE NOT NULL,
    enc_wallet_key BYTEA NOT NULL,
    enc_api_key BYTEA NOT NULL,
    api_pub TEXT NOT NULL,
    account_index INTEGER NOT NULL DEFAULT 0,
    revealed INTEGER NOT NULL DEFAULT 0,
    created_at DOUBLE PRECISION NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    bot_active INTEGER NOT NULL DEFAULT 0,
    symbols TEXT NOT NULL DEFAULT 'BTC-USD,ETH-USD,SOL-USD',
    leverage INTEGER NOT NULL DEFAULT 3,
    margin_usd DOUBLE PRECISION NOT NULL DEFAULT 100,
    sl_pct DOUBLE PRECISION NOT NULL DEFAULT 30,
    tp_pct DOUBLE PRECISION NOT NULL DEFAULT 60,
    max_daily_loss_pct DOUBLE PRECISION NOT NULL DEFAULT 5,
    adx_threshold DOUBLE PRECISION NOT NULL DEFAULT 20,
    telegram_chat_id TEXT,
    telegram_link_token TEXT
);
CREATE TABLE IF NOT EXISTS fund_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    amount_usd INTEGER NOT NULL,
    stage TEXT NOT NULL DEFAULT 'queued',
    error TEXT,
    done INTEGER NOT NULL DEFAULT 0,
    created_at DOUBLE PRECISION NOT NULL
);
CREATE TABLE IF NOT EXISTS bot_state (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    running INTEGER NOT NULL DEFAULT 0,
    snapshot TEXT,
    events TEXT,
    updated_at DOUBLE PRECISION NOT NULL
);
"""


def _q(sql: str) -> str:
    return sql.replace("?", "%s") if IS_PG else sql


class _Conn:
    """Iki backend icin ortak ince sarmalayici (context manager)."""

    def __init__(self):
        if IS_PG:
            import psycopg
            from psycopg.rows import dict_row
            self.c = psycopg.connect(DATABASE_URL, row_factory=dict_row,
                                     connect_timeout=10)
        else:
            self.c = sqlite3.connect(DB_PATH)
            self.c.row_factory = sqlite3.Row

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        if exc[0] is None:
            self.c.commit()
        self.c.close()

    def exec(self, sql, params=()):
        if IS_PG:
            return self.c.execute(_q(sql), params)
        return self.c.execute(sql, params)

    def one(self, sql, params=()):
        row = self.exec(sql, params).fetchone()
        return dict(row) if row else None

    def all(self, sql, params=()):
        return [dict(r) for r in self.exec(sql, params).fetchall()]


def init():
    with _Conn() as c:
        schema = SCHEMA_PG if IS_PG else SCHEMA_SQLITE
        if IS_PG:
            c.exec(schema)
        else:
            c.c.executescript(schema)


def get_or_create_user(email: str, name: str = "", google_sub: str = "") -> dict:
    with _Conn() as c:
        row = c.one("SELECT * FROM users WHERE email=?", (email,))
        if row is None:
            if IS_PG:
                row = c.one("INSERT INTO users (email, name, google_sub, created_at) "
                            "VALUES (?,?,?,?) RETURNING *",
                            (email, name, google_sub, time.time()))
            else:
                cur = c.exec("INSERT INTO users (email, name, google_sub, created_at)"
                             " VALUES (?,?,?,?)", (email, name, google_sub, time.time()))
                row = c.one("SELECT * FROM users WHERE id=?", (cur.lastrowid,))
            c.exec("INSERT INTO settings (user_id) VALUES (?)", (row["id"],))
        elif google_sub and not row["google_sub"]:
            c.exec("UPDATE users SET google_sub=? WHERE id=?", (google_sub, row["id"]))
    return row


def get_user(user_id: int) -> dict | None:
    with _Conn() as c:
        return c.one("SELECT * FROM users WHERE id=?", (user_id,))


def get_wallet(user_id: int) -> dict | None:
    with _Conn() as c:
        row = c.one("SELECT * FROM wallets WHERE user_id=?", (user_id,))
    if row:  # BYTEA/BLOB tipini normalize et
        for k in ("enc_wallet_key", "enc_api_key"):
            if row[k] is not None:
                row[k] = bytes(row[k])
    return row


def save_wallet(user_id, address, enc_wallet_key, enc_api_key, api_pub, account_index):
    with _Conn() as c:
        c.exec("INSERT INTO wallets (user_id, address, enc_wallet_key, enc_api_key,"
               " api_pub, account_index, created_at) VALUES (?,?,?,?,?,?,?)",
               (user_id, address, enc_wallet_key, enc_api_key, api_pub,
                account_index, time.time()))


def mark_revealed(user_id):
    with _Conn() as c:
        c.exec("UPDATE wallets SET revealed=1 WHERE user_id=?", (user_id,))


def get_settings(user_id: int) -> dict | None:
    with _Conn() as c:
        return c.one("SELECT * FROM settings WHERE user_id=?", (user_id,))


_SETTINGS_COLS = {"bot_active", "symbols", "leverage", "margin_usd", "sl_pct",
                  "tp_pct", "max_daily_loss_pct", "adx_threshold",
                  "telegram_chat_id", "telegram_link_token"}


def update_settings(user_id: int, **kw):
    kw = {k: v for k, v in kw.items() if k in _SETTINGS_COLS}
    if not kw:
        return
    cols = ", ".join(f"{k}=?" for k in kw)
    with _Conn() as c:
        c.exec(f"UPDATE settings SET {cols} WHERE user_id=?", (*kw.values(), user_id))


def active_users_with_wallets() -> list[dict]:
    with _Conn() as c:
        rows = c.all(
            "SELECT u.id, u.email, w.address, w.enc_api_key, w.enc_wallet_key,"
            " w.account_index, s.* FROM users u JOIN wallets w ON w.user_id=u.id "
            "JOIN settings s ON s.user_id=u.id WHERE s.bot_active=1")
    for r in rows:
        for k in ("enc_api_key", "enc_wallet_key"):
            if r.get(k) is not None:
                r[k] = bytes(r[k])
    return rows


def get_user_by_link_token(token: str) -> dict | None:
    if not token:
        return None
    with _Conn() as c:
        return c.one("SELECT u.* FROM users u JOIN settings s ON s.user_id=u.id "
                     "WHERE s.telegram_link_token=?", (token,))


# ------------------------------------------------------- fonlama kuyrugu

def create_fund_request(user_id: int, amount_usd: int) -> bool:
    """Acik istek varsa yenisini acmaz."""
    with _Conn() as c:
        open_req = c.one("SELECT id FROM fund_requests WHERE user_id=? AND done=0 "
                         "AND error IS NULL AND created_at > ?",
                         (user_id, time.time() - 600))
        if open_req:
            return False
        c.exec("INSERT INTO fund_requests (user_id, amount_usd, created_at) "
               "VALUES (?,?,?)", (user_id, amount_usd, time.time()))
    return True


def latest_fund_request(user_id: int) -> dict | None:
    with _Conn() as c:
        return c.one("SELECT * FROM fund_requests WHERE user_id=? "
                     "ORDER BY id DESC LIMIT 1", (user_id,))


def claim_fund_request() -> dict | None:
    """Worker: kuyruktan bir istegi atomik olarak alir."""
    with _Conn() as c:
        row = c.one("SELECT * FROM fund_requests WHERE stage='queued' "
                    "ORDER BY id LIMIT 1")
        if not row:
            return None
        c.exec("UPDATE fund_requests SET stage='gas' WHERE id=? AND stage='queued'",
               (row["id"],))
    return row


def update_fund_request(req_id: int, **kw):
    cols = ", ".join(f"{k}=?" for k in kw)
    with _Conn() as c:
        c.exec(f"UPDATE fund_requests SET {cols} WHERE id=?", (*kw.values(), req_id))


# --------------------------------------------------------- bot durumu

def upsert_bot_state(user_id: int, running: bool, snapshot: dict, events: list):
    with _Conn() as c:
        if IS_PG:
            c.exec("INSERT INTO bot_state (user_id, running, snapshot, events,"
                   " updated_at) VALUES (?,?,?,?,?) ON CONFLICT (user_id) DO UPDATE"
                   " SET running=EXCLUDED.running, snapshot=EXCLUDED.snapshot,"
                   " events=EXCLUDED.events, updated_at=EXCLUDED.updated_at",
                   (user_id, int(running), json.dumps(snapshot),
                    json.dumps(events), time.time()))
        else:
            c.exec("INSERT OR REPLACE INTO bot_state (user_id, running, snapshot,"
                   " events, updated_at) VALUES (?,?,?,?,?)",
                   (user_id, int(running), json.dumps(snapshot),
                    json.dumps(events), time.time()))


def get_bot_state(user_id: int) -> dict:
    with _Conn() as c:
        row = c.one("SELECT * FROM bot_state WHERE user_id=?", (user_id,))
    if not row or time.time() - row["updated_at"] > 120:
        return {"running": False, "snapshot": {}, "events":
                json.loads(row["events"]) if row and row["events"] else []}
    return {"running": bool(row["running"]),
            "snapshot": json.loads(row["snapshot"] or "{}"),
            "events": json.loads(row["events"] or "[]")}
