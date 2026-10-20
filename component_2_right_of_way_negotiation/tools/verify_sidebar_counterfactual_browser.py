"""Real wheel, scrollbar, live refresh and offline replay checks in Chromium."""
# Import asyncio for use in this module.
import asyncio
# Import argparse for use in this module.
import argparse
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
# Set OUT to BASE joined with the path segment 'results/offline_counterfactual/v1/browser_scroll_v1'.
OUT=BASE/'results/offline_counterfactual/v1/browser_scroll_v1'
# Set LABEL5 to the text '5. Coordination Failure Stress Test (6–7 Vehicles)'.
LABEL5='5. Coordination Failure Stress Test (6–7 Vehicles)'
# Set LABEL1 to the text '1. Rule-Based Right-of-Way (2 Vehicles)'.
LABEL1='1. Rule-Based Right-of-Way (2 Vehicles)'


# Main using the inputs and processing steps below.
# Input headed: the supplied headed.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
async def main(headed=False):
    # Import psutil for use in this module.
    import psutil
    # Import async_playwright, expect from playwright.async_api for the operations below.
    from playwright.async_api import async_playwright,expect
    # Create the directory requested by OUT.
    OUT.mkdir(parents=True,exist_ok=False)
    # Set tooling to the decoded data produced by json.loads from the text read from (BASE /
    # 'results/final_live_correction/20261016/local_browser_tooling.json').
    tooling=json.loads((BASE/'results/final_live_correction/20261016/local_browser_tooling.json').read_text(encoding='utf-8-sig'))
    # Set os.environ['PLAYWRIGHT_BROWSERS_PATH'] to tooling at 'browsers'.
    os.environ['PLAYWRIGHT_BROWSERS_PATH']=tooling['browsers']
    # Enter the result of socket.socket() as sock and run the enclosed operations within that context.
    # Call sock.bind with the supplied arguments.
    # Set port to sock.getsockname() at 1.
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    # Set url to formatted text built from the embedded values.
    url=f'http://127.0.0.1:{port}'
    # Set errors to an empty list.
    # Set records to an empty list.
    # Set result to an empty dictionary.
    # Set owned to an empty list.
    errors=[];records=[];result={};owned=[]
    # Position using the inputs and processing steps below.
    # Input page: the supplied page.
    # Output: the awaited result of the result of page.evaluate(the text '()=>{const...').
    async def position(page):
        # Return the awaited result of the result of page.evaluate(the text '()=>{const...') to the caller.
        return await page.evaluate('''()=>{const e=document.querySelector('.scenario-sidebar'),r=e.getBoundingClientRect();return {top:e.scrollTop,height:e.clientHeight,total:e.scrollHeight,x:r.x,y:r.y,width:r.width,scrollbarWidth:e.offsetWidth-e.clientWidth-2*e.clientLeft,border:e.clientLeft,stable:e===window.sidebarReference,bodyHeight:document.documentElement.scrollHeight,canvasY:document.querySelector('.sumo-canvas-host').getBoundingClientRect().y}}''')
    # Expand using the inputs and processing steps below.
    # Input page: the supplied page.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    async def expand(page):
        # Set label to the result of page.get_by_text(the text 'Recorded comparison').
        label=page.get_by_text('Recorded comparison',exact=True)
        # Run this branch when the negation of the awaited result of the result of page.get_by_text('A. Protected
        # primary', exact=True).is_visible().
        # Evaluate the awaited result of the result of label.click().
        if not await page.get_by_text('A. Protected primary',exact=True).is_visible():await label.click()
        # Evaluate the awaited result of the result of expect(page.get_by_text('A. Protected primary',
        # exact=True)).to_be_visible().
        await expect(page.get_by_text('A. Protected primary',exact=True)).to_be_visible()
        # Evaluate the awaited result of the result of page.wait_for_timeout(450).
        await page.wait_for_timeout(450)
    # Check scroll using the inputs and processing steps below.
    # Input page: the supplied page.
    # Input stage: the supplied stage.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records.
    async def check_scroll(page,stage):
        # Set side to the result of page.locator(the text '.scenario-sidebar').
        # Evaluate the awaited result of the result of side.hover().
        side=page.locator('.scenario-sidebar');await side.hover(position=dict(x=20,y=80))
        # Evaluate the awaited result of the result of page.mouse.wheel(0, 4000).
        # Evaluate the awaited result of the result of page.wait_for_timeout(250).
        await page.mouse.wheel(0,4000);await page.wait_for_timeout(250)
        # Set bottom to the awaited result of the result of position(page).
        bottom=await position(page)
        # Write the supplied text to (OUT / (stage + '_initial_scroll.json')).
        (OUT/(stage+'_initial_scroll.json')).write_text(json.dumps(bottom,indent=2))
        # Require bottom at 'top' is greater than 100 and bottom at 'total' is greater than bottom at 'height';
        # otherwise raise AssertionError with bottom.
        assert bottom['top']>100 and bottom['total']>bottom['height'],bottom
        # Evaluate the awaited result of the result of page.wait_for_timeout(2300).
        await page.wait_for_timeout(2300)
        # Set held to the awaited result of the result of position(page).
        held=await position(page)
        # Write the supplied text to (OUT / (stage + '_after_updates.json')).
        (OUT/(stage+'_after_updates.json')).write_text(json.dumps(held,indent=2))
        # Require held at 'stable' and the absolute value of held['top'] minus bottom['top'] is at most 2;
        # otherwise raise AssertionError with a tuple containing bottom, held.
        assert held['stable'] and abs(held['top']-bottom['top'])<=2,(bottom,held)
        # Require the absolute value of held at 'canvasY' minus bottom at 'canvasY' is at most 1; otherwise raise
        # AssertionError.
        assert abs(held['canvasY']-bottom['canvasY'])<=1
        # Evaluate the awaited result of the result of page.mouse.wheel(0, the negative of 4000).
        # Evaluate the awaited result of the result of page.wait_for_timeout(250).
        await page.mouse.wheel(0,-4000);await page.wait_for_timeout(250)
        # Set top to the awaited result of the result of position(page).
        # Require top at 'top' is less than bottom at 'top' minus 100; otherwise raise AssertionError.
        top=await position(page);assert top['top']<bottom['top']-100
        # Iterate over the integer range defined by 6, binding each item to _.
        # Evaluate the awaited result of the result of page.mouse.wheel(0, 35).
        # Evaluate the awaited result of the result of page.wait_for_timeout(35).
        for _ in range(6):await page.mouse.wheel(0,35);await page.wait_for_timeout(35)
        # Set incremental to the awaited result of the result of position(page).
        # Require incremental at 'top' is greater than top at 'top'; otherwise raise AssertionError.
        incremental=await position(page);assert incremental['top']>top['top']
        # Drag the actual native scrollbar thumb, not scrollTop by script.
        # Set thumb to the maximum of 20, incremental at 'height' raised to the power 2 divided by incremental at
        # 'total'.
        thumb=max(20,incremental['height']**2/incremental['total'])
        # Set sx to incremental at 'x' plus incremental at 'width' minus incremental at 'border' minus the maximum
        # of 1, incremental at 'scrollbarWidth' divided by 2.
        sx=incremental['x']+incremental['width']-incremental['border']-max(1,incremental['scrollbarWidth'])/2
        # Set sy to incremental at 'y' plus 1 plus incremental['top'] multiplied by incremental['height'] divided
        # by incremental at 'total' plus thumb divided by 2.
        sy=incremental['y']+1+incremental['top']*incremental['height']/incremental['total']+thumb/2
        # Evaluate the awaited result of the result of page.mouse.move(sx, sy).
        # Evaluate the awaited result of the result of page.mouse.down().
        await page.mouse.move(sx,sy);await page.mouse.down()
        # Evaluate the awaited result of the result of page.mouse.move(sx, incremental['y'] +
        # incremental['height'] minus thumb / 2 minus 3).
        await page.mouse.move(sx,incremental['y']+incremental['height']-thumb/2-3,steps=12)
        # Evaluate the awaited result of the result of page.mouse.up().
        # Evaluate the awaited result of the result of page.wait_for_timeout(200).
        await page.mouse.up();await page.wait_for_timeout(200)
        # Set dragged to the awaited result of the result of position(page).
        dragged=await position(page)
        # Write the supplied text to (OUT / (stage + '_drag.json')).
        (OUT/(stage+'_drag.json')).write_text(json.dumps(dict(before=incremental,after=dragged),indent=2))
        # Require dragged at 'top' is greater than incremental at 'top' plus 20; otherwise raise AssertionError
        # with a tuple containing incremental, dragged.
        assert dragged['top']>incremental['top']+20,(incremental,dragged)
        # Require dragged at 'bodyHeight' is at most bottom at 'bodyHeight' plus 2; otherwise raise
        # AssertionError.
        assert dragged['bodyHeight']<=bottom['bodyHeight']+2
        # Append a dictionary built from the supplied values to records.
        records.append(dict(stage=stage,bottom=bottom,after_updates=held,top=top,incremental=incremental,dragged=dragged))
        # Set right to the result of page.locator(the text '.viva-inspector').
        right=page.locator('.viva-inspector')
        # Evaluate the awaited result of the result of right.hover().
        # Evaluate the awaited result of the result of page.mouse.wheel(0, 250).
        # Evaluate the awaited result of the result of page.wait_for_timeout(100).
        await right.hover();await page.mouse.wheel(0,250);await page.wait_for_timeout(100)
        # Require the absolute value of await position(page) at 'top' minus dragged at 'top' is at most 2;
        # otherwise raise AssertionError.
        assert abs((await position(page))['top']-dragged['top'])<=2
    # Enter the result of (OUT / 'server.log').open(the text 'w') as log and run the enclosed operations within
    # that context.
    with (OUT/'server.log').open('w',encoding='utf-8') as log:
        # Set server to the result of subprocess.Popen(a list containing the text
        # 'C:/R26-DS-017/venv/Scripts/python.exe', the text '-B', a string...).
        server=subprocess.Popen(['C:/R26-DS-017/venv/Scripts/python.exe','-B',str(BASE.parent/'socialmind_drive_showcase/app.py'),
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
                try:urllib.request.urlopen(url+'/components',timeout=2);break
                # Handle OSError using the recovery steps below.
                except OSError:
                    # Run this branch when the monotonic clock time is greater than deadline.
                    # Re-raise the active exception.
                    if time.monotonic()>deadline:raise
                    # Evaluate the awaited result of the result of asyncio.sleep(0.2).
                    await asyncio.sleep(.2)
            # Enter the result of async_playwright() as p and run the enclosed operations within that context.
            async with async_playwright() as p:
                # Set browser to the awaited result of the result of p.chromium.launch().
                browser=await p.chromium.launch(headless=not headed,args=['--window-position=-10000,-10000'] if headed else [])
                # Set result['browser_version'] to browser.version.
                # Set result['headed'] to headed.
                result['browser_version']=browser.version;result['headed']=headed
                # Set contexts to an empty list.
                # Set pages to an empty list.
                contexts=[];pages=[]
                # Iterate over a list containing a tuple containing 1600, 1000, a tuple containing 1280, 720,
                # binding each item to (width, height).
                for width,height in [(1600,1000),(1280,720)]:
                    # Set context to the awaited result of the result of browser.new_context().
                    # Append context to contexts.
                    context=await browser.new_context(viewport=dict(width=width,height=height));contexts.append(context)
                    # Set page to the awaited result of the result of context.new_page().
                    # Append page to pages.
                    # Call page.on with the supplied arguments.
                    page=await context.new_page();pages.append(page);page.on('pageerror',lambda e:errors.append(str(e)))
                    # Evaluate the awaited result of the result of page.goto(url plus the text
                    # '/component/right-of-way/live').
                    await page.goto(url+'/component/right-of-way/live')
                    # Evaluate the awaited result of the result of page.wait_for_function(the text
                    # "document.getElementById('c2-inspector')?.dataset.ready==='1'").
                    await page.wait_for_function("document.getElementById('c2-inspector')?.dataset.ready==='1'")
                    # Evaluate the awaited result of the result of page.evaluate(the text
                    # 'window.sidebarReference=document.querySelector(".scenario-side...').
                    await page.evaluate('window.sidebarReference=document.querySelector(".scenario-sidebar")')
                    # Set initial to the awaited result of the result of position(page).
                    initial=await position(page)
                    # Evaluate the awaited result of the result of page.get_by_role('radio', name=LABEL5,
                    # exact=True).click().
                    # Evaluate the awaited result of the result of expand(page).
                    await page.get_by_role('radio',name=LABEL5,exact=True).click();await expand(page)
                    # Evaluate the awaited result of the result of check_scroll(page, formatted text built from
                    # the embedded values).
                    await check_scroll(page,f'idle_{width}x{height}')
                    # Require await position(page) at 'bodyHeight' is at most initial at 'bodyHeight' plus 2;
                    # otherwise raise AssertionError.
                    assert (await position(page))['bodyHeight']<=initial['bodyHeight']+2
                    # Evaluate the awaited result of the result of page.get_by_text('Recorded comparison',
                    # exact=True).click().
                    await page.get_by_text('Recorded comparison',exact=True).click()
                    # Evaluate the awaited result of the result of expect(page.get_by_text('A. Protected primary',
                    # exact=True)).not_to_be_visible().
                    await expect(page.get_by_text('A. Protected primary',exact=True)).not_to_be_visible()
                    # Evaluate the awaited result of the result of page.get_by_role('radio', name=LABEL1,
                    # exact=True).click().
                    await page.get_by_role('radio',name=LABEL1,exact=True).click()
                    # Evaluate the awaited result of the result of page.get_by_role('radio', name=LABEL5,
                    # exact=True).click().
                    # Evaluate the awaited result of the result of expand(page).
                    await page.get_by_role('radio',name=LABEL5,exact=True).click();await expand(page)
                    # Set radio to the result of page.get_by_role(the text 'radio').
                    # Evaluate the awaited result of the result of radio.focus().
                    radio=page.get_by_role('radio',name=LABEL5,exact=True);await radio.focus()
                    # Evaluate the awaited result of the result of page.wait_for_timeout(1100).
                    # Require the awaited result of the result of radio.evaluate(the text
                    # '(e)=>e===document.activeElement'); otherwise raise AssertionError.
                    await page.wait_for_timeout(1100);assert await radio.evaluate('(e)=>e===document.activeElement')
                    # Evaluate the awaited result of the result of page.screenshot().
                    await page.screenshot(path=str(OUT/f'idle_{width}.png'),full_page=False)
                # Set page to pages at 0.
                page=pages[0]
                # Replay must not launch a runtime or replace the live vehicle list.
                # Evaluate the awaited result of the result of page.get_by_role('button', name='View offline
                # unsafe counterfactual', exact=True).click().
                await page.get_by_role('button',name='View offline unsafe counterfactual',exact=True).click()
                # Evaluate the awaited result of the result of expect(page.get_by_text('OFFLINE UNSAFE
                # COUNTERFACTUAL — NOT THE PROPOSED SYSTEM',...().
                await expect(page.get_by_text('OFFLINE UNSAFE COUNTERFACTUAL — NOT THE PROPOSED SYSTEM',exact=True)).to_be_visible()
                # Evaluate the awaited result of the result of page.wait_for_function(the text
                # "document.querySelector('.offline-replay-player')?.dataset.fram...").
                await page.wait_for_function("document.querySelector('.offline-replay-player')?.dataset.frame==='0'")
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Play recorded
                # trace', exact=True).click().
                await page.get_by_role('button',name='Play recorded trace',exact=True).click()
                # Evaluate the awaited result of the result of page.wait_for_function(the text
                # "Number(document.querySelector('.offline-replay-player')?.datas...").
                await page.wait_for_function("Number(document.querySelector('.offline-replay-player')?.dataset.frame)>2")
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Pause recorded
                # trace', exact=True).click().
                await page.get_by_role('button',name='Pause recorded trace',exact=True).click()
                # Evaluate the awaited result of the result of expect(page.get_by_text('UNCOORDINATED OFFLINE
                # COUNTERFACTUAL — SAFETY INTERVENTIONS DISABLED IN...().
                await expect(page.get_by_text('UNCOORDINATED OFFLINE COUNTERFACTUAL — SAFETY INTERVENTIONS DISABLED IN ISOLATED SIMULATION',exact=True)).to_be_visible()
                # Evaluate the awaited result of the result of expect(page.get_by_text('ACTUAL SUMO COLLISION
                # DETECTED', exact=True)).to_be_visible().
                await expect(page.get_by_text('ACTUAL SUMO COLLISION DETECTED',exact=True)).to_be_visible()
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Restart replay',
                # exact=True).click().
                await page.get_by_role('button',name='Restart replay',exact=True).click()
                # Evaluate the awaited result of the result of page.wait_for_function(the text
                # "document.querySelector('.offline-replay-player')?.dataset.fram...").
                await page.wait_for_function("document.querySelector('.offline-replay-player')?.dataset.frame==='0'")
                # Evaluate the awaited result of the result of page.get_by_label('Replay speed',
                # exact=True).select_option(the text '0.5').
                await page.get_by_label('Replay speed',exact=True).select_option('0.5')
                # Set start to the monotonic clock time.
                start=time.monotonic()
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Play recorded
                # trace', exact=True).click().
                await page.get_by_role('button',name='Play recorded trace',exact=True).click()
                # Evaluate the awaited result of the result of page.wait_for_timeout(1600).
                await page.wait_for_timeout(1600)
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Pause recorded
                # trace', exact=True).click().
                await page.get_by_role('button',name='Pause recorded trace',exact=True).click()
                # Set timing to the awaited result of the result of
                # page.locator('.offline-replay-player').evaluate(the text '(e)=>({...e.dataset})').
                timing=await page.locator('.offline-replay-player').evaluate('(e)=>({...e.dataset})')
                # Set elapsed to the monotonic clock time minus start.
                # Set simulated to a floating-point number built from timing at 'simulationTime' minus 0.04.
                elapsed=time.monotonic()-start;simulated=float(timing['simulationTime'])-.04
                # Require 0.3 is less than simulated; is at most elapsed multiplied by 0.5 plus 0.15; otherwise
                # raise AssertionError with a tuple containing simulated, elapsed.
                assert .3<simulated<=elapsed*.5+.15,(simulated,elapsed)
                # Set result['recorded_timestamp_playback'] to a dictionary built from the supplied values.
                result['recorded_timestamp_playback']=dict(speed=.5,wall_seconds=elapsed,simulation_seconds=simulated)
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Jump to recorded
                # event', exact=True).click().
                await page.get_by_role('button',name='Jump to recorded event',exact=True).click()
                # Evaluate the awaited result of the result of page.wait_for_selector(the text
                # '.recorded-collision-marker').
                await page.wait_for_selector('.recorded-collision-marker')
                # Set replay to the awaited result of the result of
                # page.locator('.offline-replay-player').evaluate(the text '(e)=>({...e.dataset})').
                replay=await page.locator('.offline-replay-player').evaluate('(e)=>({...e.dataset})')
                # Require a floating-point number built from replay at 'simulationTime' equals 24.28 and replay at
                # 'collisionCount' equals the text '1'; otherwise raise AssertionError.
                assert float(replay['simulationTime'])==24.28 and replay['collisionCount']=='1'
                # Require the awaited result of the result of page.locator('.viva-vehicle-card').count() equals 0;
                # otherwise raise AssertionError.
                assert await page.locator('.viva-vehicle-card').count()==0
                # Evaluate the awaited result of the result of page.screenshot().
                await page.screenshot(path=str(OUT/'actual_collision_replay.png'),full_page=False)
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Close replay',
                # exact=True).click().
                await page.get_by_role('button',name='Close replay',exact=True).click()
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Run Scenario',
                # exact=True).click().
                await page.get_by_role('button',name='Run Scenario',exact=True).click()
                # Evaluate the awaited result of the result of page.wait_for_function(the text
                # "document.querySelector('.scenario-run-state')?.textContent.inc...").
                await page.wait_for_function("document.querySelector('.scenario-run-state')?.textContent.includes('RUNNING')",timeout=30000)
                # Set before to the awaited result of the result of page.locator('.live-view-time').inner_text().
                before=await page.locator('.live-view-time').inner_text()
                # Iterate over pages, binding each item to page.
                # Evaluate the awaited result of the result of check_scroll(page, the text 'running_' plus a
                # string built from page.viewport_size['width']).
                for page in pages:await check_scroll(page,'running_'+str(page.viewport_size['width']))
                # Require before differs from the awaited result of the result of
                # pages[0].locator('.live-view-time').inner_text(); otherwise raise AssertionError.
                assert before!=await pages[0].locator('.live-view-time').inner_text()
                # Set laptop to pages at 1.
                laptop=pages[1]
                # Evaluate the awaited result of the result of laptop.wait_for_function(the text '()=>{const...').
                await laptop.wait_for_function("()=>{const e=document.querySelector('.c2-synchronized-frame');return e&&Number(JSON.parse(e.textContent).simulation_time)>=25}",timeout=60000)
                # Set left_before to await position(laptop) at 'top'.
                left_before=(await position(laptop))['top']
                # Set right to the result of laptop.locator(the text '.viva-inspector').
                right=laptop.locator('.viva-inspector')
                # Set right_before to the awaited result of the result of right.evaluate(the text
                # '(e)=>({top:e.scrollTop,total:e.scrollHeight,height:e.clientHei...').
                right_before=await right.evaluate('(e)=>({top:e.scrollTop,total:e.scrollHeight,height:e.clientHeight})')
                # Evaluate the awaited result of the result of right.hover().
                # Evaluate the awaited result of the result of laptop.mouse.wheel(0, 500).
                # Evaluate the awaited result of the result of laptop.wait_for_timeout(250).
                await right.hover();await laptop.mouse.wheel(0,500);await laptop.wait_for_timeout(250)
                # Set right_after to the awaited result of the result of right.evaluate(the text
                # '(e)=>e.scrollTop').
                right_after=await right.evaluate('(e)=>e.scrollTop')
                # Write the supplied text to (OUT / 'right_panel_scroll.json').
                (OUT/'right_panel_scroll.json').write_text(json.dumps(dict(before=right_before,after=right_after),indent=2))
                # Require right_before at 'total' is greater than right_before at 'height' and right_after is
                # greater than right_before at 'top'; otherwise raise AssertionError.
                assert right_before['total']>right_before['height'] and right_after>right_before['top']
                # Require the absolute value of await position(laptop) at 'top' minus left_before is at most 2;
                # otherwise raise AssertionError.
                assert abs((await position(laptop))['top']-left_before)<=2
                # Set result['independent_right_panel_scroll'] to a dictionary built from the supplied values.
                result['independent_right_panel_scroll']=dict(before=right_before,after=right_after)
                # Iterate over pages, binding each item to page.
                # Evaluate the awaited result of the result of page.screenshot().
                for page in pages:await page.screenshot(path=str(OUT/f'running_{page.viewport_size["width"]}.png'),full_page=False)
                # Set page to pages at 0.
                # Set stop to the result of page.get_by_role(the text 'button').
                page=pages[0];stop=page.get_by_role('button',name='Stop',exact=True)
                # Run this branch when the negation of the awaited result of the result of stop.is_enabled().
                if not await stop.is_enabled():
                    # Evaluate the awaited result of the result of page.get_by_role('button', name='Run Scenario',
                    # exact=True).click().
                    await page.get_by_role('button',name='Run Scenario',exact=True).click()
                    # Evaluate the awaited result of the result of expect(stop).to_be_enabled().
                    await expect(stop).to_be_enabled(timeout=30000)
                # Evaluate the awaited result of the result of stop.click().
                await stop.click()
                # Evaluate the awaited result of the result of page.wait_for_function(the text
                # "document.querySelector('.scenario-run-state')?.textContent.inc...").
                await page.wait_for_function("document.querySelector('.scenario-run-state')?.textContent.includes('IDLE')",timeout=30000)
                # Evaluate the awaited result of the result of expect(page.get_by_role('button', name='Run
                # Scenario', exact=True)).to_be_enabled().
                await expect(page.get_by_role('button',name='Run Scenario',exact=True)).to_be_enabled()
                # Evaluate the awaited result of the result of page.get_by_role('radio', name=LABEL1,
                # exact=True).click().
                await page.get_by_role('radio',name=LABEL1,exact=True).click()
                # Evaluate the awaited result of the result of expect(page.get_by_role('button', name='View
                # offline unsafe counterfactual',...(0).
                await expect(page.get_by_role('button',name='View offline unsafe counterfactual',exact=True)).to_have_count(0)
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Run Scenario',
                # exact=True).click().
                await page.get_by_role('button',name='Run Scenario',exact=True).click()
                # Evaluate the awaited result of the result of page.wait_for_function(the text
                # "document.querySelector('.scenario-run-state')?.textContent.inc...").
                await page.wait_for_function("document.querySelector('.scenario-run-state')?.textContent.includes('RUNNING')",timeout=30000)
                # Evaluate the awaited result of the result of page.wait_for_function(the text '()=>{const...').
                await page.wait_for_function("()=>{const e=document.querySelector('.c2-synchronized-frame');return e&&JSON.parse(e.textContent).vehicles.length>0}",timeout=30000)
                # Require the awaited result of the result of
                # page.locator('.offline-replay-player:visible').count() equals 0; otherwise raise AssertionError.
                assert await page.locator('.offline-replay-player:visible').count()==0
                # Set result['another_protected_scenario_after_replay'] to the text 'Rule-Based Right-of-Way: live
                # vehicles observed; no offline...'.
                result['another_protected_scenario_after_replay']='Rule-Based Right-of-Way: live vehicles observed; no offline replay retained'
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Stop',
                # exact=True).click().
                await page.get_by_role('button',name='Stop',exact=True).click()
                # Evaluate the awaited result of the result of page.wait_for_function(the text
                # "document.querySelector('.scenario-run-state')?.textContent.inc...").
                await page.wait_for_function("document.querySelector('.scenario-run-state')?.textContent.includes('IDLE')",timeout=30000)
                # Evaluate the awaited result of the result of page.reload().
                # Evaluate the awaited result of the result of page.wait_for_function(the text
                # "document.getElementById('c2-inspector')?.dataset.ready==='1'").
                await page.reload();await page.wait_for_function("document.getElementById('c2-inspector')?.dataset.ready==='1'")
                # Evaluate the awaited result of the result of page.evaluate(the text
                # 'window.sidebarReference=document.querySelector(".scenario-side...').
                await page.evaluate('window.sidebarReference=document.querySelector(".scenario-sidebar")')
                # Evaluate the awaited result of the result of page.get_by_role('radio', name=LABEL5,
                # exact=True).click().
                # Evaluate the awaited result of the result of expand(page).
                # Evaluate the awaited result of the result of check_scroll(page, the text
                # 'after_browser_reload').
                await page.get_by_role('radio',name=LABEL5,exact=True).click();await expand(page);await check_scroll(page,'after_browser_reload')
                # Set root to the result of psutil.Process(server.pid).
                # Set owned to a list of a tuple containing q.pid, the result of q.create_time() for q in a list
                # containing root plus the result of root.children().
                root=psutil.Process(server.pid);owned=[(q.pid,q.create_time()) for q in [root]+root.children(recursive=True)]
                # Iterate over contexts, binding each item to context.
                # Evaluate the awaited result of the result of context.close().
                for context in contexts:await context.close()
                # Evaluate the awaited result of the result of browser.close().
                await browser.close()
            # Call server.send_signal with the supplied arguments.
            server.send_signal(signal.CTRL_BREAK_EVENT)
            # Attempt the enclosed operations and route matching exceptions to the handlers below.
            # Evaluate the awaited result of the result of asyncio.to_thread(server.wait, 30).
            try:await asyncio.to_thread(server.wait,30)
            # Handle subprocess.TimeoutExpired using the recovery steps below.
            # Set result['shutdown_timeout'] to True.
            except subprocess.TimeoutExpired:result['shutdown_timeout']=True
        # Handle Exception as e using the recovery steps below.
        except Exception as e:
            # Set result['failure'] to the result of repr(e).
            result['failure']=repr(e)
            # Attempt the enclosed operations and route matching exceptions to the handlers below.
            # Evaluate the awaited result of the result of page.screenshot().
            try:await page.screenshot(path=str(OUT/'failing_state.png'),full_page=True)
            # Handle Exception using the recovery steps below.
            # Keep this block syntactically valid without performing an operation.
            except Exception:pass
            # Re-raise the active exception.
            raise
        # Run these cleanup steps whether the preceding operations succeed or raise an exception.
        finally:
            # Run this branch when the result of server.poll() is the same object as None.
            if server.poll() is None:
                # Attempt the enclosed operations and route matching exceptions to the handlers below.
                try:
                    # Set root to the result of psutil.Process(server.pid).
                    # Set tree to the result of root.children().
                    root=psutil.Process(server.pid);tree=root.children(recursive=True)
                    # Iterate over the reverse traversal of tree, binding each item to child.
                    for child in reversed(tree):
                        # Attempt the enclosed operations and route matching exceptions to the handlers below.
                        # Call child.terminate with the supplied arguments.
                        try:child.terminate()
                        # Handle psutil.NoSuchProcess using the recovery steps below.
                        # Keep this block syntactically valid without performing an operation.
                        except psutil.NoSuchProcess:pass
                    # Call root.terminate with the supplied arguments.
                    # Call psutil.wait_procs with the supplied arguments.
                    root.terminate();psutil.wait_procs([root]+tree,timeout=5)
                # Handle psutil.NoSuchProcess using the recovery steps below.
                # Keep this block syntactically valid without performing an operation.
                except psutil.NoSuchProcess:pass
            # Set alive to an empty list.
            alive=[]
            # Iterate over owned, binding each item to (pid, born).
            for pid,born in owned:
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
            result.update(scroll_checks=records,page_errors=errors,remaining_owned_processes=alive)
            # Write the supplied text to (OUT / 'receipt.json').
            (OUT/'receipt.json').write_text(json.dumps(result,indent=2))
    # Require the negation of errors and the negation of alive and the number of entries in records equals 5;
    # otherwise raise AssertionError.
    assert not errors and not alive and len(records)==5
    # Display the serialized data produced by json.dumps.
    print(json.dumps(result))


# Run this branch when __name__ equals the text '__main__'.
if __name__=='__main__':
    # Set parser to the result of argparse.ArgumentParser().
    # Call parser.add_argument with the supplied arguments.
    parser=argparse.ArgumentParser();parser.add_argument('--version',default='browser_scroll_v2')
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument('--headed',action='store_true')
    # Set args to the result of parser.parse_args().
    # Set OUT to BASE joined with the path segment 'results/offline_counterfactual/v1' divided by args.version.
    args=parser.parse_args();OUT=BASE/'results/offline_counterfactual/v1'/args.version
    # Call asyncio.run with the supplied arguments.
    asyncio.run(main(args.headed))
