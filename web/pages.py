"""HTML sayfalari — EN varsayilan, TR anahtarli, koyu tema (panelle ayni dil)."""

_STYLE = """
 body{font-family:system-ui,Segoe UI,Roboto,sans-serif;background:#0d1117;color:#e6edf3;
      margin:0 auto;padding:16px;max-width:760px}
 h1{font-size:1.25rem;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
 .lang{margin-left:auto}
 .lang button{background:#21262d;color:#8b949e;border:1px solid #30363d;border-radius:6px;
      padding:4px 10px;cursor:pointer;font-size:.8rem}
 .lang button.act{color:#e6edf3;border-color:#8b949e}
 .card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:18px;margin:14px 0}
 .btn{background:#238636;color:#fff;border:0;border-radius:8px;padding:10px 18px;
      font-size:.95rem;cursor:pointer}
 .btn.sec{background:#21262d;border:1px solid #30363d}
 .btn.red{background:#da3633}
 .btn:disabled{opacity:.5}
 input{background:#0d1117;color:#e6edf3;border:1px solid #30363d;border-radius:6px;
       padding:9px;font-size:.9rem;width:100%;box-sizing:border-box}
 label{font-size:.75rem;color:#8b949e;display:block;margin-bottom:4px}
 .muted{color:#8b949e;font-size:.82rem}
 .warn{background:#341a00;border:1px solid #9e6a03;border-radius:8px;padding:12px;
       font-size:.82rem;color:#d29922;margin:10px 0}
 .keybox{background:#0d1117;border:1px dashed #f85149;border-radius:8px;padding:10px;
       font-family:monospace;font-size:.78rem;word-break:break-all;margin:8px 0}
 .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
 .presets{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin:10px 0}
 .preset{background:#0d1117;border:1px solid #30363d;border-radius:10px;padding:10px;
         cursor:pointer;text-align:left;color:#e6edf3}
 .preset:hover{border-color:#8b949e}.preset .t{font-weight:600}
 .preset .d{font-size:.7rem;color:#8b949e;margin-top:4px;line-height:1.5}
 .pos{color:#3fb950}.neg{color:#f85149}
 .chip{background:#21262d;border:1px solid #30363d;border-radius:20px;padding:4px 12px;
       font-family:monospace;font-size:.78rem}
 table{width:100%;border-collapse:collapse;font-size:.85rem}
 th,td{padding:6px 8px;text-align:left;border-bottom:1px solid #21262d}
 th{color:#8b949e;font-weight:500}
 #msg{margin-top:8px;font-size:.85rem}
"""

