"""One-action presentation of immutable SUMO positions; no simulator control."""
import json
from nicegui import ui
from socialmind_drive_showcase.config import COMPONENT2_ROOT
from socialmind_drive_showcase.services.counterfactual_reader import load_evidence,junction_evidence


def show_counterfactual_replay():
    try:evidence=load_evidence();junction=junction_evidence()
    except (OSError,ValueError,StopIteration) as error:
        ui.notify(f'Counterfactual evidence unavailable: {error}',type='warning');return
    with ui.dialog() as dialog,ui.card().classes('counterfactual-dialog'):
        ui.label('OFFLINE UNCOORDINATED COUNTERFACTUAL — SAFETY INTERVENTIONS NOT APPLIED').classes('offline-warning text-amber-4 font-bold')
        ui.html('''<div class="offline-replay-player w-full">
<div class="offline-toolbar"><button class="offline-play">Pause recorded trace</button><button class="offline-restart">Restart replay</button><button class="offline-event">Jump to recorded event</button>
<label>Replay speed <select class="offline-speed" aria-label="Replay speed"><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="2">2×</option></select></label></div>
<div class="offline-replay-time" aria-live="off"></div><div class="offline-impact-status" role="status"></div>
<input class="offline-frame-slider" aria-label="Recorded trajectory frame" type="range" min="0" value="0" step="1" style="width:100%">
<div class="offline-cameras"><div><div>All approaches · recorded paths</div><div class="offline-overview-canvas"></div></div><div><div>Central junction detail · same recorded frame</div><div class="offline-replay-canvas"></div></div></div>
<div class="offline-vehicle-list"></div></div>''',sanitize=False)
        with ui.row().classes('gap-2'):
            ui.button('Back to protected scenario',on_click=dialog.close)
            ui.button('Close replay',on_click=dialog.close).props('flat')
        with ui.expansion('Evidence, assumptions and three-mode results').classes('w-full'):
            ui.label('Actual recorded SUMO positions; blue bodies are recorded identities, not protected entry permissions. Dashed paths show recorded front-bumper trajectories, not predicted future routes.')
            ui.label('Excluded: MAPPO, regulatory execution, entry permission, shield, explicit junction stops, native safe-following-speed and junction-priority enforcement. Original dimensions, acceleration/braking limits, speed limits and safe insertion retained. No crash-response dynamics are claimed.')
            ui.label(f"Seed {evidence['seed']} · first four scheduled at 0 s; two followers at 1.5 s. Playback starts at the first recorded frame containing all six; the slider retains earlier spawn frames. Junction center {junction['center']}; collision reference {junction['collision_reference']}; distance {junction['distance_from_center_m']:.4f} m.")
            comparison=json.loads((COMPONENT2_ROOT/'results/final_demonstrations/v1/comparison.json').read_text())
            rows=[]
            for source in comparison['modes']:
                observed=source.get('completion_time_seconds') or source.get('observed_duration_seconds')
                rows.append(dict(mode='Protected MAPPO + rules + safety' if source['mode']=='PROPOSED_MAPPO_RULES_SAFETY' else 'Rules-only; safety retained',spawned=source['spawned'],completed=source['completed'],collisions=source['collisions'],mappo=source['mappo_calls'],time=f"{observed:g} s; {source['status']}"))
            rows.append(dict(mode='Uncoordinated; specified safety omitted',spawned=evidence['spawned'],completed=evidence['completed'],collisions=evidence['collision_count'],mappo=evidence['mappo_calls'],time=f"{evidence['simulation_time']:.2f} s; first detection"))
            ui.table(columns=[dict(name=k,label=k.capitalize(),field=k,align='left') for k in rows[0]],rows=rows,row_key='mode').classes('w-full')
            ui.label('This removes coordination AND specified safety interventions; the result does not isolate MAPPO alone or prove universal safety.')
            ui.label(f"Evidence SHA256: {evidence['provenance']['replay_sha256']}").classes('text-xs break-all')
    dialog.open()
    ui.run_javascript(r'''setTimeout(()=>{
const root=[...document.querySelectorAll('.offline-replay-player')].at(-1);if(!root)return;
const slider=root.querySelector('input'),clock=root.querySelector('.offline-replay-time'),canvas=root.querySelector('.offline-replay-canvas'),overview=root.querySelector('.offline-overview-canvas'),status=root.querySelector('.offline-impact-status'),playButton=root.querySelector('.offline-play'),speed=root.querySelector('.offline-speed');let playing=false,busy=false,timeline=[],eventIndex=null,startIndex=0,due=0;
function controls(){root.dataset.playing=String(playing);playButton.textContent=playing?'Pause recorded trace':'Play recorded trace'}
async function show(index){if(busy||!root.isConnected)return;busy=true;try{const r=await fetch('/api/component2/counterfactual/frame?index='+index).then(x=>x.json());if(!root.isConnected)return;if(!r.available){playing=false;clock.textContent=r.message;return}slider.max=r.total_frames-1;slider.value=r.index;root.dataset.frame=String(r.index);root.dataset.simulationTime=r.frame.simulation_time;root.dataset.collisionCount=r.frame.collisions.length;clock.textContent='RECORDED time '+Number(r.frame.simulation_time).toFixed(2)+' s · '+r.frame.vehicles.length+' vehicles · MAPPO calls: 0';canvas.innerHTML=r.rendered_svg;overview.innerHTML=r.overview_svg;root.querySelector('.offline-vehicle-list').textContent=r.frame.vehicles.map(v=>v.id.replace('PANEL_AV_','')+' '+v.movement).join(' · ');
if(r.frame.collisions.length){playing=false;status.textContent='ACTUAL SUMO COLLISION DETECTED · count '+r.collision_count+' · '+r.events.map(e=>e.collider+' / '+e.victim+' · SUMO '+e.sumo_event_time.toFixed(2)+' s (snapshot '+e.traci_detection_time.toFixed(2)+' s)').join('; ')}else{status.textContent='APPROACHING — no collision detected in this recorded frame'}
if(r.index>=r.total_frames-1)playing=false;controls()}catch(error){playing=false;status.textContent='Replay unavailable: '+error.message;controls()}finally{busy=false}}
function scheduleNext(){const i=Number(slider.value);due=performance.now()+Math.max(0,(timeline[i+1]-timeline[i])*1000/Number(speed.value))}
slider.addEventListener('input',()=>{playing=false;show(Number(slider.value));controls()});
playButton.onclick=async()=>{if(busy)return;playing=!playing;if(playing&&Number(slider.value)>=Number(slider.max))await show(startIndex);playing=Number(slider.value)<Number(slider.max)&&playing;scheduleNext();controls()};
root.querySelector('.offline-restart').onclick=async()=>{if(busy)return;playing=false;await show(startIndex);playing=true;scheduleNext();controls()};
speed.onchange=scheduleNext;
root.querySelector('.offline-event').onclick=async()=>{if(busy)return;playing=false;if(eventIndex!==null)await show(eventIndex);controls()};
async function tick(){if(!root.isConnected||root.getClientRects().length===0){playing=false;return}if(playing&&!busy&&performance.now()>=due){await show(Math.min(Number(slider.max),Number(slider.value)+1));scheduleNext()}setTimeout(tick,10)}
fetch('/api/component2/counterfactual/frame?index=0').then(x=>x.json()).then(async r=>{timeline=r.timeline;eventIndex=r.collision_frame_index;startIndex=r.first_full_demand_frame_index;root.querySelector('.offline-event').disabled=eventIndex===null;await show(startIndex);playing=true;scheduleNext();controls();tick()});
},100)''')
