"""Single-instance asynchronous launcher for predefined local components."""

import subprocess
import sys
import threading
from pathlib import Path
import time
import uuid


class ComponentLauncher:
    VALID_STATES = {"READY", "LAUNCHING", "RUNNING", "STOPPING",
                    "FINISHED", "FAILED"}

    def __init__(self, component):
        self.component = component
        self.status = "READY"
        self.exit_code = None
        self.error = None
        self._process = None
        self._extra_arguments = ()
        self._lock = threading.Lock()
        self._stop_request_path = None
        self._stop_requested = False
        self.stop_forced = False

    @property
    def running(self):
        return self.status in {"LAUNCHING", "RUNNING", "STOPPING"}

    def launch(self, extra_arguments=()):
        with self._lock:
            if self.running:
                return False
            if not self.component.live or not self.component.launch_command:
                self.status, self.error = "FAILED", "This component has no connected live runtime."
                return False
            self.status, self.exit_code, self.error = "LAUNCHING", None, None
            self._extra_arguments = tuple(extra_arguments)
            self._stop_requested = self.stop_forced = False
            run_id = uuid.uuid4().hex
            runtime = Path(self.component.working_directory) / "results" / "panel_demo" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            self._stop_request_path = runtime / f"stop_{run_id}.request"
            self._extra_arguments += ("--presentation-run-id", run_id,
                                      "--stop-request-path",
                                      str(self._stop_request_path))
            threading.Thread(target=self._run, daemon=True,
                             name="component-2-panel-demo").start()
            return True

    def request_stop(self, grace_seconds=5.0):
        """Cooperatively stop only the currently owned presentation run."""
        with self._lock:
            if self.status not in {"LAUNCHING", "RUNNING"}:
                return False
            self.status = "STOPPING"
            self._stop_requested = True
            self._stop_request_path.write_text("STOP_REQUESTED\n", encoding="utf-8")
            process = self._process
        threading.Thread(target=self._force_after_grace,
                         args=(process, float(grace_seconds)), daemon=True,
                         name="component-2-stop-grace").start()
        return True

    def _force_after_grace(self, process, grace_seconds):
        deadline = time.monotonic() + max(0.1, grace_seconds)
        while time.monotonic() < deadline:
            if process is None or process.poll() is not None:
                return
            time.sleep(0.05)
        if process.poll() is None:
            self.stop_forced = True
            self.error = "STOP_FORCED_AFTER_GRACE_TIMEOUT"
            self._terminate_owned_tree(process)

    @staticmethod
    def _terminate_owned_tree(process):
        """Terminate the exact owned process tree; never kill by image name."""
        try:
            import psutil
            owner = psutil.Process(process.pid)
            children = owner.children(recursive=True)
            for child in reversed(children):
                child.terminate()
            psutil.wait_procs(children, timeout=2.0)
        except (ImportError, OSError):
            pass
        if process.poll() is None:
            process.terminate()

    def _run(self):
        try:
            command = [sys.executable if item == "{python}" else item
                       for item in self.component.launch_command]
            command.extend(self._extra_arguments)
            self._process = subprocess.Popen(
                command, cwd=self.component.working_directory,
                shell=False)
            self.status = "RUNNING"
            self.exit_code = self._process.wait()
            self.status = ("READY" if self._stop_requested and self.exit_code == 0
                           else "FINISHED" if self.exit_code == 0 else "FAILED")
            if self.exit_code != 0:
                self.error = f"The SUMO demonstration exited with code {self.exit_code}."
        except (OSError, ValueError) as error:
            self.status, self.error = "FAILED", str(error)
        finally:
            self._process = None
            if self._stop_request_path is not None:
                self._stop_request_path.unlink(missing_ok=True)
