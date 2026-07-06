# I'm #32,000 on the Arcus Waitlist — So I Built a Multi-User Trading Bot for It While Waiting

*How a weekend of API archaeology on dYdX's new exchange turned into a full SaaS: Google login, auto-custody wallets, one-click funding, a 41-market trading engine and Telegram alerts — all on testnet, all open source.*

---

**TL;DR:** [Arcus](https://arcus.xyz) is the new DEX built by dYdX Labs on Robinhood Chain — stock tokens and perpetuals, 24/7. Perps are waitlisted (I'm somewhere around #32,000), but the **testnet is open to everyone**. So instead of waiting, I built [**ArcusBot**](https://www.atradebot.xyz): a website where anyone can sign in with Google, get a trading wallet, fund it with $10,000 of testnet collateral in one click, pick a risk profile and let a multi-signal strategy trade 41 markets for them. This is the story, including the three invisible-character bugs that almost broke me.

*(Video walkthrough: **https://youtu.be/xqTsFjYLrGc**)*

---

## Why Arcus?

Arcus pairs two things that rarely live on the same venue: **tokenized stocks** (spot, zero fee) and **cross-margined perpetuals** across crypto, equities, commodities and indices — up to 50× leverage, on Robinhood Chain. It's built by dYdX Labs, which means the API was clearly designed by people who have operated a real derivatives exchange:

- **REST + WebSocket**, with a clean OpenAPI/AsyncAPI spec
- **Ed25519 API keys** you generate locally — the server only ever sees the public half; registration is authorized by one EIP-191 signature from your master wallet
- Two signing schemes: orders sign a *compact, key-sorted typed payload* (`{"ad":…,"ai":…,"ct":…}`), everything else signs `timestamp + action + canonical_json(body)`
- Prices and sizes travel as **integer ticks and quantums** — no float ambiguity anywhere

The testnet is a full paper-trading universe: 8 crypto perps, 26 stock perps (AAPL, NVDA, TSLA…), 3 commodities, 4 indices. The collateral token has an **open mint**, so funding an account is a permissionless three-transaction dance: `mint → approve → initiateDeposit`.

## Step 1: A client, an order, a cancel

The first milestone was boring on purpose: generate keys, register them, place one limit order, see it on the book, cancel it. It worked on the first try — rare enough to celebrate.

Then the testnet started teaching me things the docs didn't say:

**Lesson 1 — `goodTilTime` is always required.** The docs say it's ignored for IOC orders. The validator disagrees: every order needs an expiry at least one month in the future, even ones that live for milliseconds.

**Lesson 2 — TP/SL orders aren't live yet.** The exchange has a beautiful position-level take-profit/stop-loss design (`isPositionTPSL` — it resizes to your whole position at trigger time). It also returns `501 NotImplemented` on testnet. My engine now tries the server-side TPSL first and silently falls back to monitoring the mark price itself, closing positions bot-side. When Arcus ships the feature, the bot upgrades itself.

**Lesson 3 — phantom liquidity is real.** The order book showed a bid of 1.12 BTC. My sell IOC returned `IOC_CANCELED` — seventeen times in a row. The book was displaying **stale orders that only expire at match time**: they look alive until you touch them. The fix shaped my whole execution model: try a few increasingly aggressive IOC orders, then park a resting GTT order near the oracle price and reprice it every 60 seconds until it fills. On a bursty-liquidity testnet, patience is an order type.

## Step 2: From script to product

The single-user bot (a port of my Binance futures strategy — EMA 9/21/200 + ADX + RSI + MACD on 15-minute candles) ran fine from my terminal with a small monitoring dashboard. But the interesting question was: *could anyone use this?*

The product version — [**atradebot.xyz**](https://www.atradebot.xyz) — does five things:

1. **Sign in with Google.** No forms, no passwords.
2. **Instant wallet.** A dedicated testnet wallet is generated server-side, registered with Arcus via `createApiKey`, encrypted at rest (Fernet), and its private keys are shown to the user **exactly once** — a second reveal request is refused by the server.
3. **One-click funding.** A sponsor wallet sends a little gas to the new wallet; the backend then mints test USDG and calls `initiateDeposit`. About sixty seconds later the account shows $10,000.
4. **Risk, your way.** Three presets (Low 2×/$50, Balanced 3×/$100, High 5×/$200) or fully custom leverage, margin, stop-loss, take-profit, daily loss limit — plus a category-tabbed picker across all 41 markets. Settings hot-apply to the running engine within ~30 seconds, no restart.
5. **Telegram alerts.** A deep-link binds your chat; every open, close and daily-halt event arrives as a personal message, in your language — the whole product is bilingual (EN/TR), down to the engine's own event log.

## The architecture

```
Browser ──► Vercel (FastAPI, serverless)  ──► Neon Postgres ◄── Worker (engine)
              auth · wallets · settings         users, wallets,     multi-user trading
              funding queue · bot state         queues, state       funding pipeline
                                                                    Telegram poller
```

The split matters because a trading engine is everything serverless is not: an infinite loop with 30-second ticks, long-polling Telegram, and a funding pipeline that babysits on-chain transactions. So the **site lives on Vercel** (always up, custom domain, SSL) and the **worker runs anywhere** — currently a PC, eventually a $5 container. They only talk through the database: the API writes funding requests and settings; the worker writes engine snapshots and event feeds.

## The bugs I'll remember

Three separate production incidents, all caused by **invisible characters**:

1. Google returned `401 invalid_client`. The client ID was correct… except for a **U+FEFF byte-order mark** that a PowerShell pipe had prepended when setting the environment variable. Google saw `﻿9194…` and shrugged.
2. Fixing that, I re-piped the Fernet master key with `cut -d= -f2` — which happily ate the key's **trailing base64 `=` padding**. The whole site 500'd on import.
3. The Telegram module read its token only from `.env` — a file that doesn't exist on Vercel. "telegram bot not configured," said production, smugly.

Every env read in the codebase now strips BOMs and carriage returns, checks `os.environ` first, and I check string lengths before piping secrets anywhere. Cheap lessons, as testnet lessons always are.

## What's next

- **AI position commentary** via Vercel AI Gateway — a two-sentence "why did the bot enter here?" attached to every Telegram alert
- Moving the worker to a cloud container for true 24/7
- And, one day, my Arcus perps cohort actually opening — at which point the only change is a base URL

## Try it

- **Live (testnet, free):** [atradebot.xyz](https://www.atradebot.xyz)
- **Code (30+ commits of history):** [github.com/izzetcakmak/arcus-trade-bot](https://github.com/izzetcakmak/arcus-trade-bot)
- **Video walkthrough:** https://youtu.be/xqTsFjYLrGc

*Everything here runs on testnet with paper money. Nothing in this post is investment advice — it's an engineering story about a very patient waitlist position.*
