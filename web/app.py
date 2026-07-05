"""ArcusBot Web — cok kullanicili testnet trade botu (Faz 1).

Calistirma (proje kokunden):
    python -m uvicorn web.app:app --host 0.0.0.0 --port 8378

Giris: GOOGLE_CLIENT_ID tanimliysa Google Sign-In; degilse DEV login (e-posta).
Cuzdan: sunucu uretir, Arcus'a kaydeder, key'leri SADECE BIR KEZ gosterir,
veritabaninda Fernet ile sifreli tutar.
"""
import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from cryptography.hazmat.primitives.asymmetric import ed25519
from dotenv import dotenv_values
from eth_account import Account
from eth_account.messages import encode_defunct
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse

from arcus.client import ArcusClient, ArcusError, canonical
from web import db, security
from web.pages import LOGIN_PAGE, APP_PAGE

ENV = dotenv_values(os.path.join(BASE_DIR, ".env"))
ARCUS_BASE = ENV.get("ARCUS_BASE", "https://api.testnet.arcus.xyz")
GOOGLE_CLIENT_ID = (ENV.get("GOOGLE_CLIENT_ID") or "").strip()

app = FastAPI(title="ArcusBot Web")
db.init()

SETTING_LIMITS = {
    "leverage": (1, 50, True), "margin_usd": (5, 1_000_000, False),
    "sl_pct": (1, 95, False), "tp_pct": (1, 500, False),
    "max_daily_loss_pct": (1, 100, False), "adx_threshold": (0, 100, False),
}

_public_client = ArcusClient(base=ARCUS_BASE)


# ------------------------------------------------------------------ yardimci

def current_user(request: Request) -> dict | None:
    token = request.cookies.get("session", "")
    uid = security.read_session(token) if token else None
    return db.get_user(uid) if uid else None


def user_client(user_id: int) -> ArcusClient | None:
    w = db.get_wallet(user_id)
    if not w:
        return None
    return ArcusClient(base=ARCUS_BASE, address=w["address"],
                       account_index=w["account_index"],
                       api_privkey_hex=security.decrypt(w["enc_api_key"]))


def set_session(resp: Response, user_id: int):
    resp.set_cookie("session", security.make_session(user_id),
                    max_age=security.SESSION_TTL, httponly=True, samesite="lax")


# -------------------------------------------------------------------- sayfa

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    user = current_user(request)
    if not user:
        page = LOGIN_PAGE.replace("__GOOGLE_CLIENT_ID__", GOOGLE_CLIENT_ID)
        page = page.replace("__DEV_MODE__", "0" if GOOGLE_CLIENT_ID else "1")
        return HTMLResponse(page)
    return HTMLResponse(APP_PAGE)


# --------------------------------------------------------------------- auth

@app.post("/auth/dev")
async def auth_dev(request: Request):
    if GOOGLE_CLIENT_ID:
        return JSONResponse({"error": "dev login disabled"}, status_code=403)
    body = await request.json()
    email = str(body.get("email", "")).strip().lower()
    if "@" not in email or len(email) > 120:
        return JSONResponse({"error": "invalid email"}, status_code=400)
    user = db.get_or_create_user(email)
    resp = JSONResponse({"ok": True})
    set_session(resp, user["id"])
    return resp


@app.post("/auth/google")
async def auth_google(request: Request):
    if not GOOGLE_CLIENT_ID:
        return JSONResponse({"error": "google login not configured"}, status_code=403)
    body = await request.json()
    credential = body.get("credential", "")
    try:
        from google.auth.transport import requests as grequests
        from google.oauth2 import id_token as gid
        info = gid.verify_oauth2_token(credential, grequests.Request(),
                                       GOOGLE_CLIENT_ID)
        email = info["email"].lower()
        if not info.get("email_verified", False):
            return JSONResponse({"error": "email not verified"}, status_code=403)
    except Exception as e:
        return JSONResponse({"error": f"token verify failed: {e}"}, status_code=401)
    user = db.get_or_create_user(email, info.get("name", ""), info.get("sub", ""))
    resp = JSONResponse({"ok": True})
    set_session(resp, user["id"])
    return resp


@app.post("/logout")
def logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("session")
    return resp


# ---------------------------------------------------------------------- api

@app.get("/api/me")
def api_me(request: Request):
    user = current_user(request)
    if not user:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    w = db.get_wallet(user["id"])
    s = db.get_settings(user["id"])
    return {"email": user["email"], "name": user["name"],
            "wallet": ({"address": w["address"], "revealed": bool(w["revealed"])}
                       if w else None),
            "settings": ({k: s[k] for k in
                          ("bot_active", "symbols", "leverage", "margin_usd",
                           "sl_pct", "tp_pct", "max_daily_loss_pct",
                           "adx_threshold")} if s else None),
            "telegram_linked": bool(s and s.get("telegram_chat_id"))}


