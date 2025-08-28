#!/usr/bin/env python3
"""
CLI interface for the dotfiles manager tool.
Designed for automated installs in devcontainers and headless environments.
"""

import argparse
import io
import sys
import traceback
from pathlib import Path
from typing import List

import df
import df.config
import df.ui
from df.modules import MODULES


class CLIOutput:
    """Simple output handler for CLI operations"""

    def __init__(self, verbose: bool = False, quiet: bool = False):
        self.verbose = verbose
        self.quiet = quiet

    def info(self, message: str):
        """Print info message unless quiet mode"""
        if not self.quiet:
            print(f"[INFO] {message}")

    def verbose_info(self, message: str):
        """Print verbose info message only in verbose mode"""
        if self.verbose and not self.quiet:
            print(f"[VERBOSE] {message}")

    def error(self, message: str):
        """Print error message (always shown)"""
        print(f"[ERROR] {message}", file=sys.stderr)

    def warning(self, message: str):
        """Print warning message unless quiet mode"""
        if not self.quiet:
            print(f"[WARN] {message}")


def resolve_dependencies(module_ids: List[str], output: CLIOutput) -> List[str]:
    """
    Resolve dependencies for the given module IDs.
    Returns a list of module IDs in the order they should be installed.
    """
    resolved = []
    visited = set()
    visiting = set()

    def visit(module_id: str):
        if module_id in visiting:
            raise ValueError(f"Circular dependency detected involving module '{module_id}'")
        if module_id in visited:
            return

        if module_id not in MODULES:
            raise ValueError(f"Unknown module: {module_id}")

        visiting.add(module_id)
        module = MODULES[module_id]

        # First, visit all dependencies
        for dep in module.DEPENDENCIES:
            visit(dep)

        visiting.remove(module_id)
        visited.add(module_id)

        if module_id not in resolved:
            resolved.append(module_id)

    for module_id in module_ids:
        visit(module_id)

    return resolved


def check_conflicts(module_ids: List[str], config: df.config.Config, output: CLIOutput) -> bool:
    """
    Check for conflicts between modules to be installed and already installed modules.
    Returns True if conflicts are found, False otherwise.
    """
    conflicts_found = False
    installed_modules = set()

    # Get currently installed modules
    for module_id, _module in MODULES.items():
        module_config = config.get_module(module_id)
        if module_config.get_installed():
            installed_modules.add(module_id)

    # Check conflicts
    for module_id in module_ids:
        module = MODULES[module_id]

        # Check if this module conflicts with any installed modules
        for conflict in module.CONFLICTING:
            if conflict in installed_modules:
                output.error(f"Module '{module_id}' conflicts with already installed module '{conflict}'")
                conflicts_found = True

        # Check if any installed modules conflict with this module
        for installed_module_id in installed_modules:
            installed_module = MODULES[installed_module_id]
            if module_id in installed_module.CONFLICTING:
                output.error(f"Module '{module_id}' conflicts with already installed module '{installed_module_id}'")
                conflicts_found = True

    return conflicts_found


def check_compatibility(module_ids: List[str], output: CLIOutput) -> bool:
    """
    Check if all modules are compatible with the current system.
    Returns True if all are compatible, False otherwise.
    """
    incompatible_found = False

    for module_id in module_ids:
        module = MODULES[module_id]
        compatibility = module.is_compatible()

        if compatibility is not True:
            reason = compatibility if isinstance(compatibility, str) else "Unknown reason"
            output.error(f"Module '{module_id}' is not compatible: {reason}")
            incompatible_found = True

    return not incompatible_found


def install_module(module_id: str, config: df.config.Config, output: CLIOutput, force: bool = False) -> bool:
    """
    Install a single module.
    Returns True on success, False on failure.
    """
    if module_id not in MODULES:
        output.error(f"Unknown module: {module_id}")
        return False

    module = MODULES[module_id]
    module_config = config.get_module(module_id)

    # Check if already installed
    if module_config.get_installed() and not force:
        output.verbose_info(f"Module '{module_id}' is already installed (use --force to reinstall)")
        return True

    try:
        output.info(f"Installing module '{module_id}' ({module.NAME})...")

        # Create a string buffer to capture module output
        stdout_buffer = io.StringIO()

        # Install the module
        module.install(module_config, stdout_buffer)

        # Mark as installed
        module_config.set_installed(True)

        # Show module output if verbose
        module_output = stdout_buffer.getvalue().strip()
        if module_output:
            output.verbose_info(f"Module output:\n{module_output}")

        output.info(f"Successfully installed module '{module_id}'")
        return True

    except Exception as e:
        output.error(f"Failed to install module '{module_id}': {str(e)}")
        if output.verbose:
            output.error(traceback.format_exc())
        return False


