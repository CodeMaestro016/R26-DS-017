"""Installed NiceGUI client simulation: real page handlers, timers and SUMO.

This is ASGI/handshake verification, not an interactive-browser visual test.
"""
# Import asyncio for use in this module.
import asyncio
# Import json for use in this module.
import json
# Import logging for use in this module.
import logging
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import sys for use in this module.
import sys
# Import time for use in this module.
import time
# Import socket for use in this module.
import socket

# Set BASE to Path(__file__).resolve().parents at 1.
BASE=Path(__file__).resolve().parents[1]
# Call sys.path.insert with the supplied arguments.
sys.path.insert(0,str(BASE.parent))
# Set sys.argv[0] to a string built from the result of Path(__file__).resolve().
sys.argv[0]=str(Path(__file__).resolve())
# Import ui from nicegui for the operations below.
from nicegui import ui
# Import user_simulation from nicegui.testing.user_simulation for the operations below.
from nicegui.testing.user_simulation import user_simulation
# Import User from nicegui.testing.user for the operations below.
from nicegui.testing.user import User
# Import asynccontextmanager from contextlib for the operations below.
from contextlib import asynccontextmanager
# Import httpx for use in this module.
import httpx

# Set OUT to BASE joined with the path segment 'results/final_live_correction/20261016/client_lifecycle_v10'.
OUT=BASE/'results/final_live_correction/20261016/client_lifecycle_v10'


# Apply asynccontextmanager as a decorator to configure the following definition.
@asynccontextmanager
# Installed client app using the inputs and processing steps below.
# Output: yield the values produced by the yield statements below.
async def installed_client_app():
    # Import app from nicegui for the operations below.
    from nicegui import app
    # Import prepare_simulation from nicegui.testing.general for the operations below.
    from nicegui.testing.general import prepare_simulation
    # Call prepare_simulation with the supplied arguments.
    prepare_simulation()
    # Import build_app from socialmind_drive_showcase.app for the operations below.
    from socialmind_drive_showcase.app import build_app
    # Call build_app with the supplied arguments.
    build_app()
    # Enter the result of app.router.lifespan_context(app) and run the enclosed operations within that context.
    async with app.router.lifespan_context(app):
        # Enter the result of httpx.AsyncClient() as client and run the enclosed operations within that context.
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://test') as client:
            # Yield the result of User(client) to the iterator consumer.
            yield User(client)


