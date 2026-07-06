"""Arcus trade motoru: cok sembollu 15dk sinyal dongusu.

Canli testnet bulgularina gore tasarim (Temmuz 2026):
- TPSL emirleri borsada henuz implemente degil (501 NotImplemented) -> once dener,
  olmazsa SL/TP'yi bot tarafinda mark fiyatiyla izler (her tick).
- Testnet likiditesi patlamali: kitap bazen bos/bayat, IOC emirler IOC_CANCELED
  ile reddedilebilir -> giris dolmadiysa sinyal atlanir; cikislar IOC denemesi
  sonrasi dinlenen GTT emre duser ve dolana kadar yeniden fiyatlanir.
- goodTilTime her TIF'te zorunlu ve >=1 ay ileri olmali (client halleder).
"""
import datetime as dt
import time
from dataclasses import dataclass, field
from decimal import Decimal

import strategy
from arcus.client import ArcusClient, ArcusError, dec_str
from config import Config

IOC_FACTORS = (0.998, 0.99, 0.97)   # satista carpan; alista 2-x uygulanir
REPRICE_SEC = 60                     # dinlenen cikis emrini yeniden fiyatlama araligi

# Bildirim kataloglari — engine.lang ("tr"/"en") secer. Standalone bot: tr.
MESSAGES = {
    "market_not_found":    {"tr": "Market bulunamadi, atlandi: {sym}",
                            "en": "Market not found, skipped: {sym}"},
    "leverage_failed":     {"tr": "{sym} kaldirac ayarlanamadi (devam): {err}",
                            "en": "{sym}: could not set leverage (continuing): {err}"},
    "engine_ready":        {"tr": "Motor hazir ({base})\nSemboller: {syms} | TF: {tf} | Kaldirac: {lev}x\nIslem basi teminat: {margin:.0f} USD | SL/TP: teminatin %{sl:.0f}/%{tp:.0f}\nEquity: {eq:.2f} USD",
                            "en": "Engine ready ({base})\nMarkets: {syms} | TF: {tf} | Leverage: {lev}x\nMargin per trade: ${margin:.0f} | SL/TP: {sl:.0f}%/{tp:.0f}% of margin\nEquity: ${eq:.2f}"},
    "cfg_unknown_market":  {"tr": "Ayar: bilinmeyen market atlandi: {sym}",
                            "en": "Settings: unknown market skipped: {sym}"},
    "cfg_updated":         {"tr": "AYARLAR GUNCELLENDI (panelden): {changes}",
                            "en": "SETTINGS UPDATED (from dashboard): {changes}"},
    "equity_read_failed":  {"tr": "Equity okunamadi: {err}",
                            "en": "Could not read equity: {err}"},
    "daily_halt":          {"tr": "GUNLUK ZARAR LIMITI asildi (%{pct:.1f}). Bugun yeni islem yok; yarin otomatik reset.",
                            "en": "DAILY LOSS LIMIT reached ({pct:.1f}%). No new trades today; resets tomorrow."},
    "tick_error":          {"tr": "{sym} tick hatasi: {err}",
                            "en": "{sym} tick error: {err}"},
    "unexpected_error":    {"tr": "{sym} beklenmeyen hata: {err}",
                            "en": "{sym} unexpected error: {err}"},
    "external_position":   {"tr": "{sym}: takip edilmeyen acik pozisyon var; otomatik islem yapilmadi.",
                            "en": "{sym}: untracked open position detected; automatic trading skipped for it."},
    "insufficient_equity": {"tr": "{sym}: yetersiz equity ({need:.0f} > {have:.2f}). Atlandi.",
                            "en": "{sym}: insufficient equity ({need:.0f} > {have:.2f}). Skipped."},
    "trade_too_small":     {"tr": "{sym}: islem cok kucuk (qty={qty}, notional={notional:.2f}).",
                            "en": "{sym}: trade too small (qty={qty}, notional={notional:.2f})."},
    "entry_not_filled":    {"tr": "{sym}: giris IOC dolmadi ({status}/{reason}) — kitap bos olabilir, sinyal atlandi.",
                            "en": "{sym}: entry IOC did not fill ({status}/{reason}) — book may be empty, signal skipped."},
    "tpsl_unsupported":    {"tr": "Not: borsa TPSL emri kabul etmedi (testnette henuz yok) — SL/TP bot tarafinda mark fiyatiyla izlenecek.",
                            "en": "Note: exchange rejected TPSL orders (not yet live on testnet) — SL/TP will be monitored bot-side via mark price."},
    "position_opened":     {"tr": "YENI POZISYON: {sym} {side}\nSebep: {reason}\nTeminat: {margin:.0f} USD x{lev} | Giris~{mark:.6g} | Miktar: {qty}\nSL: {sl:.6g} | TP: {tp:.6g} ({where})",
                            "en": "NEW POSITION: {sym} {side}\nReason: {reason}\nMargin: ${margin:.0f} x{lev} | Entry~{mark:.6g} | Size: {qty}\nSL: {sl:.6g} | TP: {tp:.6g} ({where})"},
    "tpsl_where_server":   {"tr": "borsada", "en": "on exchange"},
    "tpsl_where_bot":      {"tr": "bot izliyor", "en": "bot-monitored"},
    "close_started":       {"tr": "{sym}: {reason} — IOC dolmadi (likidite yok), dinlenen cikis emri kitapta, dolana kadar yeniden fiyatlanir.",
                            "en": "{sym}: {reason} — IOC did not fill (no liquidity); resting exit order on the book, repriced until filled."},
    "ioc_close_error":     {"tr": "{sym} IOC kapatma hatasi: {err}",
                            "en": "{sym} IOC close error: {err}"},
    "resting_exit_failed": {"tr": "{sym} dinlenen cikis emri konulamadi: {err} — sonraki tick'te yeniden denenecek.",
                            "en": "{sym}: could not place resting exit order: {err} — retrying next tick."},
    "position_closed":     {"tr": "POZISYON KAPANDI: {sym} ({reason})\nYaklasik PnL: {pnl:+.2f} USD | Toplam: {total:+.2f} | Islem: {trades} (W:{wins})",
                            "en": "POSITION CLOSED: {sym} ({reason})\nApprox PnL: {pnl:+.2f} USD | Total: {total:+.2f} | Trades: {trades} (W:{wins})"},
    "reverse_signal":      {"tr": "Ters sinyal geldi", "en": "Reverse signal"},
    "sl_hit":              {"tr": "SL tetiklendi (bot-tarafi, mark {mark:.6g})",
                            "en": "Stop-loss hit (bot-side, mark {mark:.6g})"},
    "tp_hit":              {"tr": "TP tetiklendi (bot-tarafi, mark {mark:.6g})",
                            "en": "Take-profit hit (bot-side, mark {mark:.6g})"},
    "sl_tp_default":       {"tr": "SL/TP tetiklendi", "en": "SL/TP triggered"},
    "reason_long":         {"tr": "EMA9>EMA21 kesisim + fiyat EMA200 ustu + ADX guclu + MACD+",
                            "en": "EMA9>EMA21 cross + price above EMA200 + strong ADX + MACD+"},
    "reason_short":        {"tr": "EMA9<EMA21 kesisim + fiyat EMA200 alti + ADX guclu + MACD-",
                            "en": "EMA9<EMA21 cross + price below EMA200 + strong ADX + MACD-"},
    "no_signal":           {"tr": "Sinyal yok (ADX={adx:.0f}, RSI={rsi:.0f})",
                            "en": "No signal (ADX={adx:.0f}, RSI={rsi:.0f})"},
    "price_lbl":           {"tr": "fiyat", "en": "price"},
}

