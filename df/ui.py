import asyncio
from textual.app import App, ComposeResult
from textual.css.query import NoMatches
from textual.message import Message
from textual.screen import Screen
from textual.widgets import LoadingIndicator, Static, Button, TextLog
from textual.reactive import reactive
from textual.containers import Container
from textual.binding import Binding
import df.config
import os
import re
import traceback
from df.modules import MODULES
from typing import Union, List

class ModuleItem(Static):
    """A Widget representing a module that can be installed/removed/updated."""

    """Style of the module item.
    Updating this value will add a class with the name module-style-<style> to the widget.
    The previous style will be removed.
    """
    style = reactive("", layout=True)
    """Extra information about the module.
    This is displayed under the module description.
    """
    info = reactive("", layout=True)
    """Queued action for this module.
    This changes the appearance of the module item. It can be one of:
    "install", "update", "remove", or None.
    """
    queued_action = reactive(None, layout=True)

    class ActionPressed(Message):
        """Sent when a action is pressed."""

        def __init__(self, module, action) -> None:
            super().__init__()
            self.module_id = module.ID
            self.module_name = module.NAME
            self.module = module
            self.action = action

    def __init__(self, module, *args, **kwargs):
        self.module = module
        self.module_name = module.NAME
        self.module_description = module.DESCRIPTION
        dependency_names = []
        for module_id in module.DEPENDENCIES:
            module = MODULES[module_id]
            dependency_names.append(module.NAME)
        if len(dependency_names) > 0:
            self.dependencies = "Depends on: " + ", ".join(dependency_names)
        else:
            self.dependencies = ""
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        yield Container(
            Static(self.module_name, id="name"),
            Static(self.module_description, id="description"),
            Static(self.info, id="info"),
            Static(self.dependencies, id="dependencies"),
            id="module-description",
        )
        yield Container(
            Button("Install", id="install", variant="success"),
            Button("Update", id="update", variant="warning"),
            Button("Remove", id="remove", variant="error"),
            id="module-actions",
        )

    def watch_style(self, old_style: str, new_style: str) -> None:
        if old_style == new_style:
            return

        self.remove_class(f"module-style-{old_style}")
        self.add_class(f"module-style-{new_style}")

    def watch_info(self, old_info: str, new_info: str) -> None:
        try:
            self.query("#info").first(Static).update(new_info)
        except NoMatches:
            # The widget is not yet rendered, ignore
            # compose will use the new value
            pass

    def watch_queued_action(self, old_action: Union[str, None], new_action: Union[str, None]) -> None:
        if old_action == new_action:
            return
        if new_action is None:
            self.remove_class("module-changed")
        else:
            self.add_class("module-changed")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id in ["install", "update", "remove"]:
            action = event.button.id
            self.post_message(self.ActionPressed(self.module, action))

