"""Cok kullanicili bot motoru.

Tek arka plan dongusu: botu acik her kullanici icin bir TradingEngine calistirir.
- Ayar degisikligi -> engine.apply_config (sicak)
- Bot kapatilirsa: yeni giris durur (entries_enabled=False) ama acik pozisyon
  yonetimi (bot-tarafi SL/TP, cikislar) pozisyon kapanana kadar surer.
- Bildirimler: kullanicinin bagli Telegram'ina + bellek ici olay listesine.
"""
import collections
import os
import sys
import threading
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from dotenv import dotenv_values

from config import Config
from engine import TradingEngine
from web import db, security
from web import notifier

ARCUS_BASE = (dotenv_values(os.path.join(BASE_DIR, ".env"))
              .get("ARCUS_BASE", "https://api.testnet.arcus.xyz"))
TICK_SEC = 30

_runners: dict[int, dict] = {}    # user_id -> {engine, events, sig, chat_id}
_lock = threading.Lock()
_started = False


def _sig(row) -> tuple:
    return (row["symbols"], row["leverage"], row["margin_usd"], row["sl_pct"],
            row["tp_pct"], row["max_daily_loss_pct"], row["adx_threshold"])


def _make_cfg(row) -> Config:
    return Config(
        base=ARCUS_BASE, address=row["address"],
        api_privkey=security.decrypt(row["enc_api_key"]),
        account_index=row["account_index"],
        symbols=[s.strip().upper() for s in row["symbols"].split(",") if s.strip()],
        timeframe="15m", leverage=int(row["leverage"]),
        margin_usd=float(row["margin_usd"]), sl_pct=float(row["sl_pct"]),
        tp_pct=float(row["tp_pct"]),
        max_daily_loss_pct=float(row["max_daily_loss_pct"]),
        adx_threshold=float(row["adx_threshold"]), loop_interval_sec=TICK_SEC,
        telegram_token="", telegram_chat_id="", dashboard_url="")


def _make_runner(row) -> dict:
    events = collections.deque(maxlen=60)
    user_id = row["id"]

    def notify(msg: str):
        stamp = time.strftime("%m-%d %H:%M")
        events.appendleft(f"[{stamp}] {msg}")
        s = db.get_settings(user_id) or {}
        chat = s.get("telegram_chat_id")
        if chat:
            notifier.send(chat, msg)

    eng = TradingEngine(_make_cfg(row), notify)
    return {"engine": eng, "events": events, "sig": _sig(row), "setup_done": False}


def _loop():
    while True:
        try:
            rows = {r["id"]: r for r in db.active_users_with_wallets()}
            with _lock:
                # aktif kullanicilar: kur / guncelle / tikla
                for uid, row in rows.items():
                    r = _runners.get(uid)
                    if r is None:
                        r = _runners[uid] = _make_runner(row)
                    eng = r["engine"]
                    eng.entries_enabled = True
                    if not r["setup_done"]:
                        try:
                            eng.setup()
                            r["setup_done"] = True
                        except SystemExit as e:   # fonlanmamis hesap vb.
                            r["events"].appendleft(f"[!] {e}")
                            db.update_settings(uid, bot_active=0)
                            del _runners[uid]
                            continue
                        except Exception as e:
                            r["events"].appendleft(f"[!] setup: {e}")
                            continue
                    if r["sig"] != _sig(row):
                        try:
                            eng.apply_config(_make_cfg(row))
                            r["sig"] = _sig(row)
                        except Exception as e:
                            r["events"].appendleft(f"[!] ayar: {e}")
                    try:
                        eng.tick()
                    except Exception as e:
                        r["events"].appendleft(f"[!] tick: {e}")
                    _persist(uid, r)

                # bot'u kapatilanlar: pozisyon varsa yonetmeye devam, yoksa kaldir
                for uid in list(_runners):
                    if uid in rows:
                        continue
                    r = _runners[uid]
                    eng = r["engine"]
                    if r["setup_done"] and eng.positions:
                        eng.entries_enabled = False
                        try:
                            eng.tick()   # SL/TP izleme + cikis yonetimi surer
                        except Exception as e:
                            r["events"].appendleft(f"[!] tick: {e}")
                        _persist(uid, r)
                    else:
                        _persist(uid, r, running=False)
                        del _runners[uid]
        except Exception:
            pass
        time.sleep(TICK_SEC)


def _persist(uid: int, r: dict, running: bool | None = None):
    """Durumu veritabanina yazar — web API buradan okur."""
    try:
        snap = r["engine"].snapshot() if r["setup_done"] else {}
    except Exception:
        snap = {}
    try:
        db.upsert_bot_state(uid, r["setup_done"] if running is None else running,
                            snap, list(r["events"])[:25])
    except Exception:
        pass


def start_manager():
    global _started
    if not _started:
        _started = True
        threading.Thread(target=_loop, daemon=True, name="multiengine").start()


def get_state(user_id: int) -> dict:
    with _lock:
        r = _runners.get(user_id)
        if not r:
            return {"running": False, "events": []}
        eng = r["engine"]
        try:
            snap = eng.snapshot() if r["setup_done"] else {}
        except Exception:
            snap = {}
        return {"running": r["setup_done"], "snapshot": snap,
                "events": list(r["events"])[:25]}
