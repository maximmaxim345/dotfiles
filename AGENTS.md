# Dotfiles Management System

This repository contains my dotfiles and a custom dotfiles management system written in Python.
This document provides an overview of the dotfiles management system, how it works, how to use it, and guidelines for how to extend it by creating new modules.

## Overview

The dotfiles management system is a Python-based tool designed to simplify the installation, uninstallation, and management of dotfiles and associated configurations. It uses a modular architecture where each piece of software or configuration is treated as a "module." The system provides both a Terminal User Interface (TUI) and a Command-Line Interface (CLI) for managing these modules.

The main entry point for running the system is the `dotfiles.py` script. It automatically handles the creation of a Python virtual environment and the installation of dependencies, ensuring that the tool is ready to run without manual setup.
Running `./dotfiles.py` without any arguments launches the TUI, while passing commands and arguments allows for CLI usage.
For testing, run `python ./dotfiles.py` in the repository root. It is not necessary to create and activate a virtual environment manually, as the script handles this automatically.

## Core Concepts

### Modules

Modules are the building blocks of the dotfiles management system. Each module is a Python file located in the `df/modules/` directory and represents a single piece of software or configuration that can be managed.

Modules can do various tasks, most commonly:

1. **Installation Modules**: These modules handle the installation of software in a operating system-agnostic way. They typically download binaries, extract them, and place them in a directory that is included in the user's PATH (like `~/.local/bin`). Like `bob`, `lazygit`, `zoxide`, etc. Or also `fira_code_nerd_font` which downloads and installs a font.
2. **Configuration Modules**: These modules manage configuration files for software. They typically create symbolic links to the configuration stored in this repository, ensuring that the user's environment is set up consistently. Like `lazygit_config`, `zshrc`, etc. Some highly user specific configuration modules that is not compatible with symlinks may also copy files instead of symlinking them, like `git_config`. In that case uninstalling the module should not delete the users configuration. Read more about `df/modules/git_config.py` for an example of that if working on a similar module.

For config modules, the configuration of the software is expected to be stored in this repository, see the files in the root of the repository for examples.

A module is defined by the following attributes:

- `ID`: A unique identifier for the module (e.g., `git_config`).
- `NAME`: A human-readable name for the module (e.g., "Git Configuration").
- `DESCRIPTION`: A brief description of what the module does.
- `DEPENDENCIES`: A list of other module IDs that this module depends on.
- `CONFLICTING`: A list of other module IDs that conflict with this module.
- `VERSION` (optional): The version of the module.

Each module must implement the following functions:

- `is_compatible() -> Union[bool, str]`: Checks if the module is compatible with the current system. It should return `True` if it is, or a string explaining why it is not.
- `install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None`: Contains the logic for installing the module.
- `uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None`: Contains the logic for uninstalling the module.

Optionally, a module can also implement the following functions for updates:

- `has_update(config: ModuleConfig) -> Union[bool, str]`: Checks if an update is available for the module.
- `update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None`: Contains the logic for updating the module.

See `df/modules/_template.py` for a template which should be used as a starting point for creating new modules.

### Dependencies and Conflicts

The system automatically handles dependencies and conflicts between modules:

- **Dependencies**: When you choose to install a module, the system will also automatically queue the installation of its dependencies.
- **Conflicts**: If you try to install a module that conflicts with an already installed module, the system will prevent the installation and inform you about the conflict.

### Compatibility

Before suggesting or installing a module, the system checks if it is compatible with the current operating system and environment. This is done by calling the `is_compatible()` function within each module. The TUI will show incompatible modules in a separate category.
Common compatibility checks may include verifying the operating system, checking for the presence of required commands, or ensuring that certain files exist.

### Configuration

The state of the installed modules is stored in a `config.json` file in the root of the project (excluded by the `.gitignore` and a `.dockerignore` file). This file keeps track of which modules are installed and their versions.
The `df/config.py` file provides a `ModuleConfig` class to interact with this configuration.
`ModuleConfig` instances are passed to the `install`, `uninstall`, and `update` functions of each module, allowing them to read and write their specific configuration data about the installed state. Installed state and version (through the global `VERSION` variable) are already automatically stored and do not need to be handled manually. But for example, backup paths can be stored in the module's configuration.
For backup purposes, it is recommended to store the original configuration files in a separate location before making any changes. For that purpose, the `create_backup` and `restore_backup` helper functions are provided in the `df` package.

## Usage

