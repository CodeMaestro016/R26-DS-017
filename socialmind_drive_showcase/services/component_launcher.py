"""Single-instance asynchronous launcher for predefined local components."""

import subprocess
import sys
import threading


class ComponentLauncher:
    VALID_STATES = {"READY", "LAUNCHING", "RUNNING", "FINISHED", "FAILED"}

    def __init__(self, component):
        self.component = component
        self.status = "READY"
        self.exit_code = None
        self.error = None
        self._process = None
        self._lock = threading.Lock()

    @property
    def running(self):
        return self.status in {"LAUNCHING", "RUNNING"}

    def launch(self):
        with self._lock:
            if self.running:
                return False
            if not self.component.live or not self.component.launch_command:
                self.status, self.error = "FAILED", "This component has no connected live runtime."
                return False
            self.status, self.exit_code, self.error = "LAUNCHING", None, None
            threading.Thread(target=self._run, daemon=True,
                             name="component-2-panel-demo").start()
            return True

    def _run(self):
        try:
            command = [sys.executable if item == "{python}" else item
                       for item in self.component.launch_command]
            self._process = subprocess.Popen(
                command, cwd=self.component.working_directory,
                shell=False)
            self.status = "RUNNING"
            self.exit_code = self._process.wait()
            self.status = "FINISHED" if self.exit_code == 0 else "FAILED"
            if self.exit_code != 0:
                self.error = f"The SUMO demonstration exited with code {self.exit_code}."
        except (OSError, ValueError) as error:
            self.status, self.error = "FAILED", str(error)
        finally:
            self._process = None

