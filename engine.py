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
        self._tick_markets: dict[str, dict] = {}   # tick basina taze market verisi

    # ---------- kurulum ----------
    def setup(self):
        valid = []
        for sym in self.cfg.symbols:
            try:
                self.client.market(sym)
            except KeyError:
                self.notify(f"Market bulunamadi, atlandi: {sym}")
                continue
            valid.append(sym)
            try:
                self.client.set_leverage(sym, self.cfg.leverage)
            except ArcusError as e:
                self.notify(f"{sym} kaldirac ayarlanamadi (devam): {e}")
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
        self.notify(f"Motor hazir ({self.cfg.base})\n"
                    f"Semboller: {', '.join(valid)} | TF: {self.cfg.timeframe} | "
                    f"Kaldirac: {self.cfg.leverage}x\n"
                    f"Islem basi teminat: {self.cfg.margin_usd:.0f} USD | "
                    f"SL/TP: teminatin %{self.cfg.sl_pct:.0f}/%{self.cfg.tp_pct:.0f}\n"
                    f"Equity: {eq:.2f} USD")

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
                self.notify(f"Ayar: bilinmeyen market atlandi: {sym}")
        new_cfg.symbols = valid or old.symbols

        changes = []
        for alan, ad in (("leverage", "kaldirac"), ("margin_usd", "teminat"),
                         ("sl_pct", "SL%"), ("tp_pct", "TP%"),
                         ("max_daily_loss_pct", "gunluk limit%"),
                         ("adx_threshold", "ADX")):
            if getattr(new_cfg, alan) != getattr(old, alan):
                changes.append(f"{ad} {getattr(old, alan)} -> {getattr(new_cfg, alan)}")
        if set(new_cfg.symbols) != set(old.symbols):
            changes.append(f"semboller: {', '.join(new_cfg.symbols)}")

        self.cfg = new_cfg
        if any(c.startswith("kaldirac") for c in changes) or \
           set(new_cfg.symbols) - set(old.symbols):
            for sym in new_cfg.symbols:
                try:
                    self.client.set_leverage(sym, new_cfg.leverage)
                except ArcusError as e:
                    self.notify(f"{sym} kaldirac ayarlanamadi: {e}")
        if changes:
            self.notify("AYARLAR GUNCELLENDI (panelden): " + " | ".join(changes))

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
            self.notify(f"Equity okunamadi: {e}")
            return
        self._roll_day(eq)
        if not self.halted_today and self.day_start_equity > 0:
            loss_pct = (self.day_start_equity - eq) / self.day_start_equity * 100
            if loss_pct >= self.cfg.max_daily_loss_pct:
                self.halted_today = True
                self.notify(f"GUNLUK ZARAR LIMITI asildi (%{loss_pct:.1f}). "
                            f"Bugun yeni islem yok; yarin otomatik reset.")
        # izlenen semboller + (listeden cikarilmis olsa da) acik pozisyonlular
        for sym in dict.fromkeys(list(self.cfg.symbols) + list(self.positions)):
            try:
                self._tick_symbol(sym)
            except ArcusError as e:
                self.notify(f"{sym} tick hatasi: {e}")
            except Exception as e:  # tek sembol hatasi donguyu oldurmesin
                self.notify(f"{sym} beklenmeyen hata: {type(e).__name__}: {e}")

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
                    hit = f"SL tetiklendi (bot-tarafi, mark {mark:.6g})"
                elif mark >= tracked.tp:
                    hit = f"TP tetiklendi (bot-tarafi, mark {mark:.6g})"
            else:
                if mark >= tracked.sl:
                    hit = f"SL tetiklendi (bot-tarafi, mark {mark:.6g})"
                elif mark <= tracked.tp:
                    hit = f"TP tetiklendi (bot-tarafi, mark {mark:.6g})"
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
        self.last_signal[sym] = (f"{dt.datetime.now().strftime('%H:%M')} | "
                                 f"fiyat {sig.price:.6g} | "
                                 f"{sig.side.upper() if sig.side else sig.reason}")

        if tracked:
            opp = (tracked.side == "long" and sig.side == "short") or \
                  (tracked.side == "short" and sig.side == "long")
            if opp:
                self._begin_close(sym, tracked, "Ters sinyal geldi")
            return

        if self.halted_today or not self.entries_enabled:
            return
        if size != 0:
            if sym not in self.warned_external:
                self.warned_external.add(sym)
                self.notify(f"{sym}: takip edilmeyen acik pozisyon var; "
                            f"otomatik islem yapilmadi.")
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
            self.notify(f"{sym}: yetersiz equity ({margin:.0f} > {eq:.2f}). Atlandi.")
            return

        qty = self.client.snap_quantity(m, (margin * lev) / mark)
        notional = float(qty) * mark
        if float(qty) <= 0 or notional < float(m.get("minOrderNotional", 0)):
            self.notify(f"{sym}: islem cok kucuk (qty={qty}, notional={notional:.2f}).")
            return

        long = sig.side == "long"
        entry_side = "BUY" if long else "SELL"
        bound = self.client.snap_price(m, mark * (1.02 if long else 0.98))

        r = self.client.place_order(sym, entry_side, dec_str(qty), bound,
                                    order_type="MARKET", tif="IOC")
        filled = Decimal(r.get("filledSize", "0") or "0")
        if r.get("status") != "FILLED" or filled <= 0:
            self.notify(f"{sym}: giris IOC dolmadi "
                        f"({r.get('status')}/{r.get('rejectionReason', '?')}) — "
                        f"kitap bos olabilir, sinyal atlandi.")
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
                self.notify("Not: borsa TPSL emri kabul etmedi (testnette henuz yok) — "
                            "SL/TP bot tarafinda mark fiyatiyla izlenecek.")

        self.positions[sym] = pos
        self.trades += 1
        panel = f"\nPanel: {self.cfg.dashboard_url}" if self.cfg.dashboard_url else ""
        self.notify(f"YENI POZISYON: {sym} {'LONG' if long else 'SHORT'}\n"
                    f"Sebep: {sig.reason}\n"
                    f"Teminat: {margin:.0f} USD x{lev} | Giris~{mark:.6g} | "
                    f"Miktar: {qty_s}\n"
                    f"SL: {sl:.6g} | TP: {tp:.6g} "
                    f"({'borsada' if pos.server_tpsl else 'bot izliyor'})"
                    f"{panel}")

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
        self.notify(f"{sym}: {reason} — IOC dolmadi (likidite yok), "
                    f"dinlenen cikis emri kitapta, dolana kadar yeniden fiyatlanir.")

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
                self.notify(f"{sym} IOC kapatma hatasi: {e}")
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
            self.notify(f"{sym} dinlenen cikis emri konulamadi: {e} — "
                        f"sonraki tick'te yeniden denenecek.")
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
        self.notify(f"POZISYON KAPANDI: {sym} "
                    f"({reason or pos.close_reason or 'SL/TP tetiklendi'})\n"
                    f"Yaklasik PnL: {pnl:+.2f} USD | Toplam: {self.total_pnl:+.2f} | "
                    f"Islem: {self.trades} (W:{self.wins})")
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
