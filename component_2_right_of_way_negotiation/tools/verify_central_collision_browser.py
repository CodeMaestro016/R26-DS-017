"""Verify actual presentation, end-to-end playback and protected paired run."""
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
# Set LABEL1 to the text '1. Rule-Based Right-of-Way (2 Vehicles)'.
LABEL1='1. Rule-Based Right-of-Way (2 Vehicles)'

# Main using the inputs and processing steps below.
# Input version: the supplied version.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
async def main(version):
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
                # Set result['browser_version'] to browser.version.
                result['browser_version']=browser.version
                # Set page to the awaited result of the result of browser.new_page().
                # Call page.on with the supplied arguments.
                page=await browser.new_page(viewport=dict(width=1600,height=1000));page.on('pageerror',lambda e:errors.append(str(e)))
                # Evaluate the awaited result of the result of page.goto(url plus the text
                # '/component/right-of-way/live').
                await page.goto(url+'/component/right-of-way/live')
                # Evaluate the awaited result of the result of page.wait_for_function(the text
                # "document.getElementById('c2-inspector')?.dataset.ready==='1'").
                await page.wait_for_function("document.getElementById('c2-inspector')?.dataset.ready==='1'")
                # Evaluate the awaited result of the result of page.get_by_role('radio', name=LABEL5,
                # exact=True).click().
                await page.get_by_role('radio',name=LABEL5,exact=True).click()
                # Primary action must exist without opening the recorded comparison.
                # Evaluate the awaited result of the result of expect(page.get_by_text('A. Protected primary',
                # exact=True)).not_to_be_visible().
                await expect(page.get_by_text('A. Protected primary',exact=True)).not_to_be_visible()
                # Evaluate the awaited result of the result of page.get_by_role('button', name='PLAY UNCOORDINATED
                # COLLISION REPLAY', exact=True).click().
                await page.get_by_role('button',name='PLAY UNCOORDINATED COLLISION REPLAY',exact=True).click()
                # Evaluate the awaited result of the result of page.wait_for_function(the text
                # "document.querySelector('.offline-replay-player')?.dataset.play...").
                await page.wait_for_function("document.querySelector('.offline-replay-player')?.dataset.playing==='true'")
                # Evaluate the awaited result of the result of expect(page.locator('.offline-overview-canvas
                # .offline-car')).to_have_count(6).
                await expect(page.locator('.offline-overview-canvas .offline-car')).to_have_count(6)
                # Set start to the awaited result of the result of
                # page.locator('.offline-replay-player').evaluate(the text '(e)=>({...e.dataset})').
                start=await page.locator('.offline-replay-player').evaluate('(e)=>({...e.dataset})')
                # Set initial_positions to the awaited result of the result of
                # page.locator('.offline-overview-canvas .offline-car').evaluate_all(the text
                # '(es)=>es.map(e=>e.getAttribute("transform"))').
                initial_positions=await page.locator('.offline-overview-canvas .offline-car').evaluate_all('(es)=>es.map(e=>e.getAttribute("transform"))')
                # Evaluate the awaited result of the result of page.screenshot().
                await page.screenshot(path=str(out/'six_approaching.png'))
                # Evaluate the awaited result of the result of page.wait_for_timeout(900).
                await page.wait_for_timeout(900)
                # Require initial_positions differs from the awaited result of the result of
                # page.locator('.offline-overview-canvas .offline-car').evaluate_all(the text
                # '(es)=>es.map(e=>e.getAttribute("transform"))'); otherwise raise AssertionError.
                assert initial_positions!=await page.locator('.offline-overview-canvas .offline-car').evaluate_all('(es)=>es.map(e=>e.getAttribute("transform"))')
                # Evaluate the awaited result of the result of page.get_by_label('Replay speed',
                # exact=True).select_option(the text '2').
                await page.get_by_label('Replay speed',exact=True).select_option('2')
                # Evaluate the awaited result of the result of page.wait_for_function(the text
                # "Number(document.querySelector('.offline-replay-player')?.datas...").
                await page.wait_for_function("Number(document.querySelector('.offline-replay-player')?.dataset.simulationTime)>=23.8",timeout=45000)
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Pause recorded
                # trace', exact=True).click().
                await page.get_by_role('button',name='Pause recorded trace',exact=True).click()
                # Evaluate the awaited result of the result of page.screenshot().
                await page.screenshot(path=str(out/'before_impact.png'))
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Play recorded
                # trace', exact=True).click().
                await page.get_by_role('button',name='Play recorded trace',exact=True).click()
                # Evaluate the awaited result of the result of page.wait_for_function(the text
                # "document.querySelector('.offline-replay-player')?.dataset.coll...").
                await page.wait_for_function("document.querySelector('.offline-replay-player')?.dataset.collisionCount==='1'",timeout=10000)
                # Set event to the awaited result of the result of
                # page.locator('.offline-replay-player').evaluate(the text '(e)=>({...e.dataset})').
                event=await page.locator('.offline-replay-player').evaluate('(e)=>({...e.dataset})')
                # Require event at 'playing' equals the text 'false' and a floating-point number built from event
                # at 'simulationTime' equals 24.28; otherwise raise AssertionError.
                assert event['playing']=='false' and float(event['simulationTime'])==24.28
                # Evaluate the awaited result of the result of
                # expect(page.locator('.offline-impact-status')).to_contain_text(the text 'ACTUAL SUMO COLLISION
                # DETECTED').
                await expect(page.locator('.offline-impact-status')).to_contain_text('ACTUAL SUMO COLLISION DETECTED')
                # Evaluate the awaited result of the result of
                # expect(page.locator('.offline-impact-status')).to_contain_text(the text '24.24').
                await expect(page.locator('.offline-impact-status')).to_contain_text('24.24')
                # Iterate over a list containing the text 'PANEL_AV_N_02', the text 'PANEL_AV_W_01', binding each
                # item to ego.
                for ego in ['PANEL_AV_N_02','PANEL_AV_W_01']:
                    # Set car to the result of page.locator(formatted text built from the embedded values).
                    car=page.locator(f'.offline-replay-canvas .offline-car[data-vehicle-id="{ego}"]')
                    # Set box to the awaited result of the result of car.bounding_box().
                    # Require box at 'width' is greater than 20 and box at 'height' is greater than 20; otherwise
                    # raise AssertionError with box.
                    box=await car.bounding_box();assert box['width']>20 and box['height']>20,box
                    # Set canvas to the awaited result of the result of
                    # page.locator('.offline-replay-canvas').bounding_box().
                    canvas=await page.locator('.offline-replay-canvas').bounding_box()
                    # Require canvas at 'x' is at most box at 'x' and box at 'x' plus box at 'width' is at most
                    # canvas at 'x' plus canvas at 'width'; otherwise raise AssertionError.
                    assert canvas['x']<=box['x'] and box['x']+box['width']<=canvas['x']+canvas['width']
                    # Require canvas at 'y' is at most box at 'y' and box at 'y' plus box at 'height' is at most
                    # canvas at 'y' plus canvas at 'height'; otherwise raise AssertionError.
                    assert canvas['y']<=box['y'] and box['y']+box['height']<=canvas['y']+canvas['height']
                # Evaluate the awaited result of the result of page.screenshot().
                await page.screenshot(path=str(out/'authentic_impact.png'))
                # Evaluate the awaited result of the result of page.wait_for_timeout(1400).
                await page.wait_for_timeout(1400)
                # Require event equals the awaited result of the result of
                # page.locator('.offline-replay-player').evaluate(the text '(e)=>({...e.dataset})'); otherwise
                # raise AssertionError.
                assert event==await page.locator('.offline-replay-player').evaluate('(e)=>({...e.dataset})')
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Restart replay',
                # exact=True).click().
                await page.get_by_role('button',name='Restart replay',exact=True).click()
                # Evaluate the awaited result of the result of page.wait_for_function(the text
                # "Number(document.querySelector('.offline-replay-player')?.datas...").
                await page.wait_for_function("Number(document.querySelector('.offline-replay-player')?.dataset.simulationTime)<3")
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Back to protected
                # scenario', exact=True).click().
                await page.get_by_role('button',name='Back to protected scenario',exact=True).click()
                # Evaluate the awaited result of the result of page.set_viewport_size(a dictionary built from the
                # supplied values).
                await page.set_viewport_size(dict(width=1280,height=720))
                # Evaluate the awaited result of the result of page.get_by_role('button', name='PLAY UNCOORDINATED
                # COLLISION REPLAY', exact=True).click().
                await page.get_by_role('button',name='PLAY UNCOORDINATED COLLISION REPLAY',exact=True).click()
                # Evaluate the awaited result of the result of page.wait_for_function(the text
                # "document.querySelector('.offline-replay-player')?.dataset.play...").
                await page.wait_for_function("document.querySelector('.offline-replay-player')?.dataset.playing==='true'")
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Jump to recorded
                # event', exact=True).click().
                await page.get_by_role('button',name='Jump to recorded event',exact=True).click()
                # Evaluate the awaited result of the result of page.wait_for_function(the text
                # "document.querySelector('.offline-replay-player')?.dataset.coll...").
                await page.wait_for_function("document.querySelector('.offline-replay-player')?.dataset.collisionCount==='1'")
                # Evaluate the awaited result of the result of page.screenshot().
                await page.screenshot(path=str(out/'laptop_impact.png'))
                # Iterate over a list containing the text '.offline-toolbar', the text '.offline-replay-canvas',
                # the text '.offline-warning', binding each item to selector.
                for selector in ['.offline-toolbar','.offline-replay-canvas','.offline-warning']:
                    # Set box to the awaited result of the result of page.locator(selector).bounding_box().
                    # Require box at 'y' is at least 0 and box at 'y' plus box at 'height' is at most 720;
                    # otherwise raise AssertionError with box.
                    box=await page.locator(selector).bounding_box();assert box['y']>=0 and box['y']+box['height']<=720,box
                # Evaluate the awaited result of the result of page.get_by_role('button', name='Back to protected
                # scenario', exact=True).click().
                await page.get_by_role('button',name='Back to protected scenario',exact=True).click()
                # Set side to the result of page.locator(the text '.scenario-sidebar').
                # Evaluate the awaited result of the result of side.hover().
                # Evaluate the awaited result of the result of page.mouse.wheel(0, 1000).
                # Evaluate the awaited result of the result of page.wait_for_timeout(300).
                side=page.locator('.scenario-sidebar');await side.hover();await page.mouse.wheel(0,1000);await page.wait_for_timeout(300)
                # Set bottom to the awaited result of the result of side.evaluate(the text '(e)=>e.scrollTop').
                # Evaluate the awaited result of the result of page.wait_for_timeout(1300).
                bottom=await side.evaluate('(e)=>e.scrollTop');await page.wait_for_timeout(1300)
                # Require the absolute value of bottom minus the awaited result of
                # side.evaluate('(e)=>e.scrollTop') is less than 2; otherwise raise AssertionError.
                assert abs(bottom-await side.evaluate('(e)=>e.scrollTop'))<2
                # Evaluate the awaited result of the result of page.mouse.wheel(0, the negative of 1000).
                await page.mouse.wheel(0,-1000)
                # Evaluate the awaited result of the result of page.get_by_role('button', name='PLAY PROTECTED
                # SYSTEM', exact=True).click().
                await page.get_by_role('button',name='PLAY PROTECTED SYSTEM',exact=True).click()
                # Evaluate the awaited result of the result of page.wait_for_function(the text
                # "document.querySelector('.scenario-run-state')?.textContent.inc...").
                await page.wait_for_function("document.querySelector('.scenario-run-state')?.textContent.includes('RUNNING')",timeout=30000)
                # Evaluate the awaited result of the result of page.wait_for_function(the text '()=>{const...').
                await page.wait_for_function("()=>{const e=document.querySelector('.c2-synchronized-frame');return e&&Number(JSON.parse(e.textContent).simulation_time)>=25}",timeout=90000)
                # Evaluate the awaited result of the result of page.screenshot().
                await page.screenshot(path=str(out/'protected_comparison.png'))
                # Evaluate the awaited result of the result of page.wait_for_function(the text
                # "!document.querySelector('.scenario-run-state')?.textContent.in...").
                await page.wait_for_function("!document.querySelector('.scenario-run-state')?.textContent.includes('RUNNING')",timeout=120000)
                # Read actual terminal publisher, not the separate offline counts.
                # Set terminal to the decoded data produced by json.loads from the text read from (BASE /
                # 'results/runtime_simulation/runtime/live_state.json').
                terminal=json.loads((BASE/'results/runtime_simulation/runtime/live_state.json').read_text())
                # Write the supplied text to (out / 'protected_terminal.json').
                (out/'protected_terminal.json').write_text(json.dumps(terminal,indent=2))
                # Set metrics to terminal at 'run_metrics'.
                metrics=terminal['run_metrics']
                # Require metrics at 'total_vehicles_completed' equals 6 and metrics at 'collisions' equals 0;
                # otherwise raise AssertionError with metrics.
                assert metrics['total_vehicles_completed']==6 and metrics['collisions']==0,metrics
                # Require metrics at 'mappo_decision_epochs' is at least 1 and metrics at
                # 'centralized_critic_runtime_calls' equals 0; otherwise raise AssertionError.
                assert metrics['mappo_decision_epochs']>=1 and metrics['centralized_critic_runtime_calls']==0
                # Evaluate the awaited result of the result of page.get_by_role('radio', name=LABEL1,
                # exact=True).click().
                await page.get_by_role('radio',name=LABEL1,exact=True).click()
                # Require the awaited result of the result of
                # page.locator('.offline-replay-player:visible').count() equals 0; otherwise raise AssertionError.
                assert await page.locator('.offline-replay-player:visible').count()==0
                # Evaluate the awaited result of the result of expect(page.get_by_role('button', name='PLAY
                # UNCOORDINATED COLLISION REPLAY',...(0).
                await expect(page.get_by_role('button',name='PLAY UNCOORDINATED COLLISION REPLAY',exact=True)).to_have_count(0)
                # Update result with the supplied entries.
                result.update(status='PASS',initial_frame=start,collision_frame=event,protected_metrics=metrics,sidebar_scroll_retained=True,viewports=['1600x1000','1280x720'])
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
    print(json.dumps({k:v for k,v in result.items() if k!='protected_metrics'}))

# Run this branch when __name__ equals the text '__main__'.
if __name__=='__main__':
    # Set parser to the result of argparse.ArgumentParser().
    # Call parser.add_argument with the supplied arguments.
    parser=argparse.ArgumentParser();parser.add_argument('--version',default='central_presentation_v1')
    # Call asyncio.run with the supplied arguments.
    asyncio.run(main(parser.parse_args().version))
