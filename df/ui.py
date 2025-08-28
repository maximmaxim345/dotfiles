import asyncio
import os
import re
import traceback
from typing import List, Union

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, LoadingIndicator, Static, TextLog

import df.config
from df.modules import MODULES


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
    "install", "update", "remove", "install-no-deps", "update-no-deps" or None.
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
            Button(
                "Install without dependencies", id="install-no-deps", variant="warning"
            ),
            Button(
                "Update without dependencies", id="update-no-deps", variant="warning"
            ),
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

    def watch_queued_action(
        self, old_action: Union[str, None], new_action: Union[str, None]
    ) -> None:
        if old_action == new_action:
            return
        if new_action is None:
            self.remove_class("module-changed")
        else:
            self.add_class("module-changed")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id in [
            "install",
            "update",
            "remove",
            "install-no-deps",
            "update-no-deps",
        ]:
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
            text = re.sub(r"\x1b\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]", "", text)
            self.print_log(text, end="")

        loop.remove_reader(fd)

    def add_queued_actions(self, actions: list) -> None:
        container = self.query("#queued_actions").first(Container)
        # Remove old queued actions
        for child in container.query(QueuedActionItem):
            child.remove()
        self.queued_action_items = []
        for action, module_id in actions:
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
            Button("Retry", id="retry", variant="warning", disabled=True),
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

    async def run_installation(self, resume_at=None) -> None:
        self.add_queued_actions(self.queued_actions)
        success = True
        for i, (action, module_id) in enumerate(self.queued_actions):
            if resume_at is not None and i < resume_at:
                # Skip this action
                self.queued_action_items[i].add_class("installed")
                continue
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
                if action == "install" or action == "install-no-deps":
                    await asyncio.to_thread(module.install, config, self.stdout)
                    # Mark the module as installed
                    config.set_installed(True)
                    # save the installed version
                    if hasattr(module, "VERSION"):
                        config.set_installed_version(module.VERSION)
                elif action == "update" or action == "update-no-deps":
                    await asyncio.to_thread(module.update, config, self.stdout)
                    # save the installed version
                    if hasattr(module, "VERSION"):
                        config.set_installed_version(module.VERSION)
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
                self.failed_at = i
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
            self.query("#retry").first(Button).disabled = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit()
        elif event.button.id == "retry":
            self.query("#title").first(Static).update("Applying changes...")
            self.query("#quit").first(Button).disabled = True
            self.query("#retry").first(Button).disabled = True
            asyncio.create_task(self.run_installation(resume_at=self.failed_at))


