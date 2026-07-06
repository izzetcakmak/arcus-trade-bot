"""HTML sayfalari — Apple-esintili koyu tasarim. EN varsayilan, TR anahtarli.

Tasarim dili: siyah zemin (#000), buyuk tipografi (SF/system font), cam nav
(backdrop blur), hap butonlar (980px radius), ince cizgili yumusak kartlar,
scroll'da fade-up animasyonlari. Islevsel JS onceki surumle birebir ayni.
"""

_FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
            "viewBox='0 0 100 100'%3E%3Cpolygon points='50,6 90,28 90,72 50,94 "
            "10,72 10,28' fill='none' stroke='%232997ff' stroke-width='8'/%3E"
            "%3Ccircle cx='50' cy='50' r='14' fill='%2330d158'/%3E%3C/svg%3E")

_STYLE = """
 :root{
  --bg:#000; --bg2:#0a0a0c; --card:rgba(255,255,255,.055);
  --line:rgba(255,255,255,.12); --line2:rgba(255,255,255,.07);
  --text:#f5f5f7; --muted:#86868b; --blue:#2997ff; --cta:#0071e3;
  --green:#30d158; --red:#ff453a; --amber:#ffd60a;
 }
 *{box-sizing:border-box}
 html{scroll-behavior:smooth}
 body{font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display','SF Pro Text',
      'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;
      background:var(--bg);color:var(--text);margin:0;-webkit-font-smoothing:antialiased;
      text-rendering:optimizeLegibility;overflow-x:hidden}
 a{color:var(--blue);text-decoration:none}
 a:hover{text-decoration:underline}

 /* --- cam nav --- */
 nav{position:sticky;top:0;z-index:50;display:flex;align-items:center;gap:14px;
     padding:14px max(22px,env(safe-area-inset-left));
     background:rgba(0,0,0,.72);backdrop-filter:saturate(180%) blur(20px);
     -webkit-backdrop-filter:saturate(180%) blur(20px);
     border-bottom:1px solid var(--line2)}
 .brand{display:flex;align-items:center;gap:10px;font-weight:600;font-size:1.05rem;
        letter-spacing:-.01em;color:var(--text)}
 .brand svg{display:block}
 .nav-right{margin-left:auto;display:flex;align-items:center;gap:10px}

 /* --- butonlar --- */
 .pill{display:inline-block;border:0;border-radius:980px;cursor:pointer;
       font-size:.95rem;font-weight:500;padding:11px 24px;transition:.25s;
       font-family:inherit}
 .pill.primary{background:var(--cta);color:#fff}
 .pill.primary:hover{background:#0077ed;transform:scale(1.02)}
 .pill.ghost{background:transparent;color:var(--text);border:1px solid var(--line)}
 .pill.ghost:hover{border-color:var(--muted)}
 .pill.danger{background:var(--red);color:#fff}
 .pill.small{padding:7px 16px;font-size:.85rem}
 .pill:disabled{opacity:.45;transform:none;cursor:default}
 .lang button{background:transparent;color:var(--muted);border:0;cursor:pointer;
       font-size:.85rem;padding:6px 8px;font-family:inherit;border-radius:8px}
 .lang button.act{color:var(--text);font-weight:600}

 /* --- bolumler --- */
 .wrap{max-width:1040px;margin:0 auto;padding:0 22px}
 section{padding:88px 0}
 .hero{position:relative;text-align:center;padding:110px 0 70px}
 .hero .glow{position:absolute;inset:-40% -20% auto;height:130%;z-index:-1;
   background:radial-gradient(42% 42% at 50% 38%,rgba(41,151,255,.22),transparent 70%),
              radial-gradient(30% 30% at 62% 30%,rgba(48,209,88,.12),transparent 70%);
   filter:blur(40px)}
 .kicker{font-size:.85rem;font-weight:600;letter-spacing:.14em;color:var(--blue);
        text-transform:uppercase}
 h1.big{font-size:clamp(44px,7.2vw,86px);line-height:1.04;letter-spacing:-.018em;
        font-weight:700;margin:14px 0 18px;
        background:linear-gradient(180deg,#fff 60%,#b9c4d0);
        -webkit-background-clip:text;background-clip:text;color:transparent}
 .sub{font-size:clamp(17px,2.2vw,23px);color:var(--muted);max-width:640px;
      margin:0 auto 34px;line-height:1.45;font-weight:400}
 h2.sec{font-size:clamp(30px,4.4vw,52px);letter-spacing:-.015em;font-weight:700;
        text-align:center;margin:0 0 14px}
 .sec-sub{color:var(--muted);text-align:center;max-width:560px;margin:0 auto 52px;
        font-size:1.05rem;line-height:1.5}

 /* --- kartlar --- */
 .card{background:var(--card);border:1px solid var(--line2);border-radius:22px;
       padding:26px;transition:.3s}
 .grid{display:grid;gap:16px}
 .g4{grid-template-columns:repeat(auto-fit,minmax(220px,1fr))}
 .g3{grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}
 .g2{grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
 .feature .ic{width:46px;height:46px;border-radius:14px;display:flex;align-items:center;
      justify-content:center;background:rgba(41,151,255,.14);margin-bottom:16px}
 .feature h3{margin:0 0 8px;font-size:1.1rem;letter-spacing:-.01em}
 .feature p{margin:0;color:var(--muted);font-size:.92rem;line-height:1.55}

 /* --- mock panel --- */
 .mock{max-width:620px;margin:52px auto 0;text-align:left;
       background:linear-gradient(180deg,rgba(255,255,255,.08),rgba(255,255,255,.03));
       border:1px solid var(--line);border-radius:26px;padding:26px;
       box-shadow:0 30px 80px rgba(0,0,0,.55), inset 0 1px 0 rgba(255,255,255,.08)}
 .mock .row{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
 .mock .eq{font-size:2.4rem;font-weight:700;letter-spacing:-.02em}
 .chip{font-size:.78rem;font-weight:600;padding:4px 12px;border-radius:980px}
 .chip.up{background:rgba(48,209,88,.15);color:var(--green)}
 .bars{display:flex;align-items:flex-end;gap:6px;height:74px;margin:20px 0 6px}
 .bars i{flex:1;border-radius:4px 4px 0 0;background:linear-gradient(180deg,#2997ff,#1c5fa8);
        opacity:.85}
 .posrow{display:flex;justify-content:space-between;align-items:center;
        border-top:1px solid var(--line2);padding-top:16px;margin-top:12px;font-size:.92rem}
 .lbl{color:var(--muted);font-size:.78rem}

 /* --- adimlar --- */
 .steps{counter-reset:s}
 .step{position:relative;padding-left:0}
 .step .n{width:34px;height:34px;border-radius:50%;background:rgba(41,151,255,.16);
      color:var(--blue);font-weight:700;display:flex;align-items:center;
      justify-content:center;margin-bottom:14px;font-size:.95rem}
 .step h4{margin:0 0 6px;font-size:1rem}
 .step p{margin:0;color:var(--muted);font-size:.88rem;line-height:1.5}

 /* --- tier kartlari --- */
 .tier{text-align:center;padding:34px 26px}
 .tier.mid{border-color:rgba(41,151,255,.5);
       box-shadow:0 0 60px rgba(41,151,255,.12)}
 .tier .name{font-size:1.15rem;font-weight:700;margin-bottom:4px}
 .tier .big2{font-size:2.6rem;font-weight:700;letter-spacing:-.02em;margin:10px 0 2px}
 .tier .per{color:var(--muted);font-size:.82rem;margin-bottom:18px}
 .tier ul{list-style:none;margin:0;padding:0;color:var(--muted);font-size:.9rem}
 .tier li{padding:7px 0;border-top:1px solid var(--line2)}
 .tier li:first-child{border-top:0}

 /* --- form --- */
 label{font-size:.78rem;color:var(--muted);display:block;margin-bottom:6px}
 input{width:100%;background:#1c1c1e;color:var(--text);border:1px solid var(--line2);
       border-radius:12px;padding:12px 14px;font-size:.95rem;font-family:inherit;
       transition:.2s;outline:none}
 input:focus{border-color:var(--blue);box-shadow:0 0 0 3px rgba(41,151,255,.18)}
 .fgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px}

 /* --- tablo & feed --- */
 table{width:100%;border-collapse:collapse;font-size:.9rem}
 th,td{padding:11px 12px;text-align:left;border-bottom:1px solid var(--line2)}
 th{color:var(--muted);font-weight:500;font-size:.78rem;text-transform:uppercase;
    letter-spacing:.06em}
 tr:last-child td{border-bottom:0}
 pre.feed{background:#101013;border:1px solid var(--line2);border-radius:14px;
      padding:14px;font-size:.76rem;line-height:1.65;overflow:auto;max-height:220px;
      white-space:pre-wrap;color:#c7c7cc;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}

 .pos{color:var(--green)} .neg{color:var(--red)}
 .long{color:var(--green);font-weight:600}.short{color:var(--red);font-weight:600}
 .muted{color:var(--muted);font-size:.85rem}
 .warn{background:rgba(255,214,10,.08);border:1px solid rgba(255,214,10,.25);
       border-radius:14px;padding:14px 16px;font-size:.85rem;color:var(--amber);
       line-height:1.5}
 .keybox{background:#101013;border:1px dashed var(--red);border-radius:12px;
       padding:12px;font-family:ui-monospace,Menlo,monospace;font-size:.78rem;
       word-break:break-all;margin:8px 0 16px}
 .chipmono{background:#1c1c1e;border:1px solid var(--line2);border-radius:980px;
       padding:6px 16px;font-family:ui-monospace,Menlo,monospace;font-size:.78rem}
 #msg{margin-top:10px;font-size:.88rem}

 /* --- app duzeni --- */
 .app-wrap{max-width:860px;margin:0 auto;padding:26px 22px 60px}
 .app-wrap .card{margin:16px 0}
 .card h3{margin:0 0 14px;font-size:1.15rem;letter-spacing:-.01em}
 .statgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:18px}
 .stat .v{font-size:1.5rem;font-weight:700;letter-spacing:-.01em;margin-top:2px}
 .presets{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
       gap:12px;margin:6px 0 20px}
 .preset{background:#161618;border:1px solid var(--line2);border-radius:16px;
       padding:16px;cursor:pointer;text-align:left;color:var(--text);
       font-family:inherit;transition:.2s}
 .preset:hover{border-color:var(--blue)}
 .preset.sel{border-color:var(--green)}
 .preset .t{font-weight:600;font-size:.95rem}
 .preset .d{font-size:.72rem;color:var(--muted);margin-top:6px;line-height:1.6}

 /* --- sembol secici --- */
 .symtabs{display:flex;gap:6px;flex-wrap:wrap;background:#161618;
      border:1px solid var(--line2);border-radius:980px;padding:5px;width:fit-content;
      max-width:100%;margin-bottom:14px}
 .symtabs .tab{border:0;background:transparent;color:var(--muted);cursor:pointer;
      border-radius:980px;padding:7px 16px;font-size:.82rem;font-family:inherit;
      transition:.2s;white-space:nowrap}
 .symtabs .tab.act{background:#2c2c2e;color:var(--text);font-weight:600}
 .chips{display:flex;flex-wrap:wrap;gap:8px}
 .mchip{border:1px solid var(--line2);background:#161618;color:var(--muted);
      border-radius:980px;padding:7px 14px;font-size:.8rem;cursor:pointer;
      font-family:inherit;transition:.15s}
 .mchip:hover{border-color:var(--muted);color:var(--text)}
 .mchip.sel{border-color:var(--green);color:var(--green);
      background:rgba(48,209,88,.1);font-weight:600}

 footer{border-top:1px solid var(--line2);padding:34px 22px;text-align:center;
       color:var(--muted);font-size:.82rem;line-height:1.8}

 /* --- animasyon --- */
 .reveal{opacity:0;transform:translateY(26px);
        transition:opacity .7s cubic-bezier(.2,.6,.2,1),transform .7s cubic-bezier(.2,.6,.2,1)}
 .reveal.in{opacity:1;transform:none}
 @media (max-width:640px){ section{padding:56px 0} .hero{padding:70px 0 40px} }
"""