_I18N = """
var I18N = {
 en:{tagline:'Automated perp trading on Arcus testnet — sign in, get a wallet, pick your risk.',
     signin:'Sign in', devnote:'DEV MODE — Google login not configured yet; enter any email.',
     email:'Email', login:'Log in', logout:'Log out',
     wtitle:'Your Trading Wallet', createw:'Create my wallet',
     wexplain:'A dedicated testnet wallet will be created for you and registered with Arcus. '+
              'Its private keys are encrypted at rest and shown to you exactly ONCE.',
     revealtitle:'Save your keys — shown only once!',
     revealexplain:'Store these somewhere safe (password manager). After you close this, '+
                   'the server will never display them again.',
     reveal:'Reveal my keys (one time)', saved:'I saved them — continue',
     walletaddr:'Wallet address', wkey:'Wallet private key', akey:'Arcus API private key',
     acct:'Account', notfunded:'Not funded yet. One-click testnet funding is coming next — '+
          'or deposit manually to your address on Robinhood Chain testnet.',
     equity:'Equity', free:'Free collateral', positions:'Open positions', nopos:'none',
     risk:'Risk Settings', plow:'Low Risk', pmid:'Balanced', phigh:'High Risk',
     lev:'Leverage (x)', margin:'Margin per trade ($)', sl:'Stop-loss (% of margin)',
     tp:'Take-profit (% of margin)', daily:'Max daily loss (%)', adx:'ADX threshold',
     symbols:'Symbols (comma separated)', save:'Save Settings', savedmsg:'Saved.',
     bot:'Trading Bot', boton:'Bot is ON', botoff:'Bot is OFF',
     start:'Start bot', stop:'Stop bot',
     botnote:'Multi-user engine ships in the next phase — your settings are stored and ready.',
     tg:'Telegram Notifications', tgnote:'Coming soon: link your Telegram to get '+
        'position alerts.', err:'Error: '},
 tr:{tagline:'Arcus testnet üzerinde otomatik perp trade — giriş yap, cüzdanını al, riskini seç.',
     signin:'Giriş yap', devnote:'DEV MODU — Google girişi henüz ayarlı değil; herhangi bir e-posta gir.',
     email:'E-posta', login:'Giriş', logout:'Çıkış',
     wtitle:'Trade Cüzdanın', createw:'Cüzdanımı oluştur',
     wexplain:'Sana özel bir testnet cüzdanı oluşturulup Arcus\\'a kaydedilecek. '+
              'Private key\\'ler şifreli saklanır ve sana yalnızca BİR KEZ gösterilir.',
     revealtitle:'Key\\'lerini kaydet — sadece bir kez gösterilir!',
     revealexplain:'Bunları güvenli bir yere kaydet (şifre yöneticisi). Bu ekranı kapattıktan '+
                   'sonra sunucu bir daha asla göstermez.',
     reveal:'Key\\'lerimi göster (tek sefer)', saved:'Kaydettim — devam',
     walletaddr:'Cüzdan adresi', wkey:'Cüzdan private key', akey:'Arcus API private key',
     acct:'Hesap', notfunded:'Henüz fonlanmadı. Tek tık testnet fonlama bir sonraki fazda — '+
          'ya da Robinhood Chain testnet\\'te adresine manuel yatır.',
     equity:'Equity', free:'Serbest teminat', positions:'Açık pozisyonlar', nopos:'yok',
     risk:'Risk Ayarları', plow:'Düşük Risk', pmid:'Dengeli', phigh:'Yüksek Risk',
     lev:'Kaldıraç (x)', margin:'İşlem başı teminat ($)', sl:'Stop-loss (teminatın %\\'si)',
     tp:'Take-profit (teminatın %\\'si)', daily:'Günlük azami zarar (%)', adx:'ADX eşiği',
     symbols:'Semboller (virgülle)', save:'Ayarları Kaydet', savedmsg:'Kaydedildi.',
     bot:'Trade Botu', boton:'Bot AÇIK', botoff:'Bot KAPALI',
     start:'Botu başlat', stop:'Botu durdur',
     botnote:'Çok kullanıcılı motor bir sonraki fazda geliyor — ayarların kaydedildi, hazır.',
     tg:'Telegram Bildirimleri', tgnote:'Yakında: Telegram\\'ını bağla, pozisyon '+
        'bildirimleri al.', err:'Hata: '}};
var lang = localStorage.getItem('lang') || 'en';
function t(k){ return (I18N[lang]||I18N.en)[k] || k; }
function setLang(l){ lang=l; localStorage.setItem('lang', l); render(); }
function langBtns(){ return '<span class="lang">'+
 '<button onclick="setLang(\\'en\\')" class="'+(lang==='en'?'act':'')+'">EN</button> '+
 '<button onclick="setLang(\\'tr\\')" class="'+(lang==='tr'?'act':'')+'">TR</button></span>'; }
"""

