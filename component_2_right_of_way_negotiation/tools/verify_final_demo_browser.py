"""Real browser verification of the five-option original main application."""
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
# Import DOM_SAMPLE from verify_local_browser for the operations below.
from verify_local_browser import DOM_SAMPLE

# Set BASE to Path(__file__).resolve().parents at 1.
BASE=Path(__file__).resolve().parents[1]
# Set OUT to BASE joined with the path segment 'results/final_demonstrations/v1/browser_v1'.
OUT=BASE/'results/final_demonstrations/v1/browser_v1'


# Main using the inputs and processing steps below.
# Input only: the supplied only.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
async def main(only=None):
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
    # Set menu to the decoded data produced by json.loads from the text read from (BASE /
    # 'runtime_simulation/final_demonstrations.json').
    menu=json.loads((BASE/'runtime_simulation/final_demonstrations.json').read_text(encoding='utf-8'))
    # Enter the result of socket.socket() as sock and run the enclosed operations within that context.
    # Call sock.bind with the supplied arguments.
    # Set port to sock.getsockname() at 1.
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    # Set url to formatted text built from the embedded values.
    url=f'http://127.0.0.1:{port}'
    # Set errors to an empty list.
    # Set frames to an empty list.
    # Set cases to an empty list.
    # Set owned to an empty list.
    # Set result to an empty dictionary.
    errors=[];frames=[];cases=[];owned=[];result={}
    # Set colors to a dictionary containing APPROACHING, BLOCKED, READY, NEGOTIATING.
    colors={'APPROACHING':'#2684ff','BLOCKED':'#ef3f45','READY':'#20c86b','NEGOTIATING':'#ffd21f'}
    # Sample using the inputs and processing steps below.
    # Input page: the supplied page.
    # Output: return the value selected by the matching return branch below.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    async def sample(page):
        # Set frame to the awaited result of the result of page.evaluate(DOM_SAMPLE).
        frame=await page.evaluate(DOM_SAMPLE)
        # Run this branch when the negation of frame or frame at 'card_time' is the same object as None.
        # Return None to the caller.
        if not frame or frame['card_time'] is None:return None
        # Require the number of entries in frame at 'cars' equals the number of entries in frame at 'cards';
        # equals the number of entries in frame['frame'] at 'vehicles'; otherwise raise AssertionError.
        assert len(frame['cars'])==len(frame['cards'])==len(frame['frame']['vehicles'])
        # Require a floating-point number built from frame at 'card_time' equals frame['frame'] at
        # 'simulation_time'; otherwise raise AssertionError.
        assert float(frame['card_time'])==frame['frame']['simulation_time']
        # Set cars to a dictionary of v at 'id' mapped to v for v in frame at 'cars'.
        # Set cards to a dictionary of v at 'id' mapped to v for v in frame at 'cards'.
        cars={v['id']:v for v in frame['cars']};cards={v['id']:v for v in frame['cards']}
        # Iterate over frame['frame'] at 'vehicles', binding each item to v.
        for v in frame['frame']['vehicles']:
            # Set short to the result of ''.join(v['id'].split('_') sliced by -2:).
            # Set card to cards at short.
            short=''.join(v['id'].split('_')[-2:]);card=cards[short]
            # Require cars[v['id']] at 'fill' equals colors at v['display_state']; otherwise raise AssertionError.
            assert cars[v['id']]['fill']==colors[v['display_state']]
            # Require card at 'state' equals v at 'display_state'; otherwise raise AssertionError.
            assert card['state']==v['display_state']
            # Set rgb to a tuple built from a lazy sequence of an integer built from colors[v['display_state']]
            # sliced by i:i + 2 for i in a tuple containing 1, 3, 5.
            rgb=tuple(int(colors[v['display_state']][i:i+2],16) for i in (1,3,5))
            # Require card at 'border' equals formatted text built from the embedded values; otherwise raise
            # AssertionError.
            assert card['border']==f'rgb({rgb[0]}, {rgb[1]}, {rgb[2]})'
            # Require cars[v['id']] at 'outline' equals a Boolean built from 'recent_mappo_event' from v; use None
            # if absent; otherwise raise AssertionError.
            assert cars[v['id']]['outline']==bool(v.get('recent_mappo_event'))
        # Append frame to frames.
        # Return frame to the caller.
        frames.append(frame);return frame
    # Enter the result of (OUT / 'server.log').open(the text 'w') as log and run the enclosed operations within
    # that context.
    with (OUT/'server.log').open('w',encoding='utf-8') as log:
        # Set server to the result of subprocess.Popen(a list containing the text
        # 'C:/R26-DS-017/venv/Scripts/python.exe', the text '-B', a string...).
        server=subprocess.Popen(['C:/R26-DS-017/venv/Scripts/python.exe','-B',
            # Include a string built from BASE.parent joined with the path segment 'socialmind_drive_showcase/app.py' in
            # this list.
            str(BASE.parent/'socialmind_drive_showcase/app.py'),'--server-only','--port',str(port)],
            # Supply cwd as BASE.parent.
            # Supply stdout as log.
            # Supply stderr as subprocess.STDOUT.
            # Supply creationflags as subprocess.CREATE_NEW_PROCESS_GROUP.
            cwd=BASE.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
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
                # Set result['browser_version'] to browser.version.
                browser=await p.chromium.launch(headless=True);result['browser_version']=browser.version
                # Set context to the awaited result of the result of browser.new_context().
                context=await browser.new_context(viewport=dict(width=1600,height=1000))
                # Set page to the awaited result of the result of context.new_page().
                page=await context.new_page()
                # Call page.on with the supplied arguments.
                page.on('pageerror',lambda e:errors.append(str(e)))
                # Evaluate the awaited result of the result of page.goto(url plus the text
                # '/component/right-of-way/live').
                await page.goto(url+'/component/right-of-way/live')
                # Evaluate the awaited result of the result of page.wait_for_function(the text
                # "document.getElementById('c2-inspector')?.dataset.ready==='1'").
                await page.wait_for_function("document.getElementById('c2-inspector')?.dataset.ready==='1'")
                # Require the awaited result of the result of page.get_by_role('radio').count() equals 5;
                # otherwise raise AssertionError.
                assert await page.get_by_role('radio').count()==5
                # Iterate over menu, binding each item to item.
                # Evaluate the awaited result of the result of expect(page.get_by_role('radio',
                # name=item['final_label'], exact=True)).to_be_visible().
                for item in menu:await expect(page.get_by_role('radio',name=item['final_label'],exact=True)).to_be_visible()
                # Set prior to None.
                prior=None
                # Iterate over index/value pairs from menu, binding each item to (number, item).
                for number,item in enumerate(menu,1):
                    # Run this branch when only is a different object from None and number differs from only.
                    # Skip the rest of this loop iteration and process the next item.
                    if only is not None and number!=only:continue
                    # Run this branch when number equals 5.
                    if number==5:
                        # Set deadline to the monotonic clock time plus 600.
                        deadline=time.monotonic()+600
                        # Repeat the following steps while the negation of whether (BASE /
                        # 'results/final_demonstrations/v1/comparison.json') is an existing file.
                        while not (BASE/'results/final_demonstrations/v1/comparison.json').is_file():
                            # Run this branch when the monotonic clock time is greater than deadline.
                            # Raise TimeoutError with the text 'Comparison evidence not yet recorded' to stop this
                            # execution path.
                            if time.monotonic()>deadline:raise TimeoutError('Comparison evidence not yet recorded')
                            # Evaluate the awaited result of the result of asyncio.sleep(0.5).
                            await asyncio.sleep(.5)
                    # Evaluate the awaited result of the result of page.get_by_role('radio',
                    # name=item['final_label'], exact=True).click().
                    await page.get_by_role('radio',name=item['final_label'],exact=True).click()
                    # Evaluate the awaited result of the result of expect(page.get_by_role('radio',
                    # name=item['final_label'], exact=True)).to_have_attribute(the text 'aria-checked', the text
                    # 'true').
                    await expect(page.get_by_role('radio',name=item['final_label'],exact=True)).to_have_attribute('aria-checked','true')
                    # Run this branch when number equals 5.
                    if number==5:
                        # Evaluate the awaited result of the result of page.get_by_text('Recorded comparison',
                        # exact=True).click().
                        await page.get_by_text('Recorded comparison',exact=True).click()
                        # Evaluate the awaited result of the result of page.wait_for_timeout(1200).
                        await page.wait_for_timeout(1200)
                        # Evaluate the awaited result of the result of expect(page.get_by_text('Identical demand;
                        # safety enabled in both.', exact=True)).to_be_visible().
                        await expect(page.get_by_text('Identical demand; safety enabled in both.',exact=True)).to_be_visible()
                        # Evaluate the awaited result of the result of expect(page.get_by_text('INCOMPLETE · 1/6
                        # trips', exact=True)).to_be_visible().
                        await expect(page.get_by_text('INCOMPLETE · 1/6 trips',exact=True)).to_be_visible()
                    # Evaluate the awaited result of the result of page.screenshot().
                    await page.screenshot(path=str(OUT/f'{number}_menu.png'),full_page=True)
                    # Evaluate the awaited result of the result of page.get_by_role('button', name='Run Scenario',
                    # exact=True).click().
                    await page.get_by_role('button',name='Run Scenario',exact=True).click()
                    # Set deadline to the monotonic clock time plus 180.
                    # Set outline to False.
                    # Set run_id to None.
                    deadline=time.monotonic()+180;outline=False;run_id=None
                    # Repeat the following steps while the monotonic clock time is less than deadline.
                    while time.monotonic()<deadline:
                        # Set frame to the awaited result of the result of sample(page).
                        frame=await sample(page)
                        # Run this branch when frame and frame['frame'] at 'run_id' and frame['frame'] at
                        # 'scenario_id' equals item at 'scenario_id'.
                        if frame and frame['frame']['run_id'] and frame['frame']['scenario_id']==item['scenario_id']:
                            # Set f to frame at 'frame'.
                            # Set run_id to f at 'run_id'.
                            # Require run_id differs from prior; otherwise raise AssertionError.
                            f=frame['frame'];run_id=f['run_id'];assert run_id!=prior
                            # Update outline to its current value combined with whether any item is true in a lazy
                            # sequence of 'recent_mappo_event' from v; use None if absent for v in f at
                            # 'vehicles'.
                            outline|=any(v.get('recent_mappo_event') for v in f['vehicles'])
                            # Run this branch when f at 'simulation_time' is at least 20 and f at 'vehicles' and
                            # number differs from 2 or outline.
                            # Leave the nearest enclosing loop immediately.
                            if f['simulation_time']>=20 and f['vehicles'] and (number!=2 or outline):break
                        # Evaluate the awaited result of the result of asyncio.sleep(0.12).
                        await asyncio.sleep(.12)
                    # Raise TimeoutError with the text 'No qualifying real live frame:' plus item at 'scenario_id'
                    # to stop this execution path.
                    else:raise TimeoutError('No qualifying real live frame: '+item['scenario_id'])
                    # Evaluate the awaited result of the result of page.screenshot().
                    await page.screenshot(path=str(OUT/f'{number}_live.png'),full_page=True)
                    # Append a dictionary built from the supplied values to cases.
                    cases.append(dict(scenario=item['scenario_id'],run_id=run_id,
                        # Supply simulation_time as frame['frame'] at 'simulation_time'.
                        # Supply outline_seen as outline.
                        # Supply visible_ids as a list of v at 'id' for v in frame['frame'] at 'vehicles'.
                        simulation_time=frame['frame']['simulation_time'],outline_seen=outline,visible_ids=[v['id'] for v in frame['frame']['vehicles']]))
                    # Set prior to run_id.
                    prior=run_id
                    # Evaluate the awaited result of the result of page.get_by_role('button', name='Stop',
                    # exact=True).click().
                    await page.get_by_role('button',name='Stop',exact=True).click()
                    # Evaluate the awaited result of the result of page.wait_for_function(the text
                    # "document.querySelector('.scenario-run-state')?.textContent.inc...").
                    await page.wait_for_function("document.querySelector('.scenario-run-state')?.textContent.includes('IDLE')",timeout=30000)
                    # Evaluate the awaited result of the result of page.wait_for_timeout(600).
                    await page.wait_for_timeout(600)
                    # Set idle to the awaited result of the result of sample(page).
                    # Require idle and the negation of idle['frame'] at 'vehicles'; otherwise raise
                    # AssertionError.
                    idle=await sample(page);assert idle and not idle['frame']['vehicles']
                # Set process to the result of psutil.Process(server.pid).
                # Set owned to a list of a tuple containing q.pid, the result of q.create_time() for q in a list
                # containing process plus the result of process.children().
                process=psutil.Process(server.pid);owned=[(q.pid,q.create_time()) for q in [process]+process.children(recursive=True)]
                # Evaluate the awaited result of the result of page.goto(url plus the text '/components').
                await page.goto(url+'/components')
                # Evaluate the awaited result of the result of page.close().
                # Evaluate the awaited result of the result of context.close().
                # Evaluate the awaited result of the result of browser.close().
                await page.close();await context.close();await browser.close()
                # Evaluate the awaited result of the result of asyncio.sleep(0.3).
                await asyncio.sleep(.3)
            # Call server.send_signal with the supplied arguments.
            # Evaluate the awaited result of the result of asyncio.to_thread(server.wait, 30).
            server.send_signal(signal.CTRL_BREAK_EVENT);await asyncio.to_thread(server.wait,30)
        # Handle Exception as e using the recovery steps below.
        except Exception as e:
            # Set result['failure'] to the result of repr(e).
            result['failure']=repr(e)
            # Write the supplied text to (OUT / 'intermediate_failure.json').
            (OUT/'intermediate_failure.json').write_text(json.dumps(result,indent=2))
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
                # Call server.send_signal with the supplied arguments.
                server.send_signal(signal.CTRL_BREAK_EVENT)
                # Attempt the enclosed operations and route matching exceptions to the handlers below.
                # Evaluate the awaited result of the result of asyncio.to_thread(server.wait, 30).
                try:await asyncio.to_thread(server.wait,30)
                # Handle subprocess.TimeoutExpired using the recovery steps below.
                except subprocess.TimeoutExpired:
                    # Attempt the enclosed operations and route matching exceptions to the handlers below.
                    try:
                        # Set process to the result of psutil.Process(server.pid).
                        # Set tree to the result of process.children().
                        process=psutil.Process(server.pid);tree=process.children(recursive=True)
                        # Iterate over the reverse traversal of tree, binding each item to child.
                        for child in reversed(tree):
                            # Attempt the enclosed operations and route matching exceptions to the handlers below.
                            # Call child.terminate with the supplied arguments.
                            try:child.terminate()
                            # Handle psutil.NoSuchProcess using the recovery steps below.
                            # Keep this block syntactically valid without performing an operation.
                            except psutil.NoSuchProcess:pass
                        # Call process.terminate with the supplied arguments.
                        # Set result['forced_cleanup'] to True.
                        process.terminate();result['forced_cleanup']=True
                        # Call psutil.wait_procs with the supplied arguments.
                        psutil.wait_procs([process]+tree,timeout=5)
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
            result.update(cases=cases,exactly_five_options=True,dom_samples=len(frames),page_errors=errors,remaining_owned_processes=alive)
            # Write the supplied text to (OUT / 'receipt.json').
            (OUT/'receipt.json').write_text(json.dumps(result,indent=2))
            # Write the supplied text to (OUT / 'dom_frames.json').
            (OUT/'dom_frames.json').write_text(json.dumps(frames,indent=2))
    # Require the negation of errors and the negation of alive and the number of entries in cases equals 1 when
    # only, otherwise 5; otherwise raise AssertionError.
    assert not errors and not alive and len(cases)==(1 if only else 5)
    # Require the text 'Traceback' does not belong to the text read from (OUT / 'server.log'); otherwise raise
    # AssertionError.
    assert 'Traceback' not in (OUT/'server.log').read_text()
    # Display the serialized data produced by json.dumps.
    print(json.dumps(result))


# Run this branch when __name__ equals the text '__main__'.
if __name__=='__main__':
    # Set parser to the result of argparse.ArgumentParser().
    # Call parser.add_argument with the supplied arguments.
    parser=argparse.ArgumentParser();parser.add_argument('--version',default='browser_v2')
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument('--scenario-number',type=int,choices=range(1,6))
    # Set args to the result of parser.parse_args().
    # Set OUT to BASE joined with the path segment 'results/final_demonstrations/v1' divided by args.version.
    args=parser.parse_args();OUT=BASE/'results/final_demonstrations/v1'/args.version
    # Call asyncio.run with the supplied arguments.
    asyncio.run(main(args.scenario_number))