class QueuedActionItem(Static):
    """A Widget representing a queued action."""

    def __init__(self, action, module, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.action = action
        self.module = module
        self.module_id = module.ID
        self.module_name = module.NAME

    def compose(self) -> ComposeResult:
        yield Static(f"{self.action} {self.module_name}")
        yield LoadingIndicator()

class InstallationScreen(Screen):
    """Screen for showing the installation progress."""

    CSS_PATH = "ui.css"

    def __init__(self, Config: df.config.Config, queued_actions, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Config = Config
        self.queued_actions = queued_actions
        self.log_read_stream, self.log_write_stream = os.pipe()
        # provide stdout with a file-like object that writes to the textlog
        self.stdout = os.fdopen(self.log_write_stream, "w")

    def __del__(self):
        os.close(self.log_read_stream)
        self.stdout.close()

    async def pipe_log(self) -> None:
        loop = asyncio.get_running_loop()
        reader = asyncio.StreamReader(loop=loop)
        fd = self.log_read_stream

        def callback():
            data = os.read(fd, 1024)
            reader.feed_data(data)

        loop.add_reader(fd, callback)

        while True:
            line = await reader.readline()
            if not line:
                break
            text = line.decode()
            text = re.sub(r'\x1b\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]', '', text)
            self.print_log(text, end="")

        loop.remove_reader(fd)

    def add_queued_actions(self, actions: list) -> None:
        container = self.query("#queued_actions").first(Container)
        # Remove old queued actions
        for child in container.query(QueuedActionItem):
            child.remove()
        self.queued_action_items = []
        for (action, module_id) in actions:
            module = MODULES[module_id]
            item = QueuedActionItem(action, module)
            item.add_class("queued")
            self.queued_action_items.append(item)
            container.mount(item)

    def compose(self) -> ComposeResult:
        yield Static("Applying changes...", id="title")
        yield Container(
            Static("Queued Actions", classes="queued-actions-header"),
            id="queued_actions",
        )
        self.textlog = TextLog(id="log")
        yield Container(self.textlog, id="log-container")
        yield Container(
            Button("Quit", id="quit", variant="error", disabled=True),
            id="buttons",
        )

    def print_log(self, *args, sep=" ", end="\n") -> None:
        s = sep.join(map(str, args))
        s += end
        self.textlog.write(s, shrink=False, scroll_end=True)

    def on_mount(self) -> None:
        # Start the installation in a separate thread
        asyncio.create_task(self.pipe_log())
        asyncio.create_task(self.run_installation())

    async def run_installation(self) -> None:
        self.add_queued_actions(self.queued_actions)
        success = True
        for i, (action, module_id) in enumerate(self.queued_actions):
            module = MODULES[module_id]
            # Mark the module as being installed
            self.queued_action_items[i].remove_class("queued")
            self.queued_action_items[i].add_class("installing")
            self.print_log(f"Running {action} on {module.NAME}...")
            try:
                # Replace print with a function that writes to the textlog
                module.print = self.print_log
                # Run the action inside the module
                config = self.Config.get_module(module_id)
                if action == "install":
                    await asyncio.to_thread(module.install, config, self.stdout)
                    # Mark the module as installed
                    config.set_installed(True)
                elif action == "update":
                    await asyncio.to_thread(module.update, config, self.stdout)
                elif action == "remove":
                    await asyncio.to_thread(module.uninstall, config, self.stdout)
                    # Mark the module as not installed
                    config.set_installed(False)
                self.stdout.flush()
            except Exception as e:
                self.stdout.flush()
                # Mark the module as failed
                self.queued_action_items[i].remove_class("installing")
                self.queued_action_items[i].add_class("failed")
                self.print_log(f"Error while running {action} on {module.NAME}: {e}")
                # Print the traceback
                self.print_log(traceback.format_exc())
                success = False
                break
            finally:
                # Restore print
                try:
                    del module.print
                except AttributeError:
                    pass
            # Mark the module as installed
            self.queued_action_items[i].remove_class("installing")
            self.queued_action_items[i].add_class("installed")
        # Save the config
        self.Config.save()
        # Update the UI
        if success:
            self.print_log("Done!")
            self.query("#title").first(Static).update("Changes applied!")
            self.query("#quit").first(Button).disabled = False
        else:
            self.print_log("Failed applying changes!")
            self.query("#title").first(Static).update("Failed to apply changes!")
            self.query("#quit").first(Button).disabled = False
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit()

class DotfilesApp(App):
    """A Terminal UI for managing dotfiles."""

    TITLE = "Dotfiles Manager"
    CSS_PATH = "ui.css"
    BINDINGS = [
        Binding("<ctrl-c>", "quit", "Quit the application"),
        Binding("down", "scroll_down", "Down", show=False),
        Binding("up", "scroll_up", "Up", show=False),
        Binding("left", "scroll_left", "Left", show=False),
        Binding("right", "scroll_right", "Right", show=False),
    ]

    CATEGORIES = ["updatable", "installed", "not_installed", "incompatible"]

    def __init__(self, Config: df.config.Config):
        self.Config = Config
        self.reset_to_system_state()
        super().__init__()

    def on_ready(self) -> None:
        self.update_ui()

    def reset_to_system_state(self) -> None:
        """Reset the state of the app to match the system state.
        The UI will not be updated, call update_modules_list to do that."""
        self.queued_actions = []
        self.modules_installed = {}
        self.modules_installed_version = {}
        self.modules_has_update = {}
        self.modules_is_compatible = {}

        ids_with_config = self.Config.get_module_ids()
        for module_id, module in MODULES.items():
            if module_id in ids_with_config:
                module_config = self.Config.get_module(module_id)
                is_installed = module_config.get_installed()
                self.modules_installed[module_id] = is_installed
                self.modules_installed_version[module_id] = module_config.get_installed_version()
                if is_installed and hasattr(module, "has_update"):
                    self.modules_has_update[module_id] = module.has_update(module_config)
                else:
                    self.modules_has_update[module_id] = False
            else:
                self.modules_installed[module_id] = False
                self.modules_installed_version[module_id] = None
                self.modules_has_update[module_id] = False
            self.modules_is_compatible[module_id] = module.is_compatible()

    def compose(self) -> ComposeResult:
        yield Static("Dotfiles Manager", id="title")
        # Add Containers which will have the modules
        yield Container(
            Container(
                Static("Updatable", classes="category-header"),
                id="updatable", classes="category",
            ),
            Container(
                Static("Installed", classes="category-header"),
                id="installed", classes="category",
            ),
            Container(
                Static("Not Installed", classes="category-header"),
                id="not_installed", classes="category",
            ),
            Container(
                Static("Incompatible", classes="category-header"),
                id="incompatible", classes="category",
            ),
            id="categories",
        )
        yield Container(
            Static("Queued Actions", classes="queued-actions-header"),
            id="queued_actions"
        )
        yield Container(
            Button("Quit", id="quit", variant="error"),
            Button("Reset", id="reset", variant="error"),
            Button("Apply Changes", id="apply", variant="success"),
            id="actions",
        )

    def add_module_to_category(self, module_id, category: str) -> ModuleItem:
        """Idempotently add a module to a category.
        Will remove the module from any other category it is in.
        If the module does not exist, it will be created.
        """
        widget_id = f"module_{module_id}"
        # Find the widget by searching all categories
        for searched_category in self.CATEGORIES:
            container = self.query_one(f"#{searched_category}")
            try:
                widget = container.get_widget_by_id(widget_id, expect_type=ModuleItem)
                # Found it
                if searched_category == category:
                    # The module is already in the correct category, do nothing
                    return widget
                # Otherwise, remove it from the old category
                widget.remove()
            except NoMatches:
                pass # The module is not in this category

        # At this point, the module is not in any category
        # Create the widget, it does not exist
        widget = ModuleItem(MODULES[module_id], id=widget_id)

        # Mount the module in the correct category
        container = self.query_one(f"#{category}")
        container.mount(widget)
        return widget

    def update_ui(self) -> None:
        """Update the UI to reflect the current configured state of modules.

        This function should be called whenever the configuration changes.
        The UI will show the list as if the changes have been applied.
        """
        for module_id, module in MODULES.items():
            if self.modules_installed[module_id]:
                # The module is installed, check if it can be updated
                if self.modules_has_update[module_id]:
                    # Add to Updatable
                    widget = self.add_module_to_category(module_id, "updatable")
                    widget.style = "updatable"
                    if hasattr(module, "VERSION") and module.VERSION is not None:
                        info_text = f"Version {module.VERSION} available"
                        if self.modules_installed_version[module_id] is not None:
                            info_text += f", currently installed {self.modules_installed_version[module_id]}"
                    else:
                        info_text = "Update available"
                    widget.info = info_text
                    continue
                else:
                    # Add to Installed
                    widget = self.add_module_to_category(module_id, "installed")
                    widget.style = "installed"
                    widget.info = ""
                    continue
            # The module has no config or is not installed, check if it can
            # be installed
            compatible = self.modules_is_compatible[module_id]
            reason = None
            if compatible == True:
                # The module says it is compatible, check if there are any
                # conflicting modules
                conflicting = []
                for incompatible_id in module.CONFLICTING:
                    if self.modules_installed[incompatible_id]:
                        conflicting.append(incompatible_id)
                if len(conflicting) == 0:
                    # Add to Not Installed
                    widget = self.add_module_to_category(module_id, "not_installed")
                    widget.style = "not-installed"
                    continue
                else:
                    conflicting_as_text = ", ".join([MODULES[id].NAME for id in conflicting])
                    reason = f"Conflicts with {conflicting_as_text}"
            else:
                reason = compatible
            # Add to Incompatible
            widget = self.add_module_to_category(module_id, "incompatible")
            widget.style = "incompatible"
            widget.info = reason
            continue

        # Mark modules, which are queued as changed
        queud_action = {}
        for action, module_id in self.queued_actions:
            queud_action[module_id] = action
        for module_id, module in MODULES.items():
            widget = self.query(f"#module_{module_id}").first(ModuleItem)
            if module_id in queud_action:
                widget.queued_action = queud_action[module_id]
            else:
                widget.queued_action = None

        # # Hide empty categories
        # for category in self.CATEGORIES:
        #     container = self.query_one(f"#{category}")
        #     if len(container.children) == 1:
        #         # Only the header is present
        #         container.styles.display = "none"
        #     else:
        #         container.styles.display = "block"

        # Update the list of queued actions
        queued_actions_widget = self.query_one("#queued_actions")
        # We will remove all queued actions and re-add them
        for child in queued_actions_widget.query(QueuedActionItem):
            child.remove()
        for action, module_id in self.queued_actions:
            queued_actions_widget.mount(QueuedActionItem(action, MODULES[module_id]))

        # We can't reset or apply if there are no queued actions to reset
        reset_button = self.query("#reset").first(Button)
        apply_button = self.query("#apply").first(Button)
        if len(self.queued_actions) == 0:
            reset_button.disabled = True
            apply_button.disabled = True
        else:
            reset_button.disabled = False
            apply_button.disabled = False

    def queue_action(self, module_id: str, action: str) -> None:
        """Queue an action to be applied to the module.
        """
        # The order of actions is important, since we only show possible
        # actions, we can assume that the action is valid at this point
        if action == "install":
            # Recursively queue all dependencies for installation/update
            for dependency_id in MODULES[module_id].DEPENDENCIES:
                if self.modules_has_update[dependency_id]:
                    self.queue_action(dependency_id, "update")
                else:
                    self.queue_action(dependency_id, "install")
            # Queue the module itself
            if not self.modules_installed[module_id]:
                self.modules_installed[module_id] = True
                # Remove previous actions for this module
                shouldAppend = True
                for (a, id) in self.queued_actions:
                    if id != module_id:
                        continue
                    if a == "remove":
                        # It was allready installed
                        shouldAppend = False
                    break
                self.queued_actions = [a for a in self.queued_actions if a[1] != module_id]
                if shouldAppend:
                    self.queued_actions.append((action, module_id))
        elif action == "update":
            # Recursively queue all dependencies for installation/update
            for dependency_id in MODULES[module_id].DEPENDENCIES:
                if self.modules_has_update[dependency_id]:
                    self.queue_action(dependency_id, "update")
                else:
                    self.queue_action(dependency_id, "install")
            # Queue the module itself
            if self.modules_has_update[module_id]:
                self.modules_has_update[module_id] = False # Mark as up to date
                # Remove previous actions for this module
                self.queued_actions = [a for a in self.queued_actions if a[1] != module_id]
                self.queued_actions.append((action, module_id))
        elif action == "remove":
            # Queue the module itself
            if self.modules_installed[module_id]:
                self.modules_installed[module_id] = False
                # Remove previous actions for this module
                shouldAppend = True
                for (a, id) in self.queued_actions:
                    if id != module_id:
                        continue
                    if a == "install":
                        # It is not installed, we dont need to remove it
                        shouldAppend = False
                    break
                self.queued_actions = [a for a in self.queued_actions if a[1] != module_id]
                if shouldAppend:
                    self.queued_actions.append((action, module_id))
            # Recursively queue modules that depend on this module for removal
            for module in MODULES.values():
                if module_id in module.DEPENDENCIES:
                    self.queue_action(module.ID, "remove")

    def on_module_item_action_pressed(self, message: ModuleItem.ActionPressed) -> None:
        # A action on a module was pressed
        # Update the config, as if the action was applied
        action = message.action
        id = message.module_id
        if action in ["install", "update", "remove"]:
            self.queue_action(id, action)

        # Update the UI to reflect the new config
        self.update_ui()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        id = event.button.id
        if id == "reset":
            # Reset the queued actions
            self.reset_to_system_state()
            # Update the UI to reflect the new config
            self.update_ui()
        elif id == "apply":
            # Start the installation process
            # Show a new screen with the installation progress
            self.push_screen(InstallationScreen(self.Config, self.queued_actions))
        elif id == "quit":
            # Quit the application
            self.app.exit()