The dotfiles management system can be used in two ways: through the Terminal User Interface (TUI) or the Command-Line Interface (CLI).

### Terminal User Interface (TUI)

To launch the TUI, run the `dotfiles.py` script without any arguments:

```bash
./dotfiles.py
```

The TUI provides an interactive way to manage your dotfiles. Modules are organized into the following categories:

- **Updatable**: Installed modules for which an update is available.
- **Installed**: Modules that are currently installed.
- **Not Installed**: Modules that are available for installation.
- **Incompatible**: Modules that are not compatible with your system.

You can queue actions (install, update, remove) for each module and then apply all changes at once.

### Command-Line Interface (CLI)

The CLI is ideal for automated installations, such as in development containers or headless environments. To use the CLI, pass commands and arguments to the `dotfiles.py` script.

**Examples:**

- Install specific modules:
  ```bash
  ./dotfiles.py install git_config zsh_config
  ```
- Install all compatible modules:
  ```bash
  ./dotfiles.py install --all
  ```
- Uninstall a module:
  ```bash
  ./dotfiles.py uninstall zsh_config
  ```
- Update all installed modules:
  ```bash
  ./dotfiles.py update
  ```
- List all available modules:
  ```bash
  ./dotfiles.py list
  ```
- List only installed modules:
  ```bash
  ./dotfiles.py list --installed
  ```
- Check which modules have available updates:
  ```bash
  ./dotfiles.py list --updatable
  ```
- Force reinstall a module:
  ```bash
  ./dotfiles.py install --force git_config
  ```

For a full list of commands and options, use the `--help` flag:

```bash
./dotfiles.py --help
```

### Configuration File Location

The `config.json` file is stored in the root of the dotfiles directory and contains:

- List of installed modules and their versions
- Module-specific configuration data (like backup paths)
- Last update check timestamps

## For Developers

This section provides more detailed information for developers who want to create or modify modules.

### Testing and Development

When working on the dotfiles system, you have several options for testing:

#### CLI Testing

For testing the dotfiles application itself, run it directly since it has automatic virtual environment management:

```bash
# The dotfiles.py script automatically sets up and activates the environment
python ./dotfiles.py list
python ./dotfiles.py --help
```

#### Using run-in-env.sh for Other Tools

The `run-in-env.sh` script is useful for running **other tools** that need access to the dotfiles virtual environment. **Do not use it for dotfiles.py itself** as that script already handles environment management automatically.

Common use cases for `run-in-env.sh`:

```bash
# Run pre-commit hooks (formatting, linting, etc.)
./scripts/run-in-env.sh pre-commit run -a

# Run other Python scripts that depend on the dotfiles environment
./scripts/run-in-env.sh python some_other_script.py
```

This script automatically activates the Python virtual environment and runs the command, so you don't need to manually source the environment or worry about activation.

#### GUI Testing

**Important**: When making changes to the UI (`df/ui.py`, `df/ui.css`), always ask the user to test the graphical interface manually to ensure the changes work correctly. The TUI cannot be automatically tested, so manual verification by the user is essential.

Ask the user to run:

```bash
# Launch the TUI directly (automatic environment management)
python ./dotfiles.py
```

And test various interactions including:

- Module installation/removal/updates
- UI layout and responsiveness
- Queued actions behavior
- Error handling and conflict resolution

### Creating a New Module

To add a new module to the system, follow these steps:

1. **Create the module file**: Create a new Python file in the `df/modules/` directory (e.g., `my_new_module.py`). It's best to use the `df/modules/_template.py` as a starting point.
2. **Define metadata**: Fill in the required metadata at the top of the file:
   - `ID`: A unique string to identify the module.
   - `NAME`: A human-readable name.
   - `DESCRIPTION`: A short description of the module.
   - `DEPENDENCIES`: A list of module IDs that this module depends on.
   - `CONFLICTING`: A list of module IDs that conflict with this module.
3. **Implement core functions**:
   - `is_compatible()`: This function should check if the module can be installed on the current system. For example, it can check the operating system, the presence of a specific command, or a particular file.
   - `install()`: This function contains the logic to install the module. This can involve creating symlinks, downloading files, or running commands.
   - `uninstall()`: This function should revert all the changes made by the `install()` function.
4. **Implement update functions (optional)**:
   - `has_update()`: This function should check if a new version of the module is available.
   - `update()`: This function should perform the update.