LOGIN_PAGE = ("""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ArcusBot</title><style>""" + _STYLE + """</style>
<script src="https://accounts.google.com/gsi/client" async></script>
</head><body>
<div id="root"></div>
<script>""" + _I18N + """
var DEV = '__DEV_MODE__' === '1';
var GCID = '__GOOGLE_CLIENT_ID__';
function render(){
 var h = '<h1>🤖 ArcusBot '+langBtns()+'</h1>'+
  '<div class="card"><p class="muted">'+t('tagline')+'</p>';
 if(DEV){
  h += '<div class="warn">'+t('devnote')+'</div>'+
   '<label>'+t('email')+'</label><input id="em" type="email" placeholder="you@example.com">'+
   '<p><button class="btn" onclick="devLogin()">'+t('login')+'</button></p>';
 } else {
  h += '<div id="gbtn"></div>';
 }
 h += '</div>';
 document.getElementById('root').innerHTML = h;
 if(!DEV && window.google && google.accounts){
  google.accounts.id.initialize({client_id: GCID, callback: onGoogle});
  google.accounts.id.renderButton(document.getElementById('gbtn'),
    {theme:'filled_black', size:'large'});
 }
}
async function devLogin(){
 var em = document.getElementById('em').value;
 var r = await fetch('/auth/dev', {method:'POST',
   headers:{'Content-Type':'application/json'}, body:JSON.stringify({email:em})});
 if(r.ok) location.reload(); else alert((await r.json()).error);
}
async function onGoogle(resp){
 var r = await fetch('/auth/google', {method:'POST',
   headers:{'Content-Type':'application/json'},
   body:JSON.stringify({credential: resp.credential})});
 if(r.ok) location.reload(); else alert((await r.json()).error);
}
render();
window.onload = render;
</script></body></html>""")

