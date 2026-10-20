"""Exercise the ordinary Scenario 5 controls and the original shared canvas."""
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
# Set LABEL5 to the text '5. Coordination Failure Stress Test (6–7 Vehicles)'.
LABEL5='5. Coordination Failure Stress Test (6–7 Vehicles)'

# Main using the inputs and processing steps below.
# Input version: the supplied version.
# Input presentation_only: the supplied presentation only.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
async def main(version,presentation_only=False):
    # Import psutil for use in this module.
    import psutil
    # Import async_playwright, expect from playwright.async_api for the operations below.
    from playwright.async_api import async_playwright,expect
    # Set out to BASE joined with the path segment 'results/offline_counterfactual' divided by version.
    # Create the directory requested by out.
    out=BASE/'results/offline_counterfactual'/version;out.mkdir(exist_ok=False)
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
    # Set result to an empty dictionary.
    # Set errors to an empty list.
    url=f'http://127.0.0.1:{port}';result={};errors=[]
    # Frame using the inputs and processing steps below.
    # Input page: the supplied page.
    # Output: the awaited result of the result of page.locator('.c2-synchronized-frame').evaluate(the text
    # '(e)=>JSON.parse(e.textContent)').
    async def frame(page):
        # Return the awaited result of the result of page.locator('.c2-synchronized-frame').evaluate(the text
        # '(e)=>JSON.parse(e.textContent)') to the caller.
        return await page.locator('.c2-synchronized-frame').evaluate('(e)=>JSON.parse(e.textContent)')
    # Wait replay using the inputs and processing steps below.
    # Input page: the supplied page.
    # Input impact: the supplied impact.
    # Output: no explicit value; normal completion returns None.
    async def wait_replay(page,impact=False):
        # Evaluate the awaited result of the result of page.wait_for_function("()=>{const
        # e=document.querySelector('.c2-synchronized-frame');if(!e)return false;const... plus...).
        await page.wait_for_function("()=>{const e=document.querySelector('.c2-synchronized-frame');if(!e)return false;const p=JSON.parse(e.textContent);return p.replay_mode&&p.vehicles.length===6"+("&&p.replay_events.length>0" if impact else '')+"}",timeout=45000)
    # Select using the inputs and processing steps below.
    # Input page: the supplied page.
    # Input label: the supplied label.
    # Output: no explicit value; normal completion returns None.
    async def select(page,label):
        # Evaluate the awaited result of the result of page.get_by_role('radio', name=label, exact=True).click().
        await page.get_by_role('radio',name=label,exact=True).click()
        # Evaluate the awaited result of the result of page.wait_for_timeout(300).
        await page.wait_for_timeout(300)
    # Scientific using the inputs and processing steps below.
    # Input page: the supplied page.
    # Input label: the supplied label.
    # Input filename: the supplied filename.
    # Input expected: the supplied expected.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    async def scientific(page,label,filename,expected):
        # Run this branch when presentation_only.
        if presentation_only:
            # Return a dictionary built from the supplied values to the caller.
            return dict(not_rerun=True,reason='Presentation-only recheck; full live run retained in main_canvas_v1')
        # Evaluate the awaited result of the result of select(page, label).
        await select(page,label)
        # Evaluate the awaited result of the result of page.get_by_role('button', name='Run Scenario',
        # exact=True).click().
        await page.get_by_role('button',name='Run Scenario',exact=True).click()
        # Evaluate the awaited result of the result of page.wait_for_function(the text
        # "document.querySelector('.scenario-run-state')?.textContent.inc...").
        await page.wait_for_function("document.querySelector('.scenario-run-state')?.textContent.includes('SIMULATION CURRENTLY RUNNING')",timeout=30000)
        # Evaluate the awaited result of the result of page.wait_for_function(the text '()=>{const...').
        await page.wait_for_function("()=>{const e=document.querySelector('.c2-synchronized-frame');return e&&!JSON.parse(e.textContent).replay_mode&&Number(JSON.parse(e.textContent).simulation_time)>25}",timeout=90000)
        # Evaluate the awaited result of the result of page.screenshot().
        await page.screenshot(path=str(out/(filename+'_running.png')))
        # Evaluate the awaited result of the result of page.wait_for_function(the text
        # "!document.querySelector('.scenario-run-state')?.textContent.in...").
        await page.wait_for_function("!document.querySelector('.scenario-run-state')?.textContent.includes('SIMULATION CURRENTLY RUNNING')",timeout=180000)
        # Set terminal to the decoded data produced by json.loads from the text read from (BASE /
        # 'results/runtime_simulation/runtime/live_state.json').
        terminal=json.loads((BASE/'results/runtime_simulation/runtime/live_state.json').read_text())
        # Write the supplied text to (out / (filename + '_terminal.json')).
        (out/(filename+'_terminal.json')).write_text(json.dumps(terminal,indent=2))
        # Set metrics to terminal at 'run_metrics'.
        metrics=terminal['run_metrics']
        # Require metrics at 'total_vehicles_completed' equals expected and metrics at 'collisions' equals 0;
        # otherwise raise AssertionError.
        assert metrics['total_vehicles_completed']==expected and metrics['collisions']==0
        # Require metrics at 'mappo_decision_epochs' is greater than 0 and metrics at
        # 'centralized_critic_runtime_calls' equals 0; otherwise raise AssertionError.
        assert metrics['mappo_decision_epochs']>0 and metrics['centralized_critic_runtime_calls']==0
        # Return metrics to the caller.
        return metrics
    # Enter the result of (out / 'server.log').open(the text 'w') as log and run the enclosed operations within
    # that context.
    with (out/'server.log').open('w',encoding='utf-8') as log:
        # Set server to the result of subprocess.Popen(a list containing the text
        # 'C:/R26-DS-017/venv/Scripts/python.exe', the text '-B', a string...).
        server=subprocess.Popen(['C:/R26-DS-017/venv/Scripts/python.exe','-B',str(BASE.parent/'socialmind_drive_showcase/app.py'),'--server-only','--port',str(port)],cwd=BASE.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
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
                browser=await p.chromium.launch(headless=False,args=['--window-position=-10000,-10000'])
                # Set context to the awaited result of the result of browser.new_context().
                context=await browser.new_context(viewport=dict(width=1600,height=1000))
                # Set page to the awaited result of the result of context.new_page().
                # Call page.on with the supplied arguments.
                page=await context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
                # Evaluate the awaited result of the result of page.goto(url plus the text
                # '/component/right-of-way/live').
                # Set original_url to page.url.
                await page.goto(url+'/component/right-of-way/live');original_url=page.url
                # Evaluate the awaited result of the result of page.wait_for_function(the text
                # "document.getElementById('c2-inspector')?.dataset.ready==='1'").
                await page.wait_for_function("document.getElementById('c2-inspector')?.dataset.ready==='1'")
                # Require the awaited result of the result of page.get_by_role('radio').count() equals 5;
                # otherwise raise AssertionError.
                assert await page.get_by_role('radio').count()==5
                # Evaluate the awaited result of the result of select(page, LABEL5).
                await select(page,LABEL5)
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Run Scenario',
                # exact=True).click().
                await page.get_by_role('button',name='Run Scenario',exact=True).click()
                # Evaluate the awaited result of the result of wait_replay(page).
                await wait_replay(page)
                # Set initial to the awaited result of the result of frame(page).
                initial=await frame(page)
                # Evaluate the awaited result of the result of page.evaluate(the text
                # '()=>{window.cameraSamples=[];window.cameraMonitor=setInterval(...').
                await page.evaluate('''()=>{window.cameraSamples=[];window.cameraMonitor=setInterval(()=>{const m=document.querySelector('.c2-synchronized-frame'),svg=document.querySelector('.sumo-live-canvas'),road=document.querySelector('.sumo-junction');if(!m||!svg||!road||!JSON.parse(m.textContent).replay_mode)return;const b=svg.getBoundingClientRect(),ctm=road.getScreenCTM();if(!ctm)return;window.cameraSamples.push({time:JSON.parse(m.textContent).simulation_time,zoom:svg.dataset.zoom,points:road.getAttribute('points'),x:b.x,y:b.y,width:b.width,height:b.height,scale:ctm.a,bodyLength:svg.querySelector('.sumo-car>rect')?.getAttribute('width')})},25)}''')
                # Evaluate the awaited result of the result of page.screenshot().
                await page.screenshot(path=str(out/'six_recorded_vehicles.png'))
                # Require the number of entries in context.pages equals 1 and page.url equals original_url;
                # otherwise raise AssertionError.
                assert len(context.pages)==1 and page.url==original_url
                # Require the awaited result of the result of page.locator('[role="dialog"]:visible').count()
                # equals 0; otherwise raise AssertionError.
                assert await page.locator('[role="dialog"]:visible').count()==0
                # Require the awaited result of the result of page.locator('.sumo-canvas-host').count() equals 1;
                # otherwise raise AssertionError.
                assert await page.locator('.sumo-canvas-host').count()==1
                # Require the awaited result of the result of page.locator('.offline-replay-player').count()
                # equals 0; otherwise raise AssertionError.
                assert await page.locator('.offline-replay-player').count()==0
                # Evaluate the awaited result of the result of
                # expect(page.locator('.viva-vehicle-card')).to_have_count(6).
                await expect(page.locator('.viva-vehicle-card')).to_have_count(6)
                # Evaluate the awaited result of the result of
                # expect(page.locator('#c2-viva-cards')).to_contain_text(the text 'MAPPO: DISABLED').
                await expect(page.locator('#c2-viva-cards')).to_contain_text('MAPPO: DISABLED')
                # Evaluate the awaited result of the result of page.wait_for_function(the text '()=>{const...').
                await page.wait_for_function("()=>{const e=document.querySelector('.c2-synchronized-frame');return e&&JSON.parse(e.textContent).simulation_time>=23.7}",timeout=45000)
                # Evaluate the awaited result of the result of page.screenshot().
                await page.screenshot(path=str(out/'before_impact.png'))
                # Evaluate the awaited result of the result of wait_replay(page, True).
                await wait_replay(page,True)
                # Set impact to the awaited result of the result of frame(page).
                impact=await frame(page)
                # Evaluate the awaited result of the result of
                # expect(page.locator('.viva-vehicle-card.collision-involved')).to_have_count(2).
                await expect(page.locator('.viva-vehicle-card.collision-involved')).to_have_count(2)
                # Evaluate the awaited result of the result of
                # expect(page.locator('.main-replay-collision')).to_contain_text(the text '24.24').
                await expect(page.locator('.main-replay-collision')).to_contain_text('24.24')
                # Evaluate the awaited result of the result of
                # expect(page.locator('.recorded-collision-marker')).to_have_count(1).
                await expect(page.locator('.recorded-collision-marker')).to_have_count(1)
                # Require the number of entries in the awaited result of the result of
                # page.locator('.sumo-car.collision-involved').all() equals 2; otherwise raise AssertionError.
                assert len(await page.locator('.sumo-car.collision-involved').all())==2
                # Evaluate the awaited result of the result of page.screenshot().
                await page.screenshot(path=str(out/'main_canvas_collision_desktop.png'))
                # Evaluate the awaited result of the result of page.wait_for_timeout(1500).
                # Require the awaited result of the result of frame(page) equals impact; otherwise raise
                # AssertionError.
                await page.wait_for_timeout(1500);assert await frame(page)==impact
                # Set camera to the awaited result of the result of page.evaluate(the text
                # '()=>{clearInterval(window.cameraMonitor);return...').
                camera=await page.evaluate('''()=>{clearInterval(window.cameraMonitor);return window.cameraSamples}''')
                # Require the number of entries in camera is greater than 100; otherwise raise AssertionError.
                assert len(camera)>100
                # Require whether every item is true in a lazy sequence of s at 'zoom' equals the text '1.0' for s
                # in camera; otherwise raise AssertionError.
                assert all(s['zoom']=='1.0' for s in camera)
                # Require the number of entries in a set of s at 'points' for s in camera equals 1; otherwise
                # raise AssertionError.
                assert len({s['points'] for s in camera})==1
                # Require the number of entries in a set of s at 'bodyLength' for s in camera equals 1; otherwise
                # raise AssertionError.
                assert len({s['bodyLength'] for s in camera})==1
                # Iterate over a list containing the text 'x', the text 'y', the text 'width', the text 'height',
                # the text 'scale', binding each item to key.
                for key in ['x','y','width','height','scale']:
                    # Require the maximum of a lazy sequence of s[key] for s in camera minus the minimum of a lazy
                    # sequence of s[key] for s in camera is less than 0.25; otherwise raise AssertionError with a
                    # tuple containing key, the minimum of a lazy sequence of s at key for s in camera, the
                    # maximum of a lazy sequence of s at...
                    assert max(s[key] for s in camera)-min(s[key] for s in camera)<.25,(key,min(s[key] for s in camera),max(s[key] for s in camera))
                # Write the supplied text to (out / 'fixed_camera_samples.json').
                (out/'fixed_camera_samples.json').write_text(json.dumps(camera))
                # Set result['fixed_camera'] to a dictionary built from the supplied values.
                result['fixed_camera']=dict(samples=len(camera),zoom='1.0',road_geometry_constant=True,physical_body_scale_constant=True,screen_bounds_constant=True)
                # Evaluate the awaited result of the result of page.set_viewport_size(a dictionary built from the
                # supplied values).
                await page.set_viewport_size(dict(width=1280,height=720))
                # Evaluate the awaited result of the result of page.wait_for_timeout(500).
                await page.wait_for_timeout(500)
                # Evaluate the awaited result of the result of page.screenshot().
                await page.screenshot(path=str(out/'main_canvas_collision_laptop.png'))
                # Both involved bodies lie inside the existing main canvas crop.
                # Set host to the awaited result of the result of
                # page.locator('.sumo-canvas-host').bounding_box().
                host=await page.locator('.sumo-canvas-host').bounding_box()
                # Set boxes to the awaited result of the result of
                # page.locator('.sumo-car.collision-involved').evaluate_all(the text '(es)=>es.map(e=>{const
                # r=e.getBoundingClientRect();return...').
                boxes=await page.locator('.sumo-car.collision-involved').evaluate_all('(es)=>es.map(e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}})')
                # Require whether every item is true in a lazy sequence of b['width'] is greater than 10 and
                # b['height'] is greater than 10 and host['x'] is at most b['x']; is less than host['x'] +
                # host['width'] for b in boxes; otherwise raise AssertionError with boxes.
                assert all(b['width']>10 and b['height']>10 and host['x']<=b['x']<host['x']+host['width'] for b in boxes),boxes
                # Set side to the result of page.locator(the text '.scenario-sidebar').
                # Evaluate the awaited result of the result of side.hover().
                # Evaluate the awaited result of the result of page.mouse.wheel(0, 1000).
                # Evaluate the awaited result of the result of page.wait_for_timeout(300).
                side=page.locator('.scenario-sidebar');await side.hover();await page.mouse.wheel(0,1000);await page.wait_for_timeout(300)
                # Set bottom to the awaited result of the result of side.evaluate(the text '(e)=>e.scrollTop').
                # Evaluate the awaited result of the result of page.wait_for_timeout(1200).
                bottom=await side.evaluate('(e)=>e.scrollTop');await page.wait_for_timeout(1200)
                # Require the absolute value of bottom minus the awaited result of
                # side.evaluate('(e)=>e.scrollTop') is less than 2; otherwise raise AssertionError.
                assert abs(bottom-await side.evaluate('(e)=>e.scrollTop'))<2
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Stop',
                # exact=True).click().
                await page.get_by_role('button',name='Stop',exact=True).click()
                # Evaluate the awaited result of the result of page.wait_for_function(the text
                # "!document.querySelector('.main-replay-label')").
                await page.wait_for_function("!document.querySelector('.main-replay-label')")
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Run Scenario',
                # exact=True).click().
                # Evaluate the awaited result of the result of wait_replay(page).
                await page.get_by_role('button',name='Run Scenario',exact=True).click();await wait_replay(page)
                # Require await frame(page) at 'simulation_time' is less than 4; otherwise raise AssertionError.
                assert (await frame(page))['simulation_time']<4
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Stop',
                # exact=True).click().
                await page.get_by_role('button',name='Stop',exact=True).click()
                # Set labels to the awaited result of the result of page.get_by_role('radio').evaluate_all(the
                # text '(es)=>es.map(e=>e.getAttribute("aria-label")||e.closest(".q-ra...').
                labels=await page.get_by_role('radio').evaluate_all('(es)=>es.map(e=>e.getAttribute("aria-label")||e.closest(".q-radio").textContent)')
                # Use the exact current catalog labels, preserving all five options.
                # Set label2 to the awaited result of the result of
                # page.get_by_role('radio').nth(1).get_attribute(the text 'aria-label').
                label2=await page.get_by_role('radio').nth(1).get_attribute('aria-label')
                # Set label4 to the awaited result of the result of
                # page.get_by_role('radio').nth(3).get_attribute(the text 'aria-label').
                label4=await page.get_by_role('radio').nth(3).get_attribute('aria-label')
                # Set result['scenario2'] to the awaited result of the result of scientific(page, label2, the text
                # 'scenario2', 4).
                result['scenario2']=await scientific(page,label2,'scenario2',4)
                # Set result['scenario4'] to the awaited result of the result of scientific(page, label4, the text
                # 'scenario4', 16).
                result['scenario4']=await scientific(page,label4,'scenario4',16)
                # Evaluate the awaited result of the result of select(page, LABEL5).
                await select(page,LABEL5)
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Protected
                # six-vehicle comparison', exact=True).click().
                await page.get_by_role('button',name='Protected six-vehicle comparison',exact=True).click()
                # Evaluate the awaited result of the result of page.wait_for_function(the text
                # "document.querySelector('.scenario-run-state')?.textContent.inc...").
                await page.wait_for_function("document.querySelector('.scenario-run-state')?.textContent.includes('SIMULATION CURRENTLY RUNNING')",timeout=30000)
                # Evaluate the awaited result of the result of page.wait_for_function(the text '()=>{const...').
                await page.wait_for_function("()=>{const e=document.querySelector('.c2-synchronized-frame');return e&&!JSON.parse(e.textContent).replay_mode&&JSON.parse(e.textContent).vehicles.length>0}",timeout=30000)
                # Evaluate the awaited result of the result of page.screenshot().
                await page.screenshot(path=str(out/'protected_secondary.png'))
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Stop',
                # exact=True).click().
                await page.get_by_role('button',name='Stop',exact=True).click()
                # Evaluate the awaited result of the result of page.wait_for_function(the text
                # "!document.querySelector('.scenario-run-state')?.textContent.in...").
                await page.wait_for_function("!document.querySelector('.scenario-run-state')?.textContent.includes('SIMULATION CURRENTLY RUNNING')",timeout=30000)
                # Evaluate the awaited result of the result of select(page, the awaited result of the result
                # of...).
                await select(page,await page.get_by_role('radio').nth(0).get_attribute('aria-label'))
                # Evaluate the awaited result of the result of select(page, LABEL5).
                await select(page,LABEL5)
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Run Scenario',
                # exact=True).click().
                # Evaluate the awaited result of the result of wait_replay(page).
                await page.get_by_role('button',name='Run Scenario',exact=True).click();await wait_replay(page)
                # Require await frame(page) at 'simulation_time' is less than 4; otherwise raise AssertionError.
                assert (await frame(page))['simulation_time']<4
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Stop',
                # exact=True).click().
                await page.get_by_role('button',name='Stop',exact=True).click()
                # Update result with the supplied entries.
                result.update(status='PASS',initial_time=initial['simulation_time'],impact_time=impact['simulation_time'],same_main_canvas=True,no_modal_or_navigation=True,impact_boxes=boxes,sidebar_scroll_retained=True)
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
        # Handle Exception as error using the recovery steps below.
        except Exception as error:
            # Update result with the supplied entries.
            result.update(status='FAILED',failure=repr(error))
            # Attempt the enclosed operations and route matching exceptions to the handlers below.
            # Evaluate the awaited result of the result of page.screenshot().
            try:await page.screenshot(path=str(out/'failure.png'))
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
                    # Iterate over the reverse traversal of tree, binding each item to proc.
                    for proc in reversed(tree):
                        # Attempt the enclosed operations and route matching exceptions to the handlers below.
                        # Call proc.terminate with the supplied arguments.
                        try:proc.terminate()
                        # Handle psutil.NoSuchProcess using the recovery steps below.
                        # Keep this block syntactically valid without performing an operation.
                        except psutil.NoSuchProcess:pass
                    # Call root.terminate with the supplied arguments.
                    # Call psutil.wait_procs with the supplied arguments.
                    root.terminate();psutil.wait_procs([root]+tree,timeout=5)
                # Handle psutil.NoSuchProcess using the recovery steps below.
                # Keep this block syntactically valid without performing an operation.
                except psutil.NoSuchProcess:pass
            # Set result['page_errors'] to errors.
            # Write the supplied text to (out / 'receipt.json').
            result['page_errors']=errors;(out/'receipt.json').write_text(json.dumps(result,indent=2))
    # Require the negation of errors; otherwise raise AssertionError.
    assert not errors
    # Display the serialized data produced by json.dumps.
    print(json.dumps({k:v for k,v in result.items() if k not in ['scenario2','scenario4']}))

# Run this branch when __name__ equals the text '__main__'.
if __name__=='__main__':
    # Set parser to the result of argparse.ArgumentParser().
    # Call parser.add_argument with the supplied arguments.
    parser=argparse.ArgumentParser();parser.add_argument('--version',default='main_canvas_v1')
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument('--presentation-only',action='store_true')
    # Set args to the result of parser.parse_args().
    args=parser.parse_args()
    # Call asyncio.run with the supplied arguments.
    asyncio.run(main(args.version,args.presentation_only))
