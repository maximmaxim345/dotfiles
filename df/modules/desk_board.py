import io
import os
import plistlib
import subprocess
from pathlib import Path
from typing import List, Union

from df.config import ModuleConfig
from df.osinfo import system

ID: str = "desk_board"
NAME: str = "Desk Board"
DESCRIPTION: str = "Start the desk board from ~/desk at login (macOS)"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

LABEL = "local.desk-board"
SERVER = Path.home() / "desk" / "board" / "server.py"
PLIST = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
LOG = Path.home() / "Library" / "Logs" / "desk-board.log"


def domain() -> str:
    return f"gui/{os.getuid()}"


def is_compatible() -> Union[bool, str]:
    if system() != "Darwin":
        return "Only supported on macOS"
    if not SERVER.exists():
        return f"Needs the desk repo at {SERVER.parent.parent}"
    return True


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
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
    print("Desk board runs at http://127.0.0.1:8765", file=stdout)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    if PLIST.exists():
        subprocess.run(["launchctl", "bootout", domain(), str(PLIST)], capture_output=True)
        PLIST.unlink()
