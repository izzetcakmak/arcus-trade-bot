# arcus-trade-bot

[Arcus](https://arcus.xyz) (dYdX Labs, Robinhood Chain) perp DEX'i icin otomatik trade botu.
Testnet oncelikli: `https://api.testnet.arcus.xyz`. Strateji, `trade-bot`'taki 15 dakikalik
cok-sinyalli trend takip sisteminin (EMA 9/21/200 + ADX + RSI + MACD) portudur.

## Kurulum

```bash
pip install -r requirements.txt
python onboard.py        # test cuzdani + Ed25519 API key uretir, kaydeder, .env yazar
```

## Fonlama (testnet)

Iki yol:

1. **On-chain (programatik):** cuzdanda az miktar RH-testnet ETH (gas) olmali —
   faucet: https://faucet.testnet.chain.robinhood.com/ (24 saatte 0.05 ETH).
   Sonra: `python fund_testnet.py 10000`
2. **Web app:** `.env`'deki `WALLET_PRIVATE_KEY`'i bir cuzdana import edip Arcus testnet
   web app'inde **Testnet Deposit** butonuna bas (~$1.000).

Kontrol: `python check_account.py`

## Kullanim

```bash
python first_order.py    # uctan uca dogrulama: emir koy + iptal et
python bot.py            # otomatik dongu
```

## Ayarlar (.env)

| Anahtar | Varsayilan | Aciklama |
|---|---|---|
| `SYMBOLS` | `BTC-USD,ETH-USD,SOL-USD` | Izlenecek marketler (41 market var: kripto/hisse/emtia/endeks) |
| `TIMEFRAME` | `15m` | Mum periyodu |
| `LEVERAGE` | `3` | Kaldirac |
| `MARGIN_USD` | `100` | Islem basina teminat |
| `SL_PCT` / `TP_PCT` | `30` / `60` | Teminatin yuzdesi olarak stop/kar-al |
| `MAX_DAILY_LOSS_PCT` | `5` | Gunluk zarar limiti (equity) — asilirsa o gun yeni islem yok |
| `ADX_THRESHOLD` | `20` | Trend gucu esigi |
| `LOOP_INTERVAL_SEC` | `30` | Dongu araligi |
| `TELEGRAM_TOKEN` / `TELEGRAM_CHAT_ID` | bos | Doluysa bildirimler Telegram'a da gider |

## Mimari

- `arcus/client.py` — REST istemci: Ed25519 imzalama (Sema 1: typed payload, Sema 2: legacy),
  tick/quantum donusumu, market/candle/pozisyon okuma, emir islemleri
- `strategy.py` + `indicators.py` — sinyal uretimi (saf pandas)
- `engine.py` — pozisyon yonetimi: MARKET(IOC) giris + pozisyon-seviyesi TP/SL
  (`isPositionTPSL`), gunluk zarar limiti, ters sinyalde kapama
- `bot.py` — ana dongu + bildirim
- `docs/` — indirilen Arcus API dokumanlari

## Mainnet'e gecis

Perp waitlist kohortun acildiginda `.env`'de `ARCUS_BASE`'i production URL'ine cevir ve
GERCEK cuzdanla yeniden onboard ol. Once kucuk miktarla test et.
