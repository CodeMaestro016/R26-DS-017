"""Exercise the ordinary Scenario 5 controls and the original shared canvas."""
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

async def main(version,presentation_only=False):
    import psutil
    from playwright.async_api import async_playwright,expect
    out=BASE/'results/offline_counterfactual'/version;out.mkdir(exist_ok=False)
    tooling=json.loads((BASE/'results/final_live_correction/20261016/local_browser_tooling.json').read_text(encoding='utf-8-sig'))
    os.environ['PLAYWRIGHT_BROWSERS_PATH']=tooling['browsers']
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    url=f'http://127.0.0.1:{port}';result={};errors=[]
    async def frame(page):
        return await page.locator('.c2-synchronized-frame').evaluate('(e)=>JSON.parse(e.textContent)')
    async def wait_replay(page,impact=False):
        await page.wait_for_function("()=>{const e=document.querySelector('.c2-synchronized-frame');if(!e)return false;const p=JSON.parse(e.textContent);return p.replay_mode&&p.vehicles.length===6"+("&&p.replay_events.length>0" if impact else '')+"}",timeout=45000)
    async def select(page,label):
        await page.get_by_role('radio',name=label,exact=True).click()
        await page.wait_for_timeout(300)
    async def scientific(page,label,filename,expected):
        if presentation_only:
            return dict(not_rerun=True,reason='Presentation-only recheck; full live run retained in main_canvas_v1')
        await select(page,label)
        await page.get_by_role('button',name='Run Scenario',exact=True).click()
        await page.wait_for_function("document.querySelector('.scenario-run-state')?.textContent.includes('SIMULATION CURRENTLY RUNNING')",timeout=30000)
        await page.wait_for_function("()=>{const e=document.querySelector('.c2-synchronized-frame');return e&&!JSON.parse(e.textContent).replay_mode&&Number(JSON.parse(e.textContent).simulation_time)>25}",timeout=90000)
        await page.screenshot(path=str(out/(filename+'_running.png')))
        await page.wait_for_function("!document.querySelector('.scenario-run-state')?.textContent.includes('SIMULATION CURRENTLY RUNNING')",timeout=180000)
        terminal=json.loads((BASE/'results/runtime_simulation/runtime/live_state.json').read_text())
        (out/(filename+'_terminal.json')).write_text(json.dumps(terminal,indent=2))
        metrics=terminal['run_metrics']
        assert metrics['total_vehicles_completed']==expected and metrics['collisions']==0
        assert metrics['mappo_decision_epochs']>0 and metrics['centralized_critic_runtime_calls']==0
        return metrics
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
                context=await browser.new_context(viewport=dict(width=1600,height=1000))
                page=await context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
                await page.goto(url+'/component/right-of-way/live');original_url=page.url
                await page.wait_for_function("document.getElementById('c2-inspector')?.dataset.ready==='1'")
                assert await page.get_by_role('radio').count()==5
                await select(page,LABEL5)
                await page.get_by_role('button',name='Run Scenario',exact=True).click()
                await wait_replay(page)
                initial=await frame(page)
                await page.evaluate('''()=>{window.cameraSamples=[];window.cameraMonitor=setInterval(()=>{const m=document.querySelector('.c2-synchronized-frame'),svg=document.querySelector('.sumo-live-canvas'),road=document.querySelector('.sumo-junction');if(!m||!svg||!road||!JSON.parse(m.textContent).replay_mode)return;const b=svg.getBoundingClientRect(),ctm=road.getScreenCTM();if(!ctm)return;window.cameraSamples.push({time:JSON.parse(m.textContent).simulation_time,zoom:svg.dataset.zoom,points:road.getAttribute('points'),x:b.x,y:b.y,width:b.width,height:b.height,scale:ctm.a,bodyLength:svg.querySelector('.sumo-car>rect')?.getAttribute('width')})},25)}''')
                await page.screenshot(path=str(out/'six_recorded_vehicles.png'))
                assert len(context.pages)==1 and page.url==original_url
                assert await page.locator('[role="dialog"]:visible').count()==0
                assert await page.locator('.sumo-canvas-host').count()==1
                assert await page.locator('.offline-replay-player').count()==0
                await expect(page.locator('.viva-vehicle-card')).to_have_count(6)
                await expect(page.locator('#c2-viva-cards')).to_contain_text('MAPPO: DISABLED')
                await page.wait_for_function("()=>{const e=document.querySelector('.c2-synchronized-frame');return e&&JSON.parse(e.textContent).simulation_time>=23.7}",timeout=45000)
                await page.screenshot(path=str(out/'before_impact.png'))
                await wait_replay(page,True)
                impact=await frame(page)
                await expect(page.locator('.viva-vehicle-card.collision-involved')).to_have_count(2)
                await expect(page.locator('.main-replay-collision')).to_contain_text('24.24')
                await expect(page.locator('.recorded-collision-marker')).to_have_count(1)
                assert len(await page.locator('.sumo-car.collision-involved').all())==2
                await page.screenshot(path=str(out/'main_canvas_collision_desktop.png'))
                await page.wait_for_timeout(1500);assert await frame(page)==impact
                camera=await page.evaluate('''()=>{clearInterval(window.cameraMonitor);return window.cameraSamples}''')
                assert len(camera)>100
                assert all(s['zoom']=='1.0' for s in camera)
                assert len({s['points'] for s in camera})==1
                assert len({s['bodyLength'] for s in camera})==1
                for key in ['x','y','width','height','scale']:
                    assert max(s[key] for s in camera)-min(s[key] for s in camera)<.25,(key,min(s[key] for s in camera),max(s[key] for s in camera))
                (out/'fixed_camera_samples.json').write_text(json.dumps(camera))
                result['fixed_camera']=dict(samples=len(camera),zoom='1.0',road_geometry_constant=True,physical_body_scale_constant=True,screen_bounds_constant=True)
                await page.set_viewport_size(dict(width=1280,height=720))
                await page.wait_for_timeout(500)
                await page.screenshot(path=str(out/'main_canvas_collision_laptop.png'))
                # Both involved bodies lie inside the existing main canvas crop.
                host=await page.locator('.sumo-canvas-host').bounding_box()
                boxes=await page.locator('.sumo-car.collision-involved').evaluate_all('(es)=>es.map(e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}})')
                assert all(b['width']>10 and b['height']>10 and host['x']<=b['x']<host['x']+host['width'] for b in boxes),boxes
                side=page.locator('.scenario-sidebar');await side.hover();await page.mouse.wheel(0,1000);await page.wait_for_timeout(300)
                bottom=await side.evaluate('(e)=>e.scrollTop');await page.wait_for_timeout(1200)
                assert abs(bottom-await side.evaluate('(e)=>e.scrollTop'))<2
                await page.get_by_role('button',name='Stop',exact=True).click()
                await page.wait_for_function("!document.querySelector('.main-replay-label')")
                await page.get_by_role('button',name='Run Scenario',exact=True).click();await wait_replay(page)
                assert (await frame(page))['simulation_time']<4
                await page.get_by_role('button',name='Stop',exact=True).click()
                labels=await page.get_by_role('radio').evaluate_all('(es)=>es.map(e=>e.getAttribute("aria-label")||e.closest(".q-radio").textContent)')
                # Use the exact current catalog labels, preserving all five options.
                label2=await page.get_by_role('radio').nth(1).get_attribute('aria-label')
                label4=await page.get_by_role('radio').nth(3).get_attribute('aria-label')
                result['scenario2']=await scientific(page,label2,'scenario2',4)
                result['scenario4']=await scientific(page,label4,'scenario4',16)
                await select(page,LABEL5)
                await page.get_by_role('button',name='Protected six-vehicle comparison',exact=True).click()
                await page.wait_for_function("document.querySelector('.scenario-run-state')?.textContent.includes('SIMULATION CURRENTLY RUNNING')",timeout=30000)
                await page.wait_for_function("()=>{const e=document.querySelector('.c2-synchronized-frame');return e&&!JSON.parse(e.textContent).replay_mode&&JSON.parse(e.textContent).vehicles.length>0}",timeout=30000)
                await page.screenshot(path=str(out/'protected_secondary.png'))
                await page.get_by_role('button',name='Stop',exact=True).click()
                await page.wait_for_function("!document.querySelector('.scenario-run-state')?.textContent.includes('SIMULATION CURRENTLY RUNNING')",timeout=30000)
                await select(page,await page.get_by_role('radio').nth(0).get_attribute('aria-label'))
                await select(page,LABEL5)
                await page.get_by_role('button',name='Run Scenario',exact=True).click();await wait_replay(page)
                assert (await frame(page))['simulation_time']<4
                await page.get_by_role('button',name='Stop',exact=True).click()
                result.update(status='PASS',initial_time=initial['simulation_time'],impact_time=impact['simulation_time'],same_main_canvas=True,no_modal_or_navigation=True,impact_boxes=boxes,sidebar_scroll_retained=True)
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
    print(json.dumps({k:v for k,v in result.items() if k not in ['scenario2','scenario4']}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--version',default='main_canvas_v1')
    parser.add_argument('--presentation-only',action='store_true')
    args=parser.parse_args()
    asyncio.run(main(args.version,args.presentation_only))
