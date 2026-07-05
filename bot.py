"""Arcus perp trade botu — ana dongu.

Konsol + bot.log'a loglar; TELEGRAM_TOKEN/CHAT_ID doluysa Telegram'a bildirir.
Her tick sonrasi state.json'a durum yazar (dashboard.py bunu okur).
Calistirma: python bot.py
"""
import datetime as dt
import json
import os
import time
import urllib.parse
import urllib.request

from config import Config
from engine import TradingEngine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "bot.log")
STATE_PATH = os.path.join(BASE_DIR, "state.json")


def make_notify(cfg: Config):
    def notify(msg: str):
        stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{stamp}] {msg}"
        print(line, flush=True)
        try:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except OSError:
            pass
        if cfg.telegram_token and cfg.telegram_chat_id:
            try:
                data = urllib.parse.urlencode(
                    {"chat_id": cfg.telegram_chat_id, "text": msg}).encode()
                urllib.request.urlopen(
                    f"https://api.telegram.org/bot{cfg.telegram_token}/sendMessage",
                    data=data, timeout=10).read()
            except Exception as e:
                print(f"[{stamp}] telegram bildirimi gonderilemedi: {e}", flush=True)
    return notify


def write_state(engine: TradingEngine):
    try:
        tmp = STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(engine.snapshot(), f)
        os.replace(tmp, STATE_PATH)
    except OSError:
        pass


def main():
    cfg = Config.load()
    notify = make_notify(cfg)
    engine = TradingEngine(cfg, notify)
    engine.setup()
    notify("Dongu basladi.")
    write_state(engine)
    env_path = os.path.join(BASE_DIR, ".env")
    env_mtime = os.path.getmtime(env_path)
    try:
        while True:
            engine.tick()
            write_state(engine)
            try:   # panel .env'i degistirdiyse ayarlari sicak uygula
                m = os.path.getmtime(env_path)
                if m != env_mtime:
                    env_mtime = m
                    engine.apply_config(Config.load())
                    write_state(engine)
            except OSError:
                pass
            time.sleep(engine.cfg.loop_interval_sec)
    except KeyboardInterrupt:
        notify("Bot durduruldu (Ctrl-C). Acik pozisyonlar icin dikkat: "
               "bot-tarafi SL/TP izleme de durdu.")


if __name__ == "__main__":
    main()
