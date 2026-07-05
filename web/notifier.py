"""Urun Telegram botu (@...): kisisel bildirimler + /start deep-link eslestirme."""
import json
import os
import secrets
import threading
import urllib.parse
import urllib.request

from dotenv import dotenv_values

from web import db

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = (dotenv_values(os.path.join(BASE_DIR, ".env"))
         .get("WEB_TELEGRAM_BOT_TOKEN") or "").strip()
API = f"https://api.telegram.org/bot{TOKEN}"

_username = None
_poller_started = False


def _call(method, **params):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(f"{API}/{method}", data=data)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def bot_username() -> str | None:
    global _username
    if not TOKEN:
        return None
    if _username is None:
        try:
            _username = _call("getMe")["result"]["username"]
        except Exception:
            return None
    return _username


def send(chat_id: str, text: str) -> bool:
    if not (TOKEN and chat_id):
        return False
    try:
        _call("sendMessage", chat_id=chat_id, text=text)
        return True
    except Exception:
        return False


def make_link(user_id: int) -> str | None:
    """Kullaniciya ozel deep-link uretir: t.me/<bot>?start=<token>"""
    uname = bot_username()
    if not uname:
        return None
    token = secrets.token_urlsafe(16)
    db.update_settings(user_id, telegram_link_token=token)
    return f"https://t.me/{uname}?start={token}"


def _poll_loop():
    offset = 0
    while True:
        try:
            out = _call("getUpdates", offset=offset, timeout=50)
            for upd in out.get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message") or {}
                text = (msg.get("text") or "").strip()
                chat_id = str((msg.get("chat") or {}).get("id", ""))
                if not (text.startswith("/start") and chat_id):
                    continue
                parts = text.split(maxsplit=1)
                if len(parts) < 2:
                    send(chat_id, "Link your account from the ArcusBot website "
                                  "(Telegram card -> Link).")
                    continue
                user = db.get_user_by_link_token(parts[1].strip())
                if user:
                    db.update_settings(user["id"], telegram_chat_id=chat_id,
                                       telegram_link_token=None)
                    send(chat_id, f"Linked to {user['email']} — position alerts "
                                  f"will arrive here. / Hesabina baglandi, "
                                  f"bildirimler buraya gelecek.")
                else:
                    send(chat_id, "Link expired or invalid — generate a new one "
                                  "from the website.")
        except Exception:
            import time
            time.sleep(5)


def start_poller():
    global _poller_started
    if TOKEN and not _poller_started:
        _poller_started = True
        threading.Thread(target=_poll_loop, daemon=True,
                         name="tg-poller").start()