_LOGO = ("<svg width='26' height='26' viewBox='0 0 100 100'>"
         "<polygon points='50,6 90,28 90,72 50,94 10,72 10,28' fill='none' "
         "stroke='#2997ff' stroke-width='8'/>"
         "<circle cx='50' cy='50' r='13' fill='#30d158'/></svg>")

_ICONS = {
    "wallet": ("<svg width='22' height='22' viewBox='0 0 24 24' fill='none' "
               "stroke='#2997ff' stroke-width='1.8' stroke-linecap='round'>"
               "<rect x='3' y='6' width='18' height='13' rx='3'/>"
               "<path d='M3 10h18M16 15h2'/></svg>"),
    "fund": ("<svg width='22' height='22' viewBox='0 0 24 24' fill='none' "
             "stroke='#30d158' stroke-width='1.8' stroke-linecap='round'>"
             "<circle cx='12' cy='12' r='9'/><path d='M12 7v10M8.5 10.5 12 7l3.5 3.5'/></svg>"),
    "risk": ("<svg width='22' height='22' viewBox='0 0 24 24' fill='none' "
             "stroke='#ffd60a' stroke-width='1.8' stroke-linecap='round'>"
             "<path d='M4 17l4-6 4 3 4-8 4 6'/><path d='M3 21h18'/></svg>"),
    "tg": ("<svg width='22' height='22' viewBox='0 0 24 24' fill='none' "
           "stroke='#2997ff' stroke-width='1.8' stroke-linejoin='round'>"
           "<path d='M21 4 3 11l5.5 2L19 6l-8 8.5V19l3-3 4.5 3.5z'/></svg>"),
}

