# -*- coding: utf-8 -*-

import subprocess
import threading
from typing import Callable, Optional


class DockerManager:
    """
    Manage Docker services running inside WSL2 through Makefile.

    Windows Python / PySide6
            ↓
        wsl.exe
            ↓
        Ubuntu-22.04
            ↓
        Makefile
            ↓
        Docker Compose

    Makefile targets:

        make run_with_libretranslate
        make stop
    """

    def __init__(
        self,
        distro: str = "Ubuntu-22.04",
        project_dir: str = "/mnt/c/Users/PC/translate-tool/backend",
    ):
        self.distro = distro
        self.project_dir = project_dir

    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _run_wsl(
        self,
        command: str,
        callback: Optional[Callable[[str], None]] = None,
    ) -> int:
        """
        Run a command inside WSL.

        Example:

            wsl.exe -d Ubuntu-22.04 bash -lc \
                "cd /mnt/c/Users/PC/translate-tool/backend && make run_with_libretranslate"
        """

        process = subprocess.Popen(
            [
                "wsl.exe",
                "-d",
                self.distro,
                "bash",
                "-lc",
                command,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            start_new_session=True,
        )

        if process.stdout:
            for line in process.stdout:
                line = line.rstrip()

                if callback:
                    callback(line)

        return process.wait()

    def _run_async(
        self,
        command: str,
        callback: Optional[Callable[[str], None]] = None,
        finished_callback: Optional[Callable[[int], None]] = None,
    ):
        """
        Run WSL command in background thread.

        This prevents blocking the PySide6 UI.
        """

        def worker():
            return_code = self._run_wsl(
                command,
                callback=callback,
            )

            if finished_callback:
                finished_callback(return_code)

        thread = threading.Thread(
            target=worker,
            daemon=True,
        )

        thread.start()

        return thread

    def _make_command(self, target: str) -> str:
        """
        Build Makefile command.

        Example:

            cd /mnt/c/Users/PC/translate-tool/backend &&
            make run_with_libretranslate
        """

        return (
            f"cd {self.project_dir} && "
            f"make {target}"
        )

    # ---------------------------------------------------------
    # Start
    # ---------------------------------------------------------

    def start(
        self,
        callback: Optional[Callable[[str], None]] = None,
        finished_callback: Optional[Callable[[int], None]] = None,
    ):
        """
        Start Docker services in a background thread so the Qt splash screen
        and main window remain responsive while containers bootstrap.
        """

        command = self._make_command("run_with_libretranslate")
        return self._run_async(
            command,
            callback=callback,
            finished_callback=finished_callback,
        )

    # ---------------------------------------------------------
    # Stop
    # ---------------------------------------------------------

    def stop(
        self,
        callback: Optional[Callable[[str], None]] = None,
        finished_callback: Optional[Callable[[int], None]] = None,
    ):
        """
        Stop Docker services.

        Equivalent to:

            cd /mnt/c/Users/PC/translate-tool/backend
            make stop
        """

        command = self._make_command("stop")

        return self._run_async(
            command,
            callback=callback,
            finished_callback=finished_callback,
        )

    def stop_sync(
        self,
        callback: Optional[Callable[[str], None]] = None,
    ) -> int:
        """
        Stop Docker services synchronously.

        Intended for application shutdown.

        The application waits until:

            make stop

        finishes before closing.
        """

        command = self._make_command("stop")

        return self._run_wsl(
            command,
            callback=callback,
        )

    def shutdown_wsl(self, callback: Optional[Callable[[str], None]] = None) -> int:
        """
        Shut down the WSL VM completely.

        Equivalent to:

            wsl.exe --shutdown
        """

        process = subprocess.Popen(
            ["wsl.exe", "--shutdown"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )

        if process.stdout:
            for line in process.stdout:
                line = line.rstrip()
                if callback:
                    callback(line)

        return process.wait()

    # ---------------------------------------------------------
    # Restart
    # ---------------------------------------------------------

    def restart(
        self,
        callback: Optional[Callable[[str], None]] = None,
        finished_callback: Optional[Callable[[int], None]] = None,
    ):
        """
        Restart Docker services.

        Sequence:

            make stop
            make run_with_libretranslate
        """

        def worker():
            # Stop first
            stop_code = self._run_wsl(
                self._make_command("stop"),
                callback=callback,
            )

            if stop_code != 0:
                if finished_callback:
                    finished_callback(stop_code)
                return

            # Start again
            start_code = self._run_wsl(
                self._make_command("run_with_libretranslate"),
                callback=callback,
            )

            if finished_callback:
                finished_callback(start_code)

        thread = threading.Thread(
            target=worker,
            daemon=True,
        )

        thread.start()

        return thread

    # ---------------------------------------------------------
    # Status
    # ---------------------------------------------------------

    def status(self) -> str:
        """
        Get Docker status.

        Requires this target in Makefile:

            status:
                docker compose ps
        """

        command = self._make_command("status")

        result = subprocess.run(
            [
                "wsl.exe",
                "-d",
                self.distro,
                "bash",
                "-lc",
                command,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        output = result.stdout.strip()

        if result.stderr:
            stderr = result.stderr.strip()

            if stderr:
                output += (
                    f"\n{stderr}"
                    if output
                    else stderr
                )

        return output

    # ---------------------------------------------------------
    # Running check
    # ---------------------------------------------------------

    def is_running(self) -> bool:
        """
        Check whether Docker Compose has running containers.

        This does not require a Makefile target.
        """

        command = (
            f"cd {self.project_dir} && "
            "docker compose ps "
            "--services "
            "--filter status=running"
        )

        result = subprocess.run(
            [
                "wsl.exe",
                "-d",
                self.distro,
                "bash",
                "-lc",
                command,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0:
            return False

        running_services = [
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip()
        ]

        return bool(running_services)

    # ---------------------------------------------------------
    # Logs
    # ---------------------------------------------------------

    def logs(
        self,
        callback: Optional[Callable[[str], None]] = None,
    ):
        """
        Read Docker logs.

        Requires this target in Makefile:

            logs:
                docker compose logs --tail=100
        """

        command = self._make_command("logs")

        return self._run_async(
            command,
            callback=callback,
        )

    # ---------------------------------------------------------
    # WSL check
    # ---------------------------------------------------------

    def check_wsl(self) -> bool:
        """
        Check whether the configured WSL distro exists.
        """

        result = subprocess.run(
            [
                "wsl.exe",
                "-l",
                "-q",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        distros = [
            line.strip().replace("\x00", "")
            for line in result.stdout.splitlines()
            if line.strip()
        ]

        return self.distro in distros

    # ---------------------------------------------------------
    # Docker check
    # ---------------------------------------------------------

    def check_docker(self) -> bool:
        """
        Check whether Docker works inside WSL.
        """

        result = subprocess.run(
            [
                "wsl.exe",
                "-d",
                self.distro,
                "bash",
                "-lc",
                "docker info >/dev/null 2>&1",
            ],
        )

        return result.returncode == 0

    # ---------------------------------------------------------
    # Convenience
    # ---------------------------------------------------------

    def start_default(self):
        return self.start()

    def stop_default(self):
        return self.stop()

    def restart_default(self):
        return self.restart()