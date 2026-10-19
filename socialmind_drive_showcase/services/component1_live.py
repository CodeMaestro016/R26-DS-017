from __future__ import annotations

import os
import socket
import subprocess
import time
import urllib.request
from pathlib import Path


class Component1LiveController:
    """Bridge between NiceGUI and the Vast.ai Component 1 runtime."""

    REMOTE_RUNNER = (
        "/workspace/project/adaptive_intent_project/"
        "run_viva_scenario.sh"
    )

    LOCAL_STREAM_PORT = 8095
    REMOTE_STREAM_PORT = 8085

    def __init__(self) -> None:
        self.host = os.getenv(
            "COMPONENT1_VAST_HOST",
            "1.208.108.242",
        )

        self.ssh_port = int(
            os.getenv(
                "COMPONENT1_VAST_SSH_PORT",
                "31208",
            )
        )

        self.user = os.getenv(
            "COMPONENT1_VAST_USER",
            "root",
        )

        self.ssh_key = Path(
            os.getenv(
                "COMPONENT1_SSH_KEY",
                str(
                    Path.home()
                    / ".ssh"
                    / "id_ed25519"
                ),
            )
        )

        self.project_root = (
            Path(__file__).resolve().parents[1]
        )

        self.log_path = (
            self.project_root
            / "component1_live.log"
        )

        self.demo_process: subprocess.Popen | None = None
        self.tunnel_process: subprocess.Popen | None = None

        self.current_scenario: str | None = None
        self._log_handle = None

    # ==================================================
    # BASIC HELPERS
    # ==================================================

    def _hidden_kwargs(self) -> dict:
        if os.name == "nt":
            return {
                "creationflags":
                subprocess.CREATE_NO_WINDOW
            }

        return {}

    def _ssh_base(self) -> list[str]:
        return [
            "ssh",
            "-i",
            str(self.ssh_key),
            "-p",
            str(self.ssh_port),
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=10",
            "-o",
            "ServerAliveInterval=20",
            "-o",
            "ServerAliveCountMax=6",
            f"{self.user}@{self.host}",
        ]

    @staticmethod
    def _port_open(
        host: str,
        port: int,
    ) -> bool:
        try:
            with socket.create_connection(
                (host, port),
                timeout=0.5,
            ):
                return True

        except OSError:
            return False

    @property
    def stream_url(self) -> str:
        return (
            f"http://127.0.0.1:"
            f"{self.LOCAL_STREAM_PORT}"
        )

    # ==================================================
    # REMOTE CONNECTION
    # ==================================================

    def check_remote(self) -> tuple[bool, str]:
        if not self.ssh_key.exists():
            return (
                False,
                f"SSH key not found: {self.ssh_key}",
            )

        try:
            result = subprocess.run(
                self._ssh_base()
                + [
                    "echo COMPONENT1_REMOTE_OK"
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )

            if (
                result.returncode == 0
                and "COMPONENT1_REMOTE_OK"
                in result.stdout
            ):
                return (
                    True,
                    "Vast.ai connection successful",
                )

            return (
                False,
                result.stderr.strip()
                or result.stdout.strip()
                or "Unknown SSH error",
            )

        except Exception as exc:
            return False, str(exc)

    # ==================================================
    # AUTOMATIC SSH TUNNEL
    # ==================================================

    def ensure_tunnel(
        self,
    ) -> tuple[bool, str]:

        # Existing tunnel created by this controller.
        if (
            self.tunnel_process is not None
            and self.tunnel_process.poll() is None
        ):
            return (
                True,
                "SSH tunnel already running",
            )

        # Reuse an already-open local forwarding port.
        if self._port_open(
            "127.0.0.1",
            self.LOCAL_STREAM_PORT,
        ):
            return (
                True,
                "Local stream tunnel already available",
            )

        command = [
            "ssh",
            "-N",
            "-i",
            str(self.ssh_key),
            "-p",
            str(self.ssh_port),
            "-L",
            (
                f"{self.LOCAL_STREAM_PORT}:"
                f"127.0.0.1:"
                f"{self.REMOTE_STREAM_PORT}"
            ),
            "-o",
            "BatchMode=yes",
            "-o",
            "ExitOnForwardFailure=yes",
            "-o",
            "ServerAliveInterval=20",
            "-o",
            "ServerAliveCountMax=6",
            f"{self.user}@{self.host}",
        ]

        try:
            self.tunnel_process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                **self._hidden_kwargs(),
            )

            for _ in range(40):

                if self._port_open(
                    "127.0.0.1",
                    self.LOCAL_STREAM_PORT,
                ):
                    return (
                        True,
                        (
                            "SSH tunnel ready: "
                            f"localhost:{self.LOCAL_STREAM_PORT}"
                        ),
                    )

                if (
                    self.tunnel_process.poll()
                    is not None
                ):
                    return (
                        False,
                        "SSH tunnel process stopped",
                    )

                time.sleep(0.25)

            return (
                False,
                "Timed out starting SSH tunnel",
            )

        except Exception as exc:
            return False, str(exc)

    # ==================================================
    # START SCENARIO
    # ==================================================

    def start_scenario(
        self,
        scenario: str,
    ) -> tuple[bool, str]:

        if scenario not in {
            "crossing",
            "not_crossing",
        }:
            return (
                False,
                f"Invalid scenario: {scenario}",
            )

        ok, message = self.check_remote()

        if not ok:
            return False, message

        # Stop previous Component-1 run.
        self.stop_scenario()

        # Keep/create automatic stream tunnel.
        ok, message = self.ensure_tunnel()

        if not ok:
            return False, message

        command = (
            self._ssh_base()
            + [
                self.REMOTE_RUNNER,
                scenario,
            ]
        )

        try:
            if self._log_handle is not None:
                try:
                    self._log_handle.close()
                except Exception:
                    pass

            self._log_handle = open(
                self.log_path,
                "w",
                encoding="utf-8",
            )

            self.demo_process = subprocess.Popen(
                command,
                stdout=self._log_handle,
                stderr=subprocess.STDOUT,
                **self._hidden_kwargs(),
            )

            self.current_scenario = scenario

            return (
                True,
                (
                    f"{scenario} scenario started; "
                    "waiting for live stream"
                ),
            )

        except Exception as exc:
            self.demo_process = None
            self.current_scenario = None
            return False, str(exc)

    # ==================================================
    # STOP SCENARIO
    # ==================================================

    def stop_scenario(
        self,
    ) -> tuple[bool, str]:

        remote_stop = (
            "pkill -9 -f "
            "'[v]iva_case_live_final_agentic_scenarios' "
            "2>/dev/null || true; "
            "fuser -k 8085/tcp "
            "2>/dev/null || true"
        )

        try:
            subprocess.run(
                self._ssh_base()
                + [remote_stop],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
                **self._hidden_kwargs(),
            )

        except Exception:
            pass

        if (
            self.demo_process is not None
            and self.demo_process.poll() is None
        ):
            try:
                self.demo_process.terminate()
            except Exception:
                pass

        self.demo_process = None
        self.current_scenario = None

        if self._log_handle is not None:
            try:
                self._log_handle.close()
            except Exception:
                pass

            self._log_handle = None

        # IMPORTANT:
        # Tunnel intentionally remains alive.
        # This makes repeated tests much faster.

        return (
            True,
            "Component 1 demo stopped",
        )

    # ==================================================
    # STATUS
    # ==================================================

    def is_running(self) -> bool:
        return (
            self.demo_process is not None
            and self.demo_process.poll() is None
        )

    def stream_ready(self) -> bool:
        try:
            with urllib.request.urlopen(
                self.stream_url,
                timeout=1.0,
            ) as response:
                return response.status == 200

        except Exception:
            return False


component1_live = Component1LiveController()