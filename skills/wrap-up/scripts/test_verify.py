#!/usr/bin/env python3
"""Tests for verify.py. Run:  python3 -I scripts/test_verify.py

Builds throwaway git repos. Fake credentials are assembled at runtime.
"""
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify  # noqa: E402

PROMPT = (
    "Continue work on demo. First read HANDOFF.md, then docs/dev-log/2026-11-12-01.md.\n"
    "Push policy: the wrap-up never pushes. Don't push unless I ask.\nThen: do the thing."
)


def handoff(base, entry="2026-11-12-01", prompt=PROMPT):
    return (
        f"# Handoff\n\nBased on: main@{base}\n\n## Paste this to start the next session\n\n"
        f"```\n{prompt}\n```\n\n## Read first\n\n`docs/dev-log/{entry}.md`\n"
    )


class Repo:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "t")
        self.git("config", "user.email", "t@example.com")

    def git(self, *args):
        return subprocess.run(["git", "-C", self.root, *args], capture_output=True, text=True, check=True).stdout.strip()

    def write(self, rel, text):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)

    def commit(self, msg="c"):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)
        return self.git("rev-parse", "--short", "HEAD")

    def base(self):
        """A prior commit with one old entry, then a new entry saved but uncommitted."""
        self.write("docs/dev-log/README.md", "readme\n")
        self.write("docs/dev-log/INDEX.md", "Append-only.\n2026-11-01-01: old summary.\n")
        self.write("docs/dev-log/2026-11-01-01.md", "old entry\nline two\n")
        base = self.commit("prior")
        self.write("docs/dev-log/2026-11-12-01.md", "new entry\n")
        self.write("docs/dev-log/INDEX.md", "Append-only.\n2026-11-01-01: old summary.\n2026-11-12-01: new summary.\n")
        self.write("HANDOFF.md", handoff(base))
        return base

    def problems(self):
        return verify.verify(self.root)

    def errors(self):
        return [p for p in self.problems() if p[0] == "ERROR"]


class VerifyTests(unittest.TestCase):
    def setUp(self):
        self.r = Repo()
        self.addCleanup(self.r.tmp.cleanup)

    def messages(self):
        return " | ".join(m for _, _, m in self.r.errors())

    def test_clean_wrapup_passes(self):
        self.r.base()
        self.assertEqual(self.r.problems(), [])

    def test_unfilled_placeholder_fails(self):
        base = self.r.base()
        self.r.write("HANDOFF.md", handoff(base) + "\n{{NEXT_STEPS}}\n")
        self.assertIn("placeholder", self.messages())

    def test_missing_prompt_fails(self):
        self.r.base()
        self.r.write("HANDOFF.md", "# Handoff\n\nBased on: main@" + self.r.git("rev-parse", "--short", "HEAD") + "\n2026-11-12-01\n")
        self.assertIn("continuation prompt", self.messages())

    def test_prompt_must_name_latest_entry(self):
        base = self.r.base()
        self.r.write("HANDOFF.md", handoff(base, prompt="Continue work. Then: do it."))
        self.assertIn("does not name the latest entry", self.messages())

    def test_index_missing_latest_entry_fails(self):
        self.r.base()
        self.r.write("docs/dev-log/INDEX.md", "Append-only.\n2026-11-01-01: old summary.\n")
        self.assertIn("no line for the latest entry", self.messages())

    def test_bad_base_commit_fails(self):
        self.r.base()
        self.r.write("HANDOFF.md", handoff("deadbeef"))
        self.assertIn("does not exist", self.messages())

    def test_deleted_entry_fails(self):
        self.r.base()
        os.remove(os.path.join(self.r.root, "docs/dev-log/2026-11-01-01.md"))
        self.assertIn("deleted", self.messages())

    def test_edited_old_entry_fails(self):
        self.r.base()
        self.r.write("docs/dev-log/2026-11-01-01.md", "old entry\nrewritten history\n")
        self.assertIn("append-only", self.messages())

    def test_redaction_in_old_entry_is_allowed_with_warning(self):
        self.r.base()
        self.r.write("docs/dev-log/2026-11-01-01.md", "old entry\n[redacted: GitHub token]\n")
        self.assertEqual(self.r.errors(), [])
        self.assertTrue(any(level == "WARN" and "redacted" in m for level, _, m in self.r.problems()))

    def test_index_newline_fix_is_not_a_violation(self):
        self.r.write("docs/dev-log/README.md", "readme\n")
        self.r.write("docs/dev-log/INDEX.md", "Append-only.\n2026-11-01-01: old summary")  # no trailing newline
        self.r.write("docs/dev-log/2026-11-01-01.md", "old\n")
        base = self.r.commit("prior")
        self.r.write("docs/dev-log/2026-11-12-01.md", "new\n")
        self.r.write("docs/dev-log/INDEX.md", "Append-only.\n2026-11-01-01: old summary\n2026-11-12-01: new.\n")
        self.r.write("HANDOFF.md", handoff(base))
        self.assertEqual(self.r.problems(), [])

    def test_index_without_trailing_newline_fails(self):
        self.r.base()
        self.r.write("docs/dev-log/INDEX.md", "Append-only.\n2026-11-01-01: old.\n2026-11-12-01: new.")
        self.assertIn("newline", self.messages())

    def test_secret_in_handoff_fails(self):
        base = self.r.base()
        self.r.write("HANDOFF.md", handoff(base) + "\ntoken ghp_" + "a1B2" * 10 + "\n")
        self.assertIn("github-token", self.messages())

    def test_first_ever_wrapup_in_repo_with_no_commits(self):
        self.r.write("docs/dev-log/README.md", "readme\n")
        self.r.write("docs/dev-log/INDEX.md", "Append-only.\n2026-11-12-01: first.\n")
        self.r.write("docs/dev-log/2026-11-12-01.md", "first\n")
        self.r.write("HANDOFF.md", handoff("none").replace("Based on: main@none", "Based on: no commits yet"))
        self.assertEqual(self.r.problems(), [])

    def test_prompt_without_push_policy_warns_but_passes(self):
        base = self.r.base()
        self.r.write("HANDOFF.md", handoff(base, prompt="Continue. Read docs/dev-log/2026-11-12-01.md.\nThen: go."))
        self.assertEqual(self.r.errors(), [])
        self.assertTrue(any(level == "WARN" and "push" in m for level, _, m in self.r.problems()))

    def test_oversized_prompt_warns_but_passes(self):
        base = self.r.base()
        long_prompt = PROMPT + "\n" + "\n".join(f"line {i}" for i in range(40))
        self.r.write("HANDOFF.md", handoff(base, prompt=long_prompt))
        self.assertEqual(self.r.errors(), [])
        self.assertTrue(any(level == "WARN" for level, _, _ in self.r.problems()))


if __name__ == "__main__":
    unittest.main()