@app.post("/api/wallet/create")
def wallet_create(request: Request):
    user = current_user(request)
    if not user:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    if db.get_wallet(user["id"]):
        return JSONResponse({"error": "wallet already exists"}, status_code=409)

    wallet = Account.create()
    api_priv = ed25519.Ed25519PrivateKey.generate()
    api_priv_hex = api_priv.private_bytes_raw().hex()
    api_pub = api_priv.public_key().public_bytes_raw().hex()

    valid_until = int(time.time() * 1000) + 170 * 86_400_000
    msg = canonical({"apiWalletName": "arcusbot-web",
                     "apiWalletPublicKey": api_pub, "validUntil": valid_until})
    sig = wallet.sign_message(encode_defunct(primitive=msg))
    try:
        created = _public_client.call("POST", "/v1/createApiKey", {
            "address": wallet.address, "publicKey": api_pub,
            "apiWalletName": "arcusbot-web", "validUntil": valid_until,
            "signature": {"r": hex(sig.r), "s": hex(sig.s), "v": hex(sig.v)}})
    except ArcusError as e:
        return JSONResponse({"error": f"Arcus registration failed: {e}"},
                            status_code=502)

    db.save_wallet(user["id"], wallet.address,
                   security.encrypt(wallet.key.hex()),
                   security.encrypt(api_priv_hex),
                   api_pub, created.get("accountIndex", 0))
    return {"ok": True, "address": wallet.address}


@app.get("/api/wallet/reveal")
def wallet_reveal(request: Request):
    """Key'leri BIR KEZ dondurur; ikinci cagri reddedilir."""
    user = current_user(request)
    if not user:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    w = db.get_wallet(user["id"])
    if not w:
        return JSONResponse({"error": "no wallet"}, status_code=404)
    if w["revealed"]:
        return JSONResponse({"error": "keys were already revealed once"},
                            status_code=403)
    db.mark_revealed(user["id"])
    return {"address": w["address"],
            "wallet_private_key": security.decrypt(w["enc_wallet_key"]),
            "arcus_api_private_key": security.decrypt(w["enc_api_key"])}


@app.get("/api/account")
def api_account(request: Request):
    user = current_user(request)
    if not user:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    c = user_client(user["id"])
    if not c:
        return JSONResponse({"error": "no wallet"}, status_code=404)
    out = {"funded": False, "equity": None, "positions": []}
    try:
        acct = c.account()
        out["funded"] = True
        out["equity"] = float(acct.get("equity", 0))
        out["freeCollateral"] = float(acct.get("freeCollateral", 0))
        for p in (c.positions().get("positions") or {}).values():
            if float(p.get("size", 0) or 0) != 0:
                out["positions"].append({
                    "market": p["marketDisplayName"], "side": p["side"],
                    "size": p["size"], "entry": p.get("averageEntryPrice"),
                    "upnl": float(p.get("unrealizedPnl", 0) or 0)})
    except ArcusError as e:
        if e.status != 404:
            return JSONResponse({"error": str(e)}, status_code=502)
    return out


@app.post("/api/settings")
async def api_settings(request: Request):
    user = current_user(request)
    if not user:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    body = await request.json()
    changes = {}
    for field, (lo, hi, is_int) in SETTING_LIMITS.items():
        if field in body:
            try:
                val = float(body[field])
            except (TypeError, ValueError):
                return JSONResponse({"error": f"{field}: not a number"}, status_code=400)
            if not (lo <= val <= hi):
                return JSONResponse({"error": f"{field}: must be in [{lo}, {hi}]"},
                                    status_code=400)
            changes[field] = int(val) if is_int else val
    if "symbols" in body:
        syms = [s.strip().upper() for s in str(body["symbols"]).split(",") if s.strip()]
        if not syms:
            return JSONResponse({"error": "symbols: empty"}, status_code=400)
        try:
            known = {m["marketDisplayName"] for m in _public_client.markets(refresh=True)}
            bad = [s for s in syms if s not in known]
            if bad:
                return JSONResponse({"error": "unknown market(s): " + ", ".join(bad)},
                                    status_code=400)
        except ArcusError:
            pass
        changes["symbols"] = ",".join(syms)
    if not changes:
        return JSONResponse({"error": "nothing to change"}, status_code=400)
    db.update_settings(user["id"], **changes)
    return {"ok": True, "applied": changes}


@app.post("/api/bot/{action}")
def api_bot_toggle(request: Request, action: str):
    user = current_user(request)
    if not user:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    if action not in ("start", "stop"):
        return JSONResponse({"error": "unknown action"}, status_code=400)
    if action == "start" and not db.get_wallet(user["id"]):
        return JSONResponse({"error": "create a wallet first"}, status_code=409)
    db.update_settings(user["id"], bot_active=1 if action == "start" else 0)
    return {"ok": True, "bot_active": action == "start"}
