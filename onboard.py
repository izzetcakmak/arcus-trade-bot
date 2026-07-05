"""Testnet onboarding: yeni test cuzdani + Ed25519 API key uretir ve Arcus'a kaydeder.

Uyari: Uretilen cuzdan SADECE testnet icindir. .env dosyasina yazilir.
Calistirma: python onboard.py  (mevcut .env varsa uzerine yazmaz; --force ile yazar)
"""

import os
import sys
import time

from cryptography.hazmat.primitives.asymmetric import ed25519
from eth_account import Account
from eth_account.messages import encode_defunct

from arcus.client import ArcusClient, canonical, TESTNET_BASE

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")


def main():
    if os.path.exists(ENV_PATH) and "--force" not in sys.argv:
        print(f"{ENV_PATH} zaten var. Uzerine yazmak icin: python onboard.py --force")
        sys.exit(1)

    # 1) Ed25519 API anahtari (lokal uretim — sunucu yalnizca public yarisini gorur)
    api_priv = ed25519.Ed25519PrivateKey.generate()
    api_priv_hex = api_priv.private_bytes_raw().hex()
    api_key = api_priv.public_key().public_bytes_raw().hex()

    # 2) Testnet cuzdani (master Ethereum adresi)
    wallet = Account.create()
    print(f"cuzdan     : {wallet.address}")
    print(f"api key    : {api_key}")

    # 3) createApiKey — EIP-191 imzasi cuzdandan
    valid_until = int(time.time() * 1000) + 170 * 86_400_000  # [now+1g, now+180g] araligi
    msg = canonical({"apiWalletName": "arcus-trade-bot",
                     "apiWalletPublicKey": api_key,
                     "validUntil": valid_until})
    sig = wallet.sign_message(encode_defunct(primitive=msg))

    client = ArcusClient(base=TESTNET_BASE)
    created = client.call("POST", "/v1/createApiKey", {
        "address": wallet.address,
        "publicKey": api_key,
        "apiWalletName": "arcus-trade-bot",
        "validUntil": valid_until,
        "signature": {"r": hex(sig.r), "s": hex(sig.s), "v": hex(sig.v)},
    })
    account_index = created.get("accountIndex", 0)
    print(f"createApiKey yaniti: {created}")

    # 4) Anahtarin aktiflesmesini bekle
    reader = ArcusClient(base=TESTNET_BASE, address=wallet.address)
    for i in range(90):
        try:
            keys = reader.api_keys().get("apiKeys", [])
            if any(k.get("apiKey") == api_key for k in keys):
                print(f"anahtar aktif ({i + 1}. denemede)")
                break
        except Exception:
            pass
        time.sleep(1)
    else:
        print("UYARI: anahtar 90 sn icinde listede gorunmedi — biraz sonra tekrar dene")

    # 5) .env yaz
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write(
            f"ARCUS_BASE={TESTNET_BASE}\n"
            f"WALLET_ADDRESS={wallet.address}\n"
            f"WALLET_PRIVATE_KEY={wallet.key.hex()}\n"
            f"ARCUS_API_PRIVKEY={api_priv_hex}\n"
            f"ARCUS_API_KEY={api_key}\n"
            f"ARCUS_ACCOUNT_INDEX={account_index}\n"
        )
    print(f".env yazildi: {ENV_PATH}")
    print()
    print("Sonraki adim — hesabi fonla (iki secenek):")
    print("  a) python fund_testnet.py   (on-chain; cuzdanda az miktar RH-testnet ETH ister)")
    print("  b) Arcus testnet web app'ine bu cuzdani import edip 'Testnet Deposit' butonuna bas")


if __name__ == "__main__":
    main()
