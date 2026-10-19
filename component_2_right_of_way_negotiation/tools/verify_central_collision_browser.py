"""Verify actual presentation, end-to-end playback and protected paired run."""
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
LABEL5='5. Coordination Failure Stress Test (6–7 Vehicles)'
LABEL1='1. Rule-Based Right-of-Way (2 Vehicles)'

async def main(version):
    import psutil
    from playwright.async_api import async_playwright,expect
    out=BASE/'results/offline_counterfactual'/version;out.mkdir(exist_ok=False)
    tooling=json.loads((BASE/'results/final_live_correction/20261016/local_browser_tooling.json').read_text(encoding='utf-8-sig'))
    os.environ['PLAYWRIGHT_BROWSERS_PATH']=tooling['browsers']
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    url=f'http://127.0.0.1:{port}';result={};errors=[]
    with (out/'server.log').open('w',encoding='utf-8') as log:
        server=subprocess.Popen(['C:/R26-DS-017/venv/Scripts/python.exe','-B',str(BASE.parent/'socialmind_drive_showcase/app.py'),'--server-only','--port',str(port)],cwd=BASE.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        try:
            deadline=time.monotonic()+45
            while True:
                try:urllib.request.urlopen(url+'/components',timeout=2);break
                except OSError:
                    if time.monotonic()>deadline:raise
                    await asyncio.sleep(.2)
            async with async_playwright() as p:
                browser=await p.chromium.launch(headless=False,args=['--window-position=-10000,-10000'])
                result['browser_version']=browser.version
                page=await browser.new_page(viewport=dict(width=1600,height=1000));page.on('pageerror',lambda e:errors.append(str(e)))
                await page.goto(url+'/component/right-of-way/live')
                await page.wait_for_function("document.getElementById('c2-inspector')?.dataset.ready==='1'")
                await page.get_by_role('radio',name=LABEL5,exact=True).click()
                # Primary action must exist without opening the recorded comparison.
                await expect(page.get_by_text('A. Protected primary',exact=True)).not_to_be_visible()
                await page.get_by_role('button',name='PLAY UNCOORDINATED COLLISION REPLAY',exact=True).click()
                await page.wait_for_function("document.querySelector('.offline-replay-player')?.dataset.playing==='true'")
                await expect(page.locator('.offline-overview-canvas .offline-car')).to_have_count(6)
                start=await page.locator('.offline-replay-player').evaluate('(e)=>({...e.dataset})')
                initial_positions=await page.locator('.offline-overview-canvas .offline-car').evaluate_all('(es)=>es.map(e=>e.getAttribute("transform"))')
                await page.screenshot(path=str(out/'six_approaching.png'))
                await page.wait_for_timeout(900)
                assert initial_positions!=await page.locator('.offline-overview-canvas .offline-car').evaluate_all('(es)=>es.map(e=>e.getAttribute("transform"))')
                await page.get_by_label('Replay speed',exact=True).select_option('2')
                await page.wait_for_function("Number(document.querySelector('.offline-replay-player')?.dataset.simulationTime)>=23.8",timeout=45000)
                await page.get_by_role('button',name='Pause recorded trace',exact=True).click()
                await page.screenshot(path=str(out/'before_impact.png'))
                await page.get_by_role('button',name='Play recorded trace',exact=True).click()
                await page.wait_for_function("document.querySelector('.offline-replay-player')?.dataset.collisionCount==='1'",timeout=10000)
                event=await page.locator('.offline-replay-player').evaluate('(e)=>({...e.dataset})')
                assert event['playing']=='false' and float(event['simulationTime'])==24.28
                await expect(page.locator('.offline-impact-status')).to_contain_text('ACTUAL SUMO COLLISION DETECTED')
                await expect(page.locator('.offline-impact-status')).to_contain_text('24.24')
                for ego in ['PANEL_AV_N_02','PANEL_AV_W_01']:
                    car=page.locator(f'.offline-replay-canvas .offline-car[data-vehicle-id="{ego}"]')
                    box=await car.bounding_box();assert box['width']>20 and box['height']>20,box
                    canvas=await page.locator('.offline-replay-canvas').bounding_box()
                    assert canvas['x']<=box['x'] and box['x']+box['width']<=canvas['x']+canvas['width']
                    assert canvas['y']<=box['y'] and box['y']+box['height']<=canvas['y']+canvas['height']
                await page.screenshot(path=str(out/'authentic_impact.png'))
                await page.wait_for_timeout(1400)
                assert event==await page.locator('.offline-replay-player').evaluate('(e)=>({...e.dataset})')
                await page.get_by_role('button',name='Restart replay',exact=True).click()
                await page.wait_for_function("Number(document.querySelector('.offline-replay-player')?.dataset.simulationTime)<3")
                await page.get_by_role('button',name='Back to protected scenario',exact=True).click()
                await page.set_viewport_size(dict(width=1280,height=720))
                await page.get_by_role('button',name='PLAY UNCOORDINATED COLLISION REPLAY',exact=True).click()
                await page.wait_for_function("document.querySelector('.offline-replay-player')?.dataset.playing==='true'")
                await page.get_by_role('button',name='Jump to recorded event',exact=True).click()
                await page.wait_for_function("document.querySelector('.offline-replay-player')?.dataset.collisionCount==='1'")
                await page.screenshot(path=str(out/'laptop_impact.png'))
                for selector in ['.offline-toolbar','.offline-replay-canvas','.offline-warning']:
                    box=await page.locator(selector).bounding_box();assert box['y']>=0 and box['y']+box['height']<=720,box
                await page.get_by_role('button',name='Back to protected scenario',exact=True).click()
                side=page.locator('.scenario-sidebar');await side.hover();await page.mouse.wheel(0,1000);await page.wait_for_timeout(300)
                bottom=await side.evaluate('(e)=>e.scrollTop');await page.wait_for_timeout(1300)
                assert abs(bottom-await side.evaluate('(e)=>e.scrollTop'))<2
                await page.mouse.wheel(0,-1000)
                await page.get_by_role('button',name='PLAY PROTECTED SYSTEM',exact=True).click()
                await page.wait_for_function("document.querySelector('.scenario-run-state')?.textContent.includes('RUNNING')",timeout=30000)
                await page.wait_for_function("()=>{const e=document.querySelector('.c2-synchronized-frame');return e&&Number(JSON.parse(e.textContent).simulation_time)>=25}",timeout=90000)
                await page.screenshot(path=str(out/'protected_comparison.png'))
                await page.wait_for_function("!document.querySelector('.scenario-run-state')?.textContent.includes('RUNNING')",timeout=120000)
                # Read actual terminal publisher, not the separate offline counts.
                terminal=json.loads((BASE/'results/runtime_simulation/runtime/live_state.json').read_text())
                (out/'protected_terminal.json').write_text(json.dumps(terminal,indent=2))
                metrics=terminal['run_metrics']
                assert metrics['total_vehicles_completed']==6 and metrics['collisions']==0,metrics
                assert metrics['mappo_decision_epochs']>=1 and metrics['centralized_critic_runtime_calls']==0
                await page.get_by_role('radio',name=LABEL1,exact=True).click()
                assert await page.locator('.offline-replay-player:visible').count()==0
                await expect(page.get_by_role('button',name='PLAY UNCOORDINATED COLLISION REPLAY',exact=True)).to_have_count(0)
                result.update(status='PASS',initial_frame=start,collision_frame=event,protected_metrics=metrics,sidebar_scroll_retained=True,viewports=['1600x1000','1280x720'])
                await browser.close()
            server.send_signal(signal.CTRL_BREAK_EVENT)
            try:await asyncio.to_thread(server.wait,30)
            except subprocess.TimeoutExpired:result['shutdown_timeout']=True
        except Exception as error:
            result.update(status='FAILED',failure=repr(error))
            try:await page.screenshot(path=str(out/'failure.png'))
            except Exception:pass
            raise
        finally:
            if server.poll() is None:
                try:
                    root=psutil.Process(server.pid);tree=root.children(recursive=True)
                    for proc in reversed(tree):
                        try:proc.terminate()
                        except psutil.NoSuchProcess:pass
                    root.terminate();psutil.wait_procs([root]+tree,timeout=5)
                except psutil.NoSuchProcess:pass
            result['page_errors']=errors;(out/'receipt.json').write_text(json.dumps(result,indent=2))
    assert not errors
    print(json.dumps({k:v for k,v in result.items() if k!='protected_metrics'}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--version',default='central_presentation_v1')
    asyncio.run(main(parser.parse_args().version))
