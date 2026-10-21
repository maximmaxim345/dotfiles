import io
import os
import plistlib
import shutil
import subprocess
from pathlib import Path
from typing import List, Union

from df.config import ModuleConfig
from df.osinfo import running_in_termux, system

ID: str = "desk_board"
NAME: str = "Desk Board"
DESCRIPTION: str = "Start the desk board from ~/desk at login"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

LABEL = "local.desk-board"
SERVER = Path.home() / "desk" / "board" / "server.py"
PLIST = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
LOG = Path.home() / "Library" / "Logs" / "desk-board.log"
UNIT_NAME = "desk-board.service"
UNIT = Path.home() / ".config" / "systemd" / "user" / UNIT_NAME


def domain() -> str:
    return f"gui/{os.getuid()}"


def is_compatible() -> Union[bool, str]:
    if system() == "Linux":
        if running_in_termux() or not shutil.which("systemctl"):
            return "Needs systemd"
    elif system() != "Darwin":
        return "Only supported on macOS and Linux"
    if not SERVER.exists():
        return f"Needs the desk repo at {SERVER.parent.parent}"
    return True


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    if system() == "Darwin":
        PLIST.parent.mkdir(parents=True, exist_ok=True)
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with PLIST.open("wb") as f:
            plistlib.dump(
                {
                    "Label": LABEL,
                    "ProgramArguments": ["/usr/bin/python3", str(SERVER)],
                    "RunAtLoad": True,
                    "KeepAlive": True,
                    "StandardOutPath": str(LOG),
                    "StandardErrorPath": str(LOG),
                },
                f,
            )
        subprocess.run(["launchctl", "bootout", domain(), str(PLIST)], capture_output=True)
        subprocess.run(["launchctl", "bootstrap", domain(), str(PLIST)], check=True)
    else:
        UNIT.parent.mkdir(parents=True, exist_ok=True)
        UNIT.write_text(
            "[Unit]\n"
            "Description=Desk board\n\n"
            "[Service]\n"
            f'ExecStart=/usr/bin/python3 "{SERVER}"\n'
            "Restart=always\n\n"
            "[Install]\n"
            "WantedBy=default.target\n"
        )
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "--user", "enable", UNIT_NAME], check=True)
        subprocess.run(["systemctl", "--user", "restart", UNIT_NAME], check=True)
    print("Desk board runs at http://127.0.0.1:8765", file=stdout)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    if PLIST.exists():
        subprocess.run(["launchctl", "bootout", domain(), str(PLIST)], capture_output=True)
        PLIST.unlink()
    if UNIT.exists():
        subprocess.run(["systemctl", "--user", "disable", "--now", UNIT_NAME], capture_output=True)
        UNIT.unlink()
        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
