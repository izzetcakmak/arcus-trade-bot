"""
Strateji: 15 dakikalik mumlarda cok-sinyalli trend takip sistemi.
(trade-bot'tan port — Arcus'ta df SADECE kapanmis mumlardan olusur,
bu yuzden son kapanmis mum -1, ondan onceki -2 indeksindedir.)

Mantik:
  - EMA 9 / EMA 21  : kisa vade yon (kesisim = momentum degisimi)
  - EMA 200         : ana trend filtresi (fiyat ustundeyse sadece AL, altindaysa sadece SAT)
  - ADX             : trend gucu. Zayifsa (yatay piyasa) hic islem acmaz.
  - RSI             : asiri alim/satim bolgesinde girisi engeller.
  - MACD histogram  : momentum teyidi.
"""
from dataclasses import dataclass

import pandas as pd

import indicators as ind


@dataclass
class Signal:
    side: str | None        # "long", "short" veya None
    reason: str
    price: float
    atr: float
    rsi: float
    adx: float


def build_frame(ohlcv: list) -> pd.DataFrame:
    """ohlcv: [ts, open, high, low, close, volume] listeleri (kapanmis mumlar)."""
    df = pd.DataFrame(ohlcv, columns=["ts", "open", "high", "low", "close", "volume"])
    df["ema9"] = ind.ema(df["close"], 9)
    df["ema21"] = ind.ema(df["close"], 21)
    df["ema200"] = ind.ema(df["close"], 200)
    df["rsi"] = ind.rsi(df["close"], 14)
    df["atr"] = ind.atr(df["high"], df["low"], df["close"], 14)
    df["adx"] = ind.adx(df["high"], df["low"], df["close"], 14)
    _, _, df["macd_hist"] = ind.macd(df["close"])
    return df


def evaluate(df: pd.DataFrame, adx_threshold: float) -> Signal:
    """Son kapanmis mum (-1) uzerinden sinyal uretir."""
    if len(df) < 205:
        return Signal(None, "Yetersiz veri", 0, 0, 0, 0)

    c = df.iloc[-1]      # son kapanmis mum
    p = df.iloc[-2]      # ondan onceki mum (kesisim icin)

    price = float(c["close"])
    atr_v = float(c["atr"])
    rsi_v = float(c["rsi"])
    adx_v = float(c["adx"])

    trend_up = price > c["ema200"]
    trend_down = price < c["ema200"]
    cross_up = p["ema9"] <= p["ema21"] and c["ema9"] > c["ema21"]
    cross_down = p["ema9"] >= p["ema21"] and c["ema9"] < c["ema21"]
    strong = adx_v >= adx_threshold

    if trend_up and cross_up and strong and rsi_v < 70 and c["macd_hist"] > 0:
        return Signal("long", "EMA9>EMA21 kesisim + fiyat EMA200 ustu + ADX guclu + MACD+",
                      price, atr_v, rsi_v, adx_v)

    if trend_down and cross_down and strong and rsi_v > 30 and c["macd_hist"] < 0:
        return Signal("short", "EMA9<EMA21 kesisim + fiyat EMA200 alti + ADX guclu + MACD-",
                      price, atr_v, rsi_v, adx_v)

    return Signal(None, f"Sinyal yok (ADX={adx_v:.0f}, RSI={rsi_v:.0f})", price, atr_v, rsi_v, adx_v)
