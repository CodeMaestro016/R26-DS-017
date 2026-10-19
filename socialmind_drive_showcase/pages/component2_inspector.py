"""Persistent, simplified client-side VIVA vehicle cards."""


def _document():
    return r'''
<aside id="c2-inspector" class="vehicle-inspector viva-inspector">
  <b>LIVE VEHICLES</b>
  <div class="viva-pipeline">INTENTION → RULE / GRAPH → MAPPO IF NEEDED → PLANNER → SUMO MOTION</div>
  <div id="c2-viva-cards"><span class="inspector-empty">No vehicles currently in the intersection area.</span></div>
</aside>
<script>
setTimeout(() => {
 const root=document.getElementById('c2-inspector'); if(!root||root.dataset.ready)return; root.dataset.ready='1';
 const cards=root.querySelector('#c2-viva-cards');
 let selected=null,currentVehicles=[],currentRun=null;
 const details=document.createElement('div');details.className='c2-current-selection';root.append(details);
 window.selectComponent2Vehicle=id=>{selected=currentVehicles.some(v=>v.id===id)?id:null;renderSelection()};
 function renderSelection(){const v=currentVehicles.find(v=>v.id===selected);details.textContent=v?`Selected ${v.id}: ${v.permission_label||v.display_state}; ${Number(v.speed_mps).toFixed(1)} m/s; ${(v.entry_permission||{}).reason||'Native following'}`:'';cards.querySelectorAll('[data-vehicle-id]').forEach(c=>c.setAttribute('aria-selected',String(c.dataset.vehicleId===selected)))}
 cards.addEventListener('click',event=>{const card=event.target.closest('[data-vehicle-id]');if(card)window.selectComponent2Vehicle(card.dataset.vehicleId)});
 const short=id=>{const m=String(id).match(/^PANEL_AV_([NESW])_(\d+)$/);return m?m[1]+m[2]:id};
 const action=v=>{const f=((v.negotiation||{}).factors||[]);return f.length?String(f[f.length-1].selected_action||'NOT AVAILABLE'):'NO LOCAL ACTOR ACTION'};
 const intention=v=>{const p=(v.local_intention_predictions||[])[0];return p?p.label:'WAITING'};
 const yieldTo=v=>{const ids=(v.entry_permission||{}).blocking_vehicle_ids||[];return ids.length?ids.map(short).join(', '):'NONE'};
 const status=v=>v.permission_label||v.display_state||'UNAVAILABLE';
 const rule=v=>yieldTo(v)!=='NONE'?`YIELD TO ${yieldTo(v)}`:((v.entry_permission||{}).reason||'NO CURRENT PERMISSION EVIDENCE').replaceAll('_',' ');
 const mappo=v=>{const n=v.negotiation||{};const age=n.last_event_timestamp==null?'':` · event ${Number(n.last_event_timestamp).toFixed(2)}s`;const execution=n.execution_status?` / ${n.execution_status.replaceAll('_',' ')}`:'';return `${(n.status||'UNAVAILABLE').replaceAll('_',' ')}${execution}${age}${n.current_receipt?` — ${action(v)}`:''}`};
 function paint(p){const vs=p.replay_mode?[...(p.vehicles||[])].sort((a,b)=>Number(b.collision_involved)-Number(a.collision_involved)):(p.vehicles||[]);if(currentRun!==p.run_id){selected=null;currentRun=p.run_id}currentVehicles=vs;if(!vs.some(v=>v.id===selected))selected=null;cards.dataset.simulationTime=String(p.simulation_time);cards.dataset.runId=p.run_id||'';
   const title=document.querySelector('.main-simulation-title');if(title)title.textContent=p.replay_mode?'SOCIALMIND DRIVE — RECORDED SUMO EVIDENCE':'SOCIALMIND DRIVE — LIVE SUMO SIMULATION';
   root.querySelector('.viva-pipeline').textContent=p.replay_mode?'RECORDED SUMO DATA · MAPPO DISABLED · COORDINATION AND SPECIFIED SAFETY NOT APPLIED':'INTENTION → RULE / GRAPH → MAPPO IF NEEDED → PLANNER → SUMO MOTION';
   if(p.replay_mode){cards.innerHTML=vs.map(v=>`<article class="viva-vehicle-card ${v.collision_involved?'collision-involved':''}" data-vehicle-id="${v.id}"><header><b>${short(v.id)}</b><span>${v.permission_label}</span></header><div>${v.id}</div><div>Recorded movement: ${v.movement}</div><div>Recorded speed: ${Number(v.speed_mps).toFixed(2)} m/s</div><div>MAPPO: DISABLED</div><div>Recorded time: ${Number(p.simulation_time).toFixed(2)} s</div></article>`).join('');renderSelection();return}
   cards.innerHTML=vs.length?vs.map(v=>{const state=v.display_state||'APPROACHING';return `<article class="viva-vehicle-card state-${state}"><header><b>${short(v.id)}</b><span>${status(v)}</span></header><div>Intention: <b>${intention(v)}</b></div><div>Rule: <b>${rule(v)}</b></div><div>MAPPO: <b>${mappo(v)}</b></div><div>Speed: <b>${Number(v.speed_mps||0).toFixed(1)} m/s · ${v.motion_state||'UNAVAILABLE'}</b></div></article>`}).join(''):'<span class="inspector-empty">No active vehicles</span>';
   [...cards.querySelectorAll('.viva-vehicle-card')].forEach((card,i)=>{const v=vs[i];card.dataset.vehicleId=v.id;if(v.recent_mappo_event){const note=document.createElement('div');note.className='mappo-decision-received';note.textContent=`MAPPO decision received at ${Number(v.recent_mappo_timestamp).toFixed(2)}s`;card.append(note)}});
   if(!vs.length)cards.textContent='No vehicles currently in the intersection area.';
   renderSelection();
 }
 let lastFrame='';
 function syncRoadFrame(){const metadata=document.querySelector('.c2-synchronized-frame');if(metadata&&metadata.textContent!==lastFrame){lastFrame=metadata.textContent;paint(JSON.parse(lastFrame))}}
 const observer=new MutationObserver(()=>{if(root.isConnected)syncRoadFrame();else observer.disconnect()});
 observer.observe(document.body,{childList:true,subtree:true});syncRoadFrame();
 let stopped=false;const controller=new AbortController();
 window.addEventListener('pagehide',()=>{stopped=true;controller.abort();observer.disconnect()},{once:true});
 async function tick(){if(stopped||!root.isConnected){observer.disconnect();return}try{
   const owned=()=>{const m=document.querySelector('.c2-synchronized-frame');if(!m)return false;const p=JSON.parse(m.textContent);return p.replay_mode||p.browser_owned_frame};
   if(owned()){syncRoadFrame();return}
   const zoom=document.querySelector('.sumo-live-canvas')?.dataset.zoom||'1';
   const scenario=document.querySelector('.sumo-live-canvas')?.dataset.scenario||'';
   const r=await fetch('/api/component2/live-state?zoom='+encodeURIComponent(zoom)+'&scenario='+encodeURIComponent(scenario),{cache:'no-store',signal:controller.signal}).then(x=>x.json());
   if(stopped||!root.isConnected)return;
   if(owned())return;
   if(!r.available||r.stale){cards.textContent=r.stale?'STALE TELEMETRY — waiting for a fresh frame':(r.message||'TELEMETRY UNAVAILABLE');const host=document.querySelector('.sumo-canvas-host');if(host)host.innerHTML='';return}
   const host=document.querySelector('.sumo-canvas-host');if(host&&r.rendered_svg){host.innerHTML=r.rendered_svg;syncRoadFrame()}
 }catch(e){if(!stopped)cards.textContent='TELEMETRY UNAVAILABLE'}finally{if(!stopped&&root.isConnected)setTimeout(tick,350)}}tick();
},500);
</script>'''


def stable_inspector_html():
    return _document().split("<script>", 1)[0]


def stable_inspector_script():
    return "<script>" + _document().split("<script>", 1)[1]
