import io
import os
import plistlib
import shutil
import subprocess
from pathlib import Path
from typing import List, Union

from df.config import ModuleConfig
from df.osinfo import running_in_termux, system

ID: str = "desk_listener"
NAME: str = "Desk Listener"
DESCRIPTION: str = "Run the desk listener from ~/desk at login, which wakes the desk thread through the t3 command"
DEPENDENCIES: List[str] = ["desk"]
CONFLICTING: List[str] = []

LABEL = "local.desk-listener"
LISTENER = Path.home() / "desk" / "bin" / "desk-wait"
PLIST = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
LOG = Path.home() / "Library" / "Logs" / "desk-listener.log"
UNIT_NAME = "desk-listener.service"
UNIT = Path.home() / ".config" / "systemd" / "user" / UNIT_NAME


def domain() -> str:
    return f"gui/{os.getuid()}"


def is_compatible() -> Union[bool, str]:
    if system() == "Linux":
        if running_in_termux() or not shutil.which("systemctl"):
            return "Needs systemd"
    elif system() != "Darwin":
        return "Only supported on macOS and Linux"
    return True


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    if system() == "Darwin":
        PLIST.parent.mkdir(parents=True, exist_ok=True)
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with PLIST.open("wb") as f:
            plistlib.dump(
                {
                    "Label": LABEL,
                    "ProgramArguments": ["/usr/bin/python3", str(LISTENER), "--serve"],
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
            "Description=Desk listener\n\n"
            "[Service]\n"
            f'ExecStart=/usr/bin/python3 "{LISTENER}" --serve\n'
            "Restart=always\n\n"
            "[Install]\n"
            "WantedBy=default.target\n"
        )
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "--user", "enable", UNIT_NAME], check=True)
        subprocess.run(["systemctl", "--user", "restart", UNIT_NAME], check=True)
    print("Desk listener runs", file=stdout)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    if PLIST.exists():
        subprocess.run(["launchctl", "bootout", domain(), str(PLIST)], capture_output=True)
        PLIST.unlink()
    if UNIT.exists():
        subprocess.run(["systemctl", "--user", "disable", "--now", UNIT_NAME], capture_output=True)
        UNIT.unlink()
        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
