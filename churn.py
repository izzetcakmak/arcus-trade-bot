"""Hacim dongusu (maker-oncelikli mikro cycle botu).

Amac: kar degil — dusuk maliyetle HACIM ve TX sayisi uretmek, sermayeyi korumak.
Dongu: en iyi alisa ALO (post-only) emir -> dolunca en iyi satisa reduceOnly ALO
-> pozisyon kapaninca yeni dongu. Maker ucreti 0 ppm oldugu icin dolan hacim
ucretsiz; tek maliyet mikro fiyat kaymasi. Emir dolmazsa periyodik reprice,
cikista uzun tikanmada tek seferlik IOC taker kurtarmasi (2.25 bps).

Koruma: equity gun baslangicindan CHURN_MAX_DAILY_LOSS_USD kadar duserse HALT
(Telegram bildirimi). Her dongu basinda flat kontrolu; kalinti pozisyon once
kapatilir. Durum churn_state.json'a yazilir (panel/inceleme icin).

Calistirma: python churn.py           (surekli)
           python churn.py --once    (tek dongu, smoke test)
"""

import json
import os
import socket
import sys
import time
import urllib.parse
import urllib.request
from decimal import Decimal

from dotenv import dotenv_values

from arcus.client import ArcusClient, ArcusError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(BASE_DIR, "churn_state.json")

env = dotenv_values(os.path.join(BASE_DIR, ".env"))

SYMBOL = (env.get("CHURN_SYMBOL") or "BTC-USD").strip()
REPRICE_SEC = int(env.get("CHURN_REPRICE_SEC") or 30)      # dolmayan emri tazeleme
PAUSE_SEC = int(env.get("CHURN_PAUSE_SEC") or 45)          # donguler arasi nefes
MAX_DAILY_LOSS = float(env.get("CHURN_MAX_DAILY_LOSS_USD") or 0.50)
MAX_REPRICE = int(env.get("CHURN_MAX_REPRICE") or 8)       # cikista IOC'a dusme esigi
REPORT_EVERY_SEC = int(env.get("CHURN_REPORT_SEC") or 3600)

TG_TOKEN = (env.get("TELEGRAM_TOKEN") or "").strip()
TG_CHAT = (env.get("TELEGRAM_CHAT_ID") or "").strip()

client = ArcusClient(base=env["ARCUS_BASE"], address=env["WALLET_ADDRESS"],
                     account_index=int(env.get("ARCUS_ACCOUNT_INDEX") or 0),
                     api_privkey_hex=(env.get("API_SIGNING_KEY")
                                      or env.get("ARCUS_API_PRIVKEY")))


def tg(text):
    if not (TG_TOKEN and TG_CHAT):
        return
    try:
        data = urllib.parse.urlencode({"chat_id": TG_CHAT, "text": text}).encode()
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data, timeout=10)
    except Exception:
        pass


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def backoff_429(e):
    """Sunucu 429 dondurdugunde soyledigi sureyi bekle (nazik istemci)."""
    try:
        d = json.loads(e.body)
        ms = int(d.get("retryAfterMs") or d.get("retryAfter") or 0)
    except Exception:
        ms = 0
    wait = max(30.0, min(300.0, ms / 1000.0 + 1))
    log(f"rate limit — {wait:.0f} sn bekleniyor")
    time.sleep(wait)


def cancel_quiet(order_id):
    """Tek emri iptal et; 429'da sunucuyu dinleyip bekle."""
    try:
        client.cancel_order(SYMBOL, order_id=order_id)
    except ArcusError as e:
        if e.status == 429:
            backoff_429(e)
        else:
            log(f"cancel: {e.status} {e.body[:60]}")


def my_open_orders():
    try:
        return client.open_orders().get("orders") or []
    except ArcusError as e:
        if e.status == 429:
            backoff_429(e)
            return []
        raise


def equity():
    return float(client.account().get("equity") or 0)


def position_qty():
    """SYMBOL icin imzali pozisyon miktari (long +, short -); engine ile ayni alanlar."""
    for p in (client.positions().get("positions") or {}).values():
        if p.get("marketDisplayName") == SYMBOL:
            return Decimal(str(p.get("size", "0")))
    return Decimal(0)


def cancel_all_mine():
    try:
        client.cancel_all_orders(market=SYMBOL)
    except ArcusError as e:
        log(f"cancelAll: {e.status} {e.body[:60]}")


