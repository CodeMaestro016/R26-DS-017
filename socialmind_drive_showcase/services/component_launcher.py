"""Single-instance launcher and owned-process lifecycle; no driving decisions."""
import subprocess
import importlib.util
import shutil
import sys
import threading
from pathlib import Path
import time
import uuid

class ComponentLauncher:
    VALID_STATES = {"READY", "LAUNCHING", "RUNNING", "STOPPING", "FINISHED", "FAILED"}

    def __init__(self, component):
        self.component = component
        self.status = "READY"
        self.exit_code = self.error = self._process = None
        self._extra_arguments = ()
        self._lock = threading.Lock()
        self._stop_request_path = None
        self._stop_requested = self.stop_forced = False
        self.run_id = self.log_path = self.started_at = None
        self._worker = None
        self._closing = False

    @property
    def running(self):
        return self.status in {"LAUNCHING", "RUNNING", "STOPPING"}

    def launch(self, extra_arguments=()):
        with self._lock:
            if self.running or self._closing:
                return False
            if not self.component.live or not self.component.launch_command:
                self.status, self.error = "FAILED", "This component has no connected live runtime."
                return False
            # Even a refused startup is a new attempt: an old frame/exit code
            # must not be presented as telemetry for this launch.
            self.run_id, self.started_at = uuid.uuid4().hex, time.time()
            self.log_path, self.exit_code, self.error = None, None, None
            if importlib.util.find_spec("psutil") is None:
                self.status, self.error = "FAILED", "Missing launch-cleanup dependency psutil. Install socialmind_drive_showcase/requirements.txt before starting SUMO."
                return False
            runtime_script = any(Path(str(arg)).name in {"run_runtime_simulation.py", "run_panel_demo.py"}
                                 for arg in self.component.launch_command)
            if runtime_script and not shutil.which("sumo"):
                self.status, self.error = "FAILED", "SUMO executable is not on PATH. Restore the existing SUMO installation before starting the scenario."
                return False
            checkpoint = Path(self.component.working_directory) / "results/final_mappo_selection_v2/selected_policy.pt"
            if runtime_script and not checkpoint.is_file():
                self.status, self.error = "FAILED", f"Missing frozen model asset: {checkpoint}. Restore the original E5 checkpoint; do not retrain a replacement."
                return False
            self.status, self.exit_code, self.error = "LAUNCHING", None, None
            self._stop_requested = self.stop_forced = False
            runtime = Path(self.component.working_directory) / "results" / "runtime_simulation" / "runtime"
            try:
                runtime.mkdir(parents=True, exist_ok=True)
            except OSError as error:
                self.status, self.error = "FAILED", str(error)
                return False
            self._stop_request_path = runtime / f"stop_{self.run_id}.request"
            self.log_path = runtime / f"launch_{self.run_id}.log"
            self._extra_arguments = tuple(extra_arguments) + (
                "--presentation-run-id", self.run_id,
                "--stop-request-path", str(self._stop_request_path))
            self._worker = threading.Thread(target=self._run, daemon=True,
                name="component-2-runtime-simulation")
            self._worker.start()
            return True

    def request_stop(self, grace_seconds=5.0):
        with self._lock:
            if self.status not in {"LAUNCHING", "RUNNING"}:
                return False
            try:
                self._stop_request_path.write_text("STOP_REQUESTED\n", encoding="utf-8")
            except (OSError, AttributeError) as error:
                self.error = "Cannot request cooperative stop: " + str(error)
                return False
            self.status, self._stop_requested = "STOPPING", True
            run_id = self.run_id
        threading.Thread(target=self._force_after_grace,
            args=(run_id, float(grace_seconds)), daemon=True,
            name="component-2-stop-grace").start()
        return True

    def _force_after_grace(self, run_id, grace_seconds):
        deadline = time.monotonic() + max(0.1, grace_seconds)
        while time.monotonic() < deadline:
            with self._lock:
                if self.run_id != run_id or not self.running:
                    return
                process = self._process
            if process is not None and process.poll() is not None:
                return
            time.sleep(0.05)
        with self._lock:
            if self.run_id != run_id or not self.running:
                return
            process = self._process
            if process is None or process.poll() is not None:
                return
            self.stop_forced = True
            self.error = "STOP_FORCED_AFTER_GRACE_TIMEOUT"
        self._terminate_owned_tree(process)

    @staticmethod
    def _terminate_owned_tree(process):
        """Terminate the exact owned process tree; never kill by image name."""
        if process.poll() is not None:
            return
        import psutil
        try:
            owner = psutil.Process(process.pid)
            children = owner.children(recursive=True)
            for child in reversed(children):
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            _, alive = psutil.wait_procs(children, timeout=2.0)
            for child in alive:
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
        except psutil.NoSuchProcess:
            return
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            process.kill()

    def _run(self):
        run_id, stop_path, log_path = self.run_id, self._stop_request_path, self.log_path
        try:
            with self._lock:
                if self._stop_requested:
                    self.status = "READY"
                    return
            command = [sys.executable if item == "{python}" else item
                       for item in self.component.launch_command]
            command.extend(self._extra_arguments)
            with log_path.open("w", encoding="utf-8") as log:
                process = subprocess.Popen(command, cwd=self.component.working_directory,
                    shell=False, stdout=log, stderr=subprocess.STDOUT)
                with self._lock:
                    self._process = process
                    self.status = "STOPPING" if self._stop_requested else "RUNNING"
                code = process.wait()
            with self._lock:
                self.exit_code = code
                if self._stop_requested and (code == 0 or self.stop_forced):
                    self.status = "READY"
                else:
                    self.status = "FINISHED" if code == 0 else "FAILED"
                if code != 0 and not self.stop_forced:
                    tail = log_path.read_text(encoding="utf-8", errors="replace")[-2000:]
                    self.error = f"The SUMO runtime exited with code {code}. Log: {log_path}\n{tail}"
        except (OSError, ValueError) as error:
            with self._lock:
                self.status, self.error = "FAILED", str(error)
        finally:
            with self._lock:
                if self.run_id == run_id:
                    self._process = None
            if stop_path is not None:
                try:
                    stop_path.unlink(missing_ok=True)
                except OSError:
                    pass

    def shutdown(self, grace_seconds=5.0):
        """Close only this app's launch; do not leave SUMO running on window close."""
        self._closing = True
        if self.status in {"LAUNCHING", "RUNNING"}:
            self.request_stop(grace_seconds)
        worker = self._worker
        if worker is not None and worker is not threading.current_thread():
            worker.join(timeout=max(0.1, grace_seconds) + 3.0)
        process = self._process
        if process is not None and process.poll() is None:
            self._terminate_owned_tree(process)
