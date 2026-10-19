"""Global visual language for the local research showcase."""

from nicegui import ui


CSS = r"""
:root {
  --navy:#071426;
  --navy2:#0b2038;
  --cyan:#27c7e8;
  --blue:#2f7df4;
  --ink:#132238;
  --muted:#64748b;
  --line:#dce7f1;
  --paper:#f5f9fc;
}

* {
  box-sizing:border-box;
}

body {
  margin:0;
  background:var(--paper);
  color:var(--ink);
  font-family:Inter,Segoe UI,sans-serif;
}

.page-shell {
  width:100%;
  max-width:1440px;
  margin:auto;
  padding:0 42px;
}

.nav-glass {
  background:rgba(5,18,34,.94)!important;
  backdrop-filter:blur(18px);
  border-bottom:1px solid rgba(103,210,239,.16);
}

.brand-mark {
  width:38px;
  height:38px;
  border-radius:12px;
  display:grid;
  place-items:center;
  color:white;
  background:linear-gradient(135deg,var(--cyan),var(--blue));
  box-shadow:0 0 28px rgba(39,199,232,.25);
}

.brand-logo {
  width:42px;
  height:42px;
  object-fit:contain;
  filter:drop-shadow(0 4px 12px rgba(32,201,231,.22));
}


/* ============================================================
   HOME HERO
   ============================================================ */

.hero {
  min-height:680px;
  color:white;
  overflow:hidden;
  position:relative;
  background:
    radial-gradient(
      circle at 78% 34%,
      rgba(38,190,224,.2),
      transparent 28%
    ),
    linear-gradient(
      135deg,
      #061325,
      #0b2440 58%,
      #0c3148
    );
}

.hero:before {
  content:'';
  position:absolute;
  inset:0;
  opacity:.22;
  background-image:
    linear-gradient(
      rgba(64,201,232,.15) 1px,
      transparent 1px
    ),
    linear-gradient(
      90deg,
      rgba(64,201,232,.15) 1px,
      transparent 1px
    );
  background-size:52px 52px;
  mask-image:linear-gradient(to right,transparent,black);
}

.hero-copy {
  position:relative;
  z-index:2;
  max-width:720px;
  padding:132px 0 100px;
}

.eyebrow {
  color:#73dff3;
  font-size:.76rem;
  font-weight:800;
  letter-spacing:.22em;
  text-transform:uppercase;
}

.hero-title {
  font-size:clamp(3.3rem,7vw,6.8rem);
  line-height:.88;
  letter-spacing:-.055em;
  font-weight:850;
  margin:20px 0 24px;
}

.hero-subtitle {
  font-size:clamp(1.25rem,2vw,1.8rem);
  color:#b9d8e8;
  font-weight:450;
  max-width:720px;
  line-height:1.35;
}

.hero-description {
  color:#a8bed0;
  font-size:1.05rem;
  line-height:1.75;
  max-width:680px;
  margin-top:24px;
}

.hero-visual {
  position:absolute;
  z-index:1;
  right:max(2vw,18px);
  top:94px;
  width:min(47vw,710px);
  height:540px;
  display:flex;
  align-items:center;
  justify-content:center;
  background:
    radial-gradient(
      circle,
      rgba(30,174,211,.15),
      transparent 65%
    );
}

.hero-main-image {
  width:100%;
  height:100%;
  object-fit:contain;
  filter:drop-shadow(0 26px 38px rgba(0,0,0,.28));
}


/* ============================================================
   SECTIONS
   ============================================================ */

.section {
  padding:86px 0;
}

.section-dark {
  background:var(--navy);
  color:white;
}

.section-title {
  font-size:clamp(2rem,4vw,3.2rem);
  letter-spacing:-.035em;
  font-weight:780;
  margin:10px 0 16px;
}

.section-copy {
  color:var(--muted);
  max-width:780px;
  line-height:1.75;
  font-size:1.02rem;
}

.section-dark .section-copy {
  color:#a9bdce;
}


/* ============================================================
   COMPONENT CARDS
   ============================================================ */

.component-grid {
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:24px;
  width:100%;
  margin-top:38px;
}

.component-card {
  background:white;
  border:1px solid var(--line);
  border-radius:24px;
  padding:0;
  overflow:hidden;
  transition:.22s ease;
  box-shadow:0 12px 32px rgba(23,50,76,.06);
  min-height:500px;
}

.component-card:hover {
  transform:translateY(-6px);
  box-shadow:0 22px 50px rgba(23,50,76,.13);
  border-color:#9cddec;
}

.component-card.live {
  color:white;
  background:linear-gradient(145deg,#0b2844,#0b3a54);
  border-color:#2c7893;
}

.component-image-wrap {
  width:100%;
  aspect-ratio:16/9;
  overflow:hidden;
  display:flex;
  align-items:center;
  justify-content:center;
  position:relative;
  background:linear-gradient(145deg,#0b2038,#0e4660);
}

.component-image-wrap:after {
  content:'';
  position:absolute;
  inset:auto 0 0;
  height:35%;
  background:
    linear-gradient(
      to top,
      rgba(4,18,32,.46),
      transparent
    );
  pointer-events:none;
}

.component-image {
  width:100%;
  height:100%;
  object-fit:cover;
  transition:transform .35s ease;
}

.component-card:hover .component-image {
  transform:scale(1.035);
}

.component-card-body {
  padding:27px 30px 30px;
}

.component-number {
  font-size:3.2rem;
  font-weight:850;
  color:#d9e6ef;
  letter-spacing:-.06em;
}

.live .component-number {
  color:rgba(111,223,244,.32);
}

.component-title {
  font-size:1.35rem;
  line-height:1.35;
  font-weight:740;
  margin:18px 0 12px;
}

.component-description {
  color:var(--muted);
  line-height:1.65;
  min-height:80px;
}

.live .component-description {
  color:#b7cedd;
}

.chip {
  display:inline-flex;
  padding:7px 11px;
  border-radius:999px;
  background:#edf5fa;
  color:#32536b;
  font-size:.72rem;
  font-weight:700;
  margin:4px;
}

.live .chip {
  background:rgba(80,211,236,.12);
  color:#8ce5f5;
}

.badge-live,
.badge-reserved {
  display:inline-flex;
  padding:7px 11px;
  border-radius:999px;
  font-size:.68rem;
  letter-spacing:.08em;
  font-weight:850;
}

.badge-live {
  background:#d9f8ef;
  color:#087a5b;
}

.badge-reserved {
  background:#edf1f5;
  color:#64748b;
}


/* ============================================================
   BUTTONS
   ============================================================ */

.btn-primary,
.btn-secondary {
  border-radius:12px!important;
  min-height:46px;
  font-weight:750;
  letter-spacing:.01em;
}

.btn-primary {
  background:
    linear-gradient(
      135deg,
      #17badb,
      #2878ef
    )!important;
  color:white!important;
}

.btn-secondary {
  background:transparent!important;
  color:inherit!important;
  border:1px solid rgba(137,190,211,.55);
}


/* ============================================================
   COMPONENT DETAIL PAGE
   ============================================================ */

.detail-hero {
  padding:106px 0 70px;
  color:white;
  background:linear-gradient(135deg,#071426,#0a304c);
}

.detail-number {
  color:#57d6ee;
  font-size:1rem;
  font-weight:850;
  letter-spacing:.2em;
}

.detail-title {
  max-width:1000px;
  font-size:clamp(2.3rem,5vw,4.8rem);
  line-height:1.03;
  letter-spacing:-.045em;
  font-weight:820;
  margin:18px 0;
}


/* ============================================================
   INFO / METRIC CARDS
   ============================================================ */

.info-grid {
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  gap:16px;
  width:100%;
}

.info-card,
.metric-card {
  background:white;
  border:1px solid var(--line);
  border-radius:18px;
  padding:22px;
  box-shadow:0 8px 24px rgba(23,50,76,.05);
}

.metric-value {
  font-size:2rem;
  font-weight:830;
  color:#0b3150;
}

.metric-label {
  color:#708297;
  font-size:.78rem;
  line-height:1.4;
  margin-top:6px;
}


/* ============================================================
   ARCHITECTURE FLOW
   ============================================================ */

.architecture-flow {
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  gap:14px;
  width:100%;
  margin-top:30px;
}

.flow-node {
  min-height:94px;
  padding:18px;
  border-radius:16px;
  color:white;
  background:linear-gradient(145deg,#102a43,#134a62);
  border:1px solid #2f6a7e;
  display:flex;
  align-items:center;
  justify-content:center;
  text-align:center;
  font-weight:680;
  position:relative;
}

.flow-node:not(:last-child):after {
  content:'→';
  position:absolute;
  right:-13px;
  color:#27c7e8;
  z-index:2;
}


/* ============================================================
   SHARED VISUALS
   ============================================================ */

.fallback-visual {
  min-height:310px;
  border-radius:24px;
  color:white;
  overflow:hidden;
  position:relative;
  display:flex;
  align-items:center;
  justify-content:center;
  background:
    radial-gradient(
      circle at 50% 50%,
      rgba(44,208,235,.27),
      transparent 35%
    ),
    linear-gradient(
      145deg,
      #071426,
      #0d3a55
    );
}

.fallback-visual:before,
.fallback-visual:after {
  content:'';
  position:absolute;
  background:rgba(96,226,246,.5);
}

.fallback-visual:before {
  width:78%;
  height:2px;
}

.fallback-visual:after {
  height:78%;
  width:2px;
}

.detail-image {
  min-height:310px;
  max-height:480px;
  aspect-ratio:16/9;
  object-fit:cover;
  border-radius:24px;
  box-shadow:0 16px 38px rgba(23,50,76,.12);
}

.result-panel {
  border-radius:24px;
  border:1px solid #cfe2ee;
  background:white;
  padding:30px;
  width:100%;
}


/* ============================================================
   COMPONENT 2 - SUMO LIVE VIEW
   Preserved from original theme
   ============================================================ */

.dedicated-live-view {
  background:#16202a;
  color:#eef5f8;
  padding:18px 24px 26px;
  gap:14px;
}

.live-view-header {
  min-height:52px;
  border-bottom:1px solid #42505b;
  padding-bottom:12px;
}

.live-view-empty {
  min-height:70vh;
  color:#cdd9df;
}

.live-view-time,
.live-view-mappo,
.live-view-status {
  font-weight:800;
  letter-spacing:.08em;
}

.sumo-live-canvas {
  display:block;
  width:100%;
  max-height:74vh;
  border:2px solid #8ca096;
  background:#57964c;
}

.sumo-road-boundaries polyline {
  fill:none;
  stroke:#f1f1e8;
  stroke-linecap:butt;
  stroke-linejoin:round;
}

.sumo-road-asphalt polyline {
  fill:none;
  stroke:#202326;
  stroke-linecap:butt;
  stroke-linejoin:round;
}

.sumo-junction {
  fill:#202326;
}

.sumo-car-label rect {
  fill:rgba(12,20,26,.72);
}

.sumo-car-label text {
  fill:#fff;
  font:600 8px system-ui,sans-serif;
}

.live-view-legend,
.live-view-details {
  background:#222e37;
  padding:11px 16px;
  border-radius:8px;
}

.live-view-workspace {
  gap:18px;
}

.scenario-sidebar {
  width:290px;
  min-width:290px;
  background:#202c36;
  border:1px solid #40515e;
  border-radius:12px;
  padding:18px;
  gap:12px;
}

.scenario-sidebar-title {
  color:#65d9ec;
  font-size:.74rem;
  font-weight:850;
  letter-spacing:.12em;
}

.scenario-sidebar .q-radio {
  align-items:flex-start;
  margin:3px 0;
}

.scenario-sidebar .q-radio__label {
  font-size:.82rem;
  line-height:1.25;
  color:#e7f0f4;
}

.scenario-description {
  color:#b9cad3;
  font-size:.78rem;
  line-height:1.45;
}

.scenario-tag {
  background:#304653;
  color:#8de5f4;
  border-radius:999px;
  padding:4px 7px;
  font-size:.62rem;
  font-weight:800;
}

.scenario-detail-label {
  color:#6edbed;
  font-size:.66rem;
  font-weight:800;
  letter-spacing:.08em;
  margin-top:4px;
}

.scenario-detail-value {
  color:#d8e4e9;
  font-size:.72rem;
  line-height:1.35;
}

.live-view-main {
  gap:12px;
}

@media(max-width:900px) {
  .live-view-workspace {
    flex-direction:column!important;
  }

  .scenario-sidebar {
    width:100%;
    min-width:0;
  }
}


/* ============================================================
   SHARED DETAIL PANELS
   ============================================================ */

.disclaimer {
  background:#fff8df;
  border:1px solid #f1d98d;
  border-radius:16px;
  padding:18px;
  color:#765a12;
}

.action-card {
  background:#f1f7fb;
  border-left:3px solid #21bcd9;
  border-radius:10px;
  padding:12px 14px;
  font-size:.84rem;
}

.reserved-panel {
  min-height:230px;
  border:1px dashed #9eb7ca;
  border-radius:22px;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  text-align:center;
  color:#61778a;
  background:#f7fafc;
  padding:34px;
}


/* ============================================================
   COMPONENT 3 - LIVE CARLA PANEL
   Added from updated theme
   ============================================================ */

.reachability-dot {
  width:10px;
  height:10px;
  border-radius:50%;
  display:inline-block;
}

/*
   Live CARLA demo panel.

   Matches the standalone CARLA interface's dark navy/cyan
   palette and two-column layout.
*/

.carla-live-panel {
  background:#0a1420;
  border:1px solid #1c2e3f;
  border-radius:14px;
  overflow:hidden;
  color:#e6ecf1;
  font-family:
    'Inter',
    -apple-system,
    'Segoe UI',
    Roboto,
    Helvetica,
    Arial,
    sans-serif;
}

.carla-live-grid {
  display:flex;
  align-items:flex-start;
  flex-wrap:wrap;
  width:100%;
}

.carla-scenario-panel {
  width:320px;
  flex:none;
  border-right:1px solid #1c2e3f;
  padding:24px 22px;
  display:flex;
  flex-direction:column;
  gap:16px;
  box-sizing:border-box;
}

.carla-stage {
  flex:1;
  min-width:320px;
  padding:24px;
  display:flex;
  flex-direction:column;
  gap:16px;
  box-sizing:border-box;
}

@media(max-width:860px) {
  .carla-scenario-panel {
    width:100%;
    border-right:none;
    border-bottom:1px solid #1c2e3f;
  }
}

.carla-scenario-card {
  background:#10202f;
  border:1px solid #1c2e3f;
  border-radius:10px;
  padding:16px 18px;
  display:flex;
  flex-direction:column;
  gap:8px;
  box-shadow:
    0 1px 0 rgba(0,0,0,.2),
    0 4px 12px rgba(0,0,0,.18);
  transition:border-color .15s ease;
}

.carla-scenario-card .font-bold {
  color:#fff;
}

.carla-scenario-card.active {
  border-color:#3fb8d6;
}

.carla-video-frame {
  position:relative;
  width:100%;
  aspect-ratio:16/9;
  border-radius:10px;
  overflow:hidden;
  background:#050c14;
  border:1px solid #1c2e3f;
}

.carla-video-frame img {
  width:100%;
  height:100%;
  object-fit:cover;
  display:block;
}

.carla-no-signal {
  position:absolute;
  inset:0;
  display:flex;
  align-items:center;
  justify-content:center;
  color:#7c8fa0;
  font-family:
    'JetBrains Mono',
    ui-monospace,
    'SF Mono',
    'Cascadia Code',
    Consolas,
    monospace;
  font-size:.75rem;
  letter-spacing:.08em;
  text-transform:uppercase;
}

.carla-hud-readout {
  position:absolute;
  top:12px;
  left:12px;
  display:flex;
  gap:8px;
  pointer-events:none;
}

.carla-hud-chip {
  background:rgba(6,14,22,.82);
  border:1px solid #1c2e3f;
  border-radius:7px;
  padding:6px 11px;
  font-family:
    'JetBrains Mono',
    ui-monospace,
    'SF Mono',
    'Cascadia Code',
    Consolas,
    monospace;
}

.carla-hud-label {
  font-size:9px;
  letter-spacing:.08em;
  text-transform:uppercase;
  color:#7c8fa0;
}

.carla-hud-value {
  font-size:14px;
  font-weight:600;
  color:#3fb8d6;
}

.carla-confidence-wrap {
  position:absolute;
  bottom:0;
  left:0;
  right:0;
  display:flex;
  align-items:center;
  gap:10px;
  padding:9px 12px;
  background:rgba(6,14,22,.82);
  border-top:1px solid #1c2e3f;
}

.carla-confidence-label {
  font-family:
    'JetBrains Mono',
    ui-monospace,
    'SF Mono',
    'Cascadia Code',
    Consolas,
    monospace;
  font-size:10px;
  color:#7c8fa0;
  letter-spacing:.04em;
  flex:none;
}

.carla-confidence-bar {
  flex:1;
  height:5px;
  background:rgba(255,255,255,.08);
  border-radius:3px;
  overflow:hidden;
}

.carla-confidence-fill {
  height:100%;
  width:0%;
  background:#3fb8d6;
}

.carla-decision-row {
  display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:10px;
}

@media(max-width:600px) {
  .carla-decision-row {
    grid-template-columns:repeat(2,1fr);
  }
}

.carla-stat {
  background:#10202f;
  border:1px solid #1c2e3f;
  border-radius:10px;
  padding:13px 15px;
}

.carla-stat-label {
  font-family:'Inter',sans-serif;
  font-size:10px;
  font-weight:600;
  letter-spacing:.06em;
  text-transform:uppercase;
  color:#7c8fa0;
  margin-bottom:6px;
  display:block;
}

.carla-stat-value {
  font-family:
    'JetBrains Mono',
    ui-monospace,
    'SF Mono',
    'Cascadia Code',
    Consolas,
    monospace;
  font-size:15.5px;
  font-weight:600;
  color:#fff;
}

.carla-stat-value.action-MAINTAIN {
  color:#5cb894;
}

.carla-stat-value.action-SLOW_DOWN {
  color:#d3a15a;
}

.carla-stat-value.action-STOP {
  color:#d6685f;
}

.carla-progress {
  height:4px;
  background:#1c2e3f;
  border-radius:2px;
  overflow:hidden;
}

.carla-progress-fill {
  height:100%;
  background:#3fb8d6;
  width:0%;
}

.carla-message-line {
  font-family:
    'JetBrains Mono',
    ui-monospace,
    'SF Mono',
    'Cascadia Code',
    Consolas,
    monospace;
  font-size:12.5px;
  color:#7c8fa0;
}

.carla-log-heading {
  margin:0;
  font-family:'Inter',sans-serif;
  font-size:10px;
  font-weight:600;
  letter-spacing:.08em;
  text-transform:uppercase;
  color:#7c8fa0;
}

.carla-log {
  background:#10202f;
  border:1px solid #1c2e3f;
  border-radius:10px;
  padding:15px 17px;
  min-height:120px;
  max-height:220px;
  overflow-y:auto;
  font-family:
    'JetBrains Mono',
    ui-monospace,
    'SF Mono',
    'Cascadia Code',
    Consolas,
    monospace;
  font-size:12px;
}

.carla-log-line {
  display:flex;
  gap:10px;
  padding:4px 0;
  border-bottom:1px solid rgba(255,255,255,.04);
  color:#e6ecf1;
}

.carla-log-t {
  color:#7c8fa0;
  flex-shrink:0;
}

.carla-run-btn {
  color:#9fc4d2!important;
  border-color:#1c2e3f!important;
}

.carla-run-btn:hover {
  color:#3fb8d6!important;
  border-color:#3fb8d6!important;
}

.carla-stop-btn {
  color:#d6685f!important;
  border-color:#d6685f!important;
}

.carla-error-text {
  color:#d6685f!important;
}

.carla-muted-text {
  color:#7c8fa0!important;
}


/* ============================================================
   DIRECTION / INSTITUTION
   ============================================================ */

.direction-card {
  background:white;
  border:1px solid var(--line);
  border-radius:18px;
  padding:22px;
  box-shadow:0 8px 24px rgba(23,50,76,.05);
}

.institution-section {
  background:#edf5fa;
}

.institution-card {
  width:100%;
  display:flex;
  align-items:center;
  gap:40px;
  border-radius:24px;
  background:white;
  padding:32px 42px;
  border:1px solid var(--line);
  box-shadow:0 14px 34px rgba(23,50,76,.07);
}

.institution-logo-wrap {
  width:150px;
  height:120px;
  flex:none;
  display:flex;
  align-items:center;
  justify-content:center;
}

.institution-logo {
  width:100%;
  height:100%;
  object-fit:contain;
}


/* ============================================================
   TEAM
   ============================================================ */

.team-grid {
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  gap:20px;
  width:100%;
}

.person-card {
  min-height:420px;
  background:white;
  border:1px solid var(--line);
  border-radius:22px;
  padding:28px 20px;
  text-align:center;
  display:flex;
  flex-direction:column;
  align-items:center;
  transition:.22s ease;
  box-shadow:0 10px 30px rgba(23,50,76,.06);
}

.person-card:hover {
  transform:translateY(-5px);
  box-shadow:0 20px 42px rgba(23,50,76,.12);
}

.person-portrait {
  width:124px;
  height:124px;
  border-radius:28px;
  object-fit:cover;
  border:4px solid white;
  box-shadow:0 10px 28px rgba(11,49,80,.17);
}

.person-portrait-large {
  width:138px;
  height:138px;
  border-radius:30px;
  object-fit:cover;
  flex:none;
  border:3px solid rgba(106,220,240,.3);
}

.initials-avatar {
  display:flex;
  align-items:center;
  justify-content:center;
  background:linear-gradient(135deg,#14b8d4,#2878ef);
  color:white;
  font-size:2rem;
  font-weight:850;
  letter-spacing:.04em;
}

.person-number {
  color:#159fc2;
  font-weight:850;
  font-size:1.15rem;
  margin-top:18px;
}

.person-role,
.supervisor-role {
  display:inline-flex;
  padding:6px 10px;
  border-radius:999px;
  background:#e5f8fc;
  color:#087895;
  font-size:.65rem;
  font-weight:850;
  letter-spacing:.1em;
  margin-top:8px;
}

.person-name {
  color:#10283e;
  font-weight:850;
  font-size:1.05rem;
  letter-spacing:.02em;
  margin-top:12px;
}

.person-department {
  color:#718397;
  font-size:.82rem;
  margin-top:8px;
  min-height:40px;
}

.person-email {
  color:#26637c;
  font-size:.78rem;
  text-decoration:none;
}


/* ============================================================
   SUPERVISORS
   ============================================================ */

.supervisor-grid {
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:24px;
  width:100%;
}

.supervisor-card {
  display:flex;
  align-items:center;
  gap:28px;
  border:1px solid #28536d;
  border-radius:24px;
  padding:30px;
  background:linear-gradient(145deg,#0b243d,#0c3a50);
  box-shadow:0 18px 40px rgba(0,0,0,.16);
}

.supervisor-role {
  width:max-content;
  background:rgba(62,210,235,.13);
  color:#7ce4f5;
  margin-top:0;
}


/* ============================================================
   FOOTER
   ============================================================ */

.footer {
  background:#061221;
  color:#8fa9bc;
  border-top:1px solid #17334b;
  padding:38px 0;
}


/* ============================================================
   RESPONSIVE
   ============================================================ */

@media(max-width:1100px) {
  .hero-copy {
    max-width:58%;
  }

  .hero-visual {
    width:48vw;
    opacity:.82;
  }

  .team-grid {
    grid-template-columns:repeat(2,minmax(0,1fr));
  }
}

@media(max-width:900px) {
  .page-shell {
    padding:0 22px;
  }

  .component-grid,
  .info-grid {
    grid-template-columns:1fr 1fr;
  }

  .architecture-flow {
    grid-template-columns:1fr 1fr;
  }

  .hero-visual {
    position:relative;
    inset:auto;
    width:100%;
    height:330px;
    margin-top:-90px;
    padding-bottom:30px;
  }

  .hero-copy {
    max-width:100%;
    padding-top:105px;
    padding-bottom:80px;
  }

  .nav-links {
    display:none;
  }

  .institution-card {
    padding:28px;
    gap:24px;
  }

  .supervisor-card {
    align-items:flex-start;
  }
}

@media(max-width:600px) {
  .component-grid,
  .info-grid,
  .architecture-flow,
  .team-grid,
  .supervisor-grid {
    grid-template-columns:1fr;
  }

  .hero-title {
    font-size:3.2rem;
  }

  .section {
    padding:60px 0;
  }

  .flow-node:after {
    display:none;
  }

  .institution-card,
  .supervisor-card {
    flex-direction:column;
    text-align:center;
  }

  .institution-logo-wrap {
    width:120px;
    height:95px;
  }

  .person-card {
    min-height:390px;
  }
}


/* COMPONENT 2 LATEST SELECTIVE MERGE */
.dedicated-live-view { width:100%; max-width:100%; height:100vh; height:100dvh; overflow:hidden; background:#16202a; color:#eef5f8; padding:6px 8px 8px; gap:5px; }
.live-view-header { min-height:42px; border-bottom:1px solid #42505b; padding-bottom:5px; }
.live-view-empty { min-height:70vh; color:#cdd9df; }
.live-view-time,.live-view-mappo,.live-view-status { font-weight:800; letter-spacing:.08em; }
.sumo-canvas-host { width:100%; height:100%; min-width:0; min-height:0; overflow:hidden; }
.sumo-live-canvas { display:block; width:100%; height:100%; min-width:0; min-height:0; max-width:none; max-height:none; border:2px solid #8ca096; background:#57964c; }
.sumo-road-boundaries polyline { fill:none; stroke:#f1f1e8; stroke-linecap:butt; stroke-linejoin:round; }
.sumo-road-asphalt polyline { fill:none; stroke:#202326; stroke-linecap:butt; stroke-linejoin:round; }
.sumo-junction { fill:#202326; }
.sumo-car-label rect { fill:rgba(12,20,26,.72); }
.sumo-car-label text { fill:#fff; font:600 8px system-ui,sans-serif; }
.live-view-legend,.live-view-details { min-height:24px; background:#222e37; padding:3px 10px; border-radius:6px; font-size:11px; }
.camera-controls { position:static; align-self:flex-end; min-height:30px; gap:3px; background:rgba(20,34,44,.92); border:1px solid #58707d; border-radius:7px; padding:2px 5px; }
.camera-controls .q-btn { min-height:25px; padding:2px 7px; font-size:11px; }
.camera-zoom-value { min-width:42px; text-align:center; color:#70e5f5; font-weight:850; }
.live-view-workspace { display:grid!important; grid-template-columns:205px minmax(0,1fr) 250px; width:100%; min-width:0; min-height:0; flex:1 1 auto; gap:8px; }
.scenario-sidebar { width:205px; min-width:0; max-width:205px; height:100%; background:#202c36; border:1px solid #40515e; border-radius:9px; padding:8px; gap:5px; overflow-y:auto; }
.scenario-sidebar-title { color:#65d9ec; font-size:.74rem; font-weight:850; letter-spacing:.12em; }
.live-view-workspace { grid-template-rows:minmax(0,1fr); }
.scenario-sidebar { min-height:0; overflow-x:hidden; overscroll-behavior:contain; overflow-anchor:none; scrollbar-gutter:stable; touch-action:pan-y; }
.scenario-sidebar > * { flex-shrink:0; }
.scenario-sidebar::-webkit-scrollbar { width:12px; }
.scenario-sidebar::-webkit-scrollbar-track { background:#202c36; }
.scenario-sidebar::-webkit-scrollbar-thumb { background:#58707d; border-radius:6px; border:2px solid #202c36; }
.counterfactual-dialog { width:min(1100px,95vw); max-width:min(1100px,95vw)!important; max-height:92dvh; overflow-y:auto; background:#172b36!important; color:white; overscroll-behavior:contain; }
.counterfactual-canvas { width:100%; height:100%; }
.offline-replay-player button { border:1px solid #e9b949; border-radius:4px; padding:5px; margin:3px; }
.counterfactual-dialog { display:flex; flex-direction:column; gap:8px!important; }
.offline-warning { font-size:15px; line-height:1.3; }
.offline-toolbar { display:flex; align-items:center; flex-wrap:wrap; gap:4px; }
.offline-cameras { display:grid; grid-template-columns:1fr 1.5fr; gap:10px; }
.offline-overview-canvas,.offline-replay-canvas { height:clamp(220px,43vh,420px); }
.offline-impact-status { font-weight:bold; color:#ffd166; min-height:24px; }
.sumo-car.collision-involved>rect:first-of-type { stroke:#ff4b4b; stroke-width:3px; }
.viva-vehicle-card.collision-involved { border:2px solid #ff4b4b; }
.main-replay-canvas { flex:1 1 0!important; height:0!important; min-height:180px; }
.main-replay-event { height:56px; min-height:56px; max-height:56px; flex-shrink:0; overflow:auto; }
.offline-vehicle-list { font-size:11px; line-height:1.3; overflow-wrap:anywhere; }
@media(max-width:700px) { .offline-cameras { grid-template-columns:1fr; } }
.scenario-sidebar .q-radio { align-items:flex-start; margin:1px 0; }
.scenario-sidebar .q-radio__label { font-size:.75rem; line-height:1.16; color:#e7f0f4; }
.scenario-description { color:#b9cad3; font-size:.78rem; line-height:1.45; }
.scenario-tag { background:#304653; color:#8de5f4; border-radius:999px; padding:4px 7px; font-size:.62rem; font-weight:800; }
.scenario-detail-label { color:#6edbed; font-size:.66rem; font-weight:800; letter-spacing:.08em; margin-top:4px; }
.scenario-detail-value { color:#d8e4e9; font-size:.72rem; line-height:1.35; }
.live-view-main { display:flex; flex-direction:column; width:auto; min-width:0; max-width:none; height:100%; min-height:0; gap:5px; overflow:hidden; }
.live-center-and-inspector { gap:14px; }
.live-canvas-column { position:relative; display:flex; width:100%; max-width:none; align-self:stretch; flex:1 1 auto; min-width:0; min-height:0; justify-content:center; gap:0; overflow:hidden; }
.vehicle-inspector { width:310px; min-width:310px; max-height:70vh; overflow:auto; background:#202c36; border:1px solid #40515e; border-radius:12px; padding:14px; gap:7px; }
.vehicle-inspector-title { color:#65d9ec; font-size:.72rem; font-weight:850; letter-spacing:.12em; }
.vehicle-summary-card { width:100%; justify-content:flex-start; background:#2a3944!important; color:#e8f1f5!important; font-size:.75rem; }
.selected-vehicle-name { font-size:1.35rem; font-weight:850; color:#fff; }
.selected-vehicle-id { color:#91a8b5; font-size:.68rem; }
.pipeline-stage { width:100%; border-left:3px solid #28c4df; background:#18242d; border-radius:5px; padding:7px 9px; gap:1px; }
.pipeline-stage-name { color:#69dcec; font-size:.61rem; font-weight:850; letter-spacing:.08em; }
.pipeline-stage-value { color:#edf5f7; font-size:.73rem; line-height:1.25; }
.inspector-empty { color:#9cb0bb; padding:24px 0; }
.event-timeline { background:#202c36; border:1px solid #40515e; border-radius:10px; padding:10px 14px; gap:10px; overflow-x:auto; }
.event-timeline-title { color:#65d9ec; font-size:.68rem; font-weight:850; letter-spacing:.1em; align-self:center; }
.event-timeline-item { min-width:145px; border-left:2px solid #4ecbe1; padding-left:8px; gap:1px; }
.event-time { color:#8ba2af; font-size:.62rem; }.event-name { color:#eef5f8; font-size:.68rem; font-weight:750; }.event-mappo { color:#6edbed; font-size:.6rem; }
.scenario-run-state { color:#8fe1ed; font-size:.68rem; font-weight:800; }
.sumo-car { cursor:pointer; }
.stable-inspector-host { width:250px; min-width:0; max-width:250px; height:100%; }
.stable-inspector { height:calc(100vh - 120px); overflow-y:auto; padding:14px; }
.inspector-sticky { position:sticky; top:0; z-index:3; background:#1d2b36; padding-bottom:10px; }
.auto-follow { display:block; margin:8px 0; font-size:11px; color:#8fdff4; }
.inspector-cards { display:grid; grid-template-columns:1fr 1fr; gap:6px; margin:8px 0; }
.inspector-cards button { text-align:left; border:1px solid #344b5b; background:#263946; color:#dceaf2; border-radius:5px; padding:6px; }
.inspector-cards button.selected { border-color:#16c8ef; box-shadow:0 0 0 1px #16c8ef inset; }
.inspector-cards small { display:block; font-size:10px; color:#9fc4d5; }
.stable-inspector details { border:1px solid #304856; border-radius:5px; margin:7px 0; background:#15242e; }
.stable-inspector summary { cursor:pointer; padding:8px; color:#56dcfa; display:flex; flex-direction:column; }
.stable-inspector summary span { font-size:11px; color:#fff; margin-top:2px; }
.stable-inspector details>div { padding:0 8px 8px; font-size:11px; color:#c9dbe4; }
.presentation-tabs { background:#172731; color:#d7edf6; }
.live-view-main .q-tab-panels, .live-view-main .q-tab-panel { background:#13212c; color:#e5f2f7; padding:8px; }
.mappo-observed-badge { background:#0b7f5c; color:white; padding:6px 10px; border-radius:999px; font-weight:850; }
.run-mappo-count { color:#72e7fa; font-weight:850; }
.negotiation-events-title { color:#6fe5f7; font-weight:850; letter-spacing:.08em; margin-top:8px; }
.negotiation-event-card { width:100%; background:#19313b; border:1px solid #34cde8; border-radius:8px; }
.verified-scenario-tag { border:1px solid #4bcde3; }
.viva-mode-badge { background:#168fba; color:white; border-radius:999px; padding:5px 10px; font-weight:850; }
.viva-inspector { width:100%; min-width:0; min-height:0; max-width:250px; overflow-y:auto; overflow-x:hidden; overscroll-behavior:contain; height:100%; padding:10px; }
.viva-pipeline { margin:6px 0; padding:6px; border-radius:6px; background:#132531; color:#70e5f5; font-size:9px; font-weight:800; line-height:1.25; }
#c2-viva-cards { display:grid; gap:8px; }
.viva-vehicle-card { border-left:4px solid #2684ff; background:#152630; border-radius:6px; padding:6px 7px; font-size:10px; line-height:1.3; }
.mappo-decision-received { color:#ffd21f; }
.viva-vehicle-card[aria-selected="true"] { outline:1px solid #ffffff; }
.viva-vehicle-card header { display:flex; justify-content:space-between; font-size:13px; margin-bottom:4px; }
.viva-vehicle-card.state-NEGOTIATING { border-color:#ffd21f; }.viva-vehicle-card.state-READY { border-color:#20c86b; }.viva-vehicle-card.state-BLOCKED { border-color:#ef3f45; }
.current-event-banner { min-height:38px; background:#1d303b; border:1px solid #3c5664; border-radius:7px; padding:5px 10px; }
.current-event-title { color:#69e4f6; font-size:12px; font-weight:900; }.current-event-message { color:white; font-size:11px; }.current-planner { font-size:10px; color:#c8dbe3; }
.simple-final-result { width:100%; background:#17313b!important; border:1px solid #34cde8; color:white; display:grid; grid-template-columns:repeat(3,1fr); gap:7px; }
.final-main-result { grid-column:1/-1; color:#74e6f7; font-weight:800; }
.negotiation-result-dialog { width:min(850px,90vw); background:#172b36!important; color:white; }
.technical-details-dialog { width:min(1050px,92vw); height:min(820px,90vh); background:#172b36!important; color:white; }
.technical-json { max-height:690px; overflow:auto; font-size:11px; }
@media(max-width:1399px) and (min-width:901px){
  .live-view-workspace{grid-template-columns:175px minmax(0,1fr) 220px}
  .scenario-sidebar{width:175px;max-width:175px;padding:6px}
  .stable-inspector-host,.viva-inspector{max-width:220px}
}
@media(max-width:900px){
  .dedicated-live-view{height:auto;min-height:100dvh;overflow:auto}
  .live-view-workspace{display:flex!important;flex-direction:column!important}
  .scenario-sidebar,.stable-inspector-host,.viva-inspector{width:100%;max-width:none;height:auto}
}

/* Component 2 research-detail explainer */
.c2-explainer-section{background:#f7fafc;color:#10283e}
.c2-explainer-section:nth-of-type(even){background:#fff}
.c2-explainer-section.section-dark{background:#081a2c;color:#f5fbff}
.c2-decision-flow{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;width:100%;margin-top:32px}
.c2-step-card{position:relative;min-height:190px;padding:19px 17px;border:1px solid #d6e4ed;border-top:3px solid #22b8d5;border-radius:14px;background:#fff;box-shadow:0 7px 20px rgba(15,47,70,.045)}
.c2-step-card:not(:nth-child(5n)):after{content:'→';position:absolute;right:-13px;top:46%;z-index:2;color:#24a9c5;font-weight:900}
.c2-step-number{color:#8ba1b2;font-size:.7rem;font-weight:850;letter-spacing:.14em}
.c2-step-title{margin-top:10px;color:#0b3150;font-size:.83rem;font-weight:850;letter-spacing:.055em}
.c2-step-question{margin-top:14px;color:#526b7e;font-size:.8rem;line-height:1.45}
.c2-step-output{margin-top:12px;padding-top:10px;border-top:1px solid #e5edf2;color:#087e99;font-size:.76rem;font-weight:750;line-height:1.35}
.c2-three-grid,.c2-two-grid,.c2-evidence-layout{display:grid;gap:20px;width:100%;margin-top:30px}
.c2-three-grid,.c2-evidence-layout{grid-template-columns:repeat(3,minmax(0,1fr))}.c2-two-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
.c2-explain-card,.c2-input-strip,.c2-cycle-card{border:1px solid #d8e5ed;border-radius:18px;background:#fff;padding:25px;box-shadow:0 9px 26px rgba(16,49,73,.045)}
.c2-card-kicker{color:#087e99;font-size:.72rem;font-weight:900;letter-spacing:.11em}
.c2-mini-heading{margin-top:18px;color:#385a70;font-size:.7rem;font-weight:900;letter-spacing:.1em}
.c2-bullet-row{gap:5px;margin-top:9px}.c2-bullet-text{color:#445f72;font-size:.84rem;line-height:1.4}
.c2-compact-copy{color:#506a7d;line-height:1.62}.section-dark .c2-compact-copy{color:#bfd1dc}
.c2-note{margin-top:18px;padding:11px 13px;border-left:3px solid #29b6d1;background:#eff8fb;color:#35576d;font-size:.8rem;line-height:1.5}
.c2-warning-callout{margin-top:18px;padding:15px;border:1px solid #f1c6b9;border-left:4px solid #d65e3f;border-radius:10px;background:#fff7f4;color:#7a3424;font-size:.82rem;line-height:1.5}
.c2-memory-line,.c2-invariant{display:block;margin-top:22px;padding:14px;border-radius:10px;background:#eaf6fa;color:#075e75;text-align:center;font-size:1rem;font-weight:900;letter-spacing:.055em}
.c2-mini-flow{display:flex;align-items:stretch;gap:8px;width:100%;margin-top:22px;flex-wrap:wrap}
.c2-mini-flow-node{display:flex;align-items:center;justify-content:center;flex:1 1 135px;min-height:66px;padding:11px;border:1px solid #cfe0ea;border-radius:10px;background:#f8fbfd;color:#264c63;text-align:center;font-size:.78rem;font-weight:750;line-height:1.35}
.c2-mini-arrow{align-self:center;color:#16a2bf}.c2-mini-flow-wide .c2-mini-flow-node{min-height:84px}
.c2-technical-expansion,.c2-implementation-map{margin-top:20px;border:1px solid #d5e4ec;border-radius:12px;background:#fff;color:#23465c}
.c2-formula{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;color:#086f88;font-size:1.05rem;font-weight:800}
.c2-input-strip{margin-top:28px}.c2-rule-card{border-top:3px solid #1aa9c7}.c2-rule-id{color:#087e99;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:.8rem;font-weight:900}
.c2-token-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.c2-status-token{padding:7px 10px;border:1px solid #c9dfe9;border-radius:999px;background:#f1f8fb;color:#22566d;font-size:.68rem;font-weight:800}
.c2-graph-rule{padding:26px;border:1px solid #c8e1eb;border-radius:18px;background:#f3fafc;text-align:center}
.c2-graph-example{margin:7px;color:#254d63;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-weight:800}
.c2-warning-line{margin-top:12px;color:#a33e27;font-size:1rem;font-weight:900;letter-spacing:.06em}
.c2-cycle-card{border-top:4px solid #24a86b}.c2-cycle-card.is-cycle{border-top-color:#d49225;background:#fffaf1}
.c2-cycle-edges{margin:18px 0;color:#103f59;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:1.08rem;font-weight:900;word-spacing:10px}
.c2-dark-grid .c2-authorization-card{background:#102a3e;border-color:#31536a;color:#f1f8fb}
.c2-authorization-card{display:flex;min-height:160px;flex-direction:column;align-items:center;justify-content:center;gap:10px;padding:19px;border:1px solid #31536a;border-radius:14px;text-align:center}
.c2-authorization-card.is-active{border-color:#36c5df;background:#0b3a4d}.c2-auth-outcome{color:#77dfef;font-size:.82rem;font-weight:900;letter-spacing:.07em}
.c2-semantic-card{border:1px solid #31536a;border-radius:16px;background:#102a3e;padding:24px}.c2-action-token{margin-top:10px;padding:12px;border:1px solid #28667c;border-radius:9px;background:#0b2335;color:#8ce5f5;font-weight:800}
.c2-safety-boundary{margin-top:24px;padding:22px;border:1px solid #2ebbd5;border-radius:14px;background:#0c3043;color:#eefbff}
.section-dark .c2-card-kicker,.section-dark .c2-mini-heading{color:#74ddef}
.c2-map-table{display:grid;gap:0;width:100%}.c2-map-header,.c2-map-row{display:grid;grid-template-columns:minmax(180px,.8fr) minmax(280px,1.2fr);gap:18px;padding:13px 16px}
.c2-map-header{background:#0c334d;color:#fff;font-size:.75rem;font-weight:850;letter-spacing:.07em}.c2-map-row{border-bottom:1px solid #e1eaf0}.c2-code-path{color:#086f88;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:.79rem;font-weight:800}
.c2-evidence-row{margin-top:10px;padding:9px 0;border-bottom:1px solid #e3ebf0;color:#264f65}.c2-selected-evidence{margin-top:17px;padding:12px;border-radius:9px;background:#dff5eb;color:#087253;font-weight:900}
.c2-partial-run-banner,.c2-run-complete{display:flex;align-items:center;gap:13px;margin-bottom:14px;padding:17px 19px;border-radius:12px}.c2-partial-run-banner{border:1px solid #e7bb62;background:#fff7df;color:#76510a}.c2-run-complete{border:1px solid #8ed5b5;background:#eaf8f2;color:#116848}
@media(max-width:1200px){.c2-decision-flow{grid-template-columns:repeat(2,minmax(0,1fr))}.c2-step-card:not(:nth-child(5n)):after{display:none}.c2-three-grid,.c2-evidence-layout{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:700px){.c2-decision-flow,.c2-three-grid,.c2-two-grid,.c2-evidence-layout{grid-template-columns:1fr}.c2-step-card{min-height:auto}.c2-map-header,.c2-map-row{grid-template-columns:1fr}.c2-map-header label:last-child{display:none}.c2-mini-flow{flex-direction:column}.c2-mini-arrow{transform:rotate(90deg);align-self:center}}
"""


def apply_theme():
    ui.colors(
        primary="#168fba",
        secondary="#2f7df4",
        accent="#27c7e8",
    )

    ui.add_head_html(
        '<meta name="theme-color" content="#071426">'
    )

    # Component 3 CARLA live interface uses the same fonts as
    # its standalone dark-panel interface.
    ui.add_head_html(
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link '
        'href="https://fonts.googleapis.com/css2?'
        'family=Inter:wght@400;500;600;700;800&'
        'family=JetBrains+Mono:wght@400;500;600;700&'
        'display=swap" '
        'rel="stylesheet">'
    )

    ui.add_css(CSS)
