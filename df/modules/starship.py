from df.config import ModuleConfig
import platform
import tempfile
import subprocess
import requests
import io
from pathlib import Path
import df
from typing import Union, List

ID: str = "starship"
NAME: str = "Starship"
DESCRIPTION: str = "The minimal, blazing-fast, and infinitely customizable prompt for any shell!"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

release_url = "https://github.com/starship/starship/releases/latest"
script_link = "https://starship.rs/install.sh"
bin_dir = Path.home() / ".local" / "bin"

def is_compatible() -> Union[bool, str]:
    return platform.system() in ["Linux", "Darwin"]

def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        script_path = temp_dir / "install.sh"

        print("Downloading Starship installer...")
        df.download_file(script_link, script_path)
        bin_dir.mkdir(parents=True, exist_ok=True)

        print("Installing Starship...")
        subprocess.run(["sh", script_path, "-b", bin_dir, "-y"], check=True, stdout=stdout, stderr=stdout, stdin=subprocess.DEVNULL)
        # Save the (probably) installed version
        latest_version = requests.get(release_url).url.split("/")[-1]
        config.set("version", latest_version)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # just remove the binary
    starship_path = bin_dir / "starship"
    starship_path.unlink(missing_ok=True)

def has_update(config: ModuleConfig) -> Union[bool, str]:
    latest_version = requests.get(release_url).url.split("/")[-1]
    return config.get("version") != latest_version

def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    install(config, stdout)