def best_prices():
    b = client.bbo(SYMBOL)
    return Decimal(b["bestBid"]["price"]), Decimal(b["bestAsk"]["price"])


def place_maker(side, qty, price, reduce_only=False):
    """ALO emri; cross edecekse borsa reddeder -> None doner (reprice edilir)."""
    try:
        r = client.place_order(SYMBOL, side, str(qty), str(price),
                               tif="ALO", reduce_only=reduce_only)
        return r.get("orderId")
    except ArcusError as e:
        # ALO cross/kabul reddi vb: reprice. Auth hatalari ise gercek sorun.
        if e.status in (401, 403):
            raise
        return None


def wait_fill_or_cancel(order_id, want_qty):
    """REPRICE_SEC boyunca dolum bekler. Donen: dolan miktar (Decimal)."""
    t0 = time.time()
    while time.time() - t0 < REPRICE_SEC:
        time.sleep(3)
        oo = my_open_orders()
        mine = next((o for o in oo if str(o.get("orderId")) == str(order_id)), None)
        if mine is None:                       # kitapta yok: doldu ya da dustu
            return want_qty
        rem = Decimal(str(mine.get("remainingQuantity")
                          or mine.get("quantity") or want_qty))
        if rem < want_qty:                     # kismi dolum — kalani iptal et
            cancel_quiet(order_id)
            return want_qty - rem
    cancel_quiet(order_id)
    return Decimal(0)


def taker_close(qty_signed, m):
    """Son care: IOC ile kapat (taker, 2.25bps)."""
    side = "SELL" if qty_signed > 0 else "BUY"
    bid, ask = best_prices()
    px = client.snap_price(m, float(bid) * 0.999 if side == "SELL" else float(ask) * 1.001)
    try:
        client.place_order(SYMBOL, side, str(abs(qty_signed)), str(px),
                           tif="IOC", reduce_only=True)
        log(f"taker kurtarma: {side} {abs(qty_signed)}")
        return True
    except ArcusError as e:
        if e.status == 429:
            backoff_429(e)
        else:
            log(f"taker kurtarma reddi: {e.status} {e.body[:80]}")
        return False