For good examples of modules, refer to existing modules in the `df/modules/` directory. Specifically `df/modules/starship_config.py` and `df/modules/starship.py` are good examples of the framework and should be read first before creating new modules.

### Helper Functions

The `df` package provides several helper functions that can be used in your modules. You can import them from the `df` package (e.g., `from df import download_file`).

#### File Management

- `download_file(url: str, path: Path) -> None`: Downloads a file from a URL to a specified path.
- `symlink_path(source: Path, target: Path) -> None`: Creates a symbolic link from a source to a target. It handles the creation of parent directories if they don't exist. On Windows, uses junction links for directories to avoid permission issues.
- `move_path(source: Path, target: Path) -> None`: Moves a file or directory from a source to a target. Works across filesystem boundaries.
- `delete_or_unlink(path: Path, delete_recursively: bool = False) -> bool`: Deletes a file or directory, or unlinks a symbolic link. Returns `True` if something was deleted.
- `ensure_parent_exists(path: Path) -> None`: Ensures that the parent directory of a given path exists.

#### Backup Management

- `create_backup(path: Path, config: ModuleConfig, key: str) -> None`: Creates a backup of a file or directory before modifying it. The backup path is stored in the module's configuration. Handles empty directories with special marker.
- `restore_backup(path: Path, config: ModuleConfig, key: str) -> None`: Restores a backup created with `create_backup`. Understands special markers for empty directories.
- `is_backup_required(path: Path) -> bool`: Checks if a path needs to be backed up (files, non-empty directories, symlinks).
- `find_backup_path(original: Path) -> Path`: Finds a non-conflicting backup path by appending `.old`, `.old1`, `.old2`, etc.

### Best Practices

When creating modules, please follow these best practices:

- **Idempotency**: The `install()` and `uninstall()` functions should be idempotent. This means that running them multiple times should have the same effect as running them once.
- **Error Handling**: The module should handle errors gracefully. If an error occurs, it should be caught and a descriptive message should be printed to `stdout`.
- **Cleanliness**: The `uninstall()` function should clean up all the files and directories created by the `install()` function. Use the `create_backup` and `restore_backup` helpers to handle existing user configurations.
- **Clarity**: Provide clear and concise output to the user by printing to the `stdout` stream passed to the `install`, `uninstall`, and `update` functions. This output will be displayed in the TUI's log panel.

#### Download Modules Best Practices

For modules that download binaries (like `bob`, `lazygit`, `zoxide`, etc.):

- **Platform/Architecture Handling**: Use proper platform and architecture detection. Common mappings include:
  - `amd64` → `x86_64` (for most projects)
  - `aarch64` → `arm64` or `arm` (varies by project)
  - `darwin` → `macos` (for some projects like Bob)
- **Version Management**: For tools that manage themselves (like `topgrade`), don't implement custom update logic—let the tool handle its own updates.
- **Dynamic Version Detection**: Use GitHub API or release redirects to get current versions rather than hardcoding version numbers.
- **Windows Dependencies**: Modules installing to `~/.local/bin` should depend on `windows_local_bin` module on Windows.

#### Platform Dependencies

- **Windows PATH**: Modules that install binaries should add the `windows_local_bin` dependency when running on Windows to ensure proper PATH setup.
- **Conditional Dependencies**: Use runtime platform detection to set dependencies:
  ```python
  if platform.system() == "Windows":
      DEPENDENCIES = ["windows_local_bin"]
  ```

### Debugging

Here are some tips for debugging your modules:

- **Use the `print` function**: Any output from the `print` function within your module's `install`, `uninstall`, or `update` functions will be redirected to the log panel in the TUI. This is a simple way to trace the execution of your module.
- **Run in CLI mode**: The CLI mode can be helpful for debugging, as it provides more direct output. You can use the `--verbose` flag to get more detailed information.
- **Check the `config.json` file**: This file contains the configuration of all modules. You can inspect it to see if your module is being registered correctly and if its configuration is being saved as expected.

### Troubleshooting Common Issues

#### Platform Detection Issues

Common platform detection problems:

- `platform.system()` returns "Darwin" for macOS, "Linux", or "Windows"
- `platform.machine()` returns "x86_64", "aarch64", "arm64", "AMD64" etc.
- Architecture normalization may be needed for different projects

#### Module Update Patterns

- **Self-updating tools** (like `topgrade`): Don't implement custom update logic
- **Binary downloads**: Implement `has_update()` and `update()` functions
- **Configuration modules**: Usually don't need update logic unless config format changes
