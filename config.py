"""Ayarlari .env dosyasindan okur."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _f(key, default):
    try:
        return float(os.getenv(key, default))
    except (TypeError, ValueError):
        return float(default)


def _i(key, default):
    try:
        return int(float(os.getenv(key, default)))
    except (TypeError, ValueError):
        return int(default)


@dataclass
class Config:
    base: str
    address: str
    api_privkey: str
    account_index: int
    symbols: list          # Arcus marketDisplayName listesi, or. BTC-USD
    timeframe: str
    leverage: int
    margin_usd: float      # islem basina teminat (USD)
    sl_pct: float          # stop-loss: TEMINATIN yuzdesi
    tp_pct: float          # take-profit: TEMINATIN yuzdesi
    max_daily_loss_pct: float
    adx_threshold: float
    loop_interval_sec: int
    telegram_token: str
    telegram_chat_id: str
    dashboard_url: str     # bildirimlere eklenen panel linki (bos = ekleme)

    @classmethod
    def load(cls) -> "Config":
        load_dotenv(override=True)   # .env degisiklikleri sicak-yenilemede gorunsun
        symbols = [s.strip().upper() for s in
                   os.getenv("SYMBOLS", "BTC-USD,ETH-USD,SOL-USD").split(",") if s.strip()]
        cfg = cls(
            base=os.getenv("ARCUS_BASE", "https://api.testnet.arcus.xyz").strip(),
            address=os.getenv("WALLET_ADDRESS", "").strip(),
            api_privkey=os.getenv("ARCUS_API_PRIVKEY", "").strip(),
            account_index=_i("ARCUS_ACCOUNT_INDEX", 0),
            symbols=symbols,
            timeframe=os.getenv("TIMEFRAME", "15m").strip(),
            leverage=_i("LEVERAGE", 3),
            margin_usd=_f("MARGIN_USD", 100.0),
            sl_pct=_f("SL_PCT", 30.0),
            tp_pct=_f("TP_PCT", 60.0),
            max_daily_loss_pct=_f("MAX_DAILY_LOSS_PCT", 5.0),
            adx_threshold=_f("ADX_THRESHOLD", 20.0),
            loop_interval_sec=_i("LOOP_INTERVAL_SEC", 30),
            telegram_token=os.getenv("TELEGRAM_TOKEN", "").strip(),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", "").strip(),
            dashboard_url=os.getenv("DASHBOARD_URL",
                                    "http://192.168.1.100:8377").strip(),
        )
        missing = [k for k, v in (("WALLET_ADDRESS", cfg.address),
                                  ("ARCUS_API_PRIVKEY", cfg.api_privkey)) if not v]
        if missing:
            raise SystemExit("Eksik ayar: " + ", ".join(missing) +
                             " — once 'python onboard.py' calistir.")
        return cfg
