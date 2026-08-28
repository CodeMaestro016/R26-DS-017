"""Global visual language for the local research showcase."""

from nicegui import ui


CSS = r"""
:root { --navy:#071426; --navy2:#0b2038; --cyan:#27c7e8; --blue:#2f7df4;
  --ink:#132238; --muted:#64748b; --line:#dce7f1; --paper:#f5f9fc; }
* { box-sizing:border-box; }
body { margin:0; background:var(--paper); color:var(--ink); font-family:Inter,Segoe UI,sans-serif; }
.page-shell { width:100%; max-width:1440px; margin:auto; padding:0 42px; }
.nav-glass { background:rgba(5,18,34,.94)!important; backdrop-filter:blur(18px); border-bottom:1px solid rgba(103,210,239,.16); }
.brand-mark { width:38px; height:38px; border-radius:12px; display:grid; place-items:center; color:white;
  background:linear-gradient(135deg,var(--cyan),var(--blue)); box-shadow:0 0 28px rgba(39,199,232,.25); }
.brand-logo { width:42px; height:42px; object-fit:contain; filter:drop-shadow(0 4px 12px rgba(32,201,231,.22)); }
.hero { min-height:680px; color:white; overflow:hidden; position:relative;
  background:radial-gradient(circle at 78% 34%,rgba(38,190,224,.2),transparent 28%),linear-gradient(135deg,#061325,#0b2440 58%,#0c3148); }
.hero:before { content:''; position:absolute; inset:0; opacity:.22; background-image:linear-gradient(rgba(64,201,232,.15) 1px,transparent 1px),linear-gradient(90deg,rgba(64,201,232,.15) 1px,transparent 1px); background-size:52px 52px; mask-image:linear-gradient(to right,transparent,black); }
.hero-copy { position:relative; z-index:2; max-width:720px; padding:132px 0 100px; }
.eyebrow { color:#73dff3; font-size:.76rem; font-weight:800; letter-spacing:.22em; text-transform:uppercase; }
.hero-title { font-size:clamp(3.3rem,7vw,6.8rem); line-height:.88; letter-spacing:-.055em; font-weight:850; margin:20px 0 24px; }
.hero-subtitle { font-size:clamp(1.25rem,2vw,1.8rem); color:#b9d8e8; font-weight:450; max-width:720px; line-height:1.35; }
.hero-description { color:#a8bed0; font-size:1.05rem; line-height:1.75; max-width:680px; margin-top:24px; }
.hero-visual { position:absolute; z-index:1; right:max(2vw,18px); top:94px; width:min(47vw,710px); height:540px; display:flex; align-items:center; justify-content:center; background:radial-gradient(circle,rgba(30,174,211,.15),transparent 65%); }
.hero-main-image { width:100%; height:100%; object-fit:contain; filter:drop-shadow(0 26px 38px rgba(0,0,0,.28)); }
.section { padding:86px 0; }
.section-dark { background:var(--navy); color:white; }
.section-title { font-size:clamp(2rem,4vw,3.2rem); letter-spacing:-.035em; font-weight:780; margin:10px 0 16px; }
.section-copy { color:var(--muted); max-width:780px; line-height:1.75; font-size:1.02rem; }
.section-dark .section-copy { color:#a9bdce; }
.component-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:24px; width:100%; margin-top:38px; }
.component-card { background:white; border:1px solid var(--line); border-radius:24px; padding:0; overflow:hidden; transition:.22s ease; box-shadow:0 12px 32px rgba(23,50,76,.06); min-height:500px; }
.component-card:hover { transform:translateY(-6px); box-shadow:0 22px 50px rgba(23,50,76,.13); border-color:#9cddec; }
.component-card.live { color:white; background:linear-gradient(145deg,#0b2844,#0b3a54); border-color:#2c7893; }
.component-image-wrap { width:100%; aspect-ratio:16/9; overflow:hidden; display:flex; align-items:center; justify-content:center; position:relative; background:linear-gradient(145deg,#0b2038,#0e4660); }
.component-image-wrap:after { content:''; position:absolute; inset:auto 0 0; height:35%; background:linear-gradient(to top,rgba(4,18,32,.46),transparent); pointer-events:none; }
.component-image { width:100%; height:100%; object-fit:cover; transition:transform .35s ease; }
.component-card:hover .component-image { transform:scale(1.035); }
.component-card-body { padding:27px 30px 30px; }
.component-number { font-size:3.2rem; font-weight:850; color:#d9e6ef; letter-spacing:-.06em; }
.live .component-number { color:rgba(111,223,244,.32); }
.component-title { font-size:1.35rem; line-height:1.35; font-weight:740; margin:18px 0 12px; }
.component-description { color:var(--muted); line-height:1.65; min-height:80px; }
.live .component-description { color:#b7cedd; }
.chip { display:inline-flex; padding:7px 11px; border-radius:999px; background:#edf5fa; color:#32536b; font-size:.72rem; font-weight:700; margin:4px; }
.live .chip { background:rgba(80,211,236,.12); color:#8ce5f5; }
.badge-live,.badge-reserved { display:inline-flex; padding:7px 11px; border-radius:999px; font-size:.68rem; letter-spacing:.08em; font-weight:850; }
.badge-live { background:#d9f8ef; color:#087a5b; } .badge-reserved { background:#edf1f5; color:#64748b; }
.btn-primary,.btn-secondary { border-radius:12px!important; min-height:46px; font-weight:750; letter-spacing:.01em; }
.btn-primary { background:linear-gradient(135deg,#17badb,#2878ef)!important; color:white!important; }
.btn-secondary { background:transparent!important; color:inherit!important; border:1px solid rgba(137,190,211,.55); }
.detail-hero { padding:106px 0 70px; color:white; background:linear-gradient(135deg,#071426,#0a304c); }
.detail-number { color:#57d6ee; font-size:1rem; font-weight:850; letter-spacing:.2em; }
.detail-title { max-width:1000px; font-size:clamp(2.3rem,5vw,4.8rem); line-height:1.03; letter-spacing:-.045em; font-weight:820; margin:18px 0; }
.info-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:16px; width:100%; }
.info-card,.metric-card { background:white; border:1px solid var(--line); border-radius:18px; padding:22px; box-shadow:0 8px 24px rgba(23,50,76,.05); }
.metric-value { font-size:2rem; font-weight:830; color:#0b3150; }
.metric-label { color:#708297; font-size:.78rem; line-height:1.4; margin-top:6px; }
.architecture-flow { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; width:100%; margin-top:30px; }
.flow-node { min-height:94px; padding:18px; border-radius:16px; color:white; background:linear-gradient(145deg,#102a43,#134a62); border:1px solid #2f6a7e; display:flex; align-items:center; justify-content:center; text-align:center; font-weight:680; position:relative; }
.flow-node:not(:last-child):after { content:'→'; position:absolute; right:-13px; color:#27c7e8; z-index:2; }
.fallback-visual { min-height:310px; border-radius:24px; color:white; overflow:hidden; position:relative; display:flex; align-items:center; justify-content:center; background:radial-gradient(circle at 50% 50%,rgba(44,208,235,.27),transparent 35%),linear-gradient(145deg,#071426,#0d3a55); }
.fallback-visual:before,.fallback-visual:after { content:''; position:absolute; background:rgba(96,226,246,.5); }
.fallback-visual:before { width:78%; height:2px; } .fallback-visual:after { height:78%; width:2px; }
.detail-image { min-height:310px; max-height:480px; aspect-ratio:16/9; object-fit:cover; border-radius:24px; box-shadow:0 16px 38px rgba(23,50,76,.12); }
.result-panel { border-radius:24px; border:1px solid #cfe2ee; background:white; padding:30px; width:100%; }
.disclaimer { background:#fff8df; border:1px solid #f1d98d; border-radius:16px; padding:18px; color:#765a12; }
.action-card { background:#f1f7fb; border-left:3px solid #21bcd9; border-radius:10px; padding:12px 14px; font-size:.84rem; }
.reserved-panel { min-height:230px; border:1px dashed #9eb7ca; border-radius:22px; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; color:#61778a; background:#f7fafc; padding:34px; }
.direction-card { background:white; border:1px solid var(--line); border-radius:18px; padding:22px; box-shadow:0 8px 24px rgba(23,50,76,.05); }
.institution-section { background:#edf5fa; }
.institution-card { width:100%; display:flex; align-items:center; gap:40px; border-radius:24px; background:white; padding:32px 42px; border:1px solid var(--line); box-shadow:0 14px 34px rgba(23,50,76,.07); }
.institution-logo-wrap { width:150px; height:120px; flex:none; display:flex; align-items:center; justify-content:center; }
.institution-logo { width:100%; height:100%; object-fit:contain; }
.team-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:20px; width:100%; }
.person-card { min-height:420px; background:white; border:1px solid var(--line); border-radius:22px; padding:28px 20px; text-align:center; display:flex; flex-direction:column; align-items:center; transition:.22s ease; box-shadow:0 10px 30px rgba(23,50,76,.06); }
.person-card:hover { transform:translateY(-5px); box-shadow:0 20px 42px rgba(23,50,76,.12); }
.person-portrait { width:124px; height:124px; border-radius:28px; object-fit:cover; border:4px solid white; box-shadow:0 10px 28px rgba(11,49,80,.17); }
.person-portrait-large { width:138px; height:138px; border-radius:30px; object-fit:cover; flex:none; border:3px solid rgba(106,220,240,.3); }
.initials-avatar { display:flex; align-items:center; justify-content:center; background:linear-gradient(135deg,#14b8d4,#2878ef); color:white; font-size:2rem; font-weight:850; letter-spacing:.04em; }
.person-number { color:#159fc2; font-weight:850; font-size:1.15rem; margin-top:18px; }
.person-role,.supervisor-role { display:inline-flex; padding:6px 10px; border-radius:999px; background:#e5f8fc; color:#087895; font-size:.65rem; font-weight:850; letter-spacing:.1em; margin-top:8px; }
.person-name { color:#10283e; font-weight:850; font-size:1.05rem; letter-spacing:.02em; margin-top:12px; }
.person-department { color:#718397; font-size:.82rem; margin-top:8px; min-height:40px; }
.person-email { color:#26637c; font-size:.78rem; text-decoration:none; }
.supervisor-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:24px; width:100%; }
.supervisor-card { display:flex; align-items:center; gap:28px; border:1px solid #28536d; border-radius:24px; padding:30px; background:linear-gradient(145deg,#0b243d,#0c3a50); box-shadow:0 18px 40px rgba(0,0,0,.16); }
.supervisor-role { width:max-content; background:rgba(62,210,235,.13); color:#7ce4f5; margin-top:0; }
.footer { background:#061221; color:#8fa9bc; border-top:1px solid #17334b; padding:38px 0; }
@media(max-width:1100px){ .hero-copy{max-width:58%}.hero-visual{width:48vw;opacity:.82}.team-grid{grid-template-columns:repeat(2,minmax(0,1fr))} }
@media(max-width:900px){ .page-shell{padding:0 22px}.component-grid,.info-grid{grid-template-columns:1fr 1fr}.architecture-flow{grid-template-columns:1fr 1fr}.hero-visual{position:relative;inset:auto;width:100%;height:330px;margin-top:-90px;padding-bottom:30px}.hero-copy{max-width:100%;padding-top:105px;padding-bottom:80px}.nav-links{display:none}.institution-card{padding:28px;gap:24px}.supervisor-card{align-items:flex-start} }
@media(max-width:600px){ .component-grid,.info-grid,.architecture-flow,.team-grid,.supervisor-grid{grid-template-columns:1fr}.hero-title{font-size:3.2rem}.section{padding:60px 0}.flow-node:after{display:none}.institution-card,.supervisor-card{flex-direction:column;text-align:center}.institution-logo-wrap{width:120px;height:95px}.person-card{min-height:390px} }
"""


def apply_theme():
    ui.colors(primary="#168fba", secondary="#2f7df4", accent="#27c7e8")
    ui.add_head_html('<meta name="theme-color" content="#071426">')
    ui.add_css(CSS)
