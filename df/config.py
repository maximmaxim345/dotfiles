import json
from os import path
import df
from typing import Union, List

class ModuleConfig:
    """
    Class representing the config entry for a single module

    The config entry is mutable, so changes to it will be saved to the
    config file
    """

    def __init__(self, config: object, id: str, cfg: dict):
        """Initialize the config entry
        config: The Config object (used to update the config file)
        id: The id of the module
        cfg: The config dict as loaded from the config file
        """
        self.config = config
        self.id = id
        self.config.config["modules"][self.id].setdefault("data", {})
        self.config.config["modules"][self.id].setdefault("installed", False)

    def get_installed(self) -> bool:
        """
        Returns True if the module is installed
        """
        return self.config.config["modules"][self.id]["installed"]

    def set_installed(self, installed: bool):
        """
        Set the installed status of the module
        """
        self.config.config["modules"][self.id]["installed"] = installed
        self.config.modified = True

    def get_installed_version(self) -> Union[str, None]:
        """
        Returns the installed version of the module
        """
        try:
            return self.config.config["modules"][self.id]["installed_version"]
        except KeyError:
            return None

    def set_installed_version(self, version: str):
        """
        Set the installed version of the module
        This will also set the installed status to True
        """
        self.config.config["modules"][self.id]["installed_version"] = version
        self.config.config["modules"][self.id]["installed"] = True
        self.config.modified = True


    def get(self, key, default=None):
        """
        Get a config value. If the value does not exist, the default value
        is returned
        """
        return self.config.config["modules"][self.id]["data"].get(key, default)

    def set(self, key, value):
        """
        Set a config value
        """
        # Test the value to make sure it is json serializable
        # This brings some overhead, but it is called rarely
        # and it prevents the user from having to debug a broken config file
        try:
            json.dumps(value)
        except TypeError:
            raise ValueError("Value is not json serializable")
        self.config.config["modules"][self.id]["data"][key] = value
        self.config.modified = True

    def unset(self, key):
        """
        Remove a config value, if it exists
        """
        try:
            del self.config.config["modules"][self.id]["data"][key]
            self.config.modified = True
        except KeyError:
            pass

class Config:
    """
    Wrapper class for the config file. The config file is loaded when the
    object is created and saved when the object is deleted
    """

    def __init__(self, filepath):
        self.filepath = filepath
        self.config = {}
        self.modified = True  # True if the config has been modified
        if path.exists(filepath):
            with open(filepath, "r") as f:
                self.config = json.load(f)
                self.modified = False  # The config has not been modified yet
        self.config.setdefault("modules", {})

    def save(self):
        """
        Save the config file to disk
        """
        with open(self.filepath, "w") as f:
            json.dump(self.config, f, indent=4)
        self.modified = False

    def get_module_ids(self) -> List[str]:
        """
        Returns the list of all module ids, that have a config entry
        """
        return self.config["modules"].keys()

    def get_module(self, id:str) -> ModuleConfig:
        """
        Returns the config entry for the module with the given id
        The returned entry is mutable, so changes to it will be saved to the
        config file
        If the module does not exist, a new entry is created
        """
        if id not in self.config["modules"]:
            self.config["modules"][id] = {}
            self.modified = True
        cfg = self.config["modules"][id]
        return ModuleConfig(self, id, cfg)

    # def __del__(self):
    #     # Save the config file if it has been modified
    #     if self.modified:
    #         self.save()
