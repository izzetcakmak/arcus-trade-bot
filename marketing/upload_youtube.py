"""ArcusBot tanitim videosunu @izzetc kanalina yukler (Shorts botunun token'iyla)."""
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

YT_DIR = r"D:\YoutubeKanal"
VIDEO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "arcusbot_intro_en.mp4")

TITLE = ("ArcusBot — Automated Perp Trading on Arcus DEX "
         "(dYdX × Robinhood Chain) | Testnet Demo")

DESCRIPTION = """ArcusBot is an automated perpetuals trading platform built on Arcus — the new DEX by dYdX Labs on Robinhood Chain. Sign in with Google, get an encrypted trading wallet instantly, fund it with $10,000 of testnet collateral in one click, pick a risk profile and let a multi-signal strategy trade 41 markets (crypto, stocks, commodities, indices) for you — with Telegram alerts for every move.

▶ Try it free (testnet): https://www.atradebot.xyz
▶ Source code: https://github.com/izzetcakmak/arcus-trade-bot
▶ Arcus DEX: https://arcus.xyz

⚠️ Testnet only — no real funds. Not investment advice.

Chapters:
0:00 What is ArcusBot?
0:17 Built on Arcus (dYdX × Robinhood Chain)
0:27 Google sign-in & instant wallet
0:37 One-click $10,000 testnet funding
0:45 Risk profiles: Low / Balanced / High
0:56 41 markets: crypto, stocks, commodities, indices
1:05 Start the bot + Telegram alerts
1:14 Try it now"""

TAGS = ["arcus dex", "dydx", "robinhood chain", "trading bot",
        "perpetual futures", "crypto bot", "algorithmic trading", "defi",
        "testnet", "python trading bot", "automated trading"]


def main():
    creds = Credentials.from_authorized_user_file(
        os.path.join(YT_DIR, "youtube_token_izzetc.json"))
    yt = build("youtube", "v3", credentials=creds)
    body = {
        "snippet": {"title": TITLE, "description": DESCRIPTION, "tags": TAGS,
                    "categoryId": "28", "defaultLanguage": "en"},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(VIDEO, mimetype="video/mp4", resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"yukleniyor: %{int(status.progress() * 100)}")
    vid = resp["id"]
    print("YUKLENDI:", f"https://youtu.be/{vid}")


if __name__ == "__main__":
    main()
