"""Installed NiceGUI client simulation: real page handlers, timers and SUMO.

This is ASGI/handshake verification, not an interactive-browser visual test.
"""
import asyncio
import json
import logging
from pathlib import Path
import sys
import time
import socket

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE.parent))
sys.argv[0]=str(Path(__file__).resolve())
from nicegui import ui
from nicegui.testing.user_simulation import user_simulation
from nicegui.testing.user import User
from contextlib import asynccontextmanager
import httpx

OUT=BASE/'results/final_live_correction/20261016/client_lifecycle_v10'


@asynccontextmanager
async def installed_client_app():
    from nicegui import app
    from nicegui.testing.general import prepare_simulation
    prepare_simulation()
    from socialmind_drive_showcase.app import build_app
    build_app()
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://test') as client:
            yield User(client)


async def wait_for(predicate, timeout=45):
    deadline=time.monotonic()+timeout
    while not predicate():
        if time.monotonic()>deadline:
            raise TimeoutError('Lifecycle condition timed out')
        await asyncio.sleep(.1)


async def main():
    OUT.mkdir(parents=True,exist_ok=False)
    messages=[]
    class Capture(logging.Handler):
        def emit(self,record): messages.append(self.format(record))
    logging.getLogger().addHandler(Capture())
    receipt={'mode':'NICEGUI_ASGI_CLIENT_SIMULATION_NOT_BROWSER','navigations':0}
    with socket.socket() as available:
        available.bind(('127.0.0.1',0))
        test_port=available.getsockname()[1]
    sys.argv=[str(BASE.parent/'socialmind_drive_showcase/app.py'),'--server-only','--port',str(test_port)]
    async with installed_client_app() as first:
        from socialmind_drive_showcase.pages import component2_live_view as view
        from socialmind_drive_showcase.services.live_state_reader import read_live_state
        from dataclasses import replace
        view.LAUNCHER.component=replace(view.LAUNCHER.component,
            launch_command=view.LAUNCHER.component.launch_command+('--output-dir',str(OUT/'launch_results')))
        def fresh_frame():
            state=read_live_state(view.COMPONENT2_LIVE_STATE_PATH,started_after=view.LAUNCHER.started_at)
            return state.get('available') and state['payload'].get('simulation_time',0)>=2
        second=User(first.http_client)
        old=await first.open('/component/right-of-way/live')
        other=await second.open('/component/right-of-way/live')
        with old: view.SELECTED_SCENARIO['id']='rule_resolved_two'
        with other: assert view.SELECTED_SCENARIO['id']==view.DEFAULT_SCENARIO_ID
        receipt['independent_client_preferences']=True
        # Use the actual page click handler and actual owned SUMO subprocess.
        first.find('Run Scenario').click()
        await wait_for(lambda:view.LAUNCHER.status=='RUNNING')
        await wait_for(fresh_frame)
        for iteration in range(3):
            sockets=list(old._socket_to_document_id)
            for socket_id in sockets: old.handle_disconnect(socket_id)
            await asyncio.sleep(.25)
            assert all(not t.active for t in old.elements.values() if isinstance(t,ui.timer))
            await wait_for(lambda:old.is_deleted,timeout=8)
            await first.open('/components')
            old=await first.open('/component/right-of-way/live')
            receipt['navigations']+=2
            await asyncio.sleep(.3)
            assert not other.is_deleted and other.has_socket_connection
            live_targets=[t for t in view.live_view_panel.targets if not t.container.is_deleted]
            assert {t.container.client.id for t in live_targets}=={old.id,other.id}
            assert len(live_targets)==2
        with old: view._stop_current_scenario()
        await wait_for(lambda:view.LAUNCHER.status=='READY')
        assert not view.LAUNCHER.stop_forced and view.LAUNCHER.exit_code==0
        with old:
            view.SELECTED_SCENARIO['id']='rule_resolved_two'
            view._run_selected_scenario()
        await wait_for(lambda:view.LAUNCHER.status=='RUNNING')
        await wait_for(fresh_frame)
        receipt['stop_relaunch']=True
        for client in (old,other):
            for socket_id in list(client._socket_to_document_id): client.handle_disconnect(socket_id)
        await wait_for(lambda:old.is_deleted and other.is_deleted,timeout=8)
        await asyncio.sleep(.4)
        reopened=await first.open('/component/right-of-way/live')
        assert reopened.has_socket_connection
        with reopened: assert view.SELECTED_SCENARIO['id']==view.DEFAULT_SCENARIO_ID
        receipt['close_reopen']=True
        receipt['no_accumulated_live_targets']=True
        receipt['new_client_preferences_reset']=True
        from nicegui import app
        receipt['registered_shutdown_handler']=any(
            getattr(h,'__name__','')=='shutdown_owned_runtime' for h in app._shutdown_handlers)
        if not receipt['registered_shutdown_handler']:
            raise AssertionError('Actual shutdown handler not registered in client harness')
        # Lifespan exit invokes the actual zero-argument shutdown wrapper while running.
    receipt['shutdown_process_closed']=view.LAUNCHER._process is None
    bad=[m for m in messages if 'Client has been deleted' in m or 'TypeError' in m or 'Traceback' in m]
    receipt['lifecycle_errors']=bad
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    (OUT/'captured.log').write_text('\n'.join(messages),encoding='utf-8')
    assert not bad and receipt['shutdown_process_closed']
    print(json.dumps(receipt))


if __name__=='__main__': asyncio.run(main())