def save_state(st):
    tmp = dict(st)
    tmp["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(tmp, f, indent=1)


def flatten(m):
    """Kalinti pozisyonu SABIRLA kapat: tek reduceOnly ALO kitapta dursun,
    yalnizca fiyat 5 tik'ten fazla uzaklasirsa tazele (tek emir iptali).
    Uzun tikanmada tek IOC dener. 429'da sunucunun dedigi kadar bekler."""
    tick = Decimal(str(m["tickSize"]))
    laps = 0
    while True:
        try:
            q = position_qty()
            if q == 0:
                return True
            laps += 1
            side = "SELL" if q > 0 else "BUY"
            bid, ask = best_prices()
            target = ask if q > 0 else bid
            resting = [o for o in my_open_orders() if o.get("reduceOnly")]
            if resting:
                px = Decimal(str(resting[0].get("price") or 0))
                if abs(px - target) <= tick * 5 and laps <= MAX_REPRICE * 3:
                    time.sleep(REPRICE_SEC)    # fiyat yakin: dolmasini bekle
                    continue
                cancel_quiet(resting[0].get("orderId"))
                time.sleep(2)
                continue
            if laps > MAX_REPRICE * 3:
                taker_close(q, m)
                time.sleep(10)                 # sonraki turda pozisyonu olc
                continue
            if place_maker(side, abs(q), target, reduce_only=True) is None:
                time.sleep(5)                  # ALO reddi: kisa bekle, tekrar
            else:
                time.sleep(5)                  # emir kitapta; sonraki tur olcer
        except ArcusError as e:
            if e.status == 429:
                backoff_429(e)
                continue
            raise


_LOCK = socket.socket()   # tek-ornek kilidi: ikinci kopya baslarsa kendini kapatir


def acquire_lock():
    try:
        _LOCK.bind(("127.0.0.1", int(env.get("CHURN_LOCK_PORT") or 8399)))
    except OSError:
        log("baska bir churn kopyasi zaten calisiyor — cikiliyor")
        sys.exit(0)


def main():
    acquire_lock()
    once = "--once" in sys.argv
    m = client.market(SYMBOL)
    step = Decimal(m["stepSize"])
    qty = Decimal(str(m["minOrderSize"]))
    # minNotional guvenligi: 5$ altinda kalirsa miktari buyut
    bid, _ = best_prices()
    min_notional = Decimal(str(m.get("minOrderNotional") or 5))
    while qty * bid < min_notional:
        qty += Decimal(str(m["minOrderSize"]))
    qty = (qty / step).to_integral_value() * step

    day = time.strftime("%Y-%m-%d")
    eq0 = equity()
    st = {"day": day, "day_start_equity": eq0, "cycles": 0, "entry_fills": 0,
          "exit_fills": 0, "taker_bailouts": 0, "volume_usd": 0.0,
          "halted": False, "symbol": SYMBOL, "qty": str(qty)}
    log(f"basla: {SYMBOL} qty={qty} equity=${eq0:.2f} "
        f"gunluk zarar siniri=${MAX_DAILY_LOSS:.2f}")
    tg(f"Churn basladi: {SYMBOL} x{qty} | equity ${eq0:.2f} | "
       f"gunluk stop -${MAX_DAILY_LOSS:.2f}")
    last_report = time.time()

    if not flatten(m):
        tg("Churn: acilista pozisyon kapatilamadi — 30 dk sonra tekrar denenecek.")
        time.sleep(1800)
        raise SystemExit("flatten basarisiz")

    while True:
        # gun devri + koruma
        if time.strftime("%Y-%m-%d") != st["day"]:
            st.update(day=time.strftime("%Y-%m-%d"), day_start_equity=equity())
        eq = equity()
        pnl_today = eq - st["day_start_equity"]
        if pnl_today <= -MAX_DAILY_LOSS:
            st["halted"] = True
            save_state(st)
            tg(f"Churn HALT: gunluk PnL {pnl_today:+.2f}$ siniri asti. "
               f"Equity ${eq:.2f}. Gun donunce otomatik devam.")
            log("gunluk zarar siniri — gun donusune kadar uyku")
            while time.strftime("%Y-%m-%d") == st["day"]:
                time.sleep(300)
            st.update(day=time.strftime("%Y-%m-%d"),
                      day_start_equity=equity(), halted=False)
            save_state(st)
            tg("Churn: yeni gun basladi, devam ediliyor.")
            continue

        # 1) giris: en iyi alisa ALO (yatan emir varsa onu bekle, 429'da sabret)
        filled = Decimal(0)
        for _ in range(MAX_REPRICE):
            try:
                resting = [o for o in my_open_orders() if not o.get("reduceOnly")]
                if resting:
                    wait_fill_or_cancel(resting[0].get("orderId"), qty)
                else:
                    bid, _a = best_prices()
                    oid = place_maker("BUY", qty, bid)
                    if oid is None:
                        time.sleep(5)
                        continue
                    wait_fill_or_cancel(oid, qty)
                filled = abs(position_qty())  # yer gercegi: pozisyondan oku
            except ArcusError as e:
                if e.status == 429:
                    backoff_429(e)
                    continue
                raise
            if filled > 0:
                break
        if filled == 0:
            time.sleep(PAUSE_SEC)
            continue
        st["entry_fills"] += 1
        st["volume_usd"] += float(filled) * float(best_prices()[0])

        # 2) cikis: en iyi satisa reduceOnly ALO; tikanirsa taker
        if not flatten(m):
            tg("Churn: pozisyon kapatilamadi, HALT. Elle kontrol et.")
            return
        st["exit_fills"] += 1
        _, ask2 = best_prices()
        st["volume_usd"] += float(filled * ask2)
        st["cycles"] += 1
        save_state(st)

        if time.time() - last_report >= REPORT_EVERY_SEC:
            last_report = time.time()
            eq = equity()
            tg(f"Churn saatlik: {st['cycles']} dongu | hacim ${st['volume_usd']:,.0f} | "
               f"PnL bugun {eq - st['day_start_equity']:+.3f}$ | equity ${eq:.2f}")

        if once:
            eq = equity()
            log(f"tek dongu tamam: hacim ${st['volume_usd']:.2f} "
                f"PnL {eq - st['day_start_equity']:+.4f}$")
            return
        time.sleep(PAUSE_SEC)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("kullanici durdurdu — pozisyon kontrolu...")
        try:
            flatten(client.market(SYMBOL))
        finally:
            cancel_all_mine()