def uninstall_module(module_id: str, config: df.config.Config, output: CLIOutput) -> bool:
    """
    Uninstall a single module.
    Returns True on success, False on failure.
    """
    if module_id not in MODULES:
        output.error(f"Unknown module: {module_id}")
        return False

    module = MODULES[module_id]
    module_config = config.get_module(module_id)

    # Check if installed
    if not module_config.get_installed():
        output.verbose_info(f"Module '{module_id}' is not installed")
        return True

    try:
        output.info(f"Uninstalling module '{module_id}' ({module.NAME})...")

        # Create a string buffer to capture module output
        stdout_buffer = io.StringIO()

        # Uninstall the module
        module.uninstall(module_config, stdout_buffer)

        # Mark as not installed
        module_config.set_installed(False)

        # Show module output if verbose
        module_output = stdout_buffer.getvalue().strip()
        if module_output:
            output.verbose_info(f"Module output:\n{module_output}")

        output.info(f"Successfully uninstalled module '{module_id}'")
        return True

    except Exception as e:
        output.error(f"Failed to uninstall module '{module_id}': {str(e)}")
        if output.verbose:
            output.error(traceback.format_exc())
        return False


def update_module(module_id: str, config: df.config.Config, output: CLIOutput) -> bool:
    """
    Update a single module.
    Returns True on success, False on failure.
    """
    if module_id not in MODULES:
        output.error(f"Unknown module: {module_id}")
        return False

    module = MODULES[module_id]
    module_config = config.get_module(module_id)

    # Check if installed
    if not module_config.get_installed():
        output.warning(f"Module '{module_id}' is not installed, cannot update")
        return False

    # Check if module supports updates
    if not hasattr(module, "has_update") or not hasattr(module, "update"):
        output.verbose_info(f"Module '{module_id}' does not support updates")
        return True

    try:
        # Check if update is needed
        update_info = module.has_update(module_config)
        if not update_info:
            output.verbose_info(f"Module '{module_id}' is already up to date")
            return True

        update_version = update_info if isinstance(update_info, str) else "latest"
        output.info(f"Updating module '{module_id}' to {update_version}...")

        # Create a string buffer to capture module output
        stdout_buffer = io.StringIO()

        # Update the module
        module.update(module_config, stdout_buffer)

        # Show module output if verbose
        module_output = stdout_buffer.getvalue().strip()
        if module_output:
            output.verbose_info(f"Module output:\n{module_output}")

        output.info(f"Successfully updated module '{module_id}'")
        return True

    except Exception as e:
        output.error(f"Failed to update module '{module_id}': {str(e)}")
        if output.verbose:
            output.error(traceback.format_exc())
        return False


def list_modules(config: df.config.Config, output: CLIOutput, show_all: bool = True):
    """List all available modules with their status"""

    if output.quiet:
        # In quiet mode, just print module IDs
        for module_id in sorted(MODULES.keys()):
            module_config = config.get_module(module_id)
            if show_all or module_config.get_installed():
                print(module_id)
        return

    print("Available modules:")
    print("-" * 60)

    for module_id in sorted(MODULES.keys()):
        module = MODULES[module_id]
        module_config = config.get_module(module_id)

        installed = module_config.get_installed()
        if not show_all and not installed:
            continue

        status = "✓ Installed" if installed else "  Available"

        # Check for updates if installed
        update_available = False
        if installed and hasattr(module, "has_update"):
            try:
                update_available = bool(module.has_update(module_config))
            except Exception:
                pass

        if update_available:
            status += " (update available)"

        print(f"{status:20} {module_id:20} {module.NAME}")
        if output.verbose:
            print(f"{'':20} {'':20} {module.DESCRIPTION}")
            if module.DEPENDENCIES:
                deps = ", ".join(module.DEPENDENCIES)
                print(f"{'':20} {'':20} Dependencies: {deps}")
            print()


def cmd_install(args, config: df.config.Config, output: CLIOutput) -> int:
    """Handle the install command"""

    if not args.modules:
        output.error("No modules specified for installation")
        return 1

    # Resolve dependencies
    try:
        if args.no_deps:
            resolved_modules = args.modules
        else:
            resolved_modules = resolve_dependencies(args.modules, output)
            output.verbose_info(f"Installation order: {' -> '.join(resolved_modules)}")
    except ValueError as e:
        output.error(str(e))
        return 1

    # Check compatibility
    if not check_compatibility(resolved_modules, output):
        if not args.force:
            output.error("Compatibility check failed. Use --force to install anyway.")
            return 1
        else:
            output.warning("Forcing installation despite compatibility issues")

    # Check conflicts
    if check_conflicts(resolved_modules, config, output):
        if not args.force:
            output.error("Conflict check failed. Use --force to install anyway.")
            return 1
        else:
            output.warning("Forcing installation despite conflicts")

    # Install modules
    failed_modules = []
    for module_id in resolved_modules:
        if not install_module(module_id, config, output, args.force):
            failed_modules.append(module_id)
            if not args.continue_on_error:
                break

    # Save configuration
    config.save()

    if failed_modules:
        output.error(f"Failed to install modules: {', '.join(failed_modules)}")
        return 1

    output.info(f"Successfully installed {len(resolved_modules)} module(s)")
    return 0


