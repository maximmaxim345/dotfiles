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

ID: str = "bob"
NAME: str = "Bob"
DESCRIPTION: str = "Version Manager for NeoVim"
DEPENDENCIES: List[str] = []
if platform.system() == "Windows":
    DEPENDENCIES = ["windows_local_bin"]
CONFLICTING: List[str] = []

release_url = "https://github.com/MordechaiHadad/bob/releases/latest"

def dl_link(platform: str, arch: str) -> str:
    """
    Returns the download link for the latest version of bob for the given platform and architecture.
    """
    if arch == "amd64":
        arch = "x86_64"
    return f"{release_url}/download/bob-{platform}-{arch}.zip"

def subfolder_name(platform: str, arch: str) -> str:
    """
    Returns the name of the subfolder in the bob zip file for the given platform and architecture.
    """
    if arch == "amd64":
        arch = "x86_64"
    return f"bob-{platform}-{arch}"

def is_compatible() -> Union[bool, str]:
    return (platform.system() == "Linux" and platform.machine() in ["x86_64", "aarch64"]) \
            or (platform.system() == "Windows" and platform.machine() == "AMD64")

def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Download the font
    with tempfile.TemporaryDirectory() as temp_dir:
        print("Downloading bob...")
        temp_dir = Path(temp_dir)
        download_path = temp_dir / "bob.zip"
        pf = platform.system().lower()
        arch = platform.machine().lower()
        link = dl_link(pf, arch)
        df.download_file(link, download_path)
        print("Unzipping bob...")
        shutil.unpack_archive(download_path, temp_dir)

        print("Installing bob...")
        bob_path = temp_dir / subfolder_name(pf, arch) / "bob"
        if pf != 'windows':
            bob_path.chmod(0o755)
        else:
            bob_path = bob_path.with_suffix(".exe")

        bin_dir = Path.home() / ".local" / "bin"
        
        bin_dir.mkdir(parents=True, exist_ok=True)
        bob_exec = (bin_dir / "bob.exe") if pf == 'windows' else (bin_dir / "bob")
        shutil.copy(bob_path, bob_exec)

        print("Installing latest stable version of NeoVim...")
        # Run bob install
        subprocess.run([bob_exec, "install", "stable"], stdout=stdout, stderr=stdout)
        subprocess.run([bob_exec, "use", "stable"], stdout=stdout, stderr=stdout)
        
        # Save the installed version
        latest_version = requests.get(release_url).url.split("/")[-1]
        config.set("version", latest_version)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    bin_dir = Path.home() / ".local" / "bin"
    bob_exec = (bin_dir / "bob.exe") if platform.system() == 'Windows' else (bin_dir / "bob")
    # Run bob erase
    subprocess.run([bob_exec, "erase"], stdout=stdout, stderr=stdout)
    # Delete the bob executable
    (Path.home() / ".local" / "bin" / "bob").unlink(missing_ok=True)

def has_update(config: ModuleConfig) -> Union[bool, str]:
    latest_version = requests.get(release_url).url.split("/")[-1]
    return config.get("version") != latest_version

def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    install(config, stdout) # this will overwrite the old version
