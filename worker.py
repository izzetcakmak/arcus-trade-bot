"""ArcusBot worker — surekli calisan surecler (Vercel disinda kosar).

Icerik:
- Cok kullanicili trade motoru (web/multiengine.py)
- Telegram getUpdates poller (web/notifier.py)
- Fonlama kuyrugu isleyicisi (web/funding.py)

Web API (Vercel) ile iletisim tamamen veritabani uzerinden (DATABASE_URL).
Calistirma: python worker.py
"""
import os
import time

from dotenv import dotenv_values

from web import db, security, notifier
from web.funding import process_fund_queue
from web.multiengine import start_manager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SPONSOR_KEY = (os.environ.get("WALLET_PRIVATE_KEY")
               or dotenv_values(os.path.join(BASE_DIR, ".env"))
               .get("WALLET_PRIVATE_KEY") or "").strip()


def main():
    db.init()
    backend = "Postgres" if db.IS_PG else "SQLite (lokal)"
    print(f"[worker] basladi — DB: {backend}", flush=True)
    notifier.start_poller()
    start_manager()
    while True:
        try:
            if SPONSOR_KEY:
                # kuyrukta is oldugu surece arka arkaya isle
                while process_fund_queue(SPONSOR_KEY, security.decrypt,
                                         db.get_wallet):
                    pass
        except Exception as e:
            print(f"[worker] fonlama kuyrugu hatasi: {e}", flush=True)
        time.sleep(10)


if __name__ == "__main__":
    main()
