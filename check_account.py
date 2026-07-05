"""Hesap durumu: bakiye, pozisyonlar, acik emirler."""

import json

from dotenv import dotenv_values

from arcus.client import ArcusClient, ArcusError

env = dotenv_values(".env")
client = ArcusClient(base=env["ARCUS_BASE"], address=env["WALLET_ADDRESS"],
                     account_index=env.get("ARCUS_ACCOUNT_INDEX", 0),
                     api_privkey_hex=env["ARCUS_API_PRIVKEY"])

try:
    acct = client.account()
    print("hesap:", json.dumps(acct, indent=2)[:800])
except ArcusError as e:
    if e.status == 404:
        print("Hesapta henuz aktivite yok — once fonla (fund_testnet.py veya web app).")
    else:
        raise
else:
    print("\npozisyonlar:", json.dumps(client.positions(), indent=2)[:800])
    print("\nacik emirler:", json.dumps(client.open_orders(), indent=2)[:800])