# Wait for using the inputs and processing steps below.
# Input predicate: the supplied predicate.
# Input timeout: the supplied timeout.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
async def wait_for(predicate, timeout=45):
    # Set deadline to the monotonic clock time plus timeout.
    deadline=time.monotonic()+timeout
    # Repeat the following steps while the negation of the result of predicate().
    while not predicate():
        # Run this branch when the monotonic clock time is greater than deadline.
        if time.monotonic()>deadline:
            # Raise TimeoutError with the text 'Lifecycle condition timed out' to stop this execution path.
            raise TimeoutError('Lifecycle condition timed out')
        # Evaluate the awaited result of the result of asyncio.sleep(0.1).
        await asyncio.sleep(.1)


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
async def main():
    # Create the directory requested by OUT.
    OUT.mkdir(parents=True,exist_ok=False)
    # Set messages to an empty list.
    messages=[]
    # Define Capture to group the state and operations declared below.
    # Base classes: logging.Handler.
    # Instances expose the attributes and methods implemented in this class.
    class Capture(logging.Handler):
        # Emit using the inputs and processing steps below.
        # Input record: the supplied record.
        # Output: no explicit value; normal completion returns None.
        # Append the result of self.format(record) to messages.
        def emit(self,record): messages.append(self.format(record))
    # Call logging.getLogger().addHandler with the supplied arguments.
    logging.getLogger().addHandler(Capture())
    # Set receipt to a dictionary containing mode, navigations.
    receipt={'mode':'NICEGUI_ASGI_CLIENT_SIMULATION_NOT_BROWSER','navigations':0}
    # Enter the result of socket.socket() as available and run the enclosed operations within that context.
    with socket.socket() as available:
        # Call available.bind with the supplied arguments.
        available.bind(('127.0.0.1',0))
        # Set test_port to available.getsockname() at 1.
        test_port=available.getsockname()[1]
    # Set sys.argv to a list containing a string built from BASE.parent joined with the path segment
    # 'socialmind_drive_showcase/app.py', the text...
    sys.argv=[str(BASE.parent/'socialmind_drive_showcase/app.py'),'--server-only','--port',str(test_port)]
    # Enter the result of installed_client_app() as first and run the enclosed operations within that context.
    async with installed_client_app() as first:
        # Import component2_live_view as view from socialmind_drive_showcase.pages for the operations below.
        from socialmind_drive_showcase.pages import component2_live_view as view
        # Import read_live_state from socialmind_drive_showcase.services.live_state_reader for the operations
        # below.
        from socialmind_drive_showcase.services.live_state_reader import read_live_state
        # Import replace from dataclasses for the operations below.
        from dataclasses import replace
        # Set view.LAUNCHER.component to the result of replace(view.LAUNCHER.component).
        view.LAUNCHER.component=replace(view.LAUNCHER.component,
            # Supply launch_command as view.LAUNCHER.component.launch_command plus a tuple containing the text
            # '--output-dir', a string built from OUT joined with the path segment 'launch_results'.
            launch_command=view.LAUNCHER.component.launch_command+('--output-dir',str(OUT/'launch_results')))
        # Fresh frame using the inputs and processing steps below.
        # Output: 'available' from state; use None if absent and 'simulation_time' from state['payload']; use 0 if
        # absent is at least 2.
        def fresh_frame():
            # Set state to the result of read_live_state(view.COMPONENT2_LIVE_STATE_PATH).
            state=read_live_state(view.COMPONENT2_LIVE_STATE_PATH,started_after=view.LAUNCHER.started_at)
            # Return 'available' from state; use None if absent and 'simulation_time' from state['payload']; use 0
            # if absent is at least 2 to the caller.
            return state.get('available') and state['payload'].get('simulation_time',0)>=2
        # Set second to the result of User(first.http_client).
        second=User(first.http_client)
        # Set old to the awaited result of the result of first.open(the text '/component/right-of-way/live').
        old=await first.open('/component/right-of-way/live')
        # Set other to the awaited result of the result of second.open(the text '/component/right-of-way/live').
        other=await second.open('/component/right-of-way/live')
        # Enter old and run the enclosed operations within that context.
        # Set view.SELECTED_SCENARIO['id'] to the text 'rule_resolved_two'.
        with old: view.SELECTED_SCENARIO['id']='rule_resolved_two'
        # Enter other and run the enclosed operations within that context.
        # Require view.SELECTED_SCENARIO at 'id' equals view.DEFAULT_SCENARIO_ID; otherwise raise AssertionError.
        with other: assert view.SELECTED_SCENARIO['id']==view.DEFAULT_SCENARIO_ID
        # Set receipt['independent_client_preferences'] to True.
        receipt['independent_client_preferences']=True
        # Use the actual page click handler and actual owned SUMO subprocess.
        # Call first.find('Run Scenario').click with the supplied arguments.
        first.find('Run Scenario').click()
        # Evaluate the awaited result of the result of wait_for(a callback that returns view.LAUNCHER.status
        # equals 'RUNNING').
        await wait_for(lambda:view.LAUNCHER.status=='RUNNING')
        # Evaluate the awaited result of the result of wait_for(fresh_frame).
        await wait_for(fresh_frame)
        # Iterate over the integer range defined by 3, binding each item to iteration.
        for iteration in range(3):
            # Set sockets to a list built from old._socket_to_document_id.
            sockets=list(old._socket_to_document_id)
            # Iterate over sockets, binding each item to socket_id.
            # Call old.handle_disconnect with the supplied arguments.
            for socket_id in sockets: old.handle_disconnect(socket_id)
            # Evaluate the awaited result of the result of asyncio.sleep(0.25).
            await asyncio.sleep(.25)
            # Require whether every item is true in a lazy sequence of the negation of t.active for t in values
            # from old.elements; retain entries satisfying whether t has type ui.timer; otherwise raise
            # AssertionError.
            assert all(not t.active for t in old.elements.values() if isinstance(t,ui.timer))
            # Evaluate the awaited result of the result of wait_for(a callback that returns old.is_deleted).
            await wait_for(lambda:old.is_deleted,timeout=8)
            # Evaluate the awaited result of the result of first.open(the text '/components').
            await first.open('/components')
            # Set old to the awaited result of the result of first.open(the text '/component/right-of-way/live').
            old=await first.open('/component/right-of-way/live')
            # Update receipt['navigations'] to its current value plus 2.
            receipt['navigations']+=2
            # Evaluate the awaited result of the result of asyncio.sleep(0.3).
            await asyncio.sleep(.3)
            # Require the negation of other.is_deleted and other.has_socket_connection; otherwise raise
            # AssertionError.
            assert not other.is_deleted and other.has_socket_connection
            # Set live_targets to a list of t for t in view.live_view_panel.targets; retain entries satisfying the
            # negation of t.container.is_deleted.
            live_targets=[t for t in view.live_view_panel.targets if not t.container.is_deleted]
            # Require a set of t.container.client.id for t in live_targets equals a set containing old.id,
            # other.id; otherwise raise AssertionError.
            assert {t.container.client.id for t in live_targets}=={old.id,other.id}
            # Require the number of entries in live_targets equals 2; otherwise raise AssertionError.
            assert len(live_targets)==2
        # Enter old and run the enclosed operations within that context.
        # Call view._stop_current_scenario with the supplied arguments.
        with old: view._stop_current_scenario()
        # Evaluate the awaited result of the result of wait_for(a callback that returns view.LAUNCHER.status
        # equals 'READY').
        await wait_for(lambda:view.LAUNCHER.status=='READY')
        # Require the negation of view.LAUNCHER.stop_forced and view.LAUNCHER.exit_code equals 0; otherwise raise
        # AssertionError.
        assert not view.LAUNCHER.stop_forced and view.LAUNCHER.exit_code==0
        # Enter old and run the enclosed operations within that context.
        with old:
            # Set view.SELECTED_SCENARIO['id'] to the text 'rule_resolved_two'.
            view.SELECTED_SCENARIO['id']='rule_resolved_two'
            # Call view._run_selected_scenario with the supplied arguments.
            view._run_selected_scenario()
        # Evaluate the awaited result of the result of wait_for(a callback that returns view.LAUNCHER.status
        # equals 'RUNNING').
        await wait_for(lambda:view.LAUNCHER.status=='RUNNING')
        # Evaluate the awaited result of the result of wait_for(fresh_frame).
        await wait_for(fresh_frame)
        # Set receipt['stop_relaunch'] to True.
        receipt['stop_relaunch']=True
        # Iterate over a tuple containing old, other, binding each item to client.
        for client in (old,other):
            # Iterate over a list built from client._socket_to_document_id, binding each item to socket_id.
            # Call client.handle_disconnect with the supplied arguments.
            for socket_id in list(client._socket_to_document_id): client.handle_disconnect(socket_id)
        # Evaluate the awaited result of the result of wait_for(a callback that returns old.is_deleted and
        # other.is_deleted).
        await wait_for(lambda:old.is_deleted and other.is_deleted,timeout=8)
        # Evaluate the awaited result of the result of asyncio.sleep(0.4).
        await asyncio.sleep(.4)
        # Set reopened to the awaited result of the result of first.open(the text '/component/right-of-way/live').
        reopened=await first.open('/component/right-of-way/live')
        # Require reopened.has_socket_connection; otherwise raise AssertionError.
        assert reopened.has_socket_connection
        # Enter reopened and run the enclosed operations within that context.
        # Require view.SELECTED_SCENARIO at 'id' equals view.DEFAULT_SCENARIO_ID; otherwise raise AssertionError.
        with reopened: assert view.SELECTED_SCENARIO['id']==view.DEFAULT_SCENARIO_ID
        # Set receipt['close_reopen'] to True.
        receipt['close_reopen']=True
        # Set receipt['no_accumulated_live_targets'] to True.
        receipt['no_accumulated_live_targets']=True
        # Set receipt['new_client_preferences_reset'] to True.
        receipt['new_client_preferences_reset']=True
        # Import app from nicegui for the operations below.
        from nicegui import app
        # Set receipt['registered_shutdown_handler'] to whether any item is true in a lazy sequence of the
        # requested attribute of h equals the text 'shutdown_owned_runtime' for h in app._shutdown_handlers.
        receipt['registered_shutdown_handler']=any(
            # Evaluate the requested attribute of h equals the text 'shutdown_owned_runtime' as part of the
            # enclosing expression.
            getattr(h,'__name__','')=='shutdown_owned_runtime' for h in app._shutdown_handlers)
        # Run this branch when the negation of receipt at 'registered_shutdown_handler'.
        if not receipt['registered_shutdown_handler']:
            # Raise AssertionError with the text 'Actual shutdown handler not registered in client harness' to
            # stop this execution path.
            raise AssertionError('Actual shutdown handler not registered in client harness')
        # Lifespan exit invokes the actual zero-argument shutdown wrapper while running.
    # Set receipt['shutdown_process_closed'] to view.LAUNCHER._process is the same object as None.
    receipt['shutdown_process_closed']=view.LAUNCHER._process is None
    # Set bad to a list of m for m in messages; retain entries satisfying the text 'Client has been deleted'
    # belongs to m or the text 'TypeError' belongs to m...
    bad=[m for m in messages if 'Client has been deleted' in m or 'TypeError' in m or 'Traceback' in m]
    # Set receipt['lifecycle_errors'] to bad.
    receipt['lifecycle_errors']=bad
    # Write the supplied text to (OUT / 'receipt.json').
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    # Write the supplied text to (OUT / 'captured.log').
    (OUT/'captured.log').write_text('\n'.join(messages),encoding='utf-8')
    # Require the negation of bad and receipt at 'shutdown_process_closed'; otherwise raise AssertionError.
    assert not bad and receipt['shutdown_process_closed']
    # Display the serialized data produced by json.dumps.
    print(json.dumps(receipt))


# Run this branch when __name__ equals the text '__main__'.
# Call asyncio.run with the supplied arguments.
if __name__=='__main__': asyncio.run(main())