APP_PAGE = ("""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ArcusBot</title><style>""" + _STYLE + """</style></head><body>
<div id="root"></div>
<script>""" + _I18N + """
var ME = null, ACCT = null, KEYS = null;
var PRESETS = {low:{leverage:2,margin_usd:50,sl_pct:20,tp_pct:40,max_daily_loss_pct:3,adx_threshold:25},
               mid:{leverage:3,margin_usd:100,sl_pct:30,tp_pct:60,max_daily_loss_pct:5,adx_threshold:20},
               high:{leverage:5,margin_usd:200,sl_pct:40,tp_pct:80,max_daily_loss_pct:10,adx_threshold:15}};

async function load(){
 var r = await fetch('/api/me');
 if(r.status===401){ location.reload(); return; }
 ME = await r.json();
 if(ME.wallet && ME.wallet.revealed){
  try{ ACCT = await (await fetch('/api/account')).json(); }catch(e){ ACCT=null; }
 }
 render();
}
function esc(s){ return String(s==null?'':s); }
function render(){
 if(!ME){ document.getElementById('root').innerHTML='...'; return; }
 var h = '<h1>🤖 ArcusBot <span class="muted">'+esc(ME.email)+'</span> '+langBtns()+
  ' <button class="btn sec" style="margin-left:8px" onclick="logout()">'+t('logout')+'</button></h1>';

 if(!ME.wallet){
  h += '<div class="card"><h3>'+t('wtitle')+'</h3><p class="muted">'+t('wexplain')+'</p>'+
   '<button class="btn" id="cw" onclick="createWallet()">'+t('createw')+'</button></div>';
 } else if(!ME.wallet.revealed || KEYS){
  h += '<div class="card"><h3>'+t('revealtitle')+'</h3>'+
   '<div class="warn">'+t('revealexplain')+'</div>';
  if(!KEYS){
   h += '<button class="btn red" onclick="reveal()">'+t('reveal')+'</button>';
  } else {
   h += '<label>'+t('walletaddr')+'</label><div class="keybox">'+KEYS.address+'</div>'+
    '<label>'+t('wkey')+'</label><div class="keybox">'+KEYS.wallet_private_key+'</div>'+
    '<label>'+t('akey')+'</label><div class="keybox">'+KEYS.arcus_api_private_key+'</div>'+
    '<button class="btn" onclick="KEYS=null;load()">'+t('saved')+'</button>';
  }
  h += '</div>';
 } else {
  h += '<div class="card"><h3>'+t('acct')+'</h3>'+
   '<p><span class="chip">'+ME.wallet.address+'</span></p>';
  if(ACCT && ACCT.funded){
   h += '<div class="grid">'+
    '<div><label>'+t('equity')+'</label><b>$'+ACCT.equity.toFixed(2)+'</b></div>'+
    '<div><label>'+t('free')+'</label><b>$'+(ACCT.freeCollateral||0).toFixed(2)+'</b></div></div>';
   h += '<h4>'+t('positions')+'</h4>';
   h += ACCT.positions.length
    ? '<table><tr><th>Market</th><th>Side</th><th>Size</th><th>PnL</th></tr>'+
      ACCT.positions.map(function(p){return '<tr><td>'+p.market+'</td><td>'+p.side+
       '</td><td>'+p.size+'</td><td class="'+(p.upnl>=0?'pos':'neg')+'">'+
       p.upnl.toFixed(2)+'</td></tr>';}).join('')+'</table>'
    : '<p class="muted">'+t('nopos')+'</p>';
  } else {
   h += '<div class="warn">'+t('notfunded')+'</div>';
  }
  h += '</div>';

  var s = ME.settings || {};
  h += '<div class="card"><h3>'+t('risk')+'</h3><div class="presets">'+
   '<button class="preset" onclick="preset(\\'low\\')"><div class="t">'+t('plow')+
     '</div><div class="d">2x · $50 · SL 20% · TP 40%</div></button>'+
   '<button class="preset" onclick="preset(\\'mid\\')"><div class="t">'+t('pmid')+
     '</div><div class="d">3x · $100 · SL 30% · TP 60%</div></button>'+
   '<button class="preset" onclick="preset(\\'high\\')"><div class="t">'+t('phigh')+
     '</div><div class="d">5x · $200 · SL 40% · TP 80%</div></button></div>'+
   '<div class="grid">'+
   fld('leverage', t('lev'), s.leverage)+fld('margin_usd', t('margin'), s.margin_usd)+
   fld('sl_pct', t('sl'), s.sl_pct)+fld('tp_pct', t('tp'), s.tp_pct)+
   fld('max_daily_loss_pct', t('daily'), s.max_daily_loss_pct)+
   fld('adx_threshold', t('adx'), s.adx_threshold)+'</div>'+
   '<label style="margin-top:10px">'+t('symbols')+'</label>'+
   '<input id="f_symbols" value="'+esc(s.symbols)+'">'+
   '<p><button class="btn" onclick="saveSettings()">'+t('save')+'</button></p><div id="msg"></div></div>';

  var on = s.bot_active;
  h += '<div class="card"><h3>'+t('bot')+'</h3>'+
   '<p><b class="'+(on?'pos':'neg')+'">'+(on?t('boton'):t('botoff'))+'</b></p>'+
   '<button class="btn '+(on?'red':'')+'" onclick="toggleBot('+(on?0:1)+')">'+
    (on?t('stop'):t('start'))+'</button>'+
   '<p class="muted">'+t('botnote')+'</p></div>';

  h += '<div class="card"><h3>'+t('tg')+'</h3><p class="muted">'+t('tgnote')+'</p></div>';
 }
 document.getElementById('root').innerHTML = h;
}
function fld(id, label, val){
 return '<div><label>'+label+'</label><input id="f_'+id+'" type="number" value="'+esc(val)+'"></div>';
}
function preset(p){
 var v = PRESETS[p];
 for(var k in v){ var el=document.getElementById('f_'+k); if(el) el.value=v[k]; }
}
async function createWallet(){
 document.getElementById('cw').disabled = true;
 var r = await fetch('/api/wallet/create', {method:'POST'});
 if(!r.ok){ alert((await r.json()).error); }
 await load();
}
async function reveal(){
 var r = await fetch('/api/wallet/reveal');
 if(r.ok){ KEYS = await r.json(); render(); }
 else alert((await r.json()).error);
}
async function saveSettings(){
 var b = {symbols: document.getElementById('f_symbols').value};
 ['leverage','margin_usd','sl_pct','tp_pct','max_daily_loss_pct','adx_threshold']
  .forEach(function(k){ b[k] = +document.getElementById('f_'+k).value; });
 var r = await fetch('/api/settings', {method:'POST',
   headers:{'Content-Type':'application/json'}, body:JSON.stringify(b)});
 var d = await r.json();
 var m = document.getElementById('msg');
 if(d.ok){ m.textContent=t('savedmsg'); m.className='pos'; ME.settings=Object.assign(ME.settings||{},b); }
 else{ m.textContent=t('err')+(d.error||'?'); m.className='neg'; }
}
async function toggleBot(on){
 var r = await fetch('/api/bot/'+(on?'start':'stop'), {method:'POST'});
 if(!r.ok){ alert((await r.json()).error); }
 await load();
}
async function logout(){ await fetch('/logout',{method:'POST'}); location.reload(); }
load();
</script></body></html>""")
