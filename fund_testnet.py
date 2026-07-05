"""Testnet hesabini on-chain fonlar: USDG mint -> approve -> initiateDeposit.

Robinhood Chain testnet (chainId 46630). Cuzdanda az miktar RH-testnet ETH (gas)
olmali; yoksa script adresi ve faucet uyarisini basip cikar.

Kullanim: python fund_testnet.py [usd_miktari]   (varsayilan 10000)
Adresler docs'taki testnet parametreleridir ve redeploy'da degisebilir:
https://docs.arcus.xyz/guides/fund-testnet-account
"""

import sys
import time
import json
import urllib.request

from dotenv import dotenv_values
from eth_account import Account
from eth_utils import keccak, to_checksum_address

RPC = "https://rpc.testnet.chain.robinhood.com"
CHAIN_ID = 46630
USDG = "0x022f49dbd588908b5a1805886c2107f0315223b4"
PROXY = "0x10096bec721173f70add303affc235d7c99fbfd4"


def rpc(method, params):
    req = urllib.request.Request(RPC, method="POST",
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                         "params": params}).encode(),
        headers={"Content-Type": "application/json",
                 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=20) as r:
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


def send_tx(acct, to, data):
    nonce = int(rpc("eth_getTransactionCount", [acct.address, "pending"]), 16)
    gas_price = int(rpc("eth_gasPrice", []), 16)
    gas = int(rpc("eth_estimateGas", [{"from": acct.address, "to": to,
                                       "data": "0x" + data.hex()}]), 16)
    tx = {"nonce": nonce, "to": to_checksum_address(to), "value": 0, "data": data,
          "gas": int(gas * 1.5), "gasPrice": int(gas_price * 1.5),
          "chainId": CHAIN_ID}
    signed = acct.sign_transaction(tx)
    tx_hash = rpc("eth_sendRawTransaction", ["0x" + signed.raw_transaction.hex()])
    for _ in range(60):
        rec = rpc("eth_getTransactionReceipt", [tx_hash])
        if rec is not None:
            if int(rec["status"], 16) != 1:
                raise RuntimeError(f"tx revert: {tx_hash}")
            return tx_hash
        time.sleep(2)
    raise TimeoutError(f"tx onaylanamadi: {tx_hash}")


def main():
    amount_usd = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000
    amount = amount_usd * 10**6  # USDG 6 ondalik

    env = dotenv_values(".env")
    acct = Account.from_key(env["WALLET_PRIVATE_KEY"])
    addr = acct.address
    print(f"cuzdan: {addr}, hedef: ${amount_usd:,} USDG")

    assert int(rpc("eth_chainId", []), 16) == CHAIN_ID, "beklenmeyen chain id"
    gas_bal = int(rpc("eth_getBalance", [addr, "latest"]), 16)
    print(f"gas bakiyesi: {gas_bal / 1e18:.6f} RH-testnet ETH")
    if gas_bal == 0:
        print("\nGas yok. Bu adrese az miktar RH-testnet ETH gonder/faucet'ten al:")
        print(f"  {addr}")
        sys.exit(1)

    print("1/3 mint...")
    send_tx(acct, USDG, sel("mint(address,uint256)") + enc_addr(addr) + enc_uint(amount))
    print("2/3 approve...")
    send_tx(acct, USDG, sel("approve(address,uint256)") + enc_addr(PROXY) + enc_uint(amount))
    print("3/3 initiateDeposit...")
    tx = send_tx(acct, PROXY, sel("initiateDeposit(address,uint16,address,uint256)")
                 + enc_addr(addr) + enc_uint(0) + enc_addr(USDG) + enc_uint(amount))
    print(f"deposit tx: {tx}")
    print("Borsa krediyi ~1 dk icinde islemeli. Kontrol: python check_account.py")


if __name__ == "__main__":
    main()
