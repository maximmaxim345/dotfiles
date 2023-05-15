from df.config import ModuleConfig
import df
import platform
import tempfile
import shutil
import subprocess
import io
from pathlib import Path
from typing import Union, List

ID: str = "bob"
NAME: str = "Bob"
DESCRIPTION: str = "Version Manager for NeoVim"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

def dl_link(platform: str, arch: str) -> str:
    """
    Returns the download link for the latest version of bob for the given platform and architecture.
    """
    return f"https://github.com/MordechaiHadad/bob/releases/latest/download/bob-{platform}-{arch}.zip"

def is_compatible() -> Union[bool, str]:
    # We only support Linux with x86_64 and aarch64
    return platform.system() == "Linux" and platform.machine() in ["x86_64", "aarch64"]

def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Download the font
    with tempfile.TemporaryDirectory() as temp_dir:
        print("Downloading bob...")
        temp_dir = Path(temp_dir)
        download_path = temp_dir / "bob.zip"
        link = dl_link(platform.system().lower(), platform.machine().lower())
        df.download_file(link, download_path)
        print("Unzipping bob...")
        shutil.unpack_archive(download_path, temp_dir)

        print("Installing bob...")
        bob_path = temp_dir / "bob"
        bob_path.chmod(0o755)
        # Copy bob to the bin folder (create folder if it doesn't exist)
        (Path.home() / ".local" / "bin").mkdir(parents=True, exist_ok=True)
        shutil.copy(bob_path, Path.home() / ".local" / "bin" / "bob")

        print("Installing latest stable version of NeoVim...")
        # Run bob install
        subprocess.run(["bob", "install", "stable"], stdout=stdout, stderr=stdout)
        subprocess.run(["bob", "use", "stable"], stdout=stdout, stderr=stdout)

def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Run bob erase
    subprocess.run(["bob", "erase"], stdout=stdout, stderr=stdout)
    # Delete the bob executable
    (Path.home() / ".local" / "bin" / "bob").unlink(missing_ok=True)

def has_update(config: ModuleConfig) -> Union[bool, str]:
    return False

def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
