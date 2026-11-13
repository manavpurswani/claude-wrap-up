#!/usr/bin/env python3
"""Regression tests for scan.py. Run:  python3 -I scripts/test_scan.py

Fake credentials are assembled at runtime so this file never contains a
literal token that a secret scanner would flag.
"""
import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scan  # noqa: E402


def categories(line):
    return [category for category, _ in scan.scan_line(line)]


class Detects(unittest.TestCase):
    def test_aws_key(self):
        self.assertEqual(categories("key AKIA" + "A" * 16), ["secret"])

    def test_github_token(self):
        self.assertEqual(categories("t ghp_" + "a1B2" * 10), ["secret"])

    def test_api_key(self):
        self.assertEqual(categories("sk-" + "x9Y8" * 8), ["secret"])

    def test_private_key_header(self):
        self.assertEqual(categories("-----BEGIN RSA PRIVATE KEY-----"), ["secret"])

    def test_jwt(self):
        self.assertEqual(categories("eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abcdefghijk123"), ["secret"])

    def test_credentialed_url_reported_once(self):
        # Previously also reported the user:pass@host as an email.
        self.assertEqual(categories("postgres://admin:hunter2pw@db.internal:5432/app"), ["secret"])

    def test_generic_assignment(self):
        self.assertEqual(categories("API_KEY=" + "q7Zk" * 5), ["possible-secret"])

    def test_email(self):
        self.assertEqual(categories("mail jane.doe@gmail.com"), ["email"])

    def test_phone(self):
        self.assertEqual(categories("call 415-555-0134"), ["phone"])

    def test_home_path(self):
        self.assertEqual(categories("see /Users/someone/Desktop/x.ts"), ["home-path"])
        self.assertEqual(categories(r"see C:\Users\someone\x.ts"), ["home-path"])


class IgnoresSafeThings(unittest.TestCase):
    def test_clean_lines(self):
        for line in [
            "token: string",
            "password = process.env.DB_PASSWORD_VALUE",
            "git remote git@github.com:acme/repo.git",
            "Co-Authored-By: Claude <noreply@anthropic.com>",
            "contact test@example.com",
            "see /Users/<user>/x and ~/.claude/skills",
            "installed @types/node and react@18.3.1",
            "version 1.2.3, port 8080, commit e479b6e",
            "api_key lookup happens in src/auth/getKey.ts",
        ]:
            with self.subTest(line=line):
                self.assertEqual(categories(line), [])


class Output(unittest.TestCase):
    def test_snippets_are_masked(self):
        secret = "ghp_" + "a1B2" * 10
        buf = io.StringIO()
        with redirect_stdout(buf):
            scan.scan("f.md", f"token {secret}\n")
        self.assertNotIn(secret, buf.getvalue())
        self.assertNotIn(secret[:10], buf.getvalue())

    def test_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            clean = os.path.join(tmp, "clean.md")
            dirty = os.path.join(tmp, "dirty.md")
            with open(clean, "w") as f:
                f.write("nothing to see\r\nCRLF line\r\n")
            with open(dirty, "w") as f:
                f.write("mail jane.doe@gmail.com\n")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(scan.main([clean]), 0)
                self.assertEqual(scan.main([dirty]), 1)
                self.assertEqual(scan.main([os.path.join(tmp, "missing.md")]), 2)


if __name__ == "__main__":
    unittest.main()