def cmd_uninstall(args, config: df.config.Config, output: CLIOutput) -> int:
    """Handle the uninstall command"""

    if not args.modules:
        output.error("No modules specified for uninstall")
        return 1

    # Uninstall modules
    failed_modules = []
    for module_id in args.modules:
        if not uninstall_module(module_id, config, output):
            failed_modules.append(module_id)
            if not args.continue_on_error:
                break

    # Save configuration
    config.save()

    if failed_modules:
        output.error(f"Failed to uninstall modules: {', '.join(failed_modules)}")
        return 1

    output.info(f"Successfully uninstalled {len(args.modules)} module(s)")
    return 0


def cmd_update(args, config: df.config.Config, output: CLIOutput) -> int:
    """Handle the update command"""

    modules_to_update = args.modules if args.modules else []

    # If no modules specified, update all installed modules
    if not modules_to_update:
        for module_id, _module in MODULES.items():
            module_config = config.get_module(module_id)
            if module_config.get_installed():
                modules_to_update.append(module_id)

    if not modules_to_update:
        output.info("No modules to update")
        return 0

    # Update modules
    failed_modules = []
    updated_count = 0

    for module_id in modules_to_update:
        if update_module(module_id, config, output):
            updated_count += 1
        else:
            failed_modules.append(module_id)
            if not args.continue_on_error:
                break

    # Save configuration
    config.save()

    if failed_modules:
        output.error(f"Failed to update modules: {', '.join(failed_modules)}")
        return 1

    output.info(f"Successfully processed {len(modules_to_update)} module(s)")
    return 0


def cmd_list(args, config: df.config.Config, output: CLIOutput) -> int:
    """Handle the list command"""
    list_modules(config, output, show_all=not args.installed)
    return 0


def main_cli(dotfiles_dir: str, config_file: str, args: List[str]) -> int:
    """
    Main CLI entry point.

    :param dotfiles_dir: The directory where the dotfiles are stored
    :param config_file: The path to the config file
    :param args: Command line arguments (excluding script name)
    :return: Exit code (0 for success, non-zero for error)
    """

    # Set up global variables
    global DOTFILES_DIR, DOTFILES_PATH
    df.DOTFILES_DIR = dotfiles_dir
    df.DOTFILES_PATH = Path(dotfiles_dir)

    # Load config
    config = df.config.Config(config_file)

    # Set up argument parser
    parser = argparse.ArgumentParser(
        prog="dotfiles",
        description="Dotfiles Manager CLI - Automated installation and management of dotfiles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  dotfiles install git_config zsh_config    # Install specific modules
  dotfiles install --all                    # Install all compatible modules
  dotfiles uninstall zsh_config             # Uninstall a module
  dotfiles update                           # Update all installed modules
  dotfiles list                             # List all modules
  dotfiles list --installed                # List only installed modules

For devcontainers, use:
  dotfiles install --quiet --force git_config nvim_config_lazyvim
        """,
    )

    # Global options
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress informational output")
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue processing other modules if one fails",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Install command
    install_parser = subparsers.add_parser("install", help="Install modules")
    install_parser.add_argument("modules", nargs="*", help="Module IDs to install (or --all for all compatible)")
    install_parser.add_argument("--all", action="store_true", help="Install all compatible modules")
    install_parser.add_argument(
        "--no-deps",
        action="store_true",
        help="Do not automatically install dependencies",
    )
    install_parser.add_argument(
        "--force",
        action="store_true",
        help="Force installation (ignore conflicts and compatibility)",
    )

    # Uninstall command
    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall modules")
    uninstall_parser.add_argument("modules", nargs="+", help="Module IDs to uninstall")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update modules")
    update_parser.add_argument("modules", nargs="*", help="Module IDs to update (default: all installed)")

    # List command
    list_parser = subparsers.add_parser("list", help="List modules")
    list_parser.add_argument("--installed", action="store_true", help="Show only installed modules")

    # GUI command (for backwards compatibility)
    subparsers.add_parser("gui", help="Launch graphical interface")

    # Parse arguments
    if not args:
        parser.print_help()
        return 1

    parsed_args = parser.parse_args(args)

    # Set up output handler
    output = CLIOutput(verbose=parsed_args.verbose, quiet=parsed_args.quiet)

    # Handle --all flag for install command
    if parsed_args.command == "install" and parsed_args.all:
        compatible_modules = []
        for module_id, module in MODULES.items():
            if module.is_compatible() is True:
                compatible_modules.append(module_id)
        parsed_args.modules = compatible_modules
        output.verbose_info(f"Installing all compatible modules: {', '.join(compatible_modules)}")

    # Execute command
    try:
        if parsed_args.command == "install":
            return cmd_install(parsed_args, config, output)
        elif parsed_args.command == "uninstall":
            return cmd_uninstall(parsed_args, config, output)
        elif parsed_args.command == "update":
            return cmd_update(parsed_args, config, output)
        elif parsed_args.command == "list":
            return cmd_list(parsed_args, config, output)
        elif parsed_args.command == "gui":
            # Launch the GUI
            output.info("Launching graphical interface...")
            app = df.ui.DotfilesApp(config)
            app.run()
            return 0
        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        output.info("Operation interrupted by user")
        return 1
    except Exception as e:
        output.error(f"Unexpected error: {str(e)}")
        if parsed_args.verbose:
            output.error(traceback.format_exc())
        return 1
