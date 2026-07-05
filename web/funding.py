"""Tek tik testnet fonlama.

Sponsor cuzdan (ana bot cuzdani) kullaniciya gas gonderir; kullanici cuzdani
USDG mint -> approve -> initiateDeposit yapar. Arka plan is parcaciginda kosar,
durumu fund_status[user_id] uzerinden izlenir.
"""
import threading
import time
import json
import urllib.request

from eth_account import Account
from eth_utils import keccak, to_checksum_address

RPC = "https://rpc.testnet.chain.robinhood.com"
CHAIN_ID = 46630
USDG = "0x022f49dbd588908b5a1805886c2107f0315223b4"
PROXY = "0x10096bec721173f70add303affc235d7c99fbfd4"
GAS_WEI = int(0.004e18)          # kullanici basina sponsor gas
MAX_FUND_USD = 25_000

fund_status: dict[int, dict] = {}   # user_id -> {stage, error, done, ts}


def rpc(method, params):
    req = urllib.request.Request(RPC, method="POST",
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                         "params": params}).encode(),
        headers={"Content-Type": "application/json",
                 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=25) as r:
        out = json.loads(r.read())
    if "error" in out:
        raise RuntimeError(f"{method}: {out['error']}")
    return out["result"]


def sel(signature):
    return keccak(text=signature)[:4]


def enc_addr(a):
    return bytes(12) + bytes.fromhex(a[2:].lower())


def enc_uint(n):
    return int(n).to_bytes(32, "big")


def balance(addr) -> int:
    return int(rpc("eth_getBalance", [addr, "latest"]), 16)


def send_tx(acct, to, data=b"", value=0):
    nonce = int(rpc("eth_getTransactionCount", [acct.address, "pending"]), 16)
    gas_price = int(rpc("eth_gasPrice", []), 16)
    tx = {"nonce": nonce, "to": to_checksum_address(to), "value": value,
          "data": data, "gasPrice": int(gas_price * 1.5), "chainId": CHAIN_ID}
    tx["gas"] = int(int(rpc("eth_estimateGas",
        [{"from": acct.address, "to": tx["to"], "value": hex(value),
          "data": "0x" + data.hex()}]), 16) * 1.5)
    signed = acct.sign_transaction(tx)
    tx_hash = rpc("eth_sendRawTransaction", ["0x" + signed.raw_transaction.hex()])
    for _ in range(45):
        rec = rpc("eth_getTransactionReceipt", [tx_hash])
        if rec is not None:
            if int(rec["status"], 16) != 1:
                raise RuntimeError(f"tx revert: {tx_hash}")
            return tx_hash
        time.sleep(2)
    raise TimeoutError(f"tx onaylanmadi: {tx_hash}")


def fund_user_async(user_id: int, user_key_hex: str, sponsor_key_hex: str,
                    amount_usd: int):
    """Arka planda fonlar. Ayni kullanici icin es zamanli ikinci istegi reddet."""
    st = fund_status.get(user_id)
    if st and not st.get("done") and not st.get("error") and \
       time.time() - st.get("ts", 0) < 300:
        return False
    fund_status[user_id] = {"stage": "gas", "error": None, "done": False,
                            "ts": time.time()}

    def run():
        st = fund_status[user_id]
        try:
            user = Account.from_key(user_key_hex)
            amount = int(amount_usd) * 10**6
            if balance(user.address) < GAS_WEI // 2:
                sponsor = Account.from_key(sponsor_key_hex)
                if balance(sponsor.address) < GAS_WEI * 2:
                    raise RuntimeError("sponsor gas tukendi — faucet'ten doldurun")
                send_tx(sponsor, user.address, value=GAS_WEI)
            st["stage"] = "mint"
            send_tx(user, USDG, sel("mint(address,uint256)")
                    + enc_addr(user.address) + enc_uint(amount))
            st["stage"] = "approve"
            send_tx(user, USDG, sel("approve(address,uint256)")
                    + enc_addr(PROXY) + enc_uint(amount))
            st["stage"] = "deposit"
            send_tx(user, PROXY,
                    sel("initiateDeposit(address,uint16,address,uint256)")
                    + enc_addr(user.address) + enc_uint(0)
                    + enc_addr(USDG) + enc_uint(amount))
            st["stage"] = "credit"     # borsa krediyi ~1 dk icinde isler
            st["done"] = True
        except Exception as e:
            st["error"] = str(e)

    threading.Thread(target=run, daemon=True, name=f"fund-{user_id}").start()
    return True
