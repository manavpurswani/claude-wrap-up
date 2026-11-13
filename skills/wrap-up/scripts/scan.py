#!/usr/bin/env python3
"""Scan wrap-up drafts for secrets and personal details before they reach git.

Usage:  scan.py FILE [FILE ...]      (use "-" to read stdin)

Prints one line per finding as  FILE:LINE: [category] masked-snippet
and exits 1 if anything was found, 0 if clean. Snippets are masked on purpose,
so the scan output never re-leaks what it found.

Categories:
  secret           high-confidence credential format (keys, tokens, private keys)
  possible-secret  something assigned to a name like password/token/api_key
  email            an email address (noreply and example addresses are ignored)
  phone            a phone number with separators
  home-path        an absolute home directory that exposes an OS username

This is a pattern matcher, not a reader. A clean result does not prove an entry
is safe: names, employers, clients and internal URLs still need a human read.
"""
import re
import sys

SECRET = [
    ("private-key", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ("aws-key", r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    ("github-token", r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    ("github-pat", r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    ("api-key", r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    ("slack-token", r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    ("google-key", r"\bAIza[0-9A-Za-z_-]{35}\b"),
    ("stripe-key", r"\b[sr]k_(?:live|test)_[A-Za-z0-9]{16,}\b"),
    ("jwt", r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    ("url-credentials", r"://[^/\s:@]+:[^/\s@]+@"),
]

GENERIC = re.compile(
    r"""(?ix)
    \b(?:api[_-]?key|secret|token|passwd|password|pwd|auth\w*)\w*
    \s*[:=]\s*['"]?
    (?P<value>[A-Za-z0-9/+_\-.]{12,})""",
)
# Values that are references to a secret, not the secret itself.
REFERENCE = re.compile(r"(?i)process\.env|os\.environ|getenv|\$\{|<[^>]+>|your[_-]|example|placeholder|xxxx")

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
EMAIL_IGNORE = re.compile(r"(?i)^(?:git|noreply|no-reply)@|@(?:example\.(?:com|org|net)|users\.noreply\.github\.com)$|\.noreply\.")

PHONE = re.compile(r"(?<![\w.])(?:\+\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?![\w])")

HOME = re.compile(r"(?:/Users/|/home/|[A-Za-z]:\\Users\\)(?P<name>[^/\\\s'\"`)]+)")
HOME_GENERIC = {"user", "username", "you", "name", "me", "example", "shared", "runner", "<user>", "$user"}


def mask(text):
    text = text.strip()
    if len(text) <= 6:
        return "*" * len(text)
    return f"{text[:3]}…({len(text)} chars)"


def scan_line(line):
    hits = []
    credential_spans = []
    for label, pattern in SECRET:
        for m in re.finditer(pattern, line):
            hits.append(("secret", f"{label} {mask(m.group(0))}"))
            credential_spans.append(m.span())
    for m in GENERIC.finditer(line):
        value = m.group("value")
        if not REFERENCE.search(value) and not any(h[0] == "secret" for h in hits):
            hits.append(("possible-secret", mask(value)))
    for m in EMAIL.finditer(line):
        # user:pass@host inside a credentialed URL is already reported once.
        inside_credential = any(s <= m.start() < e for s, e in credential_spans)
        if not EMAIL_IGNORE.search(m.group(0)) and not inside_credential:
            hits.append(("email", mask(m.group(0))))
    for m in PHONE.finditer(line):
        hits.append(("phone", mask(m.group(0))))
    for m in HOME.finditer(line):
        if m.group("name").lower() not in HOME_GENERIC:
            hits.append(("home-path", mask(m.group(0))))
    return hits


def scan(name, text):
    found = 0
    for number, line in enumerate(text.splitlines(), 1):
        for category, snippet in scan_line(line):
            print(f"{name}:{number}: [{category}] {snippet}")
            found += 1
    return found


def main(argv):
    if not argv:
        print(__doc__.strip().split("\n\n")[0], file=sys.stderr)
        return 2
    total = 0
    for path in argv:
        if path == "-":
            total += scan("<stdin>", sys.stdin.read())
            continue
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                total += scan(path, handle.read())
        except OSError as err:
            print(f"{path}: cannot read ({err.strerror})", file=sys.stderr)
            return 2
    if total:
        print(f"{total} finding(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
