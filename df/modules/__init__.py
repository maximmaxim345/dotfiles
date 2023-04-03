import os
import glob
import importlib.util
import re
import io
io.TextIOWrapper

MODULES = {}

# register all modules in this directory
# each python file contains a module that must define the following
# variables:
# - ID: str          a unique identifier for the module, must only contain
#                    lowercase letters, numbers and underscores
# - NAME: str        a human readable name for the module
# - DESCRIPTION: str a short description of the module
# - DEPENDENCIES: list[str]
#                    A list of module names that must be installed
#                    before this module can be installed
#                    (e.g. ["git", "zsh"] or [])
# - CONFLICTING: list[str]
#                    A list of module ids that must not be
#                    installed when this module is installed
#                    (e.g. ["zsh", "bash"] or [])
# and following functions:
# - is_compatible() -> bool | str:
#                    Check if the module is compatible with the system
#                    Must return either True if the module is compatible
#                    or a string with the reason why it is not compatible
# - install(config: df.config.ModuleConfig, stdout: io.TextIOWrapper) -> None:
#                    Install the module.
#                    The config parameter is a ModuleConfig object,
#                    it can be used to persistantly read and write
#                    data which is specific to this module. See the
#                    ModuleConfig class for more information.
#                    On an error, this function must raise an exception.
#                    For output, either use print() or the stdout parameter
# - uninstall(config: df.config.ModuleConfig, stdout: io.TextIOWrapper) -> None:
#                    On an error, this function must raise an exception.
# optional functions for modules that can be updated:
# - has_update(config: df.config.ModuleConfig) -> bool | str:
#                    Check if the module can be updated
#                    If it can be updated, this function must return True or
#                    a string with the version after the update
#                    or False if it cannot be updated
# - update(config: df.config.ModuleConfig, stdout: io.TextIOWrapper):
#                    Update the module and its configuration files
#                    On an error, this function must raise an exception.
#
# See the _template.py file for an example module
# it is recommended to name the module file after the module ID
module_files = glob.glob(os.path.join(
    os.path.dirname(__file__), "*.py"))

# import all modules and register them in the modules list
for module_file in module_files:
    if os.path.basename(module_file) in ["__init__.py", "_template.py"]:
        continue
    module_name = os.path.basename(module_file)[:-3]
    spec = importlib.util.spec_from_file_location(module_name, module_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # test if module.ID is a string from a-z, 0-9 and _
    if not re.match(r"^[a-z0-9_]+$", module.ID):
        raise ValueError(f"Invalid module ID '{module.ID}'")
    MODULES[module.ID] = module

# check all modules for errors
for module in MODULES.values():
    # We allready checked module.ID
    # check if module.NAME is a string
    if not isinstance(module.NAME, str):
        raise ValueError(f"Module '{module.ID}' has an invalid name")
    # check if module.DESCRIPTION is a string
    if not isinstance(module.DESCRIPTION, str):
        raise ValueError(f"Module '{module.ID}' has an invalid description")
    # check if module.DEPENDENCIES is a list of strings
    if not isinstance(module.DEPENDENCIES, list):
        raise ValueError(f"Module '{module.ID}' has invalid dependencies")
    for dependency in module.DEPENDENCIES:
        if not isinstance(dependency, str):
            raise ValueError(f"Module '{module.ID}' has invalid dependencies")
        # check if the dependency exists
        if dependency not in MODULES.keys():
            raise ValueError(f"Module '{module.ID}' has an invalid dependency '{dependency}'")
    # check if module.CONFLICTING is a list of strings
    if not isinstance(module.CONFLICTING, list):
        raise ValueError(f"Module '{module.ID}' has invalid conflicting modules")
    for conflicting in module.CONFLICTING:
        if not isinstance(conflicting, str):
            raise ValueError(f"Module '{module.ID}' has invalid conflicting modules")
        # check if the conflicting module exists
        if conflicting not in MODULES.keys():
            raise ValueError(f"Module '{module.ID}' has an invalid conflicting module '{conflicting}'")
    # for functions, we only check if they exist
    # we don't check if they have the correct signature
    # because running the function has unwanted side effects
    if not hasattr(module, "is_compatible"):
        raise ValueError(f"Module '{module.ID}' has no is_compatible function")
    if not hasattr(module, "install"):
        raise ValueError(f"Module '{module.ID}' has no install function")
    if not hasattr(module, "uninstall"):
        raise ValueError(f"Module '{module.ID}' has no uninstall function")
    has_has_update = hasattr(module, "has_update")
    has_update = hasattr(module, "update")
    if has_has_update != has_update:
        raise ValueError(f"Module '{module.ID}' has only one of has_update and update")
