from df.config import ModuleConfig
import df
import platform
import tempfile
import shutil
import subprocess
import io
from pathlib import Path
from typing import Union, List

ID: str = "fira_code_nerd_font"
NAME: str = "Fira Code Nerd Font"
DESCRIPTION: str = "Fira Code: free monospaced font with programming ligatures"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

dl_link = "https://raw.githubusercontent.com/ryanoasis/nerd-fonts/master/patched-fonts/FiraCode/Medium/FiraCodeNerdFont-Medium.ttf"
font_name = "Fira Code Medium Nerd Font Complete.ttf"
fonts_folder = Path.home() / ".local/share/fonts/"

def is_compatible() -> Union[bool, str]:
    return platform.system() == "Linux"

def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Download the font
    with tempfile.TemporaryDirectory() as temp_dir:
        print("Downloading font...")
        temp_dir = Path(temp_dir)
        download_path = temp_dir / font_name
        df.download_file(dl_link, download_path)
        print("Installing font...")
        # Install the font by copying it to the local fonts directory
        font_path = fonts_folder / font_name
        df.ensure_parent_exists(font_path)
        font_path.unlink(missing_ok=True)
        shutil.copy(download_path, font_path)

        print("Updating font cache...")
        # Update the font cache if fc-cache is installed
        try:
            subprocess.run(["fc-cache", "-f"], stdout=stdout, stderr=stdout, stdin=subprocess.DEVNULL)
        except FileNotFoundError:
            print("fc-cache is not installed. Font cache was not updated.")

def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Delete the font file
    font_path = fonts_folder / font_name
    font_path.unlink(missing_ok=True)

def has_update(config: ModuleConfig) -> Union[bool, str]:
    # We don't have a version number, so we can't check for updates
    return False

def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