class ErrorQueueingScreen(Screen):
    """Screen for showing incompatible modules."""

    CSS_PATH = "ui.css"

    def __init__(self, impossibleActionError, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error = impossibleActionError

    def compose(self) -> ComposeResult:
        yield Static(
            f"Error while {self.error.action} {MODULES[self.error.module_id].NAME}",
            id="title",
        )
        self.textlog = TextLog(id="log")
        for conflict in self.error.conflicts:
            if conflict.reason == "incompatible":
                self.textlog.write(
                    f"{MODULES[conflict.module_id].NAME} is incompatible with this system.",
                    shrink=False,
                    scroll_end=True,
                )
            elif conflict.reason == "conflicting":
                conflicting_as_text = ", ".join(
                    [MODULES[id].NAME for id in conflict.conflicts_with]
                )
                if len(conflict.conflicts_with) == 1:
                    self.textlog.write(
                        f'{MODULES[conflict.module_id].NAME} conflicts with the installed module "{conflicting_as_text}".',
                        shrink=False,
                        scroll_end=True,
                    )
                else:
                    self.textlog.write(
                        f"{MODULES[conflict.module_id].NAME} conflicts the following installed modules: {conflicting_as_text}.",
                        shrink=False,
                        scroll_end=True,
                    )
        yield Container(self.textlog, id="conflicts-log")
        yield Container(
            Button("Back", id="back", variant="primary", disabled=False),
            id="buttons",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()


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

    """Advanced mode.
    If enabled, we can bypass module compatibility checks."""
    advanced = reactive(False, layout=True)

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
        updates_to_check = []
        for module_id, module in MODULES.items():
            if module_id in ids_with_config:
                module_config = self.Config.get_module(module_id)
                is_installed = module_config.get_installed()
                self.modules_installed[module_id] = is_installed
                self.modules_installed_version[module_id] = (
                    module_config.get_installed_version()
                )
                if is_installed and hasattr(module, "has_update"):
                    updates_to_check.append(module_id)
                else:
                    self.modules_has_update[module_id] = False
            else:
                self.modules_installed[module_id] = False
                self.modules_installed_version[module_id] = None
                self.modules_has_update[module_id] = False
            self.modules_is_compatible[module_id] = module.is_compatible()

        # Check for updates
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for module_id in updates_to_check:
                module_config = self.Config.get_module(module_id)
                module = MODULES[module_id]
                future = executor.submit(module.has_update, module_config)
                futures.append(future)

            for future, module_id in zip(futures, updates_to_check, strict=False):
                try:
                    self.modules_has_update[module_id] = future.result()
                except Exception as e:
                    self.modules_has_update[module_id] = False
                    print(
                        f"Error while checking for updates for {MODULES[module_id].NAME}: {e}"
                    )

        # Now add modules, which have a different (module) version than the installed version
        for module_id, module in MODULES.items():
            if (
                self.modules_installed[module_id]
                and hasattr(module, "VERSION")
                and module.VERSION is not None
            ):
                if self.modules_installed_version[module_id] != module.VERSION:
                    self.modules_has_update[module_id] = True

    def compose(self) -> ComposeResult:
        yield Static("Dotfiles Manager", id="title")
        # Add Containers which will have the modules
        yield Container(
            Container(
                Static("Updatable", classes="category-header"),
                id="updatable",
                classes="category",
            ),
            Container(
                Static("Installed", classes="category-header"),
                id="installed",
                classes="category",
            ),
            Container(
                Static("Not Installed", classes="category-header"),
                id="not_installed",
                classes="category",
            ),
            Container(
                Static("Incompatible", classes="category-header"),
                id="incompatible",
                classes="category",
            ),
            id="categories",
        )
        yield Container(
            Static("Queued Actions", classes="queued-actions-header"),
            id="queued_actions",
        )
        yield Container(
            Button("Quit", id="quit", variant="error"),
            Button("Reset", id="reset", variant="error"),
            Button("Enable Advanced Mode", id="advanced-mode", variant="warning"),
            Button("Apply Changes", id="apply", variant="success"),
            id="actions",
        )

    def watch_advanced(self, old_advanced: bool, new_advanced: bool) -> None:
        if old_advanced == new_advanced:
            return
        for category in self.CATEGORIES:
            container = self.query_one(f"#{category}")
            if new_advanced:
                container.add_class("advanced")
            else:
                container.remove_class("advanced")

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
                pass  # The module is not in this category

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
                    conflicting_as_text = ", ".join(
                        [MODULES[id].NAME for id in conflicting]
                    )
                    reason = f"Conflicts with {conflicting_as_text}"
            else:
                if compatible == False:
                    reason = "Not compatible with this system"
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

        # Hide empty categories
        for category in self.CATEGORIES:
            container = self.query_one(f"#{category}")
            if len(container.children) == 1:
                # Only the header is present
                container.styles.display = "none"
            else:
                container.styles.display = "block"

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

    class ImpossibleActionError(Exception):
        """Raised when a action is impossible."""

        class Conflict:
            action: str
            module_id: str
            reason: str  # "incompatible" or "conflicting"
            conflicts_with: List[
                str
            ]  # If reason is "conflicting", this are the conflicting modules

            def __init__(
                self,
                action: str,
                module_id: str,
                reason: str,
                conflicts_with: List[str] = [],
            ) -> None:
                super().__init__()
                self.action = action
                self.module_id = module_id
                self.reason = reason
                self.conflicts_with = conflicts_with

        action: str
        module_id: str

        """
        List of subsiquent actions that would have been queued, but
        would have resulted in a invalid state.
        """
        conflicts: List[Conflict]

        def __init__(
            self, action: str, module_id: str, conflicts: List[Conflict]
        ) -> None:
            super().__init__()
            self.action = action
            self.module_id = module_id
            self.conflicts = conflicts

    def queue_action(self, module_id: str, action: str, state=None) -> None:
        """Try to Queue the action.
        This function is fail-safe, it will not queue an action that results
        in a invalid state. We only allow getting into an invalid state if
        we only uninstall modules. (If the user wants to resolve the conflict)
        Throws ImpossibleActionError if the action is cannot be applied.
        """

        class State:
            def __init__(self):
                self.modules_installed = {}
                self.queued_actions = []
                self.modules_has_update = {}
                self.conflicts = []

        if state is None:
            topmost = True
            state = State()
            state.modules_installed = self.modules_installed.copy()
            state.queued_actions = self.queued_actions.copy()
            state.modules_has_update = self.modules_has_update.copy()
        else:
            topmost = False
        # The order of actions is important, since we only show possible
        # actions, we can assume that the action is valid at this point
        if action == "install" or action == "install-no-deps":
            # Recursively queue all dependencies for installation/update
            if action == "install":
                for dependency_id in MODULES[module_id].DEPENDENCIES:
                    if state.modules_has_update[dependency_id]:
                        self.queue_action(dependency_id, "update", state=state)
                    else:
                        self.queue_action(dependency_id, "install", state=state)
            # Queue the module itself
            if not state.modules_installed[module_id]:
                if not self.modules_is_compatible[module_id]:
                    state.conflicts.append(
                        self.ImpossibleActionError.Conflict(
                            action, module_id, "incompatible"
                        )
                    )

                state.modules_installed[module_id] = True
                # Remove previous actions for this module
                shouldAppend = True
                for a, id in state.queued_actions:
                    if id != module_id:
                        continue
                    if a == "remove":
                        # It was allready installed
                        shouldAppend = False
                    break
                state.queued_actions = [
                    a for a in state.queued_actions if a[1] != module_id
                ]
                if shouldAppend:
                    state.queued_actions.append((action, module_id))
        elif action == "update" or action == "update-no-deps":
            # Recursively queue all dependencies for installation/update
            if action == "update":
                for dependency_id in MODULES[module_id].DEPENDENCIES:
                    if state.modules_has_update[dependency_id]:
                        self.queue_action(dependency_id, "update", state=state)
                    else:
                        self.queue_action(dependency_id, "install", state=state)
            # Queue the module itself
            if state.modules_has_update[module_id]:
                state.modules_has_update[module_id] = False  # Mark as up to date
                # Remove previous actions for this module
                state.queued_actions = [
                    a for a in state.queued_actions if a[1] != module_id
                ]
                state.queued_actions.append((action, module_id))
        elif action == "remove":
            # Queue the module itself
            if state.modules_installed[module_id]:
                state.modules_installed[module_id] = False
                # Remove previous actions for this module
                shouldAppend = True
                for a, id in state.queued_actions:
                    if id != module_id:
                        continue
                    if a == "install" or a == "install-no-deps":
                        # It is not installed, we dont need to remove it
                        shouldAppend = False
                    break
                state.queued_actions = [
                    a for a in state.queued_actions if a[1] != module_id
                ]
                if shouldAppend:
                    state.queued_actions.append((action, module_id))
            # Recursively queue modules that depend on this module for removal
            for module in MODULES.values():
                if module_id in module.DEPENDENCIES:
                    self.queue_action(module.ID, "remove", state=state)

        # Check if all actions we do are uninstall actions
        all_uninstall = True
        for a, id in state.queued_actions:
            if a != "remove":
                all_uninstall = False
                break
        # Check if we have incompatible modules
        for module_id, module in MODULES.items():
            if not state.modules_installed[module_id]:
                continue
            if not self.modules_is_compatible[module_id]:
                # A module is incompatible, we cannot apply the action
                # But we make an exception if we only uninstall things
                if not all_uninstall:
                    state.conflicts.append(
                        self.ImpossibleActionError.Conflict(
                            action, module_id, "incompatible"
                        )
                    )
            for incompatible_id in module.CONFLICTING:
                # Same here, just also save the conflicting module
                if state.modules_installed[incompatible_id] and not all_uninstall:
                    # If we allready have this conflict, just add the conflicting module to the list
                    added = False
                    for conflict in state.conflicts:
                        if (
                            conflict.module_id == module_id
                            and conflict.reason == "conflicting"
                        ):
                            conflict.conflicts_with.append(incompatible_id)
                            added = True
                            break
                    if not added:
                        state.conflicts.append(
                            self.ImpossibleActionError.Conflict(
                                action, module_id, "conflicting", [incompatible_id]
                            )
                        )
        # Throw an error if we have conflicts
        if len(state.conflicts) > 0:
            raise self.ImpossibleActionError(action, module_id, state.conflicts)
        # We have queued the action without errors, update the state
        self.modules_installed = state.modules_installed
        self.queued_actions = state.queued_actions
        self.modules_has_update = state.modules_has_update

    def on_module_item_action_pressed(self, message: ModuleItem.ActionPressed) -> None:
        # A action on a module was pressed
        # Update the config, as if the action was applied
        action = message.action
        id = message.module_id
        if action in [
            "install",
            "update",
            "remove",
            "install-no-deps",
            "update-no-deps",
        ]:
            try:
                self.queue_action(id, action)
            except self.ImpossibleActionError as e:
                # The action is impossible, show a message
                self.push_screen(ErrorQueueingScreen(e))
                return

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
        elif id == "advanced-mode":
            # Toggle advanced mode
            self.advanced = not self.advanced
            # Update text of the button
            button = self.get_widget_by_id("advanced-mode", expect_type=Button)
            if self.advanced:
                button.label = "Disable Advanced Mode"
            else:
                button.label = "Enable Advanced Mode"
