"""Real local Chromium rehearsal; uses an isolated temporary Playwright install."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time
import urllib.request

BASE=Path(__file__).resolve().parents[1]
EVIDENCE=BASE/'results/final_live_correction/20261016'
RESEARCH_PYTHON=Path('C:/R26-DS-017/venv/Scripts/python.exe')

DOM_SAMPLE=r'''() => {
 const metadata=document.querySelector('.c2-synchronized-frame');
 if(!metadata)return null;
 const frame=JSON.parse(metadata.textContent);
 const cards=[...document.querySelectorAll('.viva-vehicle-card')].map(c=>({
   id:c.querySelector('header b')?.textContent,state:[...c.classList].find(x=>x.startsWith('state-'))?.slice(6),
   permission:c.querySelector('header span')?.textContent,border:getComputedStyle(c).borderLeftColor}));
 const cars=[...document.querySelectorAll('g.sumo-car')].map(c=>({id:c.dataset.vehicleId,
   fill:c.querySelector('rect')?.getAttribute('fill'),outline:!!c.querySelector('.mappo-decision-outline')}));
 return {frame,cards,cars,card_time:document.getElementById('c2-viva-cards')?.dataset.simulationTime,
   inspector_ready:document.getElementById('c2-inspector')?.dataset.ready,
   status:document.querySelector('.live-view-status')?.textContent,
   viewport:innerWidth,scroll_width:document.documentElement.scrollWidth,
   layout:['body','.nicegui-content','.dedicated-live-view','.live-view-workspace',
     '.scenario-sidebar','.live-view-main','.sumo-canvas-host','.sumo-live-canvas',
     '.stable-inspector-host','.vehicle-inspector'].map(selector=>{const e=document.querySelector(selector);
       if(!e)return {selector};const r=e.getBoundingClientRect(),c=getComputedStyle(e);
       return {selector,x:r.x,width:r.width,right:r.right,minWidth:c.minWidth,display:c.display,flex:c.flex}})};
}'''


async def main(version,full_intersection=False,presentation_evidence=False):
    import psutil
    from playwright.async_api import async_playwright, expect
    out=(BASE/'results/presentation_lifecycle/20261017' if full_intersection or presentation_evidence else EVIDENCE)/version
    out.mkdir(parents=True,exist_ok=False)
    tooling=json.loads((EVIDENCE/'local_browser_tooling.json').read_text(encoding='utf-8-sig'))
    os.environ['PLAYWRIGHT_BROWSERS_PATH']=tooling['browsers']
    with socket.socket() as available:
        available.bind(('127.0.0.1',0));port=available.getsockname()[1]
    url=f'http://127.0.0.1:{port}'
    errors=[];console=[];requests=[];samples=[];api_frames={};identities=[];screenshots=set()
    result=dict(mode='LOCAL_HEADLESS_CHROMIUM_REAL_DOM',version=version,port=port)
    colors={'READY':'#20c86b','BLOCKED':'#ef3f45','APPROACHING':'#2684ff','NEGOTIATING':'#ffd21f','CLEARED':'#9aa3ad'}
    borders={'READY':'rgb(32, 200, 107)','BLOCKED':'rgb(239, 63, 69)',
             'NEGOTIATING':'rgb(255, 210, 31)','APPROACHING':'rgb(38, 132, 255)'}
    observed_states={};transitions=[];moving_red=0;matched_api=0
    def verify(sample):
        nonlocal moving_red,matched_api
        frame=sample['frame'];vehicles=frame['vehicles']
        assert sample['scroll_width']<=sample['viewport']+1,'HORIZONTAL_LAYOUT_OVERFLOW'
        assert float(sample['card_time'])==float(frame['simulation_time']),'ROAD_CARD_TIMESTAMP_MISMATCH'
        assert len(sample['cars'])==len(sample['cards'])==len(vehicles),'ROAD_CARD_VEHICLE_COUNT_MISMATCH'
        cars={c['id']:c for c in sample['cars']}
        cards={c['id']:c for c in sample['cards']}
        key=(frame['run_id'],frame['simulation_time'])
        published=api_frames.get(key)
        if published:
            assert [(v['id'],v['display_state']) for v in published['vehicles']]==[(v['id'],v['display_state']) for v in vehicles]
            matched_api+=1
        for v in vehicles:
            parts=v['id'].split('_');short=parts[-2]+parts[-1]
            assert cars[v['id']]['fill']==colors[v['display_state']],'WRONG_CAR_COLOR'
            assert cards[short]['state']==v['display_state'],'WRONG_CARD_COLOR_STATE'
            assert cards[short]['permission']==v.get('permission_label',v['display_state']),'WRONG_CARD_PERMISSION'
            if v['display_state'] in borders:
                assert cards[short]['border']==borders[v['display_state']],'WRONG_RENDERED_CARD_BORDER'
            permission=v.get('entry_permission',{})
            if permission.get('authorized') is True:assert v['display_state']=='READY'
            if permission.get('authorized') is False:
                assert v['display_state']==('APPROACHING' if v.get('display_stage')=='ORDINARY_APPROACH' else 'BLOCKED')
            assert cars[v['id']]['outline']==bool(v.get('recent_mappo_event'))
            history_key=(frame['run_id'],v['id'])
            if observed_states.get(history_key)=='BLOCKED' and v['display_state']=='READY':
                transitions.append(dict(id=v['id'],timestamp=frame['simulation_time'],
                    permission=permission,negotiation=v.get('negotiation')))
            observed_states[history_key]=v['display_state']
            if v['display_state']=='BLOCKED' and v.get('speed_mps',0)>0:moving_red+=1
    async def wire(page):
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.on('console',lambda message:console.append(dict(type=message.type,text=message.text)))
        page.on('requestfailed',lambda request:requests.append(dict(url=request.url,failure=request.failure)))
        async def response(received):
            if '/api/component2/live-state' not in received.url:return
            try:
                state=await received.json()
                if state.get('available'):
                    payload=state['payload'];api_frames[(payload.get('run_id'),payload['simulation_time'])]=payload
            except Exception:pass  # Navigation may cancel a read; captured separately.
        page.on('response',response)
    async def ready(page):
        await page.wait_for_selector('.sumo-live-canvas',timeout=30000)
        await page.wait_for_function("document.getElementById('c2-inspector')?.dataset.ready==='1'",timeout=15000)
        await page.wait_for_timeout(500)
    async def observe(page):
        sample=await page.evaluate(DOM_SAMPLE)
        if sample and sample['card_time'] is not None:
            samples.append(sample)
            try:verify(sample)
            except Exception:
                await page.screenshot(path=str(out/'failing_state.png'),full_page=True)
                raise
            if full_intersection and sample['frame'].get('run_id'):
                frame=sample['frame']
                for threshold in (2,14,16,23.24,40,70,100):
                    identity=(frame['run_id'],threshold)
                    if frame['simulation_time']>=threshold and identity not in screenshots:
                        screenshots.add(identity)
                        await page.screenshot(path=str(out/f'{frame["scenario_id"]}_stage_{threshold}.png'),full_page=True)
        return sample
    with (out/'server.log').open('w',encoding='utf-8') as log:
        server=subprocess.Popen([str(RESEARCH_PYTHON),'-B',str(BASE.parent/'socialmind_drive_showcase/app.py'),
            '--server-only','--port',str(port)],cwd=BASE.parent,stdout=log,stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        try:
            deadline=time.monotonic()+45
            while True:
                try:urllib.request.urlopen(url+'/components',timeout=3);break
                except OSError:
                    if time.monotonic()>deadline or server.poll() is not None:raise
                    await asyncio.sleep(.2)
            async with async_playwright() as p:
                browser=await p.chromium.launch(headless=True)
                result['browser_version']=browser.version
                first=await browser.new_context(viewport=dict(width=1600,height=1000))
                second=await browser.new_context(viewport=dict(width=1600,height=1000))
                page=await first.new_page();other=await second.new_page()
                await wire(page);await wire(other)
                await page.goto(url+'/component/right-of-way/live');await ready(page)
                for _ in range(20):
                    sample=await observe(page)
                    if sample and sample['status']=='IDLE' and sample['frame']['vehicles']:
                        await page.screenshot(path=str(out/'idle_previous_run.png'),full_page=True)
                        raise AssertionError('IDLE_DISPLAYS_PREVIOUS_RUN_VEHICLES')
                    await asyncio.sleep(.08)
                await page.screenshot(path=str(out/'idle.png'),full_page=True)
                await other.goto(url+'/component/right-of-way/live');await ready(other)
                await page.get_by_text('5. Congested Four-Approach Queues (16 vehicles)',exact=True).click()
                await other.get_by_text('2. Four-Way Arrival',exact=True).click()
                await expect(page.get_by_role('radio',name='5. Congested Four-Approach Queues (16 vehicles)',exact=True)).to_have_attribute('aria-checked','true')
                await expect(other.get_by_role('radio',name='2. Four-Way Arrival',exact=True)).to_have_attribute('aria-checked','true')
                result['independent_browser_preferences']=True
                await page.get_by_role('button',name='Run Scenario',exact=True).click()
                deadline=time.monotonic()+150;run_id=None
                while time.monotonic()<deadline:
                    sample=await observe(page)
                    if sample and sample['frame']['run_id']:
                        run_id=sample['frame']['run_id']
                        payload=api_frames.get((run_id,sample['frame']['simulation_time']))
                        if payload and payload.get('last_mappo_event') and sample['frame']['simulation_time']>=26:break
                    await asyncio.sleep(.2)
                else:raise TimeoutError('No real live MAPPO event rendered')
                result['first_run_id']=run_id
                result['real_mappo_event']=payload['last_mappo_event']
                await page.screenshot(path=str(out/'live_negotiation.png'),full_page=True)
                if full_intersection:
                    result['complete_scenarios']=[]
                    async def finish_scenario(scenario,timeout=600):
                        deadline=time.monotonic()+timeout;outline_seen=False;blue_seen=False;removed_seen=False
                        selected_id=None
                        while time.monotonic()<deadline:
                            sample=await observe(page)
                            if sample and sample['frame']['run_id'] and sample['frame']['scenario_id']==scenario:
                                frame=sample['frame'];state=api_frames.get((frame['run_id'],frame['simulation_time']))
                                blue_seen |= any(v['display_state']=='APPROACHING' for v in frame['vehicles'])
                                if selected_id is None and frame['vehicles']:
                                    selected_id=frame['vehicles'][0]['id']
                                    await page.evaluate('(id)=>window.selectComponent2Vehicle(id)',selected_id)
                                if selected_id and not any(v['id']==selected_id for v in frame['vehicles']):
                                    assert not await page.locator('.c2-current-selection').inner_text()
                                if state:
                                    participants=set((state.get('last_mappo_event') or {}).get('participants',()))
                                    highlighted={v['id'] for v in frame['vehicles'] if v.get('recent_mappo_event')}
                                    assert highlighted.issubset(participants)
                                    if highlighted and not outline_seen:
                                        await page.screenshot(path=str(out/(scenario+'_mappo_outline.png')),full_page=True)
                                        outline_seen=True
                                    removed_seen |= state.get('active_sumo_vehicles',0)>len(state['vehicles']) and bool(state.get('intersection_cleared_vehicle_ids'))
                                    if not state.get('running') and state.get('status')=='FINISHED':
                                        assert not frame['vehicles']
                                        assert await page.locator('#c2-viva-cards').inner_text()=='No vehicles currently in the intersection area.'
                                        await page.screenshot(path=str(out/(scenario+'_finished.png')),full_page=True)
                                        result['complete_scenarios'].append(dict(scenario=scenario,payload=state,
                                            outline_seen=outline_seen,blue_seen=blue_seen,display_exit_before_trip_completion=removed_seen))
                                        return
                            await asyncio.sleep(.12)
                        raise TimeoutError('Scenario did not finish: '+scenario)
                    await finish_scenario('congested_four_approach')
                    for scenario,label in [('four_way_simultaneous','2. Four-Way Arrival'),('regulatory_cycle','3. Regulatory Cycle')]:
                        await page.get_by_role('button',name='Stop',exact=True).click()
                        await page.wait_for_function("document.querySelector('.scenario-run-state')?.textContent.includes('IDLE')",timeout=30000)
                        await page.get_by_text(label,exact=True).click()
                        await page.get_by_role('button',name='Run Scenario',exact=True).click()
                        await page.wait_for_timeout(500)
                        await finish_scenario(scenario,180)
                    dense,four,eligible=result['complete_scenarios']
                    assert dense['payload']['completed']==16 and dense['outline_seen'] and dense['display_exit_before_trip_completion']
                    assert four['payload']['completed']==4 and not four['outline_seen']
                    assert four['payload']['run_metrics']['mappo_decision_epochs']==0
                    assert eligible['payload']['completed']==4 and eligible['outline_seen']
                    for case in result['complete_scenarios']:
                        metrics=case['payload']['run_metrics']
                        assert metrics['collisions']==metrics['blocked_zone_violations']==0
                        assert metrics['centralized_critic_runtime_calls']==0
                        assert metrics['maximum_negotiation_participants']<=4
                await observe(other)
                await page.goto(url+'/components');await page.wait_for_timeout(400)
                await page.goto(url+'/component/right-of-way/live');await ready(page)
                await observe(page);await observe(other)
                await page.reload();await ready(page);await observe(page)
                await page.close()
                page=await first.new_page();await wire(page)
                await page.goto(url+'/component/right-of-way/live');await ready(page);await observe(page)
                result['navigate_reload_close_reopen']=True
                if full_intersection and await page.get_by_role('button',name='Stop',exact=True).is_disabled():
                    # Finished runs have no process to stop. Exercise Stop on
                    # an actual active run rather than forcing a disabled UI.
                    await page.get_by_text('1. Rule-Resolved Conflict',exact=True).click()
                    await page.get_by_role('button',name='Run Scenario',exact=True).click()
                    await expect(page.get_by_role('button',name='Stop',exact=True)).to_be_enabled(timeout=30000)
                await page.get_by_role('button',name='Stop',exact=True).click()
                await page.wait_for_function("document.querySelector('.scenario-run-state')?.textContent.includes('IDLE')",timeout=30000)
                await page.wait_for_timeout(700)
                idle=await observe(page)
                assert idle and not idle['frame']['vehicles'],'STOPPED_RUN_VEHICLES_REAPPEAR_WHILE_IDLE'
                await page.get_by_text('1. Rule-Resolved Conflict',exact=True).click()
                await page.get_by_role('button',name='Run Scenario',exact=True).click()
                deadline=time.monotonic()+90;new_run=None
                while time.monotonic()<deadline:
                    sample=await observe(page)
                    if sample and sample['frame']['run_id'] not in (None,run_id) and sample['frame']['simulation_time']>=2:
                        new_run=sample['frame']['run_id'];break
                    await asyncio.sleep(.2)
                assert new_run,'RELAUNCH_DID_NOT_CREATE_FRESH_RUN'
                result['second_run_id']=new_run;result['stop_relaunch']=True
                owner=psutil.Process(server.pid)
                identities=[(q.pid,q.create_time()) for q in [owner]+owner.children(recursive=True)]
                await first.close();await second.close();await browser.close()
                server.send_signal(signal.CTRL_BREAK_EVENT)
                result['server_exit_code']=await asyncio.to_thread(server.wait,30)
                result['shutdown_while_runtime_active']=True
        except Exception as error:
            result['failure']=repr(error)
            raise
        finally:
            if server.poll() is None:
                try:server.send_signal(signal.CTRL_BREAK_EVENT);await asyncio.to_thread(server.wait,25)
                except Exception:
                    owned=psutil.Process(server.pid)
                    for child in owned.children(recursive=True):child.terminate()
                    owned.terminate()
                    result['forced_cleanup']=True
            alive=[]
            for pid,born in identities:
                try:
                    q=psutil.Process(pid)
                    if q.is_running() and q.create_time()==born:alive.append(pid)
                except psutil.NoSuchProcess:pass
            result.update(page_errors=errors,browser_console=console,failed_requests=requests,
                sampled_dom_frames=len(samples),matching_http_dom_frames=matched_api,
                moving_red_samples=moving_red,held_to_ready_transitions=transitions,
                remaining_owned_processes=alive)
            (out/'receipt.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
            (out/'dom_frames.json').write_text(json.dumps(samples,indent=2),encoding='utf-8')
    text=(out/'server.log').read_text(encoding='utf-8')
    assert not errors and not result['remaining_owned_processes']
    assert 'Client has been deleted' not in text and 'TypeError' not in text and 'Traceback' not in text
    assert matched_api>=3 and moving_red>0 and transitions
    print(json.dumps({k:v for k,v in result.items() if k not in {'browser_console','failed_requests','real_mappo_event','held_to_ready_transitions'}}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--version',default='local_browser_v1')
    parser.add_argument('--full-intersection',action='store_true')
    parser.add_argument('--presentation-evidence',action='store_true')
    args=parser.parse_args()
    asyncio.run(main(args.version,args.full_intersection,args.presentation_evidence))
