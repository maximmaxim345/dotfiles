import io
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Union

import df
from df.config import ModuleConfig

ID: str = "fira_code_nerd_font"
NAME: str = "Fira Code Nerd Font"
DESCRIPTION: str = "Fira Code: free monospaced font with programming ligatures"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

dl_link = (
    "https://raw.githubusercontent.com/ryanoasis/nerd-fonts/master/patched-fonts/FiraCode/Medium/FiraCodeNerdFont-Medium.ttf"
)
font_name = "Fira Code Medium Nerd Font Complete.ttf"
if platform.system() == "Windows":
    fonts_folder = Path.home() / "AppData/Local/Microsoft/Windows/Fonts"
elif platform.system() == "Darwin":
    fonts_folder = Path.home() / "Library/Fonts"
else:
    fonts_folder = Path.home() / ".local/share/fonts/"


def is_compatible() -> Union[bool, str]:
    return platform.system() in ["Linux", "Windows", "Darwin"]


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Download the font
    with tempfile.TemporaryDirectory() as temp_dir_str:
        print("Downloading font...")
        temp_dir = Path(temp_dir_str)
        download_path = temp_dir / font_name
        df.download_file(dl_link, download_path)
        print("Installing font...")
        # Install the font by copying it to the local fonts directory
        font_path = fonts_folder / font_name
        df.ensure_parent_exists(font_path)
        font_path.unlink(missing_ok=True)
        shutil.copy(download_path, font_path)

        if platform.system() == "Windows":
            import winreg

            # Register the font with Windows
            print("Registering font...")
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    "Software\\Microsoft\\Windows NT\\CurrentVersion\\Fonts",
                    0,
                    winreg.KEY_SET_VALUE,
                )
                winreg.SetValueEx(key, font_name[:-4], 0, winreg.REG_SZ, str(font_path))
                winreg.CloseKey(key)
            except OSError as e:
                print(f"Error registering font: {e}")
            print("It is recommended to restart your computer to apply the font changes.")
        else:
            # Update the font cache if fc-cache is installed
            print("Updating font cache...")
            try:
                subprocess.run(
                    ["fc-cache", "-f"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.DEVNULL,
                )
            except FileNotFoundError:
                print("fc-cache is not installed. Font cache was not updated.")


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    font_path = fonts_folder / font_name

    if platform.system() == "Windows":
        import winreg

        # Unregister the font with Windows
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\\Microsoft\\Windows NT\\CurrentVersion\\Fonts",
                0,
                winreg.KEY_SET_VALUE,
            )
            winreg.DeleteValue(key, font_name)
            winreg.CloseKey(key)
        except OSError as e:
            print(f"Error unregistering font: {e}")
    # Delete the font file
    font_path.unlink(missing_ok=True)


def has_update(config: ModuleConfig) -> Union[bool, str]:
    # We don't have a version number, so we can't check for updates
    return False


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
