from df.config import ModuleConfig
import platform
import tempfile
import subprocess
import requests
import io
import shutil
from pathlib import Path
import df
from typing import Union, List

ID: str = "starship"
NAME: str = "Starship"
DESCRIPTION: str = "The minimal, blazing-fast, and infinitely customizable prompt for any shell!"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

release_url = "https://github.com/starship/starship/releases/latest"
bin_dir = Path.home() / ".local" / "bin"

def _detect_libc() -> str:
    """
    Detect libc type (musl or gnu) for Linux systems.
    Returns 'musl' for Alpine/musl systems, 'gnu' for regular Linux systems.
    """
    try:
        # Check if we can run ldd to detect libc type
        result = subprocess.run(['ldd', '--version'], capture_output=True, text=True)
        if result.returncode == 0 and 'musl' in result.stdout.lower():
            return 'musl'
    except (FileNotFoundError, subprocess.SubprocessError):
        pass
    
    try:
        # Check /etc/os-release for Alpine
        with open('/etc/os-release', 'r') as f:
            content = f.read().lower()
            if 'alpine' in content:
                return 'musl'
    except (FileNotFoundError, OSError):
        pass
    
    # Default to gnu (glibc) for regular Linux systems
    return 'gnu'

def _dl_link(version: str, platform_name: str, arch: str) -> str:
    """
    Returns the download link for the specified version, platform and architecture.
    """
    url = f"https://github.com/starship/starship/releases/download/{version}/"
    
    if platform_name == "linux":
        libc_type = _detect_libc()
        return url + f"starship-{arch}-unknown-linux-{libc_type}.tar.gz"
    elif platform_name == "darwin":
        return url + f"starship-{arch}-apple-darwin.tar.gz"
    else:
        raise ValueError(f"Unsupported platform {platform_name}")

def is_compatible() -> Union[bool, str]:
    # We support Linux and macOS, and only x86_64 and aarch64 architectures
    return platform.system() in ["Linux", "Darwin"] and platform.machine() in ["x86_64", "aarch64"]

def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Get latest version
    latest_version = requests.get(release_url).url.split("/")[-1]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        
        print("Downloading Starship...")
        pf = platform.system().lower()
        arch = platform.machine()
        
        # Download the appropriate binary
        download_link = _dl_link(latest_version, pf, arch)
        download_path = temp_dir / "starship.tar.gz"
        df.download_file(download_link, download_path)
        
        print("Extracting Starship...")
        shutil.unpack_archive(download_path, temp_dir)
        
        print("Installing Starship...")
        # Find the starship binary in the extracted files
        starship_binary = temp_dir / "starship"
        if not starship_binary.exists():
            raise FileNotFoundError("Starship binary not found in downloaded archive")
        
        # Make it executable
        starship_binary.chmod(0o755)
        
        # Create bin directory and copy binary
        bin_dir.mkdir(parents=True, exist_ok=True)
        starship_target = bin_dir / "starship"
        shutil.copy(starship_binary, starship_target)
        
        # Save the installed version
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
