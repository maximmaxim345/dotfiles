import io
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import df
from df.config import Config
from df.modules import MODULES
from df.ui import InstallationScreen

opencode_config = MODULES["opencode_config"]


class OpenCodeConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.sources = self.root / "dotfiles"
        self.claude = self.sources / "claude"
        repository = Path(__file__).resolve().parents[1]
        for name in opencode_config.COMMANDS:
            shutil.copytree(repository / "claude" / "skills" / name, self.claude / "skills" / name)
        shutil.copyfile(repository / "claude" / "CLAUDE.md", self.claude / "CLAUDE.md")
        shutil.copytree(repository / "claude" / "output-styles", self.claude / "output-styles")
        for name in ("commit-guidelines.md", "pr-guidelines.md", "writing-examples.md"):
            shutil.copyfile(repository / "claude" / name, self.claude / name)
        self.commands = self.root / "home" / ".config" / "opencode" / "commands"
        self.config = Config(str(self.root / "config.json")).get_module("opencode_config")
        self.stdout = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
        self.addCleanup(self.stdout.close)
        sources_patch = patch.object(df, "DOTFILES_PATH", self.sources, create=True)
        sources_patch.start()
        self.addCleanup(sources_patch.stop)
        commands_patch = patch.object(opencode_config, "commands_path", self.commands)
        commands_patch.start()
        self.addCleanup(commands_patch.stop)
        for name, path in (
            ("instructions_path", self.commands.parent / "AGENTS.md"),
            ("sage_path", self.commands.parent / "agents" / "ohf-sage.md"),
            ("sage_source", self.root / "sage-source.md"),
        ):
            path_patch = patch.object(opencode_config, name, path)
            path_patch.start()
            self.addCleanup(path_patch.stop)

    def test_existing_install_gains_commands_without_replacing_instructions_sage_or_backups(self) -> None:
        instructions = opencode_config.instructions_path
        instructions.parent.mkdir(parents=True)
        instructions.write_text(opencode_config.build_instructions(), encoding="utf-8")
        opencode_config.sage_source.write_text(
            "---\ndescription: Review project standards\n---\nReview the diff.\n", encoding="utf-8"
        )
        sage = opencode_config.sage_path
        sage.parent.mkdir(parents=True)
        sage.write_text(opencode_config.build_sage(), encoding="utf-8")
        originals = {instructions: "Original instructions.\n", sage: "Original Sage.\n"}
        for target, key in ((instructions, "old_agents_md"), (sage, "old_ohf_sage")):
            backup = target.with_suffix(".old")
            backup.write_text(originals[target], encoding="utf-8")
            self.config.set(key, str(backup))
        self.config.set_installed(True)
        before = {path: path.read_bytes() for path in originals}
        backups = {key: self.config.get(key) for key in ("old_agents_md", "old_ohf_sage")}

        self.assertTrue(opencode_config.has_update(self.config))
        opencode_config.update(self.config, self.stdout)

        self.assertEqual({path: path.read_bytes() for path in originals}, before)
        self.assertEqual({key: self.config.get(key) for key in backups}, backups)
        self.assertEqual({path.stem for path in self.commands.iterdir()}, set(opencode_config.COMMANDS))
        self.assertFalse(opencode_config.has_update(self.config))
        opencode_config.uninstall(self.config, self.stdout)
        self.assertEqual({path: path.read_text() for path in originals}, originals)

    def test_installs_supported_commands_with_guidelines_and_native_placeholders(self) -> None:
        source = self.claude / "skills" / "open-pr" / "SKILL.md"
        source.write_text(source.read_text() + "\n$1 $2 !`git status --short`\n", encoding="utf-8")

        opencode_config.install(self.config, self.stdout)

        self.assertEqual({path.stem for path in self.commands.iterdir()}, set(opencode_config.COMMANDS))
        for target in self.commands.iterdir():
            rendered = target.read_text()
            self.assertNotIn("@~/.claude/", rendered)
            self.assertNotIn("commit-subagent", rendered)
            self.assertNotIn("commit-split-subagent", rendered)
            self.assertNotIn("argument-hint:", rendered)
        commit = (self.commands / "commit.md").read_text()
        self.assertIn("# Commit Message Guidelines", commit)
        self.assertIn("Do not delegate to a subagent.", commit)
        open_pr = (self.commands / "open-pr.md").read_text()
        self.assertIn('description: "Commit, push, and open a PR', open_pr)
        self.assertIn("# PR Message Guidelines", open_pr)
        self.assertIn("# Writing examples", open_pr)
        self.assertIn("$ARGUMENTS", open_pr)
        self.assertIn("$1 $2 !`git status --short`", open_pr)
        review = (self.commands / "review-changes.md").read_text()
        self.assertIn("Start the reviewers in the background, in parallel", review)
        self.assertNotIn("subagent: true", review)
        self.assertFalse(opencode_config.has_update(self.config))

    def test_source_command_changes_are_exported_again(self) -> None:
        opencode_config.install(self.config, self.stdout)
        source = self.claude / "skills" / "commit" / "SKILL.md"
        source.write_text(source.read_text() + "\nShow the staged diff first.\n", encoding="utf-8")

        self.assertTrue(opencode_config.has_update(self.config))
        opencode_config.update(self.config, self.stdout)

        self.assertIn("Show the staged diff first.", (self.commands / "commit.md").read_text())
        self.assertFalse(opencode_config.has_update(self.config))

    def test_shared_guideline_changes_update_only_dependent_commands(self) -> None:
        opencode_config.install(self.config, self.stdout)
        review = self.commands / "review-changes.md"
        review_mtime = review.stat().st_mtime_ns
        source = self.claude / "commit-guidelines.md"
        source.write_text(source.read_text() + "\nNew shared commit rule.\n", encoding="utf-8")

        self.assertTrue(opencode_config.has_update(self.config))
        opencode_config.update(self.config, self.stdout)

        for name in ("commit", "commit-split", "open-pr"):
            self.assertIn("New shared commit rule.", (self.commands / f"{name}.md").read_text())
        self.assertEqual(review.stat().st_mtime_ns, review_mtime)
        self.assertEqual(list(self.commands.glob("*.old*")), [])
        self.assertFalse(opencode_config.has_update(self.config))

    def test_retargeted_references_are_detected_even_with_identical_contents(self) -> None:
        opencode_config.install(self.config, self.stdout)
        shutil.copyfile(self.claude / "commit-guidelines.md", self.claude / "other-guidelines.md")
        source = self.claude / "skills" / "commit" / "SKILL.md"
        source.write_text(source.read_text().replace("commit-guidelines.md", "other-guidelines.md"), encoding="utf-8")

        self.assertTrue(opencode_config.has_update(self.config))
        opencode_config.update(self.config, self.stdout)

        rendered = (self.commands / "commit.md").read_text()
        self.assertIn('path="~/.claude/other-guidelines.md"', rendered)
        self.assertNotIn('path="~/.claude/commit-guidelines.md"', rendered)

    def test_added_nested_dependencies_are_tracked_and_included_once(self) -> None:
        opencode_config.install(self.config, self.stdout)
        guidelines = self.claude / "commit-guidelines.md"
        guidelines.write_text(guidelines.read_text() + "\nFollow @~/.claude/nested.md twice: @~/.claude/nested.md\n")
        nested = self.claude / "nested.md"
        nested.write_text("Nested rule.\nSee @~/.claude/commit-guidelines.md\n", encoding="utf-8")

        self.assertTrue(opencode_config.has_update(self.config))
        opencode_config.update(self.config, self.stdout)
        rendered = (self.commands / "commit.md").read_text()
        self.assertEqual(rendered.count('path="~/.claude/nested.md"'), 1)
        self.assertEqual(rendered.count('path="~/.claude/commit-guidelines.md"'), 1)
        self.assertNotIn("@~/.claude/", rendered)
        nested.write_text("Changed nested rule.\n", encoding="utf-8")
        self.assertTrue(opencode_config.has_update(self.config))
        opencode_config.update(self.config, self.stdout)
        self.assertIn("Changed nested rule.", (self.commands / "commit.md").read_text())
        self.assertFalse(opencode_config.has_update(self.config))

    def test_removed_dependencies_no_longer_affect_updates(self) -> None:
        opencode_config.install(self.config, self.stdout)
        source = self.claude / "skills" / "review-changes" / "SKILL.md"
        source.write_text("Review $ARGUMENTS.\n", encoding="utf-8")
        opencode_config.update(self.config, self.stdout)
        writing = self.claude / "writing-examples.md"
        writing.write_text(writing.read_text() + "\nChanged example.\n", encoding="utf-8")
        opencode_config.update(self.config, self.stdout)

        self.assertEqual((self.commands / "review-changes.md").read_text(), "Review $ARGUMENTS.\n")
        self.assertNotIn("Changed example.", (self.commands / "review-changes.md").read_text())

    def test_missing_target_is_recreated(self) -> None:
        opencode_config.install(self.config, self.stdout)
        (self.commands / "commit.md").unlink()

        self.assertTrue(opencode_config.has_update(self.config))
        opencode_config.update(self.config, self.stdout)

        self.assertTrue((self.commands / "commit.md").is_file())
        self.assertFalse(opencode_config.has_update(self.config))

    def test_new_command_is_picked_up_and_uninstalled_even_if_no_longer_defined(self) -> None:
        opencode_config.install(self.config, self.stdout)
        source = self.claude / "skills" / "new-command" / "SKILL.md"
        source.parent.mkdir(parents=True)
        source.write_text("Follow @~/.claude/pr-guidelines.md\n", encoding="utf-8")
        with patch.object(opencode_config, "COMMANDS", (*opencode_config.COMMANDS, "new-command")):
            self.assertTrue(opencode_config.has_update(self.config))
            opencode_config.update(self.config, self.stdout)
            self.assertIn("# PR Message Guidelines", (self.commands / "new-command.md").read_text())
            self.assertFalse(opencode_config.has_update(self.config))
        opencode_config.uninstall(self.config, self.stdout)
        self.assertFalse((self.commands / "new-command.md").exists())

    def test_original_file_survives_updates_reinstall_and_repeated_uninstall(self) -> None:
        self.commands.mkdir(parents=True)
        target = self.commands / "commit.md"
        target.write_text("Original command.\n", encoding="utf-8")
        unrelated = self.commands / "custom.md"
        unrelated.write_text("Unrelated command.\n", encoding="utf-8")
        opencode_config.install(self.config, self.stdout)
        original_backup = self.config.get("old_commit")
        source = self.claude / "skills" / "commit" / "SKILL.md"
        source.write_text(source.read_text() + "\nUpdated source.\n", encoding="utf-8")

        opencode_config.update(self.config, self.stdout)
        opencode_config.install(self.config, self.stdout)
        self.assertEqual(self.config.get("old_commit"), original_backup)
        self.assertEqual(Path(original_backup).read_text(), "Original command.\n")
        opencode_config.uninstall(self.config, self.stdout)
        opencode_config.uninstall(self.config, self.stdout)

        self.assertEqual(target.read_text(), "Original command.\n")
        self.assertEqual(unrelated.read_text(), "Unrelated command.\n")
        self.assertFalse((self.commands / "open-pr.md").exists())

    def test_local_edits_are_saved_separately_from_original_backup(self) -> None:
        self.commands.mkdir(parents=True)
        target = self.commands / "commit.md"
        target.write_text("Original command.\n", encoding="utf-8")
        opencode_config.install(self.config, self.stdout)
        target.write_text("Local edits before update.\n", encoding="utf-8")

        self.assertTrue(opencode_config.has_update(self.config))
        opencode_config.update(self.config, self.stdout)
        first_edit_backup = Path(self.config.get("edited_commit"))
        self.assertEqual(first_edit_backup.read_text(), "Local edits before update.\n")
        self.assertFalse(opencode_config.has_update(self.config))
        target.write_text("Local edits before uninstall.\n", encoding="utf-8")
        opencode_config.uninstall(self.config, self.stdout)

        self.assertEqual(target.read_text(), "Original command.\n")
        self.assertEqual(first_edit_backup.read_text(), "Local edits before update.\n")
        self.assertEqual(Path(self.config.get("edited_commit")).read_text(), "Local edits before uninstall.\n")

    def test_existing_symlink_is_restored_without_writing_to_its_source(self) -> None:
        self.commands.mkdir(parents=True)
        original = self.root / "original.md"
        original.write_text("Original linked command.\n", encoding="utf-8")
        target = self.commands / "commit.md"
        target.symlink_to(original)

        opencode_config.install(self.config, self.stdout)
        self.assertFalse(target.is_symlink())
        self.assertEqual(original.read_text(), "Original linked command.\n")
        opencode_config.uninstall(self.config, self.stdout)

        self.assertTrue(target.is_symlink())
        self.assertEqual(target.resolve(), original.resolve())

    def test_lifecycle_logs_to_stdout_with_tui_print_replacement(self) -> None:
        self.commands.mkdir(parents=True)
        target = self.commands / "commit.md"
        target.write_text("Original command.\n", encoding="utf-8")
        logger = InstallationScreen.print_log.__get__(SimpleNamespace(textlog=Mock()))

        with patch.object(opencode_config, "print", logger, create=True):
            opencode_config.install(self.config, self.stdout)
            target.write_text("Local edit.\n", encoding="utf-8")
            opencode_config.update(self.config, self.stdout)
            opencode_config.uninstall(self.config, self.stdout)

        self.stdout.seek(0)
        log = self.stdout.read()
        self.assertIn("Backed up ", log)
        self.assertIn("Wrote ", log)
        self.assertIn("Restored ", log)
        self.assertEqual(target.read_text(), "Original command.\n")

    def test_dangling_original_symlink_is_restored(self) -> None:
        self.commands.mkdir(parents=True)
        original = self.root / "missing.md"
        target = self.commands / "commit.md"
        target.symlink_to(original)

        opencode_config.install(self.config, self.stdout)
        opencode_config.uninstall(self.config, self.stdout)

        self.assertTrue(target.is_symlink())
        self.assertEqual(target.readlink(), original)

    def test_local_edits_do_not_overwrite_dangling_original_backup(self) -> None:
        self.commands.mkdir(parents=True)
        original = self.root / "missing.md"
        target = self.commands / "commit.md"
        target.symlink_to(original)
        opencode_config.install(self.config, self.stdout)
        original_backup = Path(self.config.get("old_commit"))
        target.write_text("Local edit.\n", encoding="utf-8")

        opencode_config.update(self.config, self.stdout)

        edited_backup = Path(self.config.get("edited_commit"))
        self.assertNotEqual(edited_backup, original_backup)
        self.assertTrue(original_backup.is_symlink())
        self.assertEqual(original_backup.readlink(), original)
        self.assertEqual(edited_backup.read_text(), "Local edit.\n")

    def test_missing_dependency_leaves_installed_commands_unchanged(self) -> None:
        opencode_config.install(self.config, self.stdout)
        before = {path.name: path.read_bytes() for path in self.commands.iterdir()}
        commit = self.claude / "skills" / "commit" / "SKILL.md"
        commit.write_text(commit.read_text() + "\nValid source change.\n", encoding="utf-8")
        review = self.claude / "skills" / "review-changes" / "SKILL.md"
        review.write_text("Follow @~/.claude/missing.md\n", encoding="utf-8")

        with self.assertRaises(FileNotFoundError):
            opencode_config.update(self.config, self.stdout)

        self.assertEqual({path.name: path.read_bytes() for path in self.commands.iterdir()}, before)


if __name__ == "__main__":
    unittest.main()
