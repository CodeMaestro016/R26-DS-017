"""Page-owned refresh targets and timers for the installed NiceGUI API."""
from nicegui import ui


class ClientLocalState(dict):
    """UI preferences belong to a page client; launcher state remains shared."""
    def __init__(self, **defaults):
        super().__init__(defaults)
        self._clients = {}

    def _state(self):
        try:
            client = ui.context.client
        except RuntimeError:
            return self
        if client.is_deleted:
            return self
        if client.id not in self._clients:
            self._clients[client.id] = dict(self)
            def dispose():
                self._clients.pop(client.id, None)
            client.on_delete(dispose)
        return self._clients[client.id]

    def __getitem__(self, key):
        state = self._state()
        return dict.__getitem__(self, key) if state is self else state[key]

    def __setitem__(self, key, value):
        state = self._state()
        if state is self:
            dict.__setitem__(self, key, value)
        else:
            state[key] = value


class client_refreshable(ui.refreshable):
    def refresh(self, *args, **kwargs):
        # Capture the owner before NiceGUI schedules its deferred response task.
        client = ui.context.client
        from nicegui.awaitable_response import AwaitableResponse
        def refresh_owned():
            from nicegui import background_tasks
            background_tasks.create(await_owned(), name='client owned refresh')
        async def await_owned():
            if not client.is_deleted and client.has_socket_connection:
                with client:
                    await super(client_refreshable, self).refresh(*args, **kwargs)
        return AwaitableResponse(refresh_owned, await_owned)

    def _execute_refresh(self, args, kwargs, *, instance):
        client = ui.context.client
        if client.is_deleted or not client.has_socket_connection:
            return []
        all_targets = self.targets
        self.targets = [t for t in all_targets
                        if not t.container.is_deleted and t.container.client is client]
        try:
            return super()._execute_refresh(args, kwargs, instance=instance)
        finally:
            self.targets = [t for t in all_targets if not t.container.is_deleted
                            and not t.container.client.is_deleted]


def page_timer(interval, callback):
    client = ui.context.client
    def tick():
        if not client.is_deleted and client.has_socket_connection:
            with client:
                callback()
    timer = ui.timer(interval, tick)
    client.on_disconnect(timer.deactivate)
    client.on_connect(timer.activate)
    client.on_delete(lambda: timer.cancel())
    return timer
