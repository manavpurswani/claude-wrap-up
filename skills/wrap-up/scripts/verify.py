#!/usr/bin/env python3
"""Verify a repo's wrap-up files after they've been saved (and before commit).

Usage:  verify.py [REPO_ROOT]        (default: the git repo containing the cwd)

Checks, mechanically, the promises the skill makes:
  structure   dev-log README + INDEX exist, entries are named YYYY-MM-DD-NN.md,
              the INDEX mentions the latest entry and ends in a newline
  handoff     HANDOFF.md has no unfilled {{placeholders}}, points at the latest
              entry, has a fenced "paste this" prompt that names it, and records
              a base commit that really exists
  append-only no entry deleted; no existing entry or INDEX line changed, except
              a line replaced by one containing "[redacted:"  (the one exception)
  privacy     scan.py is run over every wrap-up file

Output: one line per problem, "ERROR path: message" or "WARN path: message".
Exit 1 if any ERROR, else 0. WARNs are worth a look but don't block.
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scan  # noqa: E402

ENTRY = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{2}\.md$")
HANDOFF_WARN_LINES = 100
PROMPT_WARN_LINES = 25


def git(root, *args):
    proc = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)
    return proc.returncode, proc.stdout


def has_commits(root):
    return git(root, "rev-parse", "--verify", "-q", "HEAD")[0] == 0


def read(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


def paste_prompt(handoff):
    """The fenced block under the first heading containing 'paste', or None."""
    lines = handoff.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("#") and "paste" in line.lower():
            start = next((j for j in range(i + 1, len(lines)) if lines[j].startswith("```")), None)
            if start is None:
                return None
            end = next((j for j in range(start + 1, len(lines)) if lines[j].startswith("```")), None)
            return None if end is None else "\n".join(lines[start + 1:end])
    return None


def diff_lines(root, path):
    """(removed, added) text lines for a tracked file versus HEAD."""
    code, out = git(root, "diff", "HEAD", "-U0", "--", path)
    removed, added = [], []
    for line in out.splitlines():
        if line.startswith(("---", "+++", "@@", "diff ", "index ")):
            continue
        if line.startswith("-"):
            removed.append(line[1:].strip())
        elif line.startswith("+"):
            added.append(line[1:].strip())
    return removed, added


def check_append_only(root, problems):
    if not has_commits(root):
        return
    code, out = git(root, "diff", "HEAD", "--name-status", "--", "docs/dev-log")
    for row in out.splitlines():
        status, _, path = row.partition("\t")
        if status.startswith("D"):
            problems.append(("ERROR", path, "existing dev-log file was deleted; the log is append-only"))
        elif status.startswith("M"):
            removed, added = diff_lines(root, path)
            # A line that changed only by gaining a trailing newline shows as -x/+x.
            real_removed = [r for r in removed if r not in added]
            redactions = [a for a in added if "[redacted:" in a and a not in removed]
            if real_removed and len(redactions) < len(real_removed):
                problems.append((
                    "ERROR", path,
                    f"{len(real_removed)} existing line(s) changed or removed without a "
                    "'[redacted: ...]' replacement; the log is append-only",
                ))
            elif real_removed:
                problems.append(("WARN", path, "existing line(s) redacted in place; record that in the new entry"))


def verify(root):
    problems = []
    log = os.path.join(root, "docs", "dev-log")
    handoff_path = os.path.join(root, "HANDOFF.md")
    index_path = os.path.join(log, "INDEX.md")

    if not os.path.isdir(log):
        return [("ERROR", "docs/dev-log", "directory does not exist")]
    for name in ("README.md", "INDEX.md"):
        if not os.path.isfile(os.path.join(log, name)):
            problems.append(("ERROR", f"docs/dev-log/{name}", "missing"))
    entries = sorted(n for n in os.listdir(log) if ENTRY.match(n))
    strays = [n for n in os.listdir(log) if n.endswith(".md") and n not in ("README.md", "INDEX.md") and not ENTRY.match(n)]
    for n in strays:
        problems.append(("WARN", f"docs/dev-log/{n}", "not named YYYY-MM-DD-NN.md"))
    if not entries:
        problems.append(("ERROR", "docs/dev-log", "no entries found"))
        return problems
    latest = entries[-1]

    if os.path.isfile(index_path):
        index = read(index_path)
        if index and not index.endswith("\n"):
            problems.append(("ERROR", "docs/dev-log/INDEX.md", "does not end in a newline; the next append would glue onto it"))
        stem = latest[:-3]
        if stem not in index and latest not in index:
            problems.append(("ERROR", "docs/dev-log/INDEX.md", f"has no line for the latest entry ({latest})"))

    if not os.path.isfile(handoff_path):
        problems.append(("ERROR", "HANDOFF.md", "missing"))
    else:
        handoff = read(handoff_path)
        if "{{" in handoff:
            problems.append(("ERROR", "HANDOFF.md", "contains an unfilled {{placeholder}}"))
        if latest not in handoff and latest[:-3] not in handoff:
            problems.append(("ERROR", "HANDOFF.md", f"does not point at the latest entry ({latest})"))
        prompt = paste_prompt(handoff)
        if prompt is None:
            problems.append(("ERROR", "HANDOFF.md", "no fenced continuation prompt under a 'Paste this' heading"))
        else:
            if latest[:-3] not in prompt:
                problems.append(("ERROR", "HANDOFF.md", "continuation prompt does not name the latest entry"))
            if "push" not in prompt.lower():
                problems.append(("WARN", "HANDOFF.md", "continuation prompt says nothing about pushing; add the push policy line"))
            if len(prompt.splitlines()) > PROMPT_WARN_LINES:
                problems.append(("WARN", "HANDOFF.md", f"continuation prompt is over {PROMPT_WARN_LINES} lines; trim it"))
        if len(handoff.splitlines()) > HANDOFF_WARN_LINES:
            problems.append(("WARN", "HANDOFF.md", f"over {HANDOFF_WARN_LINES} lines; the detail belongs in the entry"))
        if has_commits(root):
            m = re.search(r"Based on[^\n]*?\b([0-9a-f]{7,40})\b", handoff)
            if not m:
                problems.append(("WARN", "HANDOFF.md", "no 'Based on: <branch>@<hash>' line, so a later session can't tell if it's stale"))
            elif git(root, "cat-file", "-e", m.group(1) + "^{commit}")[0] != 0:
                problems.append(("ERROR", "HANDOFF.md", f"base commit {m.group(1)} does not exist in this repo"))

    entry_text = read(os.path.join(log, latest))
    if "{{" in entry_text:
        problems.append(("ERROR", f"docs/dev-log/{latest}", "contains an unfilled {{placeholder}}"))

    check_append_only(root, problems)

    # Privacy: scan.py over everything this wrap-up writes.
    files = [os.path.join(log, latest), index_path, handoff_path]
    for path in files:
        if not os.path.isfile(path):
            continue
        rel = os.path.relpath(path, root)
        for number, line in enumerate(read(path).splitlines(), 1):
            for category, snippet in scan.scan_line(line):
                problems.append(("ERROR", f"{rel}:{number}", f"[{category}] {snippet}"))
    return problems


def main(argv):
    if argv:
        root = argv[0]
    else:
        code, out = git(os.getcwd(), "rev-parse", "--show-toplevel")
        if code != 0:
            print("ERROR .: not inside a git repository", file=sys.stderr)
            return 2
        root = out.strip()
    problems = verify(root)
    for level, path, message in problems:
        print(f"{level} {path}: {message}")
    errors = sum(1 for level, _, _ in problems if level == "ERROR")
    if not problems:
        print("OK: wrap-up files verified")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
