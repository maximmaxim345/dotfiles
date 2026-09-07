import io
import shutil
import tempfile
from pathlib import Path
from typing import List, Union

import requests

import df
from df.config import ModuleConfig
from df.osinfo import system

ID: str = "ohf_sage"
NAME: str = "OHF Sage Agent"
DESCRIPTION: str = "A Claude Code agent that reviews changes against Open Home Foundation standards"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

REPO: str = "chrisuthe/ohf-sage"
AGENT_ASSET: str = "ohf-sage.md"
CORPUS_ASSET: str = "ohf-sage-corpus.jsonl"
CORPUS_REL_PATH: str = ".claude/agents/ohf-sage-corpus.jsonl"

agents_path = Path.home() / ".claude" / "agents"


def latest_version() -> str:
    """
    Returns the tag of the latest ohf-sage release
    """
    response = requests.get(f"https://api.github.com/repos/{REPO}/releases/latest").json()
    return str(response["tag_name"])


def dl_link(asset: str) -> str:
    """
    Returns the download link for the given release asset
    """
    return f"https://github.com/{REPO}/releases/latest/download/{asset}"


def point_at_corpus(agent_path: Path, corpus_path: Path) -> None:
    """
    Rewrite the agent's corpus reference to where the corpus was installed
    """
    # The shipped path is project relative, so a user wide install resolves it to nothing and
    # the agent reports an empty search rather than a missing corpus.
    text = agent_path.read_text(encoding="utf-8")
    agent_path.write_text(text.replace(CORPUS_REL_PATH, str(corpus_path)), encoding="utf-8")


def is_compatible() -> Union[bool, str]:
    return system() in ["Linux", "Darwin", "Windows"]


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    version = latest_version()
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        print(f"Downloading OHF Sage {version}...")
        for asset in [AGENT_ASSET, CORPUS_ASSET]:
            df.download_file(dl_link(asset), temp_dir / asset)

        print("Installing OHF Sage...")
        agents_path.mkdir(parents=True, exist_ok=True)
        for asset in [AGENT_ASSET, CORPUS_ASSET]:
            shutil.copy(temp_dir / asset, agents_path / asset)

    point_at_corpus(agents_path / AGENT_ASSET, agents_path / CORPUS_ASSET)
    config.set("version", version)
    print(f"Installed OHF Sage {version} to {agents_path}")


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    for asset in [AGENT_ASSET, CORPUS_ASSET]:
        (agents_path / asset).unlink(missing_ok=True)


def has_update(config: ModuleConfig) -> Union[bool, str]:
    current_version = config.get("version", "")
    return str(current_version) != latest_version()


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    install(config, stdout)
