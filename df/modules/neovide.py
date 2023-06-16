from df.config import ModuleConfig
import df
import platform
import tempfile
import shutil
import subprocess
import io
from pathlib import Path
from typing import Union, List

ID: str = "neovide"
NAME: str = "Neovide"
DESCRIPTION: str = "No Nonsense Neovim Client in Rust"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

def dl_link(platform: str, arch: str) -> str:
    """
    Returns the download link for the latest version of bob for the given platform and architecture.
    """
    return f"https://github.com/MordechaiHadad/bob/releases/latest/download/bob-{platform}-{arch}.zip"

def is_compatible() -> Union[bool, str]:
    return platform.system() == "Linux" and platform.machine() in ["x86_64"]

def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Download the font
    with tempfile.TemporaryDirectory() as temp_dir:
        print("Downloading Neovide...")
        temp_dir = Path(temp_dir)
        download_path = temp_dir / "neovide.zip"
        link = "https://github.com/neovide/neovide/releases/latest/download/neovide.AppImage.zip"
        df.download_file(link, download_path)
        print("Unzipping Neovide...")
        shutil.unpack_archive(download_path, temp_dir)

        print("Installing Neovide...")
        # For maximum compatibility, we need to run the appimage with the --appimage-extract flag
        neovide_path = temp_dir / "neovide.AppImage"
        neovide_path.chmod(0o755)
        subprocess.run([neovide_path, "--appimage-extract"], cwd=temp_dir, stdout=stdout, stderr=stdout, check=True)
        # Copy the folder to the local lib folder
        (Path.home() / ".local" / "lib").mkdir(parents=True, exist_ok=True)
        shutil.copytree(temp_dir / "squashfs-root", Path.home() / ".local" / "lib" / "neovide")
        # Create a symlink to the executable
        (Path.home() / ".local" / "bin").mkdir(parents=True, exist_ok=True)
        (Path.home() / ".local" / "bin" / "neovide").symlink_to(Path.home() / ".local" / "lib" / "neovide" / "AppRun")

        # Copy the desktop file (with changed path, and multigrid flag)
        desktop_file = f"""
[Desktop Entry]
Type=Application
Exec={Path.home() / ".local" / "bin" / "neovide"} --multigrid %F
Icon=neovide
Name=Neovide (nvim)
Keywords=Text;Editor;
Categories=Utility;TextEditor;
Comment=No Nonsense Neovim Client in Rust
MimeType=text/english;text/plain;text/x-makefile;text/x-c++hdr;text/x-c++src;text/x-chdr;text/x-csrc;text/x-java;text/x-moc;text/x-pascal;text/x-tcl;text/x-tex;application/x-shellscript;text/x-c;text/x-c++;"""
        with open(Path.home() / ".local" / "share" / "applications" / "neovide.desktop", "w") as f:
            f.write(desktop_file)

        # Simlink the icon
        (Path.home() / ".local" / "share" / "icons" / "hicolor" / "scalable" / "apps").mkdir(parents=True, exist_ok=True)
        (Path.home() / ".local" / "share" / "icons" / "hicolor" / "scalable" / "apps" / "neovide.svg").symlink_to(Path.home() / ".local" / "lib" / "neovide" / "neovide.svg")


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Delete the executable
    (Path.home() / ".local" / "bin" / "neovide").unlink(missing_ok=True)
    # Delete the desktop file and icon
    (Path.home() / ".local" / "share" / "applications" / "neovide.desktop").unlink(missing_ok=True)
    (Path.home() / ".local" / "share" / "icons" / "hicolor" / "scalable" / "apps" / "neovide.svg").unlink(missing_ok=True)
    # Delete the folder
    shutil.rmtree(Path.home() / ".local" / "lib" / "neovide", ignore_errors=True)

def has_update(config: ModuleConfig) -> Union[bool, str]:
    return False

def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
