from df.config import ModuleConfig
import platform
import tempfile
import subprocess
import io
from pathlib import Path
import df

ID: str = "oh_my_zsh"
NAME: str = "Oh My Zsh"
DESCRIPTION: str = "Oh My Zsh is an open source, community-driven framework for managing your Zsh configuration."
DEPENDENCIES: list[str] = []
CONFLICTING: list[str] = []

dl_url = "https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh"
oh_my_zsh_path = Path.home() / ".oh-my-zsh"

def is_compatible() -> bool | str:
    return platform.system() in ("Linux", "Darwin")

def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # If the oh-my-zsh directory already exists, don't install, just update
    if oh_my_zsh_path.exists():
        print("Oh My Zsh already installed, updating...")
        ret = subprocess.run(["zsh", oh_my_zsh_path / "tools" / "upgrade.sh"], check=False,
                       stdout=stdout, stderr=stdout)
        if ret.returncode == 0:
            print("Oh My Zsh updated!")
        else:
            print("Oh My Zsh update failed!")
            print("Please run `zsh ~/.oh-my-zsh/tools/upgrade.sh` manually")
    else:
        with tempfile.TemporaryDirectory() as temp_dir:
            print("Downloading installer...")
            dl_path = Path(temp_dir) / "install.sh"
            df.download_file(dl_url, dl_path)
            print("Running installer...")
            subprocess.run(["sh", dl_path, "--unattended", "--keep-zshrc"], check=True, env={
                "ZSH": str(oh_my_zsh_path),
            }, stdout=stdout, stderr=stdout, stdin=subprocess.DEVNULL)
            print("Oh My Zsh installed!")


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # just remove the directory
    print("Removing Oh My Zsh...")
    df.delete_or_unlink(oh_my_zsh_path)

# Optional functions for modules that can be updated

def has_update(config: ModuleConfig) -> bool | str:
    return False

def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
