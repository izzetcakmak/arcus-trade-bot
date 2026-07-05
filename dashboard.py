"""Bot izleme + risk ayar paneli — http://localhost:8377

- state.json (bot kalp atisi) + Arcus API canli verisi
- EN varsayilan arayuz, TR'ye gecis (localStorage'da saklanir)
- Risk ayarlari .env'e yazilir; bot ~30 sn icinde sicak uygular (yeniden baslatma yok)
Telefondan: http://<PC-IP>:8377   Calistirma: python dashboard.py
"""
import json
import os
import re
import time
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from dotenv import dotenv_values

from arcus.client import ArcusClient, ArcusError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(BASE_DIR, "state.json")
LOG_PATH = os.path.join(BASE_DIR, "bot.log")
ENV_PATH = os.path.join(BASE_DIR, ".env")
PORT = 8377

env0 = dotenv_values(ENV_PATH)
client = ArcusClient(base=env0.get("ARCUS_BASE", "https://api.testnet.arcus.xyz"),
                     address=env0.get("WALLET_ADDRESS"),
                     account_index=env0.get("ARCUS_ACCOUNT_INDEX", 0),
                     api_privkey_hex=env0.get("ARCUS_API_PRIVKEY"))

SETTING_LIMITS = {   # env anahtari: (min, max, tam sayi mi)
    "LEVERAGE": (1, 50, True),
    "MARGIN_USD": (5, 1_000_000, False),
    "SL_PCT": (1, 95, False),
    "TP_PCT": (1, 500, False),
    "MAX_DAILY_LOSS_PCT": (1, 100, False),
    "ADX_THRESHOLD": (0, 100, False),
}

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Arcus Trade Bot</title>
<style>
 body{font-family:system-ui,Segoe UI,Roboto,sans-serif;background:#0d1117;color:#e6edf3;
      margin:0 auto;padding:16px;max-width:920px}
 h1{font-size:1.2rem;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
 .dot{width:12px;height:12px;border-radius:50%;display:inline-block}
 .on{background:#3fb950}.off{background:#f85149}
 .lang{margin-left:auto}
 .lang button{background:#21262d;color:#8b949e;border:1px solid #30363d;border-radius:6px;
      padding:4px 10px;cursor:pointer;font-size:.8rem}
 .lang button.act{color:#e6edf3;border-color:#8b949e}
 .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin:14px 0}
 .card{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:12px}
 .card .k{font-size:.72rem;color:#8b949e}.card .v{font-size:1.1rem;font-weight:600;margin-top:4px}
 .pos{color:#3fb950}.neg{color:#f85149}
 table{width:100%;border-collapse:collapse;background:#161b22;border:1px solid #30363d;
       border-radius:10px;overflow:hidden;font-size:.85rem;margin-bottom:14px}
 th,td{padding:8px 10px;text-align:left;border-bottom:1px solid #21262d}
 th{background:#21262d;color:#8b949e;font-weight:500}
 .long{color:#3fb950;font-weight:600}.short{color:#f85149;font-weight:600}
 pre{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:10px;
     font-size:.72rem;overflow-x:auto;white-space:pre-wrap;max-height:220px;overflow-y:auto}
 .muted{color:#8b949e;font-size:.8rem}
 h2{font-size:.95rem;color:#8b949e;margin:18px 0 8px}
 .presets{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-bottom:12px}
 .preset{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:12px;cursor:pointer;text-align:left}
 .preset:hover{border-color:#8b949e}
 .preset.sel{border-color:#3fb950}
 .preset .t{font-weight:600;margin-bottom:4px}
 .preset .d{font-size:.72rem;color:#8b949e;line-height:1.5}
 form{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:14px;
      display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
 label{font-size:.75rem;color:#8b949e;display:block;margin-bottom:4px}
 input{width:100%;box-sizing:border-box;background:#0d1117;color:#e6edf3;border:1px solid #30363d;
       border-radius:6px;padding:8px;font-size:.9rem}
 .full{grid-column:1/-1}
 .btn{background:#238636;color:#fff;border:0;border-radius:6px;padding:10px 18px;
      font-size:.9rem;cursor:pointer}
 .btn:disabled{opacity:.5}
 #msg{margin-top:8px;font-size:.85rem}
 .warn{background:#341a00;border:1px solid #9e6a03;border-radius:8px;padding:10px;
       font-size:.78rem;color:#d29922;margin-bottom:12px}
</style></head><body>
<h1><span id="dot" class="dot off"></span><span data-i>title</span>
 <span class="muted" id="hb"></span>
 <span class="lang"><button id="len" onclick="setLang('en')">EN</button>
 <button id="ltr" onclick="setLang('tr')">TR</button></span></h1>
<div class="cards" id="cards"></div>
<h2 data-i>positions</h2>
<table id="pos"><thead><tr><th>Market</th><th data-i>side</th><th data-i>entry</th>
<th data-i>size</th><th>SL</th><th>TP</th><th data-i>livepnl</th></tr></thead><tbody></tbody></table>
<h2 data-i>signals</h2>
<table id="sig"><thead><tr><th>Market</th><th data-i>status</th></tr></thead><tbody></tbody></table>
<h2 data-i>risk</h2>
<div class="warn" data-i>riskwarn</div>
<div class="presets">
 <button class="preset" id="p_low" onclick="preset('low')">
  <div class="t" data-i>plow</div><div class="d">2x · $50 · SL 20% · TP 40%<br><span data-i>pdaily</span> 3%</div></button>
 <button class="preset" id="p_mid" onclick="preset('mid')">
  <div class="t" data-i>pmid</div><div class="d">3x · $100 · SL 30% · TP 60%<br><span data-i>pdaily</span> 5%</div></button>
 <button class="preset" id="p_high" onclick="preset('high')">
  <div class="t" data-i>phigh</div><div class="d">5x · $200 · SL 40% · TP 80%<br><span data-i>pdaily</span> 10%</div></button>
</div>
<form id="f" onsubmit="return save(event)">
 <div><label data-i>lev</label><input id="s_lev" type="number" min="1" max="50" step="1"></div>
 <div><label data-i>margin</label><input id="s_margin" type="number" min="5" step="1"></div>
 <div><label data-i>sl</label><input id="s_sl" type="number" min="1" max="95" step="1"></div>
 <div><label data-i>tp</label><input id="s_tp" type="number" min="1" max="500" step="1"></div>
 <div><label data-i>daily</label><input id="s_daily" type="number" min="1" max="100" step="0.5"></div>
 <div><label data-i>adx</label><input id="s_adx" type="number" min="0" max="100" step="1"></div>
 <div class="full"><label data-i>symbols</label>
  <input id="s_sym" list="mkts" placeholder="BTC-USD,ETH-USD,SOL-USD"><datalist id="mkts"></datalist></div>
 <div class="full"><button class="btn" id="savebtn" type="submit" data-i>save</button>
  <div id="msg"></div></div>
</form>
<h2 data-i>events</h2>
<pre id="log">...</pre>
<div class="muted"><span data-i>foot</span></div>
<script>
var I18N = {
 en:{title:'Arcus Trade Bot', running:'RUNNING (last tick {s}s ago)', offline:'BOT OFFLINE',
     nostate:'BOT OFFLINE (no state file)',
     equity:'Equity', daypnl:'Daily PnL', totpnl:'Total PnL', trades:'Trades (W)',
     levcard:'Leverage / Margin', halt:'Daily Halt', yes:'YES', no:'no',
     positions:'Open Positions', side:'Side', entry:'Entry', size:'Size', livepnl:'Live PnL',
     nopos:'no open positions', signals:'Latest Signal Checks', status:'Status',
     nosig:'no evaluations yet (waiting for first candle close)',
     risk:'Risk Settings',
     riskwarn:'Higher leverage and larger margin mean faster losses as well as faster gains. '+
              'These settings apply to NEW positions within ~30 s; open positions keep their '+
              'original SL/TP. Testnet = play money, experiment freely.',
     plow:'Low Risk', pmid:'Balanced', phigh:'High Risk', pdaily:'daily limit',
     lev:'Leverage (x)', margin:'Margin per trade ($)', sl:'Stop-loss (% of margin)',
     tp:'Take-profit (% of margin)', daily:'Max daily loss (%)', adx:'ADX threshold',
     symbols:'Symbols (comma separated)', save:'Save Settings',
     saved:'Saved — the bot applies it within ~30 s (next tick).',
     err:'Error: ', events:'Events Log', foot:'auto-refresh every 10 s · testnet'},
 tr:{title:'Arcus Trade Bot', running:'ÇALIŞIYOR (son tick {s} sn önce)', offline:'BOT KAPALI',
     nostate:'BOT KAPALI (durum dosyası yok)',
     equity:'Equity', daypnl:'Günlük PnL', totpnl:'Toplam PnL', trades:'İşlem (W)',
     levcard:'Kaldıraç / Teminat', halt:'Günlük Halt', yes:'EVET', no:'hayır',
     positions:'Açık Pozisyonlar', side:'Yön', entry:'Giriş', size:'Miktar', livepnl:'Canlı PnL',
     nopos:'açık pozisyon yok', signals:'Son Sinyal Değerlendirmeleri', status:'Durum',
     nosig:'henüz değerlendirme yok (ilk mum kapanışı bekleniyor)',
     risk:'Risk Ayarları',
     riskwarn:'Yüksek kaldıraç ve büyük teminat, kazancı olduğu kadar kaybı da hızlandırır. '+
              'Ayarlar ~30 sn içinde YENİ pozisyonlara uygulanır; açık pozisyonların SL/TP\\'si '+
              'değişmez. Testnet = oyun parası, gönül rahatlığıyla dene.',
     plow:'Düşük Risk', pmid:'Dengeli', phigh:'Yüksek Risk', pdaily:'günlük limit',
     lev:'Kaldıraç (x)', margin:'İşlem başı teminat ($)', sl:'Stop-loss (teminatın %\\'si)',
     tp:'Take-profit (teminatın %\\'si)', daily:'Günlük azami zarar (%)', adx:'ADX eşiği',
     symbols:'Semboller (virgülle)', save:'Ayarları Kaydet',
     saved:'Kaydedildi — bot ~30 sn içinde (bir sonraki tick) uygular.',
     err:'Hata: ', events:'Son Olaylar', foot:'10 sn\\'de bir yenilenir · testnet'}};
var PRESETS = {low:{lev:2,margin:50,sl:20,tp:40,daily:3,adx:25},
               mid:{lev:3,margin:100,sl:30,tp:60,daily:5,adx:20},
               high:{lev:5,margin:200,sl:40,tp:80,daily:10,adx:15}};
var lang = localStorage.getItem('lang') || 'en';
function t(k){ return (I18N[lang]||I18N.en)[k] || k; }
function setLang(l){ lang=l; localStorage.setItem('lang', l); applyLang(); refresh(); }
function applyLang(){
 document.querySelectorAll('[data-i]').forEach(function(el){ el.textContent = t(el.getAttribute('data-i')); });
 document.getElementById('len').className = lang==='en'?'act':'';
 document.getElementById('ltr').className = lang==='tr'?'act':'';
 document.documentElement.lang = lang;
}
function preset(p){
 var v = PRESETS[p];
 document.getElementById('s_lev').value = v.lev;
 document.getElementById('s_margin').value = v.margin;
 document.getElementById('s_sl').value = v.sl;
 document.getElementById('s_tp').value = v.tp;
 document.getElementById('s_daily').value = v.daily;
 document.getElementById('s_adx').value = v.adx;
 ['p_low','p_mid','p_high'].forEach(function(id){document.getElementById(id).classList.remove('sel');});
 document.getElementById('p_'+(p==='mid'?'mid':p)).classList.add('sel');
 return false;
}
var settingsLoaded = false;
async function loadSettings(){
 var r = await fetch('/api/settings'); var d = await r.json();
 document.getElementById('s_lev').value = d.leverage;
 document.getElementById('s_margin').value = d.margin_usd;
 document.getElementById('s_sl').value = d.sl_pct;
 document.getElementById('s_tp').value = d.tp_pct;
 document.getElementById('s_daily').value = d.max_daily_loss_pct;
 document.getElementById('s_adx').value = d.adx_threshold;
 document.getElementById('s_sym').value = d.symbols.join(',');
 document.getElementById('mkts').innerHTML =
   d.markets.map(function(m){return '<option value="'+m+'">';}).join('');
 settingsLoaded = true;
}
async function save(ev){
 ev.preventDefault();
 var btn = document.getElementById('savebtn'); btn.disabled = true;
 var body = {leverage:+document.getElementById('s_lev').value,
   margin_usd:+document.getElementById('s_margin').value,
   sl_pct:+document.getElementById('s_sl').value,
   tp_pct:+document.getElementById('s_tp').value,
   max_daily_loss_pct:+document.getElementById('s_daily').value,
   adx_threshold:+document.getElementById('s_adx').value,
   symbols:document.getElementById('s_sym').value};
 var msg = document.getElementById('msg');
 try{
  var r = await fetch('/api/settings', {method:'POST',
    headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
  var d = await r.json();
  if(d.ok){ msg.textContent = t('saved'); msg.className='pos'; }
  else{ msg.textContent = t('err') + (d.error||'?'); msg.className='neg'; }
 }catch(e){ msg.textContent = t('err') + e; msg.className='neg'; }
 btn.disabled = false; return false;
}
async function refresh(){
 try{
  var r = await fetch('/api/status'); var d = await r.json();
  document.getElementById('dot').className = 'dot ' + (d.bot_alive ? 'on':'off');
  document.getElementById('hb').textContent = d.bot_alive
    ? t('running').replace('{s}', d.heartbeat_age)
    : (d.heartbeat_age===null ? t('nostate') : t('offline'));
  var s = d.state || {};
  var pnlDay = (d.equity!=null && s.day_start_equity) ? d.equity - s.day_start_equity : null;
  function cls(x){return x==null?'':(x>=0?'pos':'neg');}
  function fmt(x){return x==null?'—':(x>=0?'+':'')+x.toFixed(2)+' $';}
  var c = [
   [t('equity'), d.equity!=null?'$'+d.equity.toFixed(2):'—',''],
   [t('daypnl'), fmt(pnlDay), cls(pnlDay)],
   [t('totpnl'), s.total_pnl!=null?fmt(s.total_pnl):'—', cls(s.total_pnl)],
   [t('trades'), s.trades!=null?s.trades+' ('+s.wins+')':'—',''],
   [t('levcard'), s.leverage?s.leverage+'x / $'+s.margin_usd:'—',''],
   [t('halt'), s.halted_today?t('yes'):t('no'), s.halted_today?'neg':''],
  ];
  document.getElementById('cards').innerHTML = c.map(function(x){
   return '<div class="card"><div class="k">'+x[0]+'</div><div class="v '+x[2]+'">'+x[1]+'</div></div>';}).join('');
  var pb = document.querySelector('#pos tbody');
  pb.innerHTML = (d.positions.length ? d.positions.map(function(p){
   return '<tr><td>'+p.market+'</td><td class="'+p.side.toLowerCase()+'">'+p.side+'</td>'+
   '<td>'+p.entry+'</td><td>'+p.size+'</td><td>'+(p.sl||'—')+'</td><td>'+(p.tp||'—')+'</td>'+
   '<td class="'+(p.upnl>=0?'pos':'neg')+'">'+(p.upnl>=0?'+':'')+p.upnl.toFixed(2)+' $</td></tr>';
  }).join('') : '<tr><td colspan="7" class="muted">'+t('nopos')+'</td></tr>');
  var sg = document.querySelector('#sig tbody');
  var sigs = Object.entries(s.last_signal||{});
  sg.innerHTML = (sigs.length ? sigs.map(function(kv){
   return '<tr><td>'+kv[0]+'</td><td>'+kv[1]+'</td></tr>';}).join('')
   : '<tr><td colspan="2" class="muted">'+t('nosig')+'</td></tr>');
  document.getElementById('log').textContent = d.log || '—';
  if(!settingsLoaded) loadSettings();
 }catch(e){
  document.getElementById('dot').className = 'dot off';
  document.getElementById('hb').textContent = 'no connection';
 }
}
applyLang(); refresh(); setInterval(refresh, 10000);
</script></body></html>"""


def build_status():
    state, hb_age, alive = None, None, False
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            state = json.load(f)
        hb_age = int(time.time() - state.get("ts", 0))
        alive = hb_age < 120
    except (OSError, ValueError):
        pass

    equity, positions = None, []
    try:
        equity = float(client.account()["equity"])
        tracked = (state or {}).get("positions", {})
        for p in (client.positions().get("positions") or {}).values():
            if Decimal(p.get("size", "0")) == 0:
                continue
            sym = p["marketDisplayName"]
            t = tracked.get(sym, {})
            positions.append({
                "market": sym, "side": p["side"], "size": p["size"],
                "entry": p.get("averageEntryPrice"),
                "sl": t.get("sl"), "tp": t.get("tp"),
                "upnl": float(p.get("unrealizedPnl", 0) or 0)})
    except ArcusError:
        pass

    log = ""
    try:
        with open(LOG_PATH, encoding="utf-8") as f:
            log = "".join(f.readlines()[-25:])
    except OSError:
        pass

    return {"bot_alive": alive, "heartbeat_age": hb_age, "equity": equity,
            "state": state, "positions": positions, "log": log}


def current_settings():
    env = dotenv_values(ENV_PATH)
    try:
        markets = [m["marketDisplayName"] for m in client.markets()
                   if m.get("type") == "PERPETUAL"]
    except ArcusError:
        markets = []
    return {
        "leverage": int(float(env.get("LEVERAGE", 3))),
        "margin_usd": float(env.get("MARGIN_USD", 100)),
        "sl_pct": float(env.get("SL_PCT", 30)),
        "tp_pct": float(env.get("TP_PCT", 60)),
        "max_daily_loss_pct": float(env.get("MAX_DAILY_LOSS_PCT", 5)),
        "adx_threshold": float(env.get("ADX_THRESHOLD", 20)),
        "symbols": [s.strip().upper() for s in
                    env.get("SYMBOLS", "BTC-USD,ETH-USD,SOL-USD").split(",") if s.strip()],
        "markets": sorted(markets),
    }


def validate_settings(body: dict):
    """(env_degisiklikleri, hata) doner."""
    changes = {}
    mapping = {"leverage": "LEVERAGE", "margin_usd": "MARGIN_USD",
               "sl_pct": "SL_PCT", "tp_pct": "TP_PCT",
               "max_daily_loss_pct": "MAX_DAILY_LOSS_PCT",
               "adx_threshold": "ADX_THRESHOLD"}
    for field, key in mapping.items():
        if field not in body:
            continue
        try:
            val = float(body[field])
        except (TypeError, ValueError):
            return None, f"{field}: not a number"
        lo, hi, is_int = SETTING_LIMITS[key]
        if not (lo <= val <= hi):
            return None, f"{field}: must be in [{lo}, {hi}]"
        changes[key] = str(int(val)) if is_int else f"{val:g}"

    if "symbols" in body:
        syms = [s.strip().upper() for s in str(body["symbols"]).split(",") if s.strip()]
        if not syms:
            return None, "symbols: empty"
        try:
            known = {m["marketDisplayName"] for m in client.markets(refresh=True)}
        except ArcusError:
            known = None
        if known is not None:
            bad = [s for s in syms if s not in known]
            if bad:
                return None, "unknown market(s): " + ", ".join(bad)
        changes["SYMBOLS"] = ",".join(syms)
    return changes, None


def update_env(changes: dict):
    with open(ENV_PATH, encoding="utf-8") as f:
        lines = f.read().splitlines()
    seen = set()
    out = []
    for ln in lines:
        m = re.match(r"^([A-Z0-9_]+)=", ln)
        if m and m.group(1) in changes:
            k = m.group(1)
            if k in seen:      # ayni anahtarin eski kopyalarini at
                continue
            out.append(f"{k}={changes[k]}")
            seen.add(k)
        else:
            out.append(ln)
    for k, v in changes.items():
        if k not in seen:
            out.append(f"{k}={v}")
    tmp = ENV_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    os.replace(tmp, ENV_PATH)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/status"):
            self._send(200, json.dumps(build_status()).encode())
        elif self.path.startswith("/api/settings"):
            self._send(200, json.dumps(current_settings()).encode())
        elif self.path == "/" or self.path.startswith("/index"):
            self._send(200, PAGE.encode(), "text/html; charset=utf-8")
        else:
            self._send(404, b'{"error":"not found"}')

    def do_POST(self):
        if not self.path.startswith("/api/settings"):
            self._send(404, b'{"error":"not found"}')
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, TypeError):
            self._send(400, b'{"ok":false,"error":"invalid json"}')
            return
        changes, err = validate_settings(body)
        if err:
            self._send(400, json.dumps({"ok": False, "error": err}).encode())
            return
        if not changes:
            self._send(400, b'{"ok":false,"error":"nothing to change"}')
            return
        try:
            update_env(changes)
        except OSError as e:
            self._send(500, json.dumps({"ok": False, "error": str(e)}).encode())
            return
        self._send(200, json.dumps({"ok": True, "applied": changes}).encode())

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"Panel: http://localhost:{PORT}  (telefondan: http://192.168.1.193:{PORT})")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
