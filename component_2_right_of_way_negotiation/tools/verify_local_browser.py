"""Real local Chromium rehearsal; uses an isolated temporary Playwright install."""
# Import argparse for use in this module.
import argparse
# Import asyncio for use in this module.
import asyncio
# Import json for use in this module.
import json
# Import os for use in this module.
import os
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import signal for use in this module.
import signal
# Import socket for use in this module.
import socket
# Import subprocess for use in this module.
import subprocess
# Import time for use in this module.
import time
# Import urllib.request for use in this module.
import urllib.request

# Set BASE to Path(__file__).resolve().parents at 1.
BASE=Path(__file__).resolve().parents[1]
# Set EVIDENCE to BASE joined with the path segment 'results/final_live_correction/20261016'.
EVIDENCE=BASE/'results/final_live_correction/20261016'
# Set RESEARCH_PYTHON to the result of Path(the text 'C:/R26-DS-017/venv/Scripts/python.exe').
RESEARCH_PYTHON=Path('C:/R26-DS-017/venv/Scripts/python.exe')

# Set DOM_SAMPLE to the text '() => { const...'.
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


# Main using the inputs and processing steps below.
# Input version: the supplied version.
# Input full_intersection: the supplied full intersection.
# Input presentation_evidence: the supplied presentation evidence.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
async def main(version,full_intersection=False,presentation_evidence=False):
    # Import psutil for use in this module.
    import psutil
    # Import async_playwright, expect from playwright.async_api for the operations below.
    from playwright.async_api import async_playwright, expect
    # Set out to BASE joined with the path segment 'results/presentation_lifecycle/20261017' when full_intersection or
    # presentation_evidence, otherwise EVIDENCE divided by version.
    out=(BASE/'results/presentation_lifecycle/20261017' if full_intersection or presentation_evidence else EVIDENCE)/version
    # Create the directory requested by out.
    out.mkdir(parents=True,exist_ok=False)
    # Set tooling to the decoded data produced by json.loads from the text read from (EVIDENCE /
    # 'local_browser_tooling.json').
    tooling=json.loads((EVIDENCE/'local_browser_tooling.json').read_text(encoding='utf-8-sig'))
    # Set os.environ['PLAYWRIGHT_BROWSERS_PATH'] to tooling at 'browsers'.
    os.environ['PLAYWRIGHT_BROWSERS_PATH']=tooling['browsers']
    # Enter the result of socket.socket() as available and run the enclosed operations within that context.
    with socket.socket() as available:
        # Call available.bind with the supplied arguments.
        # Set port to available.getsockname() at 1.
        available.bind(('127.0.0.1',0));port=available.getsockname()[1]
    # Set url to formatted text built from the embedded values.
    url=f'http://127.0.0.1:{port}'
    # Set errors to an empty list.
    # Set console to an empty list.
    # Set requests to an empty list.
    # Set samples to an empty list.
    # Set api_frames to an empty dictionary.
    # Set identities to an empty list.
    # Set screenshots to an empty set.
    errors=[];console=[];requests=[];samples=[];api_frames={};identities=[];screenshots=set()
    # Set result to a dictionary built from the supplied values.
    result=dict(mode='LOCAL_HEADLESS_CHROMIUM_REAL_DOM',version=version,port=port)
    # Set colors to a dictionary containing READY, BLOCKED, APPROACHING, NEGOTIATING, CLEARED.
    colors={'READY':'#20c86b','BLOCKED':'#ef3f45','APPROACHING':'#2684ff','NEGOTIATING':'#ffd21f','CLEARED':'#9aa3ad'}
    # Set borders to a dictionary containing READY, BLOCKED, NEGOTIATING, APPROACHING.
    borders={'READY':'rgb(32, 200, 107)','BLOCKED':'rgb(239, 63, 69)',
             'NEGOTIATING':'rgb(255, 210, 31)','APPROACHING':'rgb(38, 132, 255)'}
    # Set observed_states to an empty dictionary.
    # Set transitions to an empty list.
    # Set moving_red to 0.
    # Set matched_api to 0.
    observed_states={};transitions=[];moving_red=0;matched_api=0
    # Verify using the inputs and processing steps below.
    # Input sample: the supplied sample.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def verify(sample):
        # Bind moving_red, matched_api in the enclosing function scope.
        nonlocal moving_red,matched_api
        # Set frame to sample at 'frame'.
        # Set vehicles to frame at 'vehicles'.
        frame=sample['frame'];vehicles=frame['vehicles']
        # Require sample at 'scroll_width' is at most sample at 'viewport' plus 1; otherwise raise AssertionError
        # with the text 'HORIZONTAL_LAYOUT_OVERFLOW'.
        assert sample['scroll_width']<=sample['viewport']+1,'HORIZONTAL_LAYOUT_OVERFLOW'
        # Require a floating-point number built from sample at 'card_time' equals a floating-point number built
        # from frame at 'simulation_time'; otherwise raise AssertionError with the text
        # 'ROAD_CARD_TIMESTAMP_MISMATCH'.
        assert float(sample['card_time'])==float(frame['simulation_time']),'ROAD_CARD_TIMESTAMP_MISMATCH'
        # Require the number of entries in sample at 'cars' equals the number of entries in sample at 'cards';
        # equals the number of entries in vehicles; otherwise raise AssertionError with the text
        # 'ROAD_CARD_VEHICLE_COUNT_MISMATCH'.
        assert len(sample['cars'])==len(sample['cards'])==len(vehicles),'ROAD_CARD_VEHICLE_COUNT_MISMATCH'
        # Set cars to a dictionary of c at 'id' mapped to c for c in sample at 'cars'.
        cars={c['id']:c for c in sample['cars']}
        # Set cards to a dictionary of c at 'id' mapped to c for c in sample at 'cards'.
        cards={c['id']:c for c in sample['cards']}
        # Set key to a tuple containing frame at 'run_id', frame at 'simulation_time'.
        key=(frame['run_id'],frame['simulation_time'])
        # Set published to key from api_frames; use None if absent.
        published=api_frames.get(key)
        # Run this branch when published.
        if published:
            # Require a list of a tuple containing v at 'id', v at 'display_state' for v in published at
            # 'vehicles' equals a list of a tuple containing v at 'id', v at 'display_state' for v in vehicles;
            # otherwise raise AssertionError.
            assert [(v['id'],v['display_state']) for v in published['vehicles']]==[(v['id'],v['display_state']) for v in vehicles]
            # Update matched_api to its current value plus 1.
            matched_api+=1
        # Iterate over vehicles, binding each item to v.
        for v in vehicles:
            # Set parts to the result of v['id'].split(the text '_').
            # Set short to parts at -2 plus parts at -1.
            parts=v['id'].split('_');short=parts[-2]+parts[-1]
            # Require cars[v['id']] at 'fill' equals colors at v['display_state']; otherwise raise AssertionError
            # with the text 'WRONG_CAR_COLOR'.
            assert cars[v['id']]['fill']==colors[v['display_state']],'WRONG_CAR_COLOR'
            # Require cards[short] at 'state' equals v at 'display_state'; otherwise raise AssertionError with the
            # text 'WRONG_CARD_COLOR_STATE'.
            assert cards[short]['state']==v['display_state'],'WRONG_CARD_COLOR_STATE'
            # Require cards[short] at 'permission' equals 'permission_label' from v; use v at 'display_state' if
            # absent; otherwise raise AssertionError with the text 'WRONG_CARD_PERMISSION'.
            assert cards[short]['permission']==v.get('permission_label',v['display_state']),'WRONG_CARD_PERMISSION'
            # Run this branch when v at 'display_state' belongs to borders.
            if v['display_state'] in borders:
                # Require cards[short] at 'border' equals borders at v['display_state']; otherwise raise
                # AssertionError with the text 'WRONG_RENDERED_CARD_BORDER'.
                assert cards[short]['border']==borders[v['display_state']],'WRONG_RENDERED_CARD_BORDER'
            # Set permission to 'entry_permission' from v; use an empty dictionary if absent.
            permission=v.get('entry_permission',{})
            # Run this branch when 'authorized' from permission; use None if absent is the same object as True.
            # Require v at 'display_state' equals the text 'READY'; otherwise raise AssertionError.
            if permission.get('authorized') is True:assert v['display_state']=='READY'
            # Run this branch when 'authorized' from permission; use None if absent is the same object as False.
            if permission.get('authorized') is False:
                # Require v at 'display_state' equals the text 'APPROACHING' when 'display_stage' from v; use None
                # if absent equals the text 'ORDINARY_APPROACH', otherwise the text 'BLOCKED'; otherwise raise
                # AssertionError.
                assert v['display_state']==('APPROACHING' if v.get('display_stage')=='ORDINARY_APPROACH' else 'BLOCKED')
            # Require cars[v['id']] at 'outline' equals a Boolean built from 'recent_mappo_event' from v; use None
            # if absent; otherwise raise AssertionError.
            assert cars[v['id']]['outline']==bool(v.get('recent_mappo_event'))
            # Set history_key to a tuple containing frame at 'run_id', v at 'id'.
            history_key=(frame['run_id'],v['id'])
            # Run this branch when history_key from observed_states; use None if absent equals the text 'BLOCKED'
            # and v at 'display_state' equals the text 'READY'.
            if observed_states.get(history_key)=='BLOCKED' and v['display_state']=='READY':
                # Append a dictionary built from the supplied values to transitions.
                transitions.append(dict(id=v['id'],timestamp=frame['simulation_time'],
                    # Supply permission as permission.
                    # Supply negotiation as 'negotiation' from v; use None if absent.
                    permission=permission,negotiation=v.get('negotiation')))
            # Set observed_states[history_key] to v at 'display_state'.
            observed_states[history_key]=v['display_state']
            # Run this branch when v at 'display_state' equals the text 'BLOCKED' and 'speed_mps' from v; use 0 if
            # absent is greater than 0.
            # Update moving_red to its current value plus 1.
            if v['display_state']=='BLOCKED' and v.get('speed_mps',0)>0:moving_red+=1
    # Wire using the inputs and processing steps below.
    # Input page: the supplied page.
    # Output: no explicit value; normal completion returns None.
    async def wire(page):
        # Call page.on with the supplied arguments.
        page.on('pageerror',lambda error:errors.append(str(error)))
        # Call page.on with the supplied arguments.
        page.on('console',lambda message:console.append(dict(type=message.type,text=message.text)))
        # Call page.on with the supplied arguments.
        page.on('requestfailed',lambda request:requests.append(dict(url=request.url,failure=request.failure)))
        # Response using the inputs and processing steps below.
        # Input received: the supplied received.
        # Output: no explicit value; normal completion returns None.
        # Processing: select branches using the stated conditions, then handle the specified errors.
        async def response(received):
            # Run this branch when the text '/api/component2/live-state' does not belong to received.url.
            # Return no value to the caller.
            if '/api/component2/live-state' not in received.url:return
            # Attempt the enclosed operations and route matching exceptions to the handlers below.
            try:
                # Set state to the awaited result of the result of received.json().
                state=await received.json()
                # Run this branch when 'available' from state; use None if absent.
                if state.get('available'):
                    # Set payload to state at 'payload'.
                    # Set api_frames[payload.get('run_id'), payload['simulation_time']] to payload.
                    payload=state['payload'];api_frames[(payload.get('run_id'),payload['simulation_time'])]=payload
            # Handle Exception using the recovery steps below.
            # Keep this block syntactically valid without performing an operation.
            except Exception:pass  # Navigation may cancel a read; captured separately.
        # Call page.on with the supplied arguments.
        page.on('response',response)
    # Ready using the inputs and processing steps below.
    # Input page: the supplied page.
    # Output: no explicit value; normal completion returns None.
    async def ready(page):
        # Evaluate the awaited result of the result of page.wait_for_selector(the text '.sumo-live-canvas').
        await page.wait_for_selector('.sumo-live-canvas',timeout=30000)
        # Evaluate the awaited result of the result of page.wait_for_function(the text
        # "document.getElementById('c2-inspector')?.dataset.ready==='1'").
        await page.wait_for_function("document.getElementById('c2-inspector')?.dataset.ready==='1'",timeout=15000)
        # Evaluate the awaited result of the result of page.wait_for_timeout(500).
        await page.wait_for_timeout(500)
    # Observe using the inputs and processing steps below.
    # Input page: the supplied page.
    # Output: sample.
    # Processing: iterate over the relevant records, then select branches using the stated conditions, then handle
    # the specified errors.
    async def observe(page):
        # Set sample to the awaited result of the result of page.evaluate(DOM_SAMPLE).
        sample=await page.evaluate(DOM_SAMPLE)
        # Run this branch when sample and sample at 'card_time' is a different object from None.
        if sample and sample['card_time'] is not None:
            # Append sample to samples.
            samples.append(sample)
            # Attempt the enclosed operations and route matching exceptions to the handlers below.
            # Call verify with the supplied arguments.
            try:verify(sample)
            # Handle Exception using the recovery steps below.
            except Exception:
                # Evaluate the awaited result of the result of page.screenshot().
                await page.screenshot(path=str(out/'failing_state.png'),full_page=True)
                # Re-raise the active exception.
                raise
            # Run this branch when full_intersection and 'run_id' from sample['frame']; use None if absent.
            if full_intersection and sample['frame'].get('run_id'):
                # Set frame to sample at 'frame'.
                frame=sample['frame']
                # Iterate over a tuple containing 2, 14, 16, 23.24, 40, 70, 100, binding each item to threshold.
                for threshold in (2,14,16,23.24,40,70,100):
                    # Set identity to a tuple containing frame at 'run_id', threshold.
                    identity=(frame['run_id'],threshold)
                    # Run this branch when frame at 'simulation_time' is at least threshold and identity does not
                    # belong to screenshots.
                    if frame['simulation_time']>=threshold and identity not in screenshots:
                        # Add identity to screenshots.
                        screenshots.add(identity)
                        # Evaluate the awaited result of the result of page.screenshot().
                        await page.screenshot(path=str(out/f'{frame["scenario_id"]}_stage_{threshold}.png'),full_page=True)
        # Return sample to the caller.
        return sample
    # Enter the result of (out / 'server.log').open(the text 'w') as log and run the enclosed operations within
    # that context.
    with (out/'server.log').open('w',encoding='utf-8') as log:
        # Set server to the result of subprocess.Popen(a list containing a string built from RESEARCH_PYTHON, the
        # text '-B', a string built from...).
        server=subprocess.Popen([str(RESEARCH_PYTHON),'-B',str(BASE.parent/'socialmind_drive_showcase/app.py'),
            # Supply cwd as BASE.parent.
            # Supply stdout as log.
            # Supply stderr as subprocess.STDOUT.
            '--server-only','--port',str(port)],cwd=BASE.parent,stdout=log,stderr=subprocess.STDOUT,
            # Supply creationflags as subprocess.CREATE_NEW_PROCESS_GROUP.
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set deadline to the monotonic clock time plus 45.
            deadline=time.monotonic()+45
            # Repeat the following steps while True.
            while True:
                # Attempt the enclosed operations and route matching exceptions to the handlers below.
                # Call urllib.request.urlopen with the supplied arguments.
                # Leave the nearest enclosing loop immediately.
                try:urllib.request.urlopen(url+'/components',timeout=3);break
                # Handle OSError using the recovery steps below.
                except OSError:
                    # Run this branch when the monotonic clock time is greater than deadline or the result of
                    # server.poll() is a different object from None.
                    # Re-raise the active exception.
                    if time.monotonic()>deadline or server.poll() is not None:raise
                    # Evaluate the awaited result of the result of asyncio.sleep(0.2).
                    await asyncio.sleep(.2)
            # Enter the result of async_playwright() as p and run the enclosed operations within that context.
            async with async_playwright() as p:
                # Set browser to the awaited result of the result of p.chromium.launch().
                browser=await p.chromium.launch(headless=True)
                # Set result['browser_version'] to browser.version.
                result['browser_version']=browser.version
                # Set first to the awaited result of the result of browser.new_context().
                first=await browser.new_context(viewport=dict(width=1600,height=1000))
                # Set second to the awaited result of the result of browser.new_context().
                second=await browser.new_context(viewport=dict(width=1600,height=1000))
                # Set page to the awaited result of the result of first.new_page().
                # Set other to the awaited result of the result of second.new_page().
                page=await first.new_page();other=await second.new_page()
                # Evaluate the awaited result of the result of wire(page).
                # Evaluate the awaited result of the result of wire(other).
                await wire(page);await wire(other)
                # Evaluate the awaited result of the result of page.goto(url plus the text
                # '/component/right-of-way/live').
                # Evaluate the awaited result of the result of ready(page).
                await page.goto(url+'/component/right-of-way/live');await ready(page)
                # Iterate over the integer range defined by 20, binding each item to _.
                for _ in range(20):
                    # Set sample to the awaited result of the result of observe(page).
                    sample=await observe(page)
                    # Run this branch when sample and sample at 'status' equals the text 'IDLE' and
                    # sample['frame'] at 'vehicles'.
                    if sample and sample['status']=='IDLE' and sample['frame']['vehicles']:
                        # Evaluate the awaited result of the result of page.screenshot().
                        await page.screenshot(path=str(out/'idle_previous_run.png'),full_page=True)
                        # Raise AssertionError with the text 'IDLE_DISPLAYS_PREVIOUS_RUN_VEHICLES' to stop this
                        # execution path.
                        raise AssertionError('IDLE_DISPLAYS_PREVIOUS_RUN_VEHICLES')
                    # Evaluate the awaited result of the result of asyncio.sleep(0.08).
                    await asyncio.sleep(.08)
                # Evaluate the awaited result of the result of page.screenshot().
                await page.screenshot(path=str(out/'idle.png'),full_page=True)
                # Evaluate the awaited result of the result of other.goto(url plus the text
                # '/component/right-of-way/live').
                # Evaluate the awaited result of the result of ready(other).
                await other.goto(url+'/component/right-of-way/live');await ready(other)
                # Evaluate the awaited result of the result of page.get_by_text('5. Congested Four-Approach Queues
                # (16 vehicles)', exact=True).click().
                await page.get_by_text('5. Congested Four-Approach Queues (16 vehicles)',exact=True).click()
                # Evaluate the awaited result of the result of other.get_by_text('2. Four-Way Arrival',
                # exact=True).click().
                await other.get_by_text('2. Four-Way Arrival',exact=True).click()
                # Evaluate the awaited result of the result of expect(page.get_by_role('radio', name='5. Congested
                # Four-Approach Queues (16 vehicles)',...(the text 'aria-checked', the text 'true').
                await expect(page.get_by_role('radio',name='5. Congested Four-Approach Queues (16 vehicles)',exact=True)).to_have_attribute('aria-checked','true')
                # Evaluate the awaited result of the result of expect(other.get_by_role('radio', name='2. Four-Way
                # Arrival', exact=True)).to_have_attribute(the text 'aria-checked', the text 'true').
                await expect(other.get_by_role('radio',name='2. Four-Way Arrival',exact=True)).to_have_attribute('aria-checked','true')
                # Set result['independent_browser_preferences'] to True.
                result['independent_browser_preferences']=True
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Run Scenario',
                # exact=True).click().
                await page.get_by_role('button',name='Run Scenario',exact=True).click()
                # Set deadline to the monotonic clock time plus 150.
                # Set run_id to None.
                deadline=time.monotonic()+150;run_id=None
                # Repeat the following steps while the monotonic clock time is less than deadline.
                while time.monotonic()<deadline:
                    # Set sample to the awaited result of the result of observe(page).
                    sample=await observe(page)
                    # Run this branch when sample and sample['frame'] at 'run_id'.
                    if sample and sample['frame']['run_id']:
                        # Set run_id to sample['frame'] at 'run_id'.
                        run_id=sample['frame']['run_id']
                        # Set payload to (run_id, sample['frame']['simulation_time']) from api_frames; use None if
                        # absent.
                        payload=api_frames.get((run_id,sample['frame']['simulation_time']))
                        # Run this branch when payload and 'last_mappo_event' from payload; use None if absent and
                        # sample['frame'] at 'simulation_time' is at least 26.
                        # Leave the nearest enclosing loop immediately.
                        if payload and payload.get('last_mappo_event') and sample['frame']['simulation_time']>=26:break
                    # Evaluate the awaited result of the result of asyncio.sleep(0.2).
                    await asyncio.sleep(.2)
                # Raise TimeoutError with the text 'No real live MAPPO event rendered' to stop this execution
                # path.
                else:raise TimeoutError('No real live MAPPO event rendered')
                # Set result['first_run_id'] to run_id.
                result['first_run_id']=run_id
                # Set result['real_mappo_event'] to payload at 'last_mappo_event'.
                result['real_mappo_event']=payload['last_mappo_event']
                # Evaluate the awaited result of the result of page.screenshot().
                await page.screenshot(path=str(out/'live_negotiation.png'),full_page=True)
                # Run this branch when full_intersection.
                if full_intersection:
                    # Set result['complete_scenarios'] to an empty list.
                    result['complete_scenarios']=[]
                    # Finish scenario using the inputs and processing steps below.
                    # Input scenario: the supplied scenario.
                    # Input timeout: the supplied timeout.
                    # Output: no explicit value; normal completion returns None.
                    # Processing: iterate over the relevant records, then select branches using the stated
                    # conditions.
                    async def finish_scenario(scenario,timeout=600):
                        # Set deadline to the monotonic clock time plus timeout.
                        # Set outline_seen to False.
                        # Set blue_seen to False.
                        # Set removed_seen to False.
                        deadline=time.monotonic()+timeout;outline_seen=False;blue_seen=False;removed_seen=False
                        # Set selected_id to None.
                        selected_id=None
                        # Repeat the following steps while the monotonic clock time is less than deadline.
                        while time.monotonic()<deadline:
                            # Set sample to the awaited result of the result of observe(page).
                            sample=await observe(page)
                            # Run this branch when sample and sample['frame'] at 'run_id' and sample['frame'] at
                            # 'scenario_id' equals scenario.
                            if sample and sample['frame']['run_id'] and sample['frame']['scenario_id']==scenario:
                                # Set frame to sample at 'frame'.
                                # Set state to (frame['run_id'], frame['simulation_time']) from api_frames; use
                                # None if absent.
                                frame=sample['frame'];state=api_frames.get((frame['run_id'],frame['simulation_time']))
                                # Update blue_seen to its current value combined with whether any item is true in
                                # a lazy sequence of v at 'display_state' equals the text 'APPROACHING' for v in
                                # frame at 'vehicles'.
                                blue_seen |= any(v['display_state']=='APPROACHING' for v in frame['vehicles'])
                                # Run this branch when selected_id is the same object as None and frame at
                                # 'vehicles'.
                                if selected_id is None and frame['vehicles']:
                                    # Set selected_id to frame['vehicles'][0] at 'id'.
                                    selected_id=frame['vehicles'][0]['id']
                                    # Evaluate the awaited result of the result of page.evaluate(the text
                                    # '(id)=>window.selectComponent2Vehicle(id)', selected_id).
                                    await page.evaluate('(id)=>window.selectComponent2Vehicle(id)',selected_id)
                                # Run this branch when selected_id and the negation of whether any item is true in
                                # a lazy sequence of v['id'] == selected_id for v in frame['vehicles'].
                                if selected_id and not any(v['id']==selected_id for v in frame['vehicles']):
                                    # Require the negation of the awaited result of the result of
                                    # page.locator('.c2-current-selection').inner_text(); otherwise raise
                                    # AssertionError.
                                    assert not await page.locator('.c2-current-selection').inner_text()
                                # Run this branch when state.
                                if state:
                                    # Set participants to a set built from 'participants' from
                                    # (state.get('last_mappo_event') or {}); use an empty tuple if absent.
                                    participants=set((state.get('last_mappo_event') or {}).get('participants',()))
                                    # Set highlighted to a set of v at 'id' for v in frame at 'vehicles'; retain
                                    # entries satisfying 'recent_mappo_event' from v; use None if absent.
                                    highlighted={v['id'] for v in frame['vehicles'] if v.get('recent_mappo_event')}
                                    # Require the result of highlighted.issubset(participants); otherwise raise
                                    # AssertionError.
                                    assert highlighted.issubset(participants)
                                    # Run this branch when highlighted and the negation of outline_seen.
                                    if highlighted and not outline_seen:
                                        # Evaluate the awaited result of the result of page.screenshot().
                                        await page.screenshot(path=str(out/(scenario+'_mappo_outline.png')),full_page=True)
                                        # Set outline_seen to True.
                                        outline_seen=True
                                    # Update removed_seen to its current value combined with
                                    # 'active_sumo_vehicles' from state; use 0 if absent is greater than the
                                    # number of entries in state at 'vehicles' and a Boolean built from
                                    # 'intersection_cleared_vehicle_ids' from state; use None if absent.
                                    removed_seen |= state.get('active_sumo_vehicles',0)>len(state['vehicles']) and bool(state.get('intersection_cleared_vehicle_ids'))
                                    # Run this branch when the negation of 'running' from state; use None if
                                    # absent and 'status' from state; use None if absent equals the text
                                    # 'FINISHED'.
                                    if not state.get('running') and state.get('status')=='FINISHED':
                                        # Require the negation of frame at 'vehicles'; otherwise raise
                                        # AssertionError.
                                        assert not frame['vehicles']
                                        # Require the awaited result of the result of
                                        # page.locator('#c2-viva-cards').inner_text() equals the text 'No vehicles
                                        # currently in the intersection area.'; otherwise raise AssertionError.
                                        assert await page.locator('#c2-viva-cards').inner_text()=='No vehicles currently in the intersection area.'
                                        # Evaluate the awaited result of the result of page.screenshot().
                                        await page.screenshot(path=str(out/(scenario+'_finished.png')),full_page=True)
                                        # Append a dictionary built from the supplied values to
                                        # result['complete_scenarios'].
                                        result['complete_scenarios'].append(dict(scenario=scenario,payload=state,
                                            # Supply outline_seen as outline_seen.
                                            # Supply blue_seen as blue_seen.
                                            # Supply display_exit_before_trip_completion as removed_seen.
                                            outline_seen=outline_seen,blue_seen=blue_seen,display_exit_before_trip_completion=removed_seen))
                                        # Return no value to the caller.
                                        return
                            # Evaluate the awaited result of the result of asyncio.sleep(0.12).
                            await asyncio.sleep(.12)
                        # Raise TimeoutError with the text 'Scenario did not finish:' plus scenario to stop this
                        # execution path.
                        raise TimeoutError('Scenario did not finish: '+scenario)
                    # Evaluate the awaited result of the result of finish_scenario(the text
                    # 'congested_four_approach').
                    await finish_scenario('congested_four_approach')
                    # Iterate over a list containing a tuple containing the text 'four_way_simultaneous', the text
                    # '2. Four-Way Arrival', a tuple containing..., binding each item to (scenario, label).
                    for scenario,label in [('four_way_simultaneous','2. Four-Way Arrival'),('regulatory_cycle','3. Regulatory Cycle')]:
                        # Evaluate the awaited result of the result of page.get_by_role('button', name='Stop',
                        # exact=True).click().
                        await page.get_by_role('button',name='Stop',exact=True).click()
                        # Evaluate the awaited result of the result of page.wait_for_function(the text
                        # "document.querySelector('.scenario-run-state')?.textContent.inc...").
                        await page.wait_for_function("document.querySelector('.scenario-run-state')?.textContent.includes('IDLE')",timeout=30000)
                        # Evaluate the awaited result of the result of page.get_by_text(label,
                        # exact=True).click().
                        await page.get_by_text(label,exact=True).click()
                        # Evaluate the awaited result of the result of page.get_by_role('button', name='Run
                        # Scenario', exact=True).click().
                        await page.get_by_role('button',name='Run Scenario',exact=True).click()
                        # Evaluate the awaited result of the result of page.wait_for_timeout(500).
                        await page.wait_for_timeout(500)
                        # Evaluate the awaited result of the result of finish_scenario(scenario, 180).
                        await finish_scenario(scenario,180)
                    # Set (dense, four, eligible) to result at 'complete_scenarios'.
                    dense,four,eligible=result['complete_scenarios']
                    # Require dense['payload'] at 'completed' equals 16 and dense at 'outline_seen' and dense at
                    # 'display_exit_before_trip_completion'; otherwise raise AssertionError.
                    assert dense['payload']['completed']==16 and dense['outline_seen'] and dense['display_exit_before_trip_completion']
                    # Require four['payload'] at 'completed' equals 4 and the negation of four at 'outline_seen';
                    # otherwise raise AssertionError.
                    assert four['payload']['completed']==4 and not four['outline_seen']
                    # Require four['payload']['run_metrics'] at 'mappo_decision_epochs' equals 0; otherwise raise
                    # AssertionError.
                    assert four['payload']['run_metrics']['mappo_decision_epochs']==0
                    # Require eligible['payload'] at 'completed' equals 4 and eligible at 'outline_seen';
                    # otherwise raise AssertionError.
                    assert eligible['payload']['completed']==4 and eligible['outline_seen']
                    # Iterate over result at 'complete_scenarios', binding each item to case.
                    for case in result['complete_scenarios']:
                        # Set metrics to case['payload'] at 'run_metrics'.
                        metrics=case['payload']['run_metrics']
                        # Require metrics at 'collisions' equals metrics at 'blocked_zone_violations'; equals 0;
                        # otherwise raise AssertionError.
                        assert metrics['collisions']==metrics['blocked_zone_violations']==0
                        # Require metrics at 'centralized_critic_runtime_calls' equals 0; otherwise raise
                        # AssertionError.
                        assert metrics['centralized_critic_runtime_calls']==0
                        # Require metrics at 'maximum_negotiation_participants' is at most 4; otherwise raise
                        # AssertionError.
                        assert metrics['maximum_negotiation_participants']<=4
                # Evaluate the awaited result of the result of observe(other).
                await observe(other)
                # Evaluate the awaited result of the result of page.goto(url plus the text '/components').
                # Evaluate the awaited result of the result of page.wait_for_timeout(400).
                await page.goto(url+'/components');await page.wait_for_timeout(400)
                # Evaluate the awaited result of the result of page.goto(url plus the text
                # '/component/right-of-way/live').
                # Evaluate the awaited result of the result of ready(page).
                await page.goto(url+'/component/right-of-way/live');await ready(page)
                # Evaluate the awaited result of the result of observe(page).
                # Evaluate the awaited result of the result of observe(other).
                await observe(page);await observe(other)
                # Evaluate the awaited result of the result of page.reload().
                # Evaluate the awaited result of the result of ready(page).
                # Evaluate the awaited result of the result of observe(page).
                await page.reload();await ready(page);await observe(page)
                # Evaluate the awaited result of the result of page.close().
                await page.close()
                # Set page to the awaited result of the result of first.new_page().
                # Evaluate the awaited result of the result of wire(page).
                page=await first.new_page();await wire(page)
                # Evaluate the awaited result of the result of page.goto(url plus the text
                # '/component/right-of-way/live').
                # Evaluate the awaited result of the result of ready(page).
                # Evaluate the awaited result of the result of observe(page).
                await page.goto(url+'/component/right-of-way/live');await ready(page);await observe(page)
                # Set result['navigate_reload_close_reopen'] to True.
                result['navigate_reload_close_reopen']=True
                # Run this branch when full_intersection and the awaited result of the result of
                # page.get_by_role('button', name='Stop', exact=True).is_disabled().
                if full_intersection and await page.get_by_role('button',name='Stop',exact=True).is_disabled():
                    # Finished runs have no process to stop. Exercise Stop on
                    # an actual active run rather than forcing a disabled UI.
                    # Evaluate the awaited result of the result of page.get_by_text('1. Rule-Resolved Conflict',
                    # exact=True).click().
                    await page.get_by_text('1. Rule-Resolved Conflict',exact=True).click()
                    # Evaluate the awaited result of the result of page.get_by_role('button', name='Run Scenario',
                    # exact=True).click().
                    await page.get_by_role('button',name='Run Scenario',exact=True).click()
                    # Evaluate the awaited result of the result of expect(page.get_by_role('button', name='Stop',
                    # exact=True)).to_be_enabled().
                    await expect(page.get_by_role('button',name='Stop',exact=True)).to_be_enabled(timeout=30000)
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Stop',
                # exact=True).click().
                await page.get_by_role('button',name='Stop',exact=True).click()
                # Evaluate the awaited result of the result of page.wait_for_function(the text
                # "document.querySelector('.scenario-run-state')?.textContent.inc...").
                await page.wait_for_function("document.querySelector('.scenario-run-state')?.textContent.includes('IDLE')",timeout=30000)
                # Evaluate the awaited result of the result of page.wait_for_timeout(700).
                await page.wait_for_timeout(700)
                # Set idle to the awaited result of the result of observe(page).
                idle=await observe(page)
                # Require idle and the negation of idle['frame'] at 'vehicles'; otherwise raise AssertionError
                # with the text 'STOPPED_RUN_VEHICLES_REAPPEAR_WHILE_IDLE'.
                assert idle and not idle['frame']['vehicles'],'STOPPED_RUN_VEHICLES_REAPPEAR_WHILE_IDLE'
                # Evaluate the awaited result of the result of page.get_by_text('1. Rule-Resolved Conflict',
                # exact=True).click().
                await page.get_by_text('1. Rule-Resolved Conflict',exact=True).click()
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Run Scenario',
                # exact=True).click().
                await page.get_by_role('button',name='Run Scenario',exact=True).click()
                # Set deadline to the monotonic clock time plus 90.
                # Set new_run to None.
                deadline=time.monotonic()+90;new_run=None
                # Repeat the following steps while the monotonic clock time is less than deadline.
                while time.monotonic()<deadline:
                    # Set sample to the awaited result of the result of observe(page).
                    sample=await observe(page)
                    # Run this branch when sample and sample['frame'] at 'run_id' does not belong to a tuple
                    # containing None, run_id and sample['frame'] at 'simulation_time' is at least 2.
                    if sample and sample['frame']['run_id'] not in (None,run_id) and sample['frame']['simulation_time']>=2:
                        # Set new_run to sample['frame'] at 'run_id'.
                        # Leave the nearest enclosing loop immediately.
                        new_run=sample['frame']['run_id'];break
                    # Evaluate the awaited result of the result of asyncio.sleep(0.2).
                    await asyncio.sleep(.2)
                # Require new_run; otherwise raise AssertionError with the text
                # 'RELAUNCH_DID_NOT_CREATE_FRESH_RUN'.
                assert new_run,'RELAUNCH_DID_NOT_CREATE_FRESH_RUN'
                # Set result['second_run_id'] to new_run.
                # Set result['stop_relaunch'] to True.
                result['second_run_id']=new_run;result['stop_relaunch']=True
                # Set owner to the result of psutil.Process(server.pid).
                owner=psutil.Process(server.pid)
                # Set identities to a list of a tuple containing q.pid, the result of q.create_time() for q in a
                # list containing owner plus the result of owner.children().
                identities=[(q.pid,q.create_time()) for q in [owner]+owner.children(recursive=True)]
                # Evaluate the awaited result of the result of first.close().
                # Evaluate the awaited result of the result of second.close().
                # Evaluate the awaited result of the result of browser.close().
                await first.close();await second.close();await browser.close()
                # Call server.send_signal with the supplied arguments.
                server.send_signal(signal.CTRL_BREAK_EVENT)
                # Set result['server_exit_code'] to the awaited result of the result of
                # asyncio.to_thread(server.wait, 30).
                result['server_exit_code']=await asyncio.to_thread(server.wait,30)
                # Set result['shutdown_while_runtime_active'] to True.
                result['shutdown_while_runtime_active']=True
        # Handle Exception as error using the recovery steps below.
        except Exception as error:
            # Set result['failure'] to the result of repr(error).
            result['failure']=repr(error)
            # Re-raise the active exception.
            raise
        # Run these cleanup steps whether the preceding operations succeed or raise an exception.
        finally:
            # Run this branch when the result of server.poll() is the same object as None.
            if server.poll() is None:
                # Attempt the enclosed operations and route matching exceptions to the handlers below.
                # Call server.send_signal with the supplied arguments.
                # Evaluate the awaited result of the result of asyncio.to_thread(server.wait, 25).
                try:server.send_signal(signal.CTRL_BREAK_EVENT);await asyncio.to_thread(server.wait,25)
                # Handle Exception using the recovery steps below.
                except Exception:
                    # Set owned to the result of psutil.Process(server.pid).
                    owned=psutil.Process(server.pid)
                    # Iterate over the result of owned.children(), binding each item to child.
                    # Call child.terminate with the supplied arguments.
                    for child in owned.children(recursive=True):child.terminate()
                    # Call owned.terminate with the supplied arguments.
                    owned.terminate()
                    # Set result['forced_cleanup'] to True.
                    result['forced_cleanup']=True
            # Set alive to an empty list.
            alive=[]
            # Iterate over identities, binding each item to (pid, born).
            for pid,born in identities:
                # Attempt the enclosed operations and route matching exceptions to the handlers below.
                try:
                    # Set q to the result of psutil.Process(pid).
                    q=psutil.Process(pid)
                    # Run this branch when the result of q.is_running() and the result of q.create_time() equals
                    # born.
                    # Append pid to alive.
                    if q.is_running() and q.create_time()==born:alive.append(pid)
                # Handle psutil.NoSuchProcess using the recovery steps below.
                # Keep this block syntactically valid without performing an operation.
                except psutil.NoSuchProcess:pass
            # Update result with the supplied entries.
            result.update(page_errors=errors,browser_console=console,failed_requests=requests,
                # Supply sampled_dom_frames as the number of entries in samples.
                # Supply matching_http_dom_frames as matched_api.
                sampled_dom_frames=len(samples),matching_http_dom_frames=matched_api,
                # Supply moving_red_samples as moving_red.
                # Supply held_to_ready_transitions as transitions.
                moving_red_samples=moving_red,held_to_ready_transitions=transitions,
                # Supply remaining_owned_processes as alive.
                remaining_owned_processes=alive)
            # Write the supplied text to (out / 'receipt.json').
            (out/'receipt.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
            # Write the supplied text to (out / 'dom_frames.json').
            (out/'dom_frames.json').write_text(json.dumps(samples,indent=2),encoding='utf-8')
    # Set text to the text read from (out / 'server.log').
    text=(out/'server.log').read_text(encoding='utf-8')
    # Require the negation of errors and the negation of result at 'remaining_owned_processes'; otherwise raise
    # AssertionError.
    assert not errors and not result['remaining_owned_processes']
    # Require the text 'Client has been deleted' does not belong to text and the text 'TypeError' does not belong
    # to text and the text 'Traceback' does not belong to text; otherwise raise AssertionError.
    assert 'Client has been deleted' not in text and 'TypeError' not in text and 'Traceback' not in text
    # Require matched_api is at least 3 and moving_red is greater than 0 and transitions; otherwise raise
    # AssertionError.
    assert matched_api>=3 and moving_red>0 and transitions
    # Display the serialized data produced by json.dumps.
    print(json.dumps({k:v for k,v in result.items() if k not in {'browser_console','failed_requests','real_mappo_event','held_to_ready_transitions'}}))


# Run this branch when __name__ equals the text '__main__'.
if __name__=='__main__':
    # Set parser to the result of argparse.ArgumentParser().
    # Call parser.add_argument with the supplied arguments.
    parser=argparse.ArgumentParser();parser.add_argument('--version',default='local_browser_v1')
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument('--full-intersection',action='store_true')
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument('--presentation-evidence',action='store_true')
    # Set args to the result of parser.parse_args().
    args=parser.parse_args()
    # Call asyncio.run with the supplied arguments.
    asyncio.run(main(args.version,args.full_intersection,args.presentation_evidence))
