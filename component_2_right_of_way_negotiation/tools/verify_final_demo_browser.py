"""Real browser verification of the five-option original main application."""
import asyncio
import argparse
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time
import urllib.request
from verify_local_browser import DOM_SAMPLE

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'results/final_demonstrations/v1/browser_v1'


async def main(only=None):
    import psutil
    from playwright.async_api import async_playwright,expect
    OUT.mkdir(parents=True,exist_ok=False)
    tooling=json.loads((BASE/'results/final_live_correction/20261016/local_browser_tooling.json').read_text(encoding='utf-8-sig'))
    os.environ['PLAYWRIGHT_BROWSERS_PATH']=tooling['browsers']
    menu=json.loads((BASE/'runtime_simulation/final_demonstrations.json').read_text(encoding='utf-8'))
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    url=f'http://127.0.0.1:{port}'
    errors=[];frames=[];cases=[];owned=[];result={}
    colors={'APPROACHING':'#2684ff','BLOCKED':'#ef3f45','READY':'#20c86b','NEGOTIATING':'#ffd21f'}
    async def sample(page):
        frame=await page.evaluate(DOM_SAMPLE)
        if not frame or frame['card_time'] is None:return None
        assert len(frame['cars'])==len(frame['cards'])==len(frame['frame']['vehicles'])
        assert float(frame['card_time'])==frame['frame']['simulation_time']
        cars={v['id']:v for v in frame['cars']};cards={v['id']:v for v in frame['cards']}
        for v in frame['frame']['vehicles']:
            short=''.join(v['id'].split('_')[-2:]);card=cards[short]
            assert cars[v['id']]['fill']==colors[v['display_state']]
            assert card['state']==v['display_state']
            rgb=tuple(int(colors[v['display_state']][i:i+2],16) for i in (1,3,5))
            assert card['border']==f'rgb({rgb[0]}, {rgb[1]}, {rgb[2]})'
            assert cars[v['id']]['outline']==bool(v.get('recent_mappo_event'))
        frames.append(frame);return frame
    with (OUT/'server.log').open('w',encoding='utf-8') as log:
        server=subprocess.Popen(['C:/R26-DS-017/venv/Scripts/python.exe','-B',
            str(BASE.parent/'socialmind_drive_showcase/app.py'),'--server-only','--port',str(port)],
            cwd=BASE.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        try:
            deadline=time.monotonic()+45
            while True:
                try:urllib.request.urlopen(url+'/components',timeout=2);break
                except OSError:
                    if time.monotonic()>deadline:raise
                    await asyncio.sleep(.2)
            async with async_playwright() as p:
                browser=await p.chromium.launch(headless=True);result['browser_version']=browser.version
                context=await browser.new_context(viewport=dict(width=1600,height=1000))
                page=await context.new_page()
                page.on('pageerror',lambda e:errors.append(str(e)))
                await page.goto(url+'/component/right-of-way/live')
                await page.wait_for_function("document.getElementById('c2-inspector')?.dataset.ready==='1'")
                assert await page.get_by_role('radio').count()==5
                for item in menu:await expect(page.get_by_role('radio',name=item['final_label'],exact=True)).to_be_visible()
                prior=None
                for number,item in enumerate(menu,1):
                    if only is not None and number!=only:continue
                    if number==5:
                        deadline=time.monotonic()+600
                        while not (BASE/'results/final_demonstrations/v1/comparison.json').is_file():
                            if time.monotonic()>deadline:raise TimeoutError('Comparison evidence not yet recorded')
                            await asyncio.sleep(.5)
                    await page.get_by_role('radio',name=item['final_label'],exact=True).click()
                    await expect(page.get_by_role('radio',name=item['final_label'],exact=True)).to_have_attribute('aria-checked','true')
                    if number==5:
                        await page.get_by_text('Recorded comparison',exact=True).click()
                        await page.wait_for_timeout(1200)
                        await expect(page.get_by_text('Identical demand; safety enabled in both.',exact=True)).to_be_visible()
                        await expect(page.get_by_text('INCOMPLETE · 1/6 trips',exact=True)).to_be_visible()
                    await page.screenshot(path=str(OUT/f'{number}_menu.png'),full_page=True)
                    await page.get_by_role('button',name='Run Scenario',exact=True).click()
                    deadline=time.monotonic()+180;outline=False;run_id=None
                    while time.monotonic()<deadline:
                        frame=await sample(page)
                        if frame and frame['frame']['run_id'] and frame['frame']['scenario_id']==item['scenario_id']:
                            f=frame['frame'];run_id=f['run_id'];assert run_id!=prior
                            outline|=any(v.get('recent_mappo_event') for v in f['vehicles'])
                            if f['simulation_time']>=20 and f['vehicles'] and (number!=2 or outline):break
                        await asyncio.sleep(.12)
                    else:raise TimeoutError('No qualifying real live frame: '+item['scenario_id'])
                    await page.screenshot(path=str(OUT/f'{number}_live.png'),full_page=True)
                    cases.append(dict(scenario=item['scenario_id'],run_id=run_id,
                        simulation_time=frame['frame']['simulation_time'],outline_seen=outline,visible_ids=[v['id'] for v in frame['frame']['vehicles']]))
                    prior=run_id
                    await page.get_by_role('button',name='Stop',exact=True).click()
                    await page.wait_for_function("document.querySelector('.scenario-run-state')?.textContent.includes('IDLE')",timeout=30000)
                    await page.wait_for_timeout(600)
                    idle=await sample(page);assert idle and not idle['frame']['vehicles']
                process=psutil.Process(server.pid);owned=[(q.pid,q.create_time()) for q in [process]+process.children(recursive=True)]
                await page.goto(url+'/components')
                await page.close();await context.close();await browser.close()
                await asyncio.sleep(.3)
            server.send_signal(signal.CTRL_BREAK_EVENT);await asyncio.to_thread(server.wait,30)
        except Exception as e:
            result['failure']=repr(e)
            (OUT/'intermediate_failure.json').write_text(json.dumps(result,indent=2))
            try:await page.screenshot(path=str(OUT/'failing_state.png'),full_page=True)
            except Exception:pass
            raise
        finally:
            if server.poll() is None:
                server.send_signal(signal.CTRL_BREAK_EVENT)
                try:await asyncio.to_thread(server.wait,30)
                except subprocess.TimeoutExpired:
                    try:
                        process=psutil.Process(server.pid);tree=process.children(recursive=True)
                        for child in reversed(tree):
                            try:child.terminate()
                            except psutil.NoSuchProcess:pass
                        process.terminate();result['forced_cleanup']=True
                        psutil.wait_procs([process]+tree,timeout=5)
                    except psutil.NoSuchProcess:pass
            alive=[]
            for pid,born in owned:
                try:
                    q=psutil.Process(pid)
                    if q.is_running() and q.create_time()==born:alive.append(pid)
                except psutil.NoSuchProcess:pass
            result.update(cases=cases,exactly_five_options=True,dom_samples=len(frames),page_errors=errors,remaining_owned_processes=alive)
            (OUT/'receipt.json').write_text(json.dumps(result,indent=2))
            (OUT/'dom_frames.json').write_text(json.dumps(frames,indent=2))
    assert not errors and not alive and len(cases)==(1 if only else 5)
    assert 'Traceback' not in (OUT/'server.log').read_text()
    print(json.dumps(result))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--version',default='browser_v2')
    parser.add_argument('--scenario-number',type=int,choices=range(1,6))
    args=parser.parse_args();OUT=BASE/'results/final_demonstrations/v1'/args.version
    asyncio.run(main(args.scenario_number))