_I18N = """
var I18N = {
 en:{nav_signin:'Sign in',
     kicker:'Testnet Beta — Arcus DEX',
     hero_t:'Trade perpetuals.<br>On autopilot.',
     hero_s:'ArcusBot watches the markets 24/7 and trades BTC, ETH, stocks and more on the Arcus exchange — with your risk rules, not your emotions.',
     hero_hint:'Free · Testnet funds only · No card required',
     f_title:'Everything set up in a minute.',
     f_sub:'Sign in with Google and the rest is one click each.',
     f1t:'Instant wallet', f1d:'A dedicated trading wallet is created and registered with Arcus the moment you sign up. Keys are shown to you once, then stored encrypted.',
     f2t:'One-click funding', f2d:'Get $10,000 of testnet collateral deposited to your account automatically. No faucets, no bridges, no gas hunting.',
     f3t:'Risk, your way', f3d:'Pick Low, Balanced or High Risk — or fine-tune leverage, margin, stop-loss and take-profit yourself. Changes apply live.',
     f4t:'Telegram alerts', f4d:'Link Telegram in two taps and get every position open, close and daily-limit event as a personal message.',
     how_t:'How it works', how_s:'From zero to a running bot in four steps.',
     s1t:'Sign in', s1d:'Use your Google account. No forms, no passwords.',
     s2t:'Create your wallet', s2d:'Auto-generated, registered on Arcus, keys shown once.',
     s3t:'Fund & pick risk', s3d:'$10,000 testnet collateral and a risk preset.',
     s4t:'Start the bot', s4d:'A multi-signal 15-minute strategy takes over.',
     tiers_t:'Three risk profiles.', tiers_s:'Start conservative. Change any time — settings apply within ~30 seconds.',
     lev:'leverage', pertrade:'per trade', dl:'daily loss limit',
     sec_t:'Your keys, encrypted.', sec_s:'Wallet keys are encrypted at rest and revealed to you exactly once. The bot signs orders with a scoped API key — this is a testnet product, no real funds are ever involved.',
     login_t:'Get started', login_s:'Sign in with Google — your wallet is ready in seconds.',
     devnote:'DEV MODE — Google login not configured; enter any email.',
     email:'Email', login:'Log in',
     foot:'Testnet only — no real funds. Not investment advice.',
     contact:'Contact'},
 tr:{nav_signin:'Giriş yap',
     kicker:'Testnet Beta — Arcus DEX',
     hero_t:'Perp ticareti.<br>Otopilotta.',
     hero_s:'ArcusBot piyasaları 7/24 izler; BTC, ETH, hisse ve daha fazlasını Arcus borsasında senin risk kurallarınla işler — duygularınla değil.',
     hero_hint:'Ücretsiz · Yalnızca testnet parası · Kart gerekmez',
     f_title:'Her şey bir dakikada hazır.',
     f_sub:'Google ile gir, gerisi birer tık.',
     f1t:'Anında cüzdan', f1d:'Kayıt olduğun an sana özel bir trade cüzdanı oluşturulur ve Arcus\\'a kaydedilir. Key\\'ler bir kez gösterilir, sonra şifreli saklanır.',
     f2t:'Tek tık fonlama', f2d:'Hesabına otomatik olarak $10.000 testnet teminatı yatırılır. Faucet yok, köprü yok, gas derdi yok.',
     f3t:'Risk senin kuralın', f3d:'Düşük, Dengeli veya Yüksek Risk seç — ya da kaldıraç, teminat, SL/TP\\'yi kendin ayarla. Değişiklikler canlı uygulanır.',
     f4t:'Telegram bildirimleri', f4d:'İki dokunuşla Telegram\\'ı bağla; her pozisyon açılışı, kapanışı ve günlük limit olayı kişisel mesaj olarak gelsin.',
     how_t:'Nasıl çalışır', how_s:'Sıfırdan çalışan bota dört adım.',
     s1t:'Giriş yap', s1d:'Google hesabınla. Form yok, şifre yok.',
     s2t:'Cüzdanını oluştur', s2d:'Otomatik üretilir, Arcus\\'a kaydedilir, key\\'ler bir kez gösterilir.',
     s3t:'Fonla & risk seç', s3d:'$10.000 testnet teminatı ve bir risk profili.',
     s4t:'Botu başlat', s4d:'Çok sinyalli 15 dakikalık strateji devralır.',
     tiers_t:'Üç risk profili.', tiers_s:'Temkinli başla. İstediğin an değiştir — ayarlar ~30 saniyede uygulanır.',
     lev:'kaldıraç', pertrade:'işlem başı', dl:'günlük zarar limiti',
     sec_t:'Key\\'lerin, şifreli.', sec_s:'Cüzdan anahtarları şifreli saklanır ve sana yalnızca bir kez gösterilir. Bot, emirleri kapsamı sınırlı bir API anahtarıyla imzalar — bu bir testnet ürünüdür, gerçek para hiçbir zaman işin içinde değildir.',
     login_t:'Hemen başla', login_s:'Google ile gir — cüzdanın saniyeler içinde hazır.',
     devnote:'DEV MODU — Google girişi ayarlı değil; herhangi bir e-posta gir.',
     email:'E-posta', login:'Giriş',
     foot:'Yalnızca testnet — gerçek para yok. Yatırım tavsiyesi değildir.',
     contact:'İletişim'}};
var APPI18N = {
 en:{logout:'Log out',
     wtitle:'Your trading wallet', createw:'Create my wallet',
     wexplain:'A dedicated testnet wallet will be created and registered with Arcus. Its private keys are encrypted at rest and shown to you exactly once.',
     revealtitle:'Save your keys — shown only once',
     revealexplain:'Store these in a password manager. After this screen, the server never displays them again.',
     reveal:'Reveal my keys (one time)', saved:'I saved them — continue',
     walletaddr:'Wallet address', wkey:'Wallet private key', akey:'Arcus API private key',
     acct:'Account', notfunded:'Not funded yet — get free testnet collateral with one click.',
     fund:'Fund my account · $10,000 testnet', fundprog:'Funding: ',
     funddone:'Deposit sent — balance appears within ~1 minute.',
     equity:'Equity', free:'Free collateral', positions:'Open positions', nopos:'No open positions',
     risk:'Risk settings', plow:'Low Risk', pmid:'Balanced', phigh:'High Risk',
     lev:'Leverage (x)', margin:'Margin per trade ($)', sl:'Stop-loss (% of margin)',
     tp:'Take-profit (% of margin)', daily:'Max daily loss (%)', adx:'ADX threshold',
     symbols:'Markets to trade', save:'Save settings', savedmsg:'Saved.',
     cat_ALL:'All', cat_CRYPTO:'Crypto', cat_EQUITIES:'Stocks',
     cat_COMMODITIES:'Commodities', cat_INDICES:'Indices',
     selectall:'Select visible', clearall:'Clear', selected:'selected',
     sym_note:'Tip: every selected market is scanned each cycle — more markets, more signals, more open positions at once.',
     bot:'Trading bot', boton:'Bot is running', botoff:'Bot is off',
     start:'Start bot', stop:'Stop bot',
     tg:'Telegram notifications', tglinkbtn:'Link my Telegram', tglinked:'Telegram linked',
     tgopen:'Telegram opened — press START in the chat; this page updates automatically.',
     tgchange:'Change / unlink', tgwarn:'Open the link on the phone whose Telegram should receive the alerts.',
     events:'Recent events', engon:'engine running', engoff:'engine starting…',
     err:'Error: '},
 tr:{logout:'Çıkış',
     wtitle:'Trade cüzdanın', createw:'Cüzdanımı oluştur',
     wexplain:'Sana özel bir testnet cüzdanı oluşturulup Arcus\\'a kaydedilecek. Private key\\'ler şifreli saklanır ve yalnızca BİR KEZ gösterilir.',
     revealtitle:'Key\\'lerini kaydet — sadece bir kez gösterilir',
     revealexplain:'Bunları bir şifre yöneticisine kaydet. Bu ekrandan sonra sunucu bir daha asla göstermez.',
     reveal:'Key\\'lerimi göster (tek sefer)', saved:'Kaydettim — devam',
     walletaddr:'Cüzdan adresi', wkey:'Cüzdan private key', akey:'Arcus API private key',
     acct:'Hesap', notfunded:'Henüz fonlanmadı — tek tıkla ücretsiz testnet teminatı al.',
     fund:'Hesabımı fonla · $10.000 testnet', fundprog:'Fonlama: ',
     funddone:'Yatırma gönderildi — bakiye ~1 dakika içinde görünür.',
     equity:'Equity', free:'Serbest teminat', positions:'Açık pozisyonlar', nopos:'Açık pozisyon yok',
     risk:'Risk ayarları', plow:'Düşük Risk', pmid:'Dengeli', phigh:'Yüksek Risk',
     lev:'Kaldıraç (x)', margin:'İşlem başı teminat ($)', sl:'Stop-loss (teminatın %\\'si)',
     tp:'Take-profit (teminatın %\\'si)', daily:'Günlük azami zarar (%)', adx:'ADX eşiği',
     symbols:'İşlem açılacak marketler', save:'Ayarları kaydet', savedmsg:'Kaydedildi.',
     cat_ALL:'Tümü', cat_CRYPTO:'Kripto', cat_EQUITIES:'Hisse',
     cat_COMMODITIES:'Emtia', cat_INDICES:'Endeks',
     selectall:'Görünenleri seç', clearall:'Temizle', selected:'seçili',
     sym_note:'İpucu: seçilen her market her döngüde taranır — market sayısı arttıkça sinyal ve aynı anda açık pozisyon sayısı da artar.',
     bot:'Trade botu', boton:'Bot çalışıyor', botoff:'Bot kapalı',
     start:'Botu başlat', stop:'Botu durdur',
     tg:'Telegram bildirimleri', tglinkbtn:'Telegram\\'ımı bağla', tglinked:'Telegram bağlı',
     tgopen:'Telegram açıldı — sohbette START\\'a bas; bu sayfa otomatik güncellenir.',
     tgchange:'Değiştir / bağlantıyı kes', tgwarn:'Linki, bildirimleri alacak telefonun Telegram\\'ında aç.',
     events:'Son olaylar', engon:'motor çalışıyor', engoff:'motor başlıyor…',
     err:'Hata: '}};
var lang = localStorage.getItem('lang') || 'en';
function t(k){ var d = I18N[lang]||I18N.en; if(k in d) return d[k];
               var a = APPI18N[lang]||APPI18N.en; return a[k]||k; }
function setLang(l){ lang=l; localStorage.setItem('lang', l); render(); }
function langBtns(){ return '<span class="lang">'+
 '<button onclick="setLang(\\'en\\')" class="'+(lang==='en'?'act':'')+'">EN</button>'+
 '<button onclick="setLang(\\'tr\\')" class="'+(lang==='tr'?'act':'')+'">TR</button></span>'; }
function pageFooter(){
 return '<footer>'+t('foot')+'<br>'+t('contact')+': '+
  '<a href="mailto:info@atradebot.xyz">info@atradebot.xyz</a> · '+
  '<a href="https://github.com/izzetcakmak/arcus-trade-bot">GitHub</a> · '+
  '<a href="https://arcus.xyz">Arcus</a></footer>';
}
function revealInit(){
 var io = new IntersectionObserver(function(es){
  es.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add('in');
    io.unobserve(e.target);} });
 }, {threshold:.12});
 document.querySelectorAll('.reveal').forEach(function(el){ io.observe(el); });
}
"""

