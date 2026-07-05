"""Ilk uctan uca test: BTC-USD'de oracle'in %5 altina GTT limit emri koy,
acik emirlerde gor, sonra iptal et. Gercek dolmasi beklenmez — imza ve
tick/quantum donusumunun dogru calistigini kanitlar."""

import time

from dotenv import dotenv_values

from arcus.client import ArcusClient

env = dotenv_values(".env")
client = ArcusClient(base=env["ARCUS_BASE"], address=env["WALLET_ADDRESS"],
                     account_index=env.get("ARCUS_ACCOUNT_INDEX", 0),
                     api_privkey_hex=env["ARCUS_API_PRIVKEY"])

m = client.market("BTC-USD")
price = client.snap_price(m, float(m["oraclePrice"]) * 0.95)
qty = "0.0001"  # ~%5 alti fiyatla ~6 USD notional (min 5 USD)
print(f"market={m['marketDisplayName']} oracle={m['oraclePrice']} "
      f"emir: BUY {qty} @ {price}")

placed = client.place_order("BTC-USD", "BUY", qty, price, tif="GTT")
print("placed:", placed)
order_id = placed["orderId"]

time.sleep(2)
open_orders = client.open_orders()
print("acik emir sayisi:", len(open_orders.get("orders", open_orders)))

canceled = client.cancel_order("BTC-USD", order_id=order_id)
print("canceled:", canceled)
