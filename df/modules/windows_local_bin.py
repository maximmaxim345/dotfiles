from df.config import ModuleConfig
import df
import platform
import tempfile
import shutil
import subprocess
import requests
import io
from pathlib import Path
from typing import Union, List

ID: str = "windows_local_bin"
NAME: str = "Windows Local Bin"
DESCRIPTION: str = "Add ~/.local/bin to the PATH on Windows"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

def is_compatible() -> Union[bool, str]:
    return platform.system() == "Windows"

def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    bin_dir = Path.home() / ".local" / "bin"
    
    bin_dir.mkdir(parents=True, exist_ok=True)

    print("Adding ~/.local/bin to the PATH")
    import winreg
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS)
    path_value, _ = winreg.QueryValueEx(key, "Path")
    bin_dir = str(bin_dir)
    if bin_dir not in path_value:
        path_value += ";" + bin_dir
    winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, path_value)
    winreg.CloseKey(key)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    bin_dir = Path.home() / ".local" / "bin"

    import winreg
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS)
    path_value, _ = winreg.QueryValueEx(key, "Path")
    bin_dir = str(bin_dir)
    if bin_dir in path_value:
        path_value = path_value.replace(bin_dir, "")
        path_value = path_value.replace(";;", ";")
        winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, path_value)
    winreg.CloseKey(key)