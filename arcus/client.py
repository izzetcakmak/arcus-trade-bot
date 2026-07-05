"""Arcus exchange REST istemcisi (testnet oncelikli).

Imzalama kurallari: https://docs.arcus.xyz/api-reference/authentication
- Sema 1 (placeOrder/cancelOrder/modifyOrder/batch*): imzalanan mesaj, compact ve
  anahtarlari alfabetik sirali "typed payload" JSON'unun kendisidir (prefix yok).
  Timestamp payload icinde `ct` olarak tasinir ve X-Timestamp header'ina esittir.
- Sema 2 (cancelAllOrders/setLeverage): ed25519(timestamp + action + canonical(body)).

Fiyat/miktar donusumu: p = price / tickSize, q = quantity / stepSize — tam bolunmeli.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

from cryptography.hazmat.primitives.asymmetric import ed25519

TESTNET_BASE = "https://api.testnet.arcus.xyz"

SIDE = {"BUY": 0, "SELL": 1}
TIF = {"GTT": 0, "FOK": 1, "IOC": 2, "ALO": 3}
OP_PLACE, OP_CANCEL, OP_MODIFY, OP_PLACE_UNTRIGGERED = 1, 2, 3, 4


def canonical(obj) -> bytes:
    """Anahtarlari sirali, bosluksuz JSON — hem imza mesaji hem istek govdesi."""
    return json.dumps(obj, separators=(",", ":"), sort_keys=True).encode()


def dec_str(value) -> str:
    """Decimal'i üstel gosterim olmadan stringe cevirir ('1E-7' degil '0.0000001')."""
    d = Decimal(str(value))
    return format(d.normalize(), "f")


class ArcusError(RuntimeError):
    def __init__(self, status, body):
        super().__init__(f"HTTP {status}: {body}")
        self.status = status
        self.body = body