LOGIN_PAGE = ("""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ArcusBot — Automated perp trading on Arcus</title>
<meta name="description" content="Sign in with Google, get a wallet, pick your risk. ArcusBot trades perpetuals for you on the Arcus DEX testnet.">
<link rel="icon" href='""" + _FAVICON + """'>
<style>""" + _STYLE + """</style>
<script src="https://accounts.google.com/gsi/client" async></script>
</head><body>
<div id="root"></div>
<script>""" + _I18N + """
var DEV = '__DEV_MODE__' === '1';
var GCID = '__GOOGLE_CLIENT_ID__';
var LOGO = `""" + _LOGO + """`;
var ICONS = {wallet:`""" + _ICONS["wallet"] + """`, fund:`""" + _ICONS["fund"] + """`,
             risk:`""" + _ICONS["risk"] + """`, tg:`""" + _ICONS["tg"] + """`};

function loginBox(){
 var h = '<div class="card" id="login" style="max-width:420px;margin:0 auto;text-align:center;padding:34px">'+
  '<h3 style="margin:0 0 6px;font-size:1.3rem">'+t('login_t')+'</h3>'+
  '<p class="muted" style="margin:0 0 22px">'+t('login_s')+'</p>';
 if(DEV){
  h += '<div class="warn" style="text-align:left;margin-bottom:14px">'+t('devnote')+'</div>'+
   '<div style="text-align:left"><label>'+t('email')+'</label>'+
   '<input id="em" type="email" placeholder="you@example.com"></div>'+
   '<p style="margin:18px 0 0"><button class="pill primary" onclick="devLogin()">'+t('login')+'</button></p>';
 } else {
  h += '<div id="gbtn" style="display:flex;justify-content:center"></div>';
 }
 h += '<p class="muted" style="margin:18px 0 0;font-size:.75rem">'+t('hero_hint')+'</p></div>';
 return h;
}

function render(){
 var h = '<nav><span class="brand">'+LOGO+' ArcusBot</span>'+
  '<span class="nav-right">'+langBtns()+
  '<a href="#login" class="pill ghost small" style="text-decoration:none">'+t('nav_signin')+'</a></span></nav>';

 // hero
 h += '<div class="hero"><div class="glow"></div><div class="wrap">'+
  '<div class="kicker reveal">'+t('kicker')+'</div>'+
  '<h1 class="big reveal">'+t('hero_t')+'</h1>'+
  '<p class="sub reveal">'+t('hero_s')+'</p>'+
  '<div class="reveal">'+loginBox()+'</div>'+
  '<div class="mock reveal">'+
   '<div class="lbl">EQUITY</div>'+
   '<div class="row"><span class="eq">$10,247.88</span>'+
   '<span class="chip up">▲ +2.47% today</span></div>'+
   '<div class="bars">'+
    [34,48,42,60,55,72,66,84,78,95,88,100].map(function(v){
      return '<i style="height:'+v+'%"></i>';}).join('')+'</div>'+
   '<div class="posrow"><span><b class="long">LONG</b> · BTC-USD · 3×</span>'+
   '<span class="pos">+$84.20</span></div>'+
  '</div></div></div>';

 // features
 h += '<section><div class="wrap">'+
  '<h2 class="sec reveal">'+t('f_title')+'</h2>'+
  '<p class="sec-sub reveal">'+t('f_sub')+'</p>'+
  '<div class="grid g4">'+
  [['wallet','f1t','f1d'],['fund','f2t','f2d'],['risk','f3t','f3d'],['tg','f4t','f4d']]
  .map(function(f){ return '<div class="card feature reveal"><div class="ic">'+ICONS[f[0]]+
    '</div><h3>'+t(f[1])+'</h3><p>'+t(f[2])+'</p></div>'; }).join('')+
  '</div></div></section>';

 // how it works
 h += '<section style="background:var(--bg2);border-top:1px solid var(--line2);'+
  'border-bottom:1px solid var(--line2)"><div class="wrap">'+
  '<h2 class="sec reveal">'+t('how_t')+'</h2>'+
  '<p class="sec-sub reveal">'+t('how_s')+'</p>'+
  '<div class="grid g4 steps">'+
  [1,2,3,4].map(function(i){ return '<div class="step reveal"><div class="n">'+i+'</div>'+
   '<h4>'+t('s'+i+'t')+'</h4><p>'+t('s'+i+'d')+'</p></div>'; }).join('')+
  '</div></div></section>';

 // risk tiers
 h += '<section><div class="wrap">'+
  '<h2 class="sec reveal">'+t('tiers_t')+'</h2>'+
  '<p class="sec-sub reveal">'+t('tiers_s')+'</p>'+
  '<div class="grid g3">'+
  [['plow','2×','$50','3%',''],['pmid','3×','$100','5%','mid'],['phigh','5×','$200','10%','']]
  .map(function(x){ return '<div class="card tier '+x[4]+' reveal">'+
   '<div class="name">'+t(x[0])+'</div><div class="big2">'+x[1]+'</div>'+
   '<div class="per">'+t('lev')+'</div><ul>'+
   '<li>'+x[2]+' '+t('pertrade')+'</li><li>'+x[3]+' '+t('dl')+'</li>'+
   '<li>SL/TP auto</li></ul></div>'; }).join('')+
  '</div></div></section>';

 // security
 h += '<section style="background:var(--bg2);border-top:1px solid var(--line2)">'+
  '<div class="wrap" style="text-align:center;max-width:640px">'+
  '<h2 class="sec reveal">'+t('sec_t')+'</h2>'+
  '<p class="sec-sub reveal" style="margin-bottom:0">'+t('sec_s')+'</p>'+
  '</div></section>';

 h += pageFooter();
 document.getElementById('root').innerHTML = h;
 revealInit();
 if(!DEV && window.google && google.accounts){
  google.accounts.id.initialize({client_id: GCID, callback: onGoogle});
  google.accounts.id.renderButton(document.getElementById('gbtn'),
    {theme:'filled_black', size:'large', shape:'pill'});
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
<title>ArcusBot — Dashboard</title>
<link rel="icon" href='""" + _FAVICON + """'>
<style>""" + _STYLE + """</style></head><body>
<div id="root"></div>
<script>""" + _I18N + """
var LOGO = `""" + _LOGO + """`;
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
function card(title, inner){ return '<div class="card reveal"><h3>'+title+'</h3>'+inner+'</div>'; }

function render(){
 if(!ME){ document.getElementById('root').innerHTML=''; return; }
 var h = '<nav><span class="brand">'+LOGO+' ArcusBot</span>'+
  '<span class="nav-right"><span class="muted" style="font-size:.82rem">'+esc(ME.email)+'</span>'+
  langBtns()+'<button class="pill ghost small" onclick="logout()">'+t('logout')+'</button></span></nav>'+
  '<div class="app-wrap">';

 if(!ME.wallet){
  h += card(t('wtitle'),
   '<p class="muted" style="margin-top:0">'+t('wexplain')+'</p>'+
   '<button class="pill primary" id="cw" onclick="createWallet()">'+t('createw')+'</button>');
 } else if(!ME.wallet.revealed || KEYS){
  var inner = '<div class="warn">'+t('revealexplain')+'</div>';
  if(!KEYS){
   inner += '<p><button class="pill danger" onclick="reveal()">'+t('reveal')+'</button></p>';
  } else {
   inner += '<label>'+t('walletaddr')+'</label><div class="keybox">'+KEYS.address+'</div>'+
    '<label>'+t('wkey')+'</label><div class="keybox">'+KEYS.wallet_private_key+'</div>'+
    '<label>'+t('akey')+'</label><div class="keybox">'+KEYS.arcus_api_private_key+'</div>'+
    '<button class="pill primary" onclick="KEYS=null;load()">'+t('saved')+'</button>';
  }
  h += card(t('revealtitle'), inner);
 } else {
  // hesap
  var acc = '<p style="margin-top:0"><span class="chipmono">'+ME.wallet.address+'</span></p>';
  if(ACCT && ACCT.funded){
   acc += '<div class="statgrid">'+
    '<div class="stat"><label>'+t('equity')+'</label><div class="v">$'+ACCT.equity.toFixed(2)+'</div></div>'+
    '<div class="stat"><label>'+t('free')+'</label><div class="v">$'+(ACCT.freeCollateral||0).toFixed(2)+'</div></div></div>';
   acc += '<h3 style="margin-top:22px;font-size:.95rem">'+t('positions')+'</h3>';
   acc += ACCT.positions.length
    ? '<table><tr><th>Market</th><th>Side</th><th>Size</th><th>PnL</th></tr>'+
      ACCT.positions.map(function(p){return '<tr><td>'+p.market+'</td>'+
       '<td class="'+p.side.toLowerCase()+'">'+p.side+'</td><td>'+p.size+'</td>'+
       '<td class="'+(p.upnl>=0?'pos':'neg')+'">'+(p.upnl>=0?'+':'')+p.upnl.toFixed(2)+' $</td></tr>';}).join('')+
      '</table>'
    : '<p class="muted">'+t('nopos')+'</p>';
  } else {
   acc += '<div class="warn" style="margin-bottom:16px">'+t('notfunded')+'</div>'+
    '<p><button class="pill primary" id="fundbtn" onclick="fund()">'+t('fund')+'</button></p>'+
    '<div id="fundmsg" class="muted"></div>';
  }
  h += card(t('acct'), acc);

  // risk ayarlari
  var s = ME.settings || {};
  var risk = '<div class="presets">'+
   [['low','plow','2× · $50 · SL 20% · TP 40%'],
    ['mid','pmid','3× · $100 · SL 30% · TP 60%'],
    ['high','phigh','5× · $200 · SL 40% · TP 80%']].map(function(p){
    return '<button class="preset" id="p_'+p[0]+'" onclick="preset(\\''+p[0]+'\\')">'+
     '<div class="t">'+t(p[1])+'</div><div class="d">'+p[2]+'</div></button>';}).join('')+
   '</div><div class="fgrid">'+
   fld('leverage', t('lev'), s.leverage)+fld('margin_usd', t('margin'), s.margin_usd)+
   fld('sl_pct', t('sl'), s.sl_pct)+fld('tp_pct', t('tp'), s.tp_pct)+
   fld('max_daily_loss_pct', t('daily'), s.max_daily_loss_pct)+
   fld('adx_threshold', t('adx'), s.adx_threshold)+'</div>'+
   '<div style="margin-top:18px"><label>'+t('symbols')+'</label>'+
   '<div id="sympick" class="muted">…</div>'+
   '<p class="muted" style="font-size:.75rem;margin:10px 0 0">'+t('sym_note')+'</p></div>'+
   '<p style="margin:18px 0 0"><button class="pill primary" onclick="saveSettings()">'+
   t('save')+'</button></p><div id="msg"></div>';
  h += card(t('risk'), risk);

  // bot
  var on = s.bot_active;
  var bot = '<p style="margin-top:0"><span class="chip '+(on?'up':'')+'" '+
   'style="'+(on?'':'background:rgba(255,69,58,.15);color:var(--red)')+'">'+
   (on?t('boton'):t('botoff'))+'</span></p>'+
   '<button class="pill '+(on?'danger':'primary')+'" onclick="toggleBot('+(on?0:1)+')">'+
   (on?t('stop'):t('start'))+'</button><div id="botstate"></div>';
  h += card(t('bot'), bot);

  // telegram
  var tg = ME.telegram_linked
   ? '<p style="margin:0 0 12px"><span class="chip up">✓ '+t('tglinked')+'</span></p>'+
     '<button class="pill ghost small" onclick="tgUnlink()">'+t('tgchange')+'</button>'
   : '<button class="pill ghost" onclick="tgLink()">'+t('tglinkbtn')+'</button>'+
     '<div class="muted" style="margin-top:10px;font-size:.75rem">'+t('tgwarn')+'</div>'+
     '<div id="tgmsg" class="muted" style="margin-top:6px"></div>';
  h += card(t('tg'), tg);
 }
 h += '</div>' + pageFooter();
 document.getElementById('root').innerHTML = h;
 revealInit();
 setTimeout(loadState, 100);
 if(ME && ME.settings){
  SELECTED = (ME.settings.symbols||'').split(',').filter(Boolean);
  loadMarkets().then(renderSymPick);
 }
}

/* --- sembol secici --- */
var MARKETS = null, SELECTED = [], CURTAB = 'ALL';
async function loadMarkets(){
 if(MARKETS) return;
 try{ MARKETS = (await (await fetch('/api/markets')).json()).markets || []; }
 catch(e){ MARKETS = []; }
}
function renderSymPick(){
 var el = document.getElementById('sympick');
 if(!el || !MARKETS) return;
 var cats = ['ALL','CRYPTO','EQUITIES','COMMODITIES','INDICES'];
 var tabs = '<div class="symtabs">'+cats.map(function(c){
  return '<button class="tab'+(CURTAB===c?' act':'')+'" onclick="symTab(\\''+c+'\\')">'+
   t('cat_'+c)+'</button>';}).join('')+'</div>';
 var list = MARKETS.filter(function(m){ return CURTAB==='ALL'||m.category===CURTAB; });
 var chips = '<div class="chips">'+list.map(function(m){
  return '<button class="mchip'+(SELECTED.indexOf(m.name)>=0?' sel':'')+
   '" onclick="symToggle(\\''+m.name+'\\')">'+m.name.replace('-USD','')+'</button>';
 }).join('')+'</div>';
 var act = '<div style="margin-top:12px">'+
  '<button class="pill ghost small" onclick="symAll()">'+t('selectall')+'</button> '+
  '<button class="pill ghost small" onclick="symClear()">'+t('clearall')+'</button>'+
  '<span class="muted" style="margin-left:10px">'+SELECTED.length+' '+t('selected')+'</span></div>';
 el.innerHTML = tabs + chips + act;
 el.classList.remove('muted');
}
function symTab(c){ CURTAB = c; renderSymPick(); }
function symToggle(name){
 var i = SELECTED.indexOf(name);
 if(i>=0) SELECTED.splice(i,1); else SELECTED.push(name);
 renderSymPick();
}
function symAll(){
 MARKETS.filter(function(m){ return CURTAB==='ALL'||m.category===CURTAB; })
  .forEach(function(m){ if(SELECTED.indexOf(m.name)<0) SELECTED.push(m.name); });
 renderSymPick();
}
function symClear(){ SELECTED = []; renderSymPick(); }
function fld(id, label, val){
 return '<div><label>'+label+'</label><input id="f_'+id+'" type="number" value="'+esc(val)+'"></div>';
}
function preset(p){
 var v = PRESETS[p];
 for(var k in v){ var el=document.getElementById('f_'+k); if(el) el.value=v[k]; }
 ['p_low','p_mid','p_high'].forEach(function(id){
   var el=document.getElementById(id); if(el) el.classList.remove('sel');});
 var sel=document.getElementById('p_'+p); if(sel) sel.classList.add('sel');
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
 var b = {symbols: SELECTED.join(',')};
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
async function fund(){
 var b = document.getElementById('fundbtn'); if(b) b.disabled = true;
 var r = await fetch('/api/fund', {method:'POST',
   headers:{'Content-Type':'application/json'}, body:JSON.stringify({amount_usd:10000})});
 if(!r.ok){ alert((await r.json()).error); if(b) b.disabled=false; return; }
 pollFund();
}
async function pollFund(){
 var d = await (await fetch('/api/fund/status')).json();
 var m = document.getElementById('fundmsg');
 if(d.error){ if(m){ m.textContent=t('err')+d.error; m.className='neg'; } return; }
 if(m){ m.textContent = t('fundprog') + (d.stage||'…'); m.className='muted'; }
 if(d.done){ if(m) m.textContent = t('funddone');
  setTimeout(load, 15000); setTimeout(load, 45000); return; }
 setTimeout(pollFund, 4000);
}
async function tgLink(){
 var r = await fetch('/api/telegram/link', {method:'POST'});
 var d = await r.json();
 if(d.ok){
  // window.open popup engeline takiliyor — tiklanabilir gercek link goster
  var m = document.getElementById('tgmsg');
  if(m) m.innerHTML =
   '<a class="pill primary" style="display:inline-block;margin-top:10px;'+
   'text-decoration:none" href="'+d.url+'" target="_blank" rel="noopener">'+
   'Open @arcusTradeBot →</a>'+
   '<div class="muted" style="margin-top:10px">'+t('tgopen')+'</div>';
  pollTg();
 } else alert(d.error||'?');
}
async function tgUnlink(){
 await fetch('/api/telegram/unlink', {method:'POST'});
 await load();
}
async function pollTg(){
 var me = await (await fetch('/api/me')).json();
 if(me.telegram_linked){ ME = me; render(); return; }
 setTimeout(pollTg, 4000);
}
async function loadState(){
 if(!(ME && ME.settings && ME.settings.bot_active)) return;
 var el = document.getElementById('botstate'); if(!el) return;
 try{
  var d = await (await fetch('/api/botstate')).json();
  var s = d.snapshot || {};
  var hh = '<p class="muted" style="margin:14px 0 6px">'+(d.running?t('engon'):t('engoff'))+'</p>';
  if(s.equity!=null) hh += '<p style="margin:0 0 10px">Equity: <b>$'+s.equity.toFixed(2)+'</b></p>';
  var ev = d.events || [];
  if(ev.length) hh += '<label>'+t('events')+'</label><pre class="feed">'+
    ev.map(esc).join('\\n')+'</pre>';
  el.innerHTML = hh;
 }catch(e){}
}
setInterval(loadState, 10000);
load();
</script></body></html>""")
