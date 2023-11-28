from df.config import ModuleConfig
import platform
import tempfile
import subprocess
from pathlib import Path
import df
import io
from typing import Union, List

ID: str = ""
NAME: str = ""
DESCRIPTION: str = ""
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

# Optional attributes
VERSION: str = ""

def is_compatible() -> Union[bool, str]:
    return True

def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass

def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass

# Optional functions for modules that can be updated

def has_update(config: ModuleConfig) -> Union[bool, str]:
    return False

def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