class ArcusClient:
    def __init__(self, base=TESTNET_BASE, address=None, account_index=0,
                 api_privkey_hex=None, timeout=15):
        self.base = base.rstrip("/")
        self.address = address
        self.account_index = int(account_index)
        self.timeout = timeout
        self._markets_cache = None
        if api_privkey_hex:
            raw = bytes.fromhex(api_privkey_hex.removeprefix("0x"))
            self._priv = ed25519.Ed25519PrivateKey.from_private_bytes(raw)
            self.api_key = self._priv.public_key().public_bytes_raw().hex()
        else:
            self._priv = None
            self.api_key = None

    # ------------------------------------------------------------- transport

    def call(self, method, path, body=None, headers=None):
        data = canonical(body) if body is not None else None
        base_headers = {"Content-Type": "application/json"}
        if self.api_key:
            base_headers["X-API-Key"] = self.api_key
        req = urllib.request.Request(
            self.base + path, data=data, method=method,
            headers={**base_headers, **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            raise ArcusError(e.code, e.read().decode(errors="replace")) from None

    def get(self, path, **params):
        qs = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        return self.call("GET", path + ("?" + qs if qs else ""))

    # ----------------------------------------------------------- public data

    def markets(self, refresh=False):
        if self._markets_cache is None or refresh:
            self._markets_cache = self.get("/v1/markets")["markets"]
        return self._markets_cache

    def market(self, key):
        """marketId (int), 'BTC-USD' veya 'BTC' ile market bulur."""
        for m in self.markets():
            if key in (m["marketId"], m["marketDisplayName"], m["baseAsset"]):
                return m
        # cache bayat olabilir — bir kez tazele
        for m in self.markets(refresh=True):
            if key in (m["marketId"], m["marketDisplayName"], m["baseAsset"]):
                return m
        raise KeyError(f"market bulunamadi: {key}")

    def candles(self, market_display_name, timeframe="15m", hours=48, **params):
        """OHLCV mumlari. from/to unix mikrosaniye ister; timeframe or. '15m'."""
        now_us = int(time.time() * 1_000_000)
        params.setdefault("to", now_us)
        params.setdefault("from", now_us - int(hours * 3600) * 1_000_000)
        r = self.get("/v1/candles", market=market_display_name,
                     timeframe=timeframe, **params)
        return r.get("candles", r)

    def funding_rates(self, **params):
        return self.get("/v1/fundingRates", **params)

    def bbo(self, market_display_name):
        return self.get(f"/v1/bbo/{urllib.parse.quote(market_display_name)}")

    def rate_limit(self):
        return self.get("/v1/rateLimit")

    # -------------------------------------------------------- account reads

    def account(self):
        return self.get("/v1/account", address=self.address,
                        accountIndex=self.account_index)

    def positions(self):
        return self.get("/v1/positions", address=self.address,
                        accountIndex=self.account_index)

    def open_orders(self):
        return self.get("/v1/openOrders", address=self.address,
                        accountIndex=self.account_index)

    def fills(self, **params):
        return self.get("/v1/fills", address=self.address,
                        accountIndex=self.account_index, **params)

    def order_status(self, order_id):
        return self.get(f"/v1/order/{urllib.parse.quote(str(order_id))}",
                        address=self.address)

    def transfer_updates(self, limit=50):
        return self.get("/v1/accountTransferUpdates", address=self.address,
                        limit=limit)

    def api_keys(self):
        return self.get("/v1/apiKeys", address=self.address)

    # ----------------------------------------------------------- conversions

    @staticmethod
    def to_int(value, unit):
        """Ondalik fiyat/miktari tam sayi tick/quantum'a cevirir; kalan varsa hata."""
        n = Decimal(str(value)) / Decimal(str(unit))
        if n != n.to_integral_value():
            raise ValueError(f"{value}, {unit} biriminin tam kati degil")
        return int(n)

    @staticmethod
    def snap_price(market, price):
        """Fiyati marketin (kademeli) tick boyutuna yuvarlar, Decimal dondurur."""
        p = Decimal(str(price))
        tick = Decimal(market["tickSize"])
        for t in market.get("tickTiers", []):
            tick = Decimal(t["tick"])
            if "upToPrice" not in t or p <= Decimal(t["upToPrice"]):
                break
        return (p / tick).to_integral_value(rounding=ROUND_HALF_UP) * tick

    @staticmethod
    def snap_quantity(market, quantity):
        """Miktari step boyutuna ASAGI yuvarlar (pozisyon buyutmemek icin)."""
        q = Decimal(str(quantity))
        step = Decimal(market["stepSize"])
        return (q / step).to_integral_value(rounding=ROUND_DOWN) * step

    # -------------------------------------------------------- order building

    def _require_signer(self):
        if not (self._priv and self.address):
            raise RuntimeError("imzali istek icin address + api_privkey_hex gerekli")

    def _make_order(self, ts, market, side, quantity, price, *, order_type="LIMIT",
                    tif="GTT", reduce_only=False, good_til_days=45, client_id=None,
                    tpsl_type=None, stop_price=None, is_position_tpsl=False,
                    parent_order_id=None):
        """Tek emir icin (canonical_payload_bytes, request_body) uretir."""
        m = self.market(market)
        price_s = dec_str(price)
        qty_s = dec_str(quantity)

        # Validator her TIF'te >=1 ay ileri goodTilTime ister (IOC/FOK dahil,
        # docs'taki "ignored" ifadesine ragmen) — canli testte dogrulandi.
        good_til_us = int(time.time() * 1_000_000) + good_til_days * 86_400 * 1_000_000

        op = OP_PLACE_UNTRIGGERED if tpsl_type else OP_PLACE
        payload = {
            "ad": self.address.lower(),
            "ai": self.account_index,
            "ct": ts,
            "g": good_til_us * 1000,           # payload'da nanosaniye
            "m": m["marketId"],
            "op": op,
            "p": self.to_int(price_s, m["tickSize"]),
            "q": self.to_int(qty_s, m["stepSize"]),
            "r": 1 if reduce_only else 0,
            "s": SIDE[side],
            "t": TIF[tif],
            "v": 1,
        }
        if client_id:
            payload["c"] = client_id.lower()

        body = {
            "address": self.address,
            "accountIndex": self.account_index,
            "marketId": m["marketId"],
            "orderSide": side,
            "orderType": order_type,
            "quantity": qty_s,
            "price": price_s,
            "timeInForce": tif,
            "timestamp": ts,
        }
        # govdede mikrosaniye (string); IOC/FOK icin "0" — alan yine de zorunlu
        body["goodTilTime"] = str(good_til_us)
        if client_id:
            body["clientId"] = client_id
        if reduce_only:
            body["reduceOnly"] = True
        if tpsl_type:
            body["tpslType"] = tpsl_type           # STOP_LOSS | TAKE_PROFIT
            body["stopPrice"] = dec_str(stop_price)
            if is_position_tpsl:
                body["isPositionTPSL"] = True
            if parent_order_id:
                body["parentOrderId"] = parent_order_id
        return canonical(payload), body

    def _signed_headers(self, ts, signature):
        return {"X-API-Key": self.api_key, "X-Timestamp": str(ts),
                "X-Signature": signature}

    # --------------------------------------------------------- order actions

    def place_order(self, market, side, quantity, price, **kw):
        """Tek emir. side: BUY/SELL, tif: GTT/FOK/IOC/ALO. TP/SL icin tpsl_type +
        stop_price ver. MARKET emirlerde tif=IOC zorunlu, price koruyucu sinirdir."""
        self._require_signer()
        ts = time.time_ns()
        payload, body = self._make_order(ts, market, side, quantity, price, **kw)
        sig = self._priv.sign(payload).hex()
        return self.call("POST", "/v1/placeOrder", body, self._signed_headers(ts, sig))

    def place_batch(self, orders):
        """orders: place_order kwargs sozlukleri listesi. Her eleman ayri imzalanir,
        ortak tek X-Timestamp kullanilir."""
        self._require_signer()
        ts = time.time_ns()
        elements = []
        for kw in orders:
            kw = dict(kw)
            args = (kw.pop("market"), kw.pop("side"), kw.pop("quantity"), kw.pop("price"))
            payload, body = self._make_order(ts, *args, **kw)
            body["signature"] = self._priv.sign(payload).hex()
            elements.append(body)
        # X-Signature header'i batch'te dogrulanmaz ama zorunlu — ilk elemani koy
        return self.call("POST", "/v1/batchPlaceOrders", {"orders": elements},
                         self._signed_headers(ts, elements[0]["signature"]))

    def cancel_order(self, market, order_id=None, client_id=None):
        self._require_signer()
        if not (order_id or client_id):
            raise ValueError("order_id veya client_id gerekli")
        m = self.market(market)
        ts = time.time_ns()
        payload = {"ad": self.address.lower(), "ai": self.account_index, "ct": ts,
                   "m": m["marketId"], "op": OP_CANCEL, "v": 1}
        body = {"address": self.address, "accountIndex": self.account_index,
                "marketId": m["marketId"], "timestamp": ts}
        if order_id:
            payload["id"] = str(order_id)
            body["kind"] = "orderId"
            body["orderId"] = str(order_id)
        else:
            payload["c"] = client_id.lower()
            body["kind"] = "clientId"
            body["clientId"] = client_id
        sig = self._priv.sign(canonical(payload)).hex()
        return self.call("POST", "/v1/cancelOrder", body, self._signed_headers(ts, sig))

    # ------------------------------------------------- scheme-2 (legacy) ops

    def _legacy_call(self, action, body):
        self._require_signer()
        ts = time.time_ns()
        msg = str(ts).encode() + action.encode() + canonical(body)
        sig = self._priv.sign(msg).hex()
        return self.call("POST", f"/v1/{action}", body, self._signed_headers(ts, sig))

    def cancel_all_orders(self, market=None):
        body = {"address": self.address, "accountIndex": self.account_index}
        if market is not None:
            body["marketId"] = self.market(market)["marketId"]
        return self._legacy_call("cancelAllOrders", body)

    def set_leverage(self, market, leverage):
        body = {"address": self.address, "accountIndex": self.account_index,
                "marketId": self.market(market)["marketId"],
                "leverage": int(leverage)}
        return self._legacy_call("setLeverage", body)
