import io
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Union

import df
from df.config import ModuleConfig

ID: str = "monaspace_argon_font"
NAME: str = "Monaspace Argon Font"
DESCRIPTION: str = "Monaspace Argon: a superfamily of fonts for code"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

# Font configurations: [(download_url, filename, registry_name)]
fonts = [
    (
        "https://raw.githubusercontent.com/githubnext/monaspace/main/fonts/NerdFonts/Monaspace%20Argon/MonaspaceArgonNF-Regular.otf",
        "MonaspaceArgonNF-Regular.otf",
        "MonaspaceArgonNF-Regular (OpenType)",
    ),
    (
        "https://raw.githubusercontent.com/githubnext/monaspace/main/fonts/Variable%20Fonts/Monaspace%20Argon/Monaspace%20Argon%20Var.ttf",
        "Monaspace Argon Var.ttf",
        "Monaspace Argon Var (TrueType)",
    ),
]

if platform.system() == "Windows":
    fonts_folder = Path.home() / "AppData/Local/Microsoft/Windows/Fonts"
elif platform.system() == "Darwin":
    fonts_folder = Path.home() / "Library/Fonts"
else:
    fonts_folder = Path.home() / ".local/share/fonts/"


def is_compatible() -> Union[bool, str]:
    return platform.system() in ["Linux", "Windows", "Darwin"]


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Download and install all fonts
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        for dl_link, font_name, registry_name in fonts:
            print(f"Downloading {font_name}...")
            download_path = temp_dir / font_name
            df.download_file(dl_link, download_path)

            print(f"Installing {font_name}...")
            # Install the font by copying it to the local fonts directory
            font_path = fonts_folder / font_name
            df.ensure_parent_exists(font_path)
            font_path.unlink(missing_ok=True)
            shutil.copy(download_path, font_path)

            if platform.system() == "Windows":
                import winreg

                # Register the font with Windows
                print(f"Registering {font_name}...")
                try:
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        "Software\\Microsoft\\Windows NT\\CurrentVersion\\Fonts",
                        0,
                        winreg.KEY_SET_VALUE,
                    )
                    winreg.SetValueEx(key, registry_name, 0, winreg.REG_SZ, str(font_path))
                    winreg.CloseKey(key)
                except OSError as e:
                    print(f"Error registering font {font_name}: {e}")

        if platform.system() == "Windows":
            print("It is recommended to restart your computer to apply the font changes.")
        else:
            # Update the font cache if fc-cache is installed
            print("Updating font cache...")
            try:
                subprocess.run(
                    ["fc-cache", "-f"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, text=True
                )
            except FileNotFoundError:
                print("fc-cache is not installed. Font cache was not updated.")


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for _, font_name, registry_name in fonts:
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
                winreg.DeleteValue(key, registry_name)
                winreg.CloseKey(key)
            except OSError as e:
                print(f"Error unregistering font {font_name}: {e}")

        # Delete the font file
        font_path.unlink(missing_ok=True)
        print(f"Uninstalled {font_name}")


def has_update(config: ModuleConfig) -> Union[bool, str]:
    # We don't have a version number, so we can't check for updates
    return False


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