# apply_config degisiklik etiketleri (alan -> (tr, en))
_CHANGE_LABELS = {
    "leverage": ("kaldirac", "leverage"),
    "margin_usd": ("teminat", "margin"),
    "sl_pct": ("SL%", "SL%"),
    "tp_pct": ("TP%", "TP%"),
    "max_daily_loss_pct": ("gunluk limit%", "daily limit%"),
    "adx_threshold": ("ADX", "ADX"),
}


@dataclass
class Position:
    side: str                # "long" / "short"
    entry: float
    qty: str                 # insan-okur miktar
    sl: float
    tp: float
    opened_ts: float
    equity_at_open: float
    server_tpsl: bool = False    # TPSL borsaya konulabildi mi?
    closing: bool = False
    close_reason: str = ""
    exit_order_id: str | None = None
    exit_placed_ts: float = 0.0


class TradingEngine:
    def __init__(self, cfg: Config, notify):
        self.cfg = cfg
        self.notify = notify
        self.client = ArcusClient(base=cfg.base, address=cfg.address,
                                  account_index=cfg.account_index,
                                  api_privkey_hex=cfg.api_privkey)
        self.positions: dict[str, Position] = {}
        self.last_candle_ts: dict[str, int] = {}
        self.day = dt.date.today().isoformat()
        self.day_start_equity = 0.0
        self.halted_today = False
        self.warned_external: set[str] = set()
        self.warned_tpsl_unsupported = False
        self.entries_enabled = True   # False: yeni giris yok, acik pozisyon yonetimi surer
        self.trades = 0
        self.wins = 0
        self.total_pnl = 0.0
        self.last_signal: dict[str, str] = {}      # sym -> son degerlendirme ozeti
        self.lang = "tr"                           # bildirim dili (multiengine gecersiz kilar)
        self._tick_markets: dict[str, dict] = {}   # tick basina taze market verisi

    def _msg(self, key: str, **kw) -> str:
        tpl = MESSAGES[key]
        return tpl.get(self.lang, tpl["en"]).format(**kw)

    # ---------- kurulum ----------
    def setup(self):
        valid = []
        for sym in self.cfg.symbols:
            try:
                self.client.market(sym)
            except KeyError:
                self.notify(self._msg("market_not_found", sym=sym))
                continue
            valid.append(sym)
            try:
                self.client.set_leverage(sym, self.cfg.leverage)
            except ArcusError as e:
                self.notify(self._msg("leverage_failed", sym=sym, err=e))
        if not valid:
            raise SystemExit("Gecerli sembol yok.")
        self.cfg.symbols = valid

        try:
            eq = self._equity()
        except ArcusError as e:
            if e.status == 404:
                raise SystemExit("Hesap fonlanmamis — once fund_testnet.py veya "
                                 "web app 'Testnet Deposit'.") from None
            raise
        self.day_start_equity = eq
        self.notify(self._msg("engine_ready", base=self.cfg.base,
                              syms=", ".join(valid), tf=self.cfg.timeframe,
                              lev=self.cfg.leverage, margin=self.cfg.margin_usd,
                              sl=self.cfg.sl_pct, tp=self.cfg.tp_pct, eq=eq))

    # ---------- ayar sicak-yenileme ----------
    def apply_config(self, new_cfg: Config):
        """Panel .env'i degistirdiginde bot yeniden baslatilmadan ayarlari uygular.
        Acik pozisyonlar etkilenmez; yeni degerler sonraki islemlerde gecerli."""
        old = self.cfg
        valid = []
        for sym in new_cfg.symbols:
            try:
                self.client.market(sym)
                valid.append(sym)
            except KeyError:
                self.notify(self._msg("cfg_unknown_market", sym=sym))
        new_cfg.symbols = valid or old.symbols

        li = 0 if self.lang == "tr" else 1
        changes, leverage_changed = [], False
        for alan, labels in _CHANGE_LABELS.items():
            if getattr(new_cfg, alan) != getattr(old, alan):
                if alan == "leverage":
                    leverage_changed = True
                changes.append(f"{labels[li]} {getattr(old, alan)} -> "
                               f"{getattr(new_cfg, alan)}")
        if set(new_cfg.symbols) != set(old.symbols):
            lbl = "semboller" if self.lang == "tr" else "markets"
            changes.append(f"{lbl}: {', '.join(new_cfg.symbols)}")

        self.cfg = new_cfg
        if leverage_changed or set(new_cfg.symbols) - set(old.symbols):
            for sym in new_cfg.symbols:
                try:
                    self.client.set_leverage(sym, new_cfg.leverage)
                except ArcusError as e:
                    self.notify(self._msg("leverage_failed", sym=sym, err=e))
        if changes:
            self.notify(self._msg("cfg_updated", changes=" | ".join(changes)))

    # ---------- yardimcilar ----------
    def _equity(self) -> float:
        return float(self.client.account()["equity"])

    def _position_size(self, sym) -> Decimal:
        """Acik pozisyon (isaretli). positions yaniti marketId->pozisyon sozlugu."""
        try:
            resp = self.client.positions()
        except ArcusError:
            return Decimal(0)
        for p in (resp.get("positions") or {}).values():
            if p.get("marketDisplayName") == sym:
                return Decimal(p.get("size", "0"))
        return Decimal(0)

    def _fresh_market(self, sym) -> dict:
        if sym not in self._tick_markets:
            self._tick_markets = {m["marketDisplayName"]: m
                                  for m in self.client.markets(refresh=True)}
        return self._tick_markets[sym]

    def _ohlcv(self, sym) -> list:
        candles = self.client.candles(sym, self.cfg.timeframe, hours=60)
        return [[c["openTime"], float(c["open"]), float(c["high"]),
                 float(c["low"]), float(c["close"]), float(c["volume"])]
                for c in candles if c.get("isFinal")]

    def _best_level(self, sym, side_needed) -> float | None:
        """Kitaptan en iyi karsi seviye; kitap bos/erisilemez ise None."""
        try:
            ob = self.client.get(f"/v1/l2OrderBook/{sym}")
            levels = ob.get("bids" if side_needed == "SELL" else "asks") or []
            return float(levels[0][0]) if levels else None
        except (ArcusError, ValueError, IndexError):
            return None

    def _roll_day(self, equity: float):
        today = dt.date.today().isoformat()
        if today != self.day:
            self.day = today
            self.day_start_equity = equity
            self.halted_today = False

    # ---------- ana dongu ----------
    def tick(self):
        self._tick_markets = {}   # her tick taze fiyat
        try:
            eq = self._equity()
        except ArcusError as e:
            self.notify(self._msg("equity_read_failed", err=e))
            return
        self._roll_day(eq)
        if not self.halted_today and self.day_start_equity > 0:
            loss_pct = (self.day_start_equity - eq) / self.day_start_equity * 100
            if loss_pct >= self.cfg.max_daily_loss_pct:
                self.halted_today = True
                self.notify(self._msg("daily_halt", pct=loss_pct))
        # izlenen semboller + (listeden cikarilmis olsa da) acik pozisyonlular
        for sym in dict.fromkeys(list(self.cfg.symbols) + list(self.positions)):
            try:
                self._tick_symbol(sym)
            except ArcusError as e:
                self.notify(self._msg("tick_error", sym=sym, err=e))
            except Exception as e:  # tek sembol hatasi donguyu oldurmesin
                self.notify(self._msg("unexpected_error", sym=sym,
                                      err=f"{type(e).__name__}: {e}"))

    def _tick_symbol(self, sym):
        size = self._position_size(sym)
        tracked = self.positions.get(sym)

        # pozisyon borsada kapandi mi? (TPSL/cikis emri doldu)
        if tracked and size == 0:
            self._on_closed(sym)
            tracked = None
        if size == 0:
            self.warned_external.discard(sym)

        # kapanis surecindeki pozisyon: cikis emrini yonet, sinyal isleme
        if tracked and tracked.closing:
            self._manage_exit(sym, tracked)
            return

        # bot-tarafi SL/TP izleme (borsa TPSL kabul etmediyse)
        if tracked and not tracked.server_tpsl:
            mark = float(self._fresh_market(sym)["markPrice"])
            hit = None
            if tracked.side == "long":
                if mark <= tracked.sl:
                    hit = self._msg("sl_hit", mark=mark)
                elif mark >= tracked.tp:
                    hit = self._msg("tp_hit", mark=mark)
            else:
                if mark >= tracked.sl:
                    hit = self._msg("sl_hit", mark=mark)
                elif mark <= tracked.tp:
                    hit = self._msg("tp_hit", mark=mark)
            if hit:
                self._begin_close(sym, tracked, hit)
                return

        # sinyal degerlendirme: sadece yeni kapanmis mumda
        rows = self._ohlcv(sym)
        if len(rows) < 205:
            return
        last_ts = rows[-1][0]
        if last_ts == self.last_candle_ts.get(sym):
            return
        self.last_candle_ts[sym] = last_ts

        df = strategy.build_frame(rows)
        sig = strategy.evaluate(df, self.cfg.adx_threshold)
        state = (sig.side.upper() if sig.side
                 else self._msg("no_signal", adx=sig.adx, rsi=sig.rsi))
        self.last_signal[sym] = (f"{dt.datetime.now().strftime('%H:%M')} | "
                                 f"{self._msg('price_lbl')} {sig.price:.6g} | {state}")

        if tracked:
            opp = (tracked.side == "long" and sig.side == "short") or \
                  (tracked.side == "short" and sig.side == "long")
            if opp:
                self._begin_close(sym, tracked, self._msg("reverse_signal"))
            return

        if self.halted_today or not self.entries_enabled:
            return
        if size != 0:
            if sym not in self.warned_external:
                self.warned_external.add(sym)
                self.notify(self._msg("external_position", sym=sym))
            return
        if sig.side:
            self._open(sym, sig)

    # ---------- pozisyon ac ----------
    def _open(self, sym, sig):
        m = self._fresh_market(sym)
        if m.get("status") != "ONLINE":
            return
        mark = float(m["markPrice"])
        lev = self.cfg.leverage
        margin = self.cfg.margin_usd

        eq = self._equity()
        if margin > eq:
            self.notify(self._msg("insufficient_equity", sym=sym, need=margin, have=eq))
            return

        qty = self.client.snap_quantity(m, (margin * lev) / mark)
        notional = float(qty) * mark
        if float(qty) <= 0 or notional < float(m.get("minOrderNotional", 0)):
            self.notify(self._msg("trade_too_small", sym=sym, qty=qty,
                                  notional=notional))
            return

        long = sig.side == "long"
        entry_side = "BUY" if long else "SELL"
        bound = self.client.snap_price(m, mark * (1.02 if long else 0.98))

        r = self.client.place_order(sym, entry_side, dec_str(qty), bound,
                                    order_type="MARKET", tif="IOC")
        filled = Decimal(r.get("filledSize", "0") or "0")
        if r.get("status") != "FILLED" or filled <= 0:
            self.notify(self._msg("entry_not_filled", sym=sym,
                                  status=r.get("status"),
                                  reason=r.get("rejectionReason", "?")))
            return
        qty_s = dec_str(filled)

        # SL/TP seviyeleri: teminatin yuzdesi = fiyatta %(pct/kaldirac)
        sl_move = (self.cfg.sl_pct / 100) / lev
        tp_move = (self.cfg.tp_pct / 100) / lev
        sl = float(self.client.snap_price(m, mark * (1 - sl_move if long else 1 + sl_move)))
        tp = float(self.client.snap_price(m, mark * (1 + tp_move if long else 1 - tp_move)))

        pos = Position(side=sig.side, entry=mark, qty=qty_s, sl=sl, tp=tp,
                       opened_ts=time.time(), equity_at_open=eq)

        # borsa TPSL dene; desteklenmiyorsa bot-tarafi izlemeye dus
        exit_side = "SELL" if long else "BUY"
        try:
            for tpsl_type, trig in (("STOP_LOSS", sl), ("TAKE_PROFIT", tp)):
                guard = self.client.snap_price(
                    m, trig * (0.95 if exit_side == "SELL" else 1.05))
                self.client.place_order(
                    sym, exit_side, qty_s, guard, order_type="MARKET", tif="IOC",
                    reduce_only=True, tpsl_type=tpsl_type,
                    stop_price=dec_str(self.client.snap_price(m, trig)),
                    is_position_tpsl=True)
            pos.server_tpsl = True
        except ArcusError:
            if not self.warned_tpsl_unsupported:
                self.warned_tpsl_unsupported = True
                self.notify(self._msg("tpsl_unsupported"))

        self.positions[sym] = pos
        self.trades += 1
        panel = f"\nPanel: {self.cfg.dashboard_url}" if self.cfg.dashboard_url else ""
        reason = self._msg("reason_long" if long else "reason_short")
        where = self._msg("tpsl_where_server" if pos.server_tpsl else "tpsl_where_bot")
        self.notify(self._msg("position_opened", sym=sym,
                              side="LONG" if long else "SHORT", reason=reason,
                              margin=margin, lev=lev, mark=mark, qty=qty_s,
                              sl=sl, tp=tp, where=where) + panel)

    # ---------- kapanis surecleri ----------
    def _begin_close(self, sym, pos: Position, reason: str):
        """Once IOC dene; olmazsa dinlenen GTT cikis emri birak."""
        pos.closing = True
        pos.close_reason = reason
        try:
            self.client.cancel_all_orders(sym)   # varsa TPSL/eski emir temizligi
        except ArcusError:
            pass
        if self._try_ioc_close(sym, pos):
            return
        self._place_resting_exit(sym, pos)
        self.notify(self._msg("close_started", sym=sym, reason=reason))

    def _try_ioc_close(self, sym, pos: Position) -> bool:
        m = self._fresh_market(sym)
        exit_side = "SELL" if pos.side == "long" else "BUY"
        for f in IOC_FACTORS:
            factor = f if exit_side == "SELL" else (2 - f)
            ref = self._best_level(sym, exit_side) or float(m["oraclePrice"])
            bound = self.client.snap_price(m, ref * factor)
            try:
                r = self.client.place_order(sym, exit_side, pos.qty, bound,
                                            order_type="LIMIT", tif="IOC",
                                            reduce_only=True)
            except ArcusError as e:
                self.notify(self._msg("ioc_close_error", sym=sym, err=e))
                return False
            if r.get("status") == "FILLED":
                self._on_closed(sym)
                return True
            time.sleep(1)
        return self._position_size(sym) == 0

    def _place_resting_exit(self, sym, pos: Position):
        m = self._fresh_market(sym)
        exit_side = "SELL" if pos.side == "long" else "BUY"
        oracle = float(m["oraclePrice"])
        px = self.client.snap_price(m, oracle * (0.999 if exit_side == "SELL" else 1.001))
        try:
            r = self.client.place_order(sym, exit_side, pos.qty, px,
                                        order_type="LIMIT", tif="GTT")
            pos.exit_order_id = r.get("orderId")
            pos.exit_placed_ts = time.time()
        except ArcusError as e:
            self.notify(self._msg("resting_exit_failed", sym=sym, err=e))
            pos.exit_order_id = None

    def _manage_exit(self, sym, pos: Position):
        """Kapanis surecinde: dolduysa kapat, eskidiyse yeniden fiyatla."""
        if self._position_size(sym) == 0:
            self._on_closed(sym)
            return
        if pos.exit_order_id is None:
            if self._try_ioc_close(sym, pos):
                return
            self._place_resting_exit(sym, pos)
            return
        if time.time() - pos.exit_placed_ts >= REPRICE_SEC:
            try:
                self.client.cancel_order(sym, order_id=pos.exit_order_id)
            except ArcusError:
                pass   # zaten dolmus/iptal olmus olabilir
            pos.exit_order_id = None
            if self._position_size(sym) == 0:
                self._on_closed(sym)
                return
            if self._try_ioc_close(sym, pos):
                return
            self._place_resting_exit(sym, pos)

    def _on_closed(self, sym, reason: str | None = None):
        pos = self.positions.pop(sym, None)
        if not pos:
            return
        try:
            self.client.cancel_all_orders(sym)   # artakalan emir temizligi
        except ArcusError:
            pass
        try:
            pnl = self._equity() - pos.equity_at_open   # yaklasik (cross hesap)
        except ArcusError:
            pnl = 0.0
        self.total_pnl += pnl
        if pnl >= 0:
            self.wins += 1
        self.notify(self._msg(
            "position_closed", sym=sym,
            reason=reason or pos.close_reason or self._msg("sl_tp_default"),
            pnl=pnl, total=self.total_pnl, trades=self.trades, wins=self.wins))
        self.warned_external.discard(sym)

    # ---------- durum ----------
    def snapshot(self) -> dict:
        """Panel icin makine-okur durum (state.json'a yazilir)."""
        try:
            eq = self._equity()
        except ArcusError:
            eq = None
        return {
            "ts": time.time(),
            "base": self.cfg.base,
            "equity": eq,
            "day_start_equity": self.day_start_equity,
            "halted_today": self.halted_today,
            "symbols": self.cfg.symbols,
            "timeframe": self.cfg.timeframe,
            "leverage": self.cfg.leverage,
            "margin_usd": self.cfg.margin_usd,
            "positions": {sym: {"side": p.side, "entry": p.entry, "qty": p.qty,
                                "sl": p.sl, "tp": p.tp, "closing": p.closing,
                                "server_tpsl": p.server_tpsl,
                                "opened_ts": p.opened_ts}
                          for sym, p in self.positions.items()},
            "last_signal": self.last_signal,
            "trades": self.trades,
            "wins": self.wins,
            "total_pnl": self.total_pnl,
        }

    def status_text(self) -> str:
        try:
            eq = self._equity()
        except ArcusError:
            eq = 0.0
        lines = [f"Equity: {eq:.2f} USD | Gunluk halt: {self.halted_today}",
                 f"Semboller: {', '.join(self.cfg.symbols)}"]
        for sym, p in self.positions.items():
            extra = " (kapanis surecinde)" if p.closing else ""
            lines.append(f"  {sym}: {p.side.upper()} @ {p.entry:.6g} "
                         f"(SL {p.sl:.6g} / TP {p.tp:.6g}){extra}")
        if not self.positions:
            lines.append("Acik pozisyon: yok")
        lines.append(f"Istatistik: {self.trades} islem | PnL {self.total_pnl:+.2f} USD")
        return "\n".join(lines)
