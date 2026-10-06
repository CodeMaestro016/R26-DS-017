"""Persistent, simplified client-side VIVA vehicle cards."""


def _document():
    return r'''
<aside id="c2-inspector" class="vehicle-inspector viva-inspector">
  <b>LIVE VEHICLES</b>
  <div class="viva-pipeline">INTENTION → RULE / GRAPH → MAPPO IF NEEDED → PLANNER → SUMO MOTION</div>
  <div id="c2-viva-cards"><span class="inspector-empty">No active vehicles</span></div>
</aside>
<script>
setTimeout(() => {
 const root=document.getElementById('c2-inspector'); if(!root||root.dataset.ready)return; root.dataset.ready='1';
 const cards=root.querySelector('#c2-viva-cards');
 const short=id=>{const m=String(id).match(/^PANEL_AV_([NESW])_(\d+)$/);return m?m[1]+m[2]:id};
 const action=v=>{const f=((v.negotiation||{}).factors||[]);return f.length?String(f[f.length-1].selected_action||'NOT AVAILABLE'):'NOT REQUIRED'};
 const intention=v=>{const p=(v.local_intention_predictions||[])[0];return p?p.label:'WAITING'};
 const yieldTo=v=>{const e=(v.local_precedence_edges||[]).find(x=>x[0]===v.id);return e?short(e[1]):'NONE'};
 const status=v=>v.display_state==='BLOCKED'&&yieldTo(v)!=='NONE'?'YIELDING / WAIT':v.display_state==='BLOCKED'?'BLOCKED / WAIT':v.display_state==='READY'?'READY / GO':v.display_state||'APPROACHING';
 const rule=v=>yieldTo(v)!=='NONE'?`YIELD TO ${yieldTo(v)}`:(v.display_state==='READY'?'HAS PRECEDENCE':'WAITING FOR RULE');
 const mappo=v=>v.display_state==='NEGOTIATING'?`ACTIVE${action(v)==='NOT REQUIRED'?'':` — ${action(v)}`}`:action(v);
 async function tick(){try{const r=await fetch('/api/component2/live-state',{cache:'no-store'}).then(x=>x.json());const p=r.payload||{},vs=p.vehicles||[];
   cards.innerHTML=vs.length?vs.map(v=>{const state=v.display_state||'APPROACHING';return `<article class="viva-vehicle-card state-${state}"><header><b>${short(v.id)}</b><span>${status(v)}</span></header><div>Intention: <b>${intention(v)}</b></div><div>Rule: <b>${rule(v)}</b></div><div>MAPPO: <b>${mappo(v)}</b></div><div>Speed: <b>${Number(v.speed_mps||0).toFixed(1)} m/s</b></div></article>`}).join(''):'<span class="inspector-empty">No active vehicles</span>';
 }catch(e){}finally{setTimeout(tick,350)}}tick();
},500);
</script>'''


def stable_inspector_html():
    return _document().split("<script>", 1)[0]


def stable_inspector_script():
    return "<script>" + _document().split("<script>", 1)[1]
