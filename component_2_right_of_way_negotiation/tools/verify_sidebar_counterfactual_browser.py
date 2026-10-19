"""Real wheel, scrollbar, live refresh and offline replay checks in Chromium."""
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

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'results/offline_counterfactual/v1/browser_scroll_v1'
LABEL5='5. Coordination Failure Stress Test (6–7 Vehicles)'
LABEL1='1. Rule-Based Right-of-Way (2 Vehicles)'


async def main(headed=False):
    import psutil
    from playwright.async_api import async_playwright,expect
    OUT.mkdir(parents=True,exist_ok=False)
    tooling=json.loads((BASE/'results/final_live_correction/20261016/local_browser_tooling.json').read_text(encoding='utf-8-sig'))
    os.environ['PLAYWRIGHT_BROWSERS_PATH']=tooling['browsers']
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    url=f'http://127.0.0.1:{port}'
    errors=[];records=[];result={};owned=[]
    async def position(page):
        return await page.evaluate('''()=>{const e=document.querySelector('.scenario-sidebar'),r=e.getBoundingClientRect();return {top:e.scrollTop,height:e.clientHeight,total:e.scrollHeight,x:r.x,y:r.y,width:r.width,scrollbarWidth:e.offsetWidth-e.clientWidth-2*e.clientLeft,border:e.clientLeft,stable:e===window.sidebarReference,bodyHeight:document.documentElement.scrollHeight,canvasY:document.querySelector('.sumo-canvas-host').getBoundingClientRect().y}}''')
    async def expand(page):
        label=page.get_by_text('Recorded comparison',exact=True)
        if not await page.get_by_text('A. Protected primary',exact=True).is_visible():await label.click()
        await expect(page.get_by_text('A. Protected primary',exact=True)).to_be_visible()
        await page.wait_for_timeout(450)
    async def check_scroll(page,stage):
        side=page.locator('.scenario-sidebar');await side.hover(position=dict(x=20,y=80))
        await page.mouse.wheel(0,4000);await page.wait_for_timeout(250)
        bottom=await position(page)
        (OUT/(stage+'_initial_scroll.json')).write_text(json.dumps(bottom,indent=2))
        assert bottom['top']>100 and bottom['total']>bottom['height'],bottom
        await page.wait_for_timeout(2300)
        held=await position(page)
        (OUT/(stage+'_after_updates.json')).write_text(json.dumps(held,indent=2))
        assert held['stable'] and abs(held['top']-bottom['top'])<=2,(bottom,held)
        assert abs(held['canvasY']-bottom['canvasY'])<=1
        await page.mouse.wheel(0,-4000);await page.wait_for_timeout(250)
        top=await position(page);assert top['top']<bottom['top']-100
        for _ in range(6):await page.mouse.wheel(0,35);await page.wait_for_timeout(35)
        incremental=await position(page);assert incremental['top']>top['top']
        # Drag the actual native scrollbar thumb, not scrollTop by script.
        thumb=max(20,incremental['height']**2/incremental['total'])
        sx=incremental['x']+incremental['width']-incremental['border']-max(1,incremental['scrollbarWidth'])/2
        sy=incremental['y']+1+incremental['top']*incremental['height']/incremental['total']+thumb/2
        await page.mouse.move(sx,sy);await page.mouse.down()
        await page.mouse.move(sx,incremental['y']+incremental['height']-thumb/2-3,steps=12)
        await page.mouse.up();await page.wait_for_timeout(200)
        dragged=await position(page)
        (OUT/(stage+'_drag.json')).write_text(json.dumps(dict(before=incremental,after=dragged),indent=2))
        assert dragged['top']>incremental['top']+20,(incremental,dragged)
        assert dragged['bodyHeight']<=bottom['bodyHeight']+2
        records.append(dict(stage=stage,bottom=bottom,after_updates=held,top=top,incremental=incremental,dragged=dragged))
        right=page.locator('.viva-inspector')
        await right.hover();await page.mouse.wheel(0,250);await page.wait_for_timeout(100)
        assert abs((await position(page))['top']-dragged['top'])<=2
    with (OUT/'server.log').open('w',encoding='utf-8') as log:
        server=subprocess.Popen(['C:/R26-DS-017/venv/Scripts/python.exe','-B',str(BASE.parent/'socialmind_drive_showcase/app.py'),
            '--server-only','--port',str(port)],cwd=BASE.parent,stdout=log,stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        try:
            deadline=time.monotonic()+45
            while True:
                try:urllib.request.urlopen(url+'/components',timeout=2);break
                except OSError:
                    if time.monotonic()>deadline:raise
                    await asyncio.sleep(.2)
            async with async_playwright() as p:
                browser=await p.chromium.launch(headless=not headed,args=['--window-position=-10000,-10000'] if headed else [])
                result['browser_version']=browser.version;result['headed']=headed
                contexts=[];pages=[]
                for width,height in [(1600,1000),(1280,720)]:
                    context=await browser.new_context(viewport=dict(width=width,height=height));contexts.append(context)
                    page=await context.new_page();pages.append(page);page.on('pageerror',lambda e:errors.append(str(e)))
                    await page.goto(url+'/component/right-of-way/live')
                    await page.wait_for_function("document.getElementById('c2-inspector')?.dataset.ready==='1'")
                    await page.evaluate('window.sidebarReference=document.querySelector(".scenario-sidebar")')
                    initial=await position(page)
                    await page.get_by_role('radio',name=LABEL5,exact=True).click();await expand(page)
                    await check_scroll(page,f'idle_{width}x{height}')
                    assert (await position(page))['bodyHeight']<=initial['bodyHeight']+2
                    await page.get_by_text('Recorded comparison',exact=True).click()
                    await expect(page.get_by_text('A. Protected primary',exact=True)).not_to_be_visible()
                    await page.get_by_role('radio',name=LABEL1,exact=True).click()
                    await page.get_by_role('radio',name=LABEL5,exact=True).click();await expand(page)
                    radio=page.get_by_role('radio',name=LABEL5,exact=True);await radio.focus()
                    await page.wait_for_timeout(1100);assert await radio.evaluate('(e)=>e===document.activeElement')
                    await page.screenshot(path=str(OUT/f'idle_{width}.png'),full_page=False)
                page=pages[0]
                # Replay must not launch a runtime or replace the live vehicle list.
                await page.get_by_role('button',name='View offline unsafe counterfactual',exact=True).click()
                await expect(page.get_by_text('OFFLINE UNSAFE COUNTERFACTUAL — NOT THE PROPOSED SYSTEM',exact=True)).to_be_visible()
                await page.wait_for_function("document.querySelector('.offline-replay-player')?.dataset.frame==='0'")
                await page.get_by_role('button',name='Play recorded trace',exact=True).click()
                await page.wait_for_function("Number(document.querySelector('.offline-replay-player')?.dataset.frame)>2")
                await page.get_by_role('button',name='Pause recorded trace',exact=True).click()
                await expect(page.get_by_text('UNCOORDINATED OFFLINE COUNTERFACTUAL — SAFETY INTERVENTIONS DISABLED IN ISOLATED SIMULATION',exact=True)).to_be_visible()
                await expect(page.get_by_text('ACTUAL SUMO COLLISION DETECTED',exact=True)).to_be_visible()
                await page.get_by_role('button',name='Restart replay',exact=True).click()
                await page.wait_for_function("document.querySelector('.offline-replay-player')?.dataset.frame==='0'")
                await page.get_by_label('Replay speed',exact=True).select_option('0.5')
                start=time.monotonic()
                await page.get_by_role('button',name='Play recorded trace',exact=True).click()
                await page.wait_for_timeout(1600)
                await page.get_by_role('button',name='Pause recorded trace',exact=True).click()
                timing=await page.locator('.offline-replay-player').evaluate('(e)=>({...e.dataset})')
                elapsed=time.monotonic()-start;simulated=float(timing['simulationTime'])-.04
                assert .3<simulated<=elapsed*.5+.15,(simulated,elapsed)
                result['recorded_timestamp_playback']=dict(speed=.5,wall_seconds=elapsed,simulation_seconds=simulated)
                await page.get_by_role('button',name='Jump to recorded event',exact=True).click()
                await page.wait_for_selector('.recorded-collision-marker')
                replay=await page.locator('.offline-replay-player').evaluate('(e)=>({...e.dataset})')
                assert float(replay['simulationTime'])==24.28 and replay['collisionCount']=='1'
                assert await page.locator('.viva-vehicle-card').count()==0
                await page.screenshot(path=str(OUT/'actual_collision_replay.png'),full_page=False)
                await page.get_by_role('button',name='Close replay',exact=True).click()
                await page.get_by_role('button',name='Run Scenario',exact=True).click()
                await page.wait_for_function("document.querySelector('.scenario-run-state')?.textContent.includes('RUNNING')",timeout=30000)
                before=await page.locator('.live-view-time').inner_text()
                for page in pages:await check_scroll(page,'running_'+str(page.viewport_size['width']))
                assert before!=await pages[0].locator('.live-view-time').inner_text()
                laptop=pages[1]
                await laptop.wait_for_function("()=>{const e=document.querySelector('.c2-synchronized-frame');return e&&Number(JSON.parse(e.textContent).simulation_time)>=25}",timeout=60000)
                left_before=(await position(laptop))['top']
                right=laptop.locator('.viva-inspector')
                right_before=await right.evaluate('(e)=>({top:e.scrollTop,total:e.scrollHeight,height:e.clientHeight})')
                await right.hover();await laptop.mouse.wheel(0,500);await laptop.wait_for_timeout(250)
                right_after=await right.evaluate('(e)=>e.scrollTop')
                (OUT/'right_panel_scroll.json').write_text(json.dumps(dict(before=right_before,after=right_after),indent=2))
                assert right_before['total']>right_before['height'] and right_after>right_before['top']
                assert abs((await position(laptop))['top']-left_before)<=2
                result['independent_right_panel_scroll']=dict(before=right_before,after=right_after)
                for page in pages:await page.screenshot(path=str(OUT/f'running_{page.viewport_size["width"]}.png'),full_page=False)
                page=pages[0];stop=page.get_by_role('button',name='Stop',exact=True)
                if not await stop.is_enabled():
                    await page.get_by_role('button',name='Run Scenario',exact=True).click()
                    await expect(stop).to_be_enabled(timeout=30000)
                await stop.click()
                await page.wait_for_function("document.querySelector('.scenario-run-state')?.textContent.includes('IDLE')",timeout=30000)
                await expect(page.get_by_role('button',name='Run Scenario',exact=True)).to_be_enabled()
                await page.get_by_role('radio',name=LABEL1,exact=True).click()
                await expect(page.get_by_role('button',name='View offline unsafe counterfactual',exact=True)).to_have_count(0)
                await page.get_by_role('button',name='Run Scenario',exact=True).click()
                await page.wait_for_function("document.querySelector('.scenario-run-state')?.textContent.includes('RUNNING')",timeout=30000)
                await page.wait_for_function("()=>{const e=document.querySelector('.c2-synchronized-frame');return e&&JSON.parse(e.textContent).vehicles.length>0}",timeout=30000)
                assert await page.locator('.offline-replay-player:visible').count()==0
                result['another_protected_scenario_after_replay']='Rule-Based Right-of-Way: live vehicles observed; no offline replay retained'
                await page.get_by_role('button',name='Stop',exact=True).click()
                await page.wait_for_function("document.querySelector('.scenario-run-state')?.textContent.includes('IDLE')",timeout=30000)
                await page.reload();await page.wait_for_function("document.getElementById('c2-inspector')?.dataset.ready==='1'")
                await page.evaluate('window.sidebarReference=document.querySelector(".scenario-sidebar")')
                await page.get_by_role('radio',name=LABEL5,exact=True).click();await expand(page);await check_scroll(page,'after_browser_reload')
                root=psutil.Process(server.pid);owned=[(q.pid,q.create_time()) for q in [root]+root.children(recursive=True)]
                for context in contexts:await context.close()
                await browser.close()
            server.send_signal(signal.CTRL_BREAK_EVENT)
            try:await asyncio.to_thread(server.wait,30)
            except subprocess.TimeoutExpired:result['shutdown_timeout']=True
        except Exception as e:
            result['failure']=repr(e)
            try:await page.screenshot(path=str(OUT/'failing_state.png'),full_page=True)
            except Exception:pass
            raise
        finally:
            if server.poll() is None:
                try:
                    root=psutil.Process(server.pid);tree=root.children(recursive=True)
                    for child in reversed(tree):
                        try:child.terminate()
                        except psutil.NoSuchProcess:pass
                    root.terminate();psutil.wait_procs([root]+tree,timeout=5)
                except psutil.NoSuchProcess:pass
            alive=[]
            for pid,born in owned:
                try:
                    q=psutil.Process(pid)
                    if q.is_running() and q.create_time()==born:alive.append(pid)
                except psutil.NoSuchProcess:pass
            result.update(scroll_checks=records,page_errors=errors,remaining_owned_processes=alive)
            (OUT/'receipt.json').write_text(json.dumps(result,indent=2))
    assert not errors and not alive and len(records)==5
    print(json.dumps(result))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--version',default='browser_scroll_v2')
    parser.add_argument('--headed',action='store_true')
    args=parser.parse_args();OUT=BASE/'results/offline_counterfactual/v1'/args.version
    asyncio.run(main(args.headed))
