# wrap-up

**Your Claude Code session ends. The context doesn't have to.**

Run `/keepsession:wrap-up` (or just say "wrap up this session") before you
close a session you'll want to come back to. Claude
writes down everything that happened (what changed, why, what was decided,
what's still broken) into your project's own git repo as an append-only dev
log, scans it for secrets and personal details before it can reach a public
repo, checks what's actually committed and pushed, and hands you a short
prompt to paste into the next session so it starts with full context instead
of from zero.

```
/plugin marketplace add manavpurswani/claude-wrap-up
/plugin install keepsession@claude-wrap-up
```

## Why

Long Claude Code sessions build up context that's expensive to rebuild: the
bug you found and what really caused it, the number you measured instead of
guessed, the approach you tried and dropped, the decision you made in chat
that never became a commit. None of that is in `git log`, and summaries lose
it, because a summary's whole job is to compress.

Most handoff setups write one summary file and overwrite it each time. If one
of those rewrites misses something, it's gone, and nothing tells you.

## How it works

Two files with different jobs:

| File | What it is | Ever edited? |
|---|---|---|
| `docs/dev-log/YYYY-MM-DD-NN.md` | The record. One entry per wrap-up. | **Never.** A later entry corrects an earlier one; the old one stays as written. |
| `HANDOFF.md` (repo root) | A short index: status, next steps, the paste-ready prompt. | Rewritten every time, which is safe because the log underneath never shrinks. |

Each wrap-up:

1. Works out **which repos the session touched** (not just the folder you're
   in) and runs everything below once per repo, so a session that spanned two
   repos leaves an entry in each.
2. Reads the existing handoff and recent log entries, so it adds to the
   record instead of repeating it.
3. **Audits git for real:** uncommitted work, missing remotes, unpushed
   branches, branches that look merged but aren't. It reports what's true,
   not what seems likely.
4. **Asks whether the repo is public**, and treats "can't tell" as public.
5. Drafts the new entry outside your repo: concrete file paths, the reasoning
   behind non-obvious changes, decisions that never produced code, open bugs,
   and conversations that didn't resolve.
6. **Scans the drafts for secrets and personal details before anything is
   saved.** A bundled scanner (`scripts/scan.py`) catches API keys, tokens,
   private keys, passwords in URLs, emails, phone numbers and home-directory
   paths that expose your username. Claude then reads the drafts for what a
   pattern can't see: names, clients, internal URLs. Secrets are replaced by
   the *name* of the thing ("the `STRIPE_KEY` env var"), never the value, and
   if one showed up in the session it tells you to rotate it.
7. Writes the entry, adds one line to `docs/dev-log/INDEX.md`, and rewrites
   `HANDOFF.md` with a **continuation prompt**: a block of text you paste as
   the first message of your next session. It names the one question that
   needs answering first (or says nothing is blocking), the concrete next
   step, and any **standing rules** you give it for the repo (commit to main,
   no co-author line, never push). It asks you once, and uses only what you
   say; it doesn't go through your memory or config files.
8. **Runs a verifier** (`scripts/verify.py`) over what it just wrote: no
   leftover placeholders, the index and handoff point at the new entry, the
   prompt names it, and **no existing entry or index line was edited or
   deleted** (the only exception is a `[redacted: ...]` replacement). The
   append-only promise is checked by a script, not taken on trust.
9. **Offers to commit just the wrap-up files** (`docs/dev-log/` and
   `HANDOFF.md`, nothing else), asking first because you may have commit
   rules. It never pushes.
10. Shows you the prompt in chat, so you don't have to go and open a file.

### Built so the next session starts cheap

A cold session's budget goes on exploring. The entry is organized to cut that:

- a **TL;DR** first, so a reader can stop early and still start right
- **Start here**: the few files (with functions or line ranges) to open first,
  and what's safe to skip
- **Commands that worked**: the exact test, build and run commands and what
  they showed, so the baseline is confirmed in seconds
- **Tried and abandoned**, with why, so dead ends aren't retried
- `HANDOFF.md` records the **base commit**, and the prompt tells the next
  session to run `git log <hash>..HEAD` first, so it notices when the handoff
  has gone stale instead of trusting it blindly
- `HANDOFF.md` stays near 60 lines; the detail lives in the entry

It only runs when you ask. It never triggers itself because a session "feels
long".

## What you get

Everything below is invented, to show the shape. The project, the people and
the numbers are made up.

`docs/dev-log/2026-11-12-01.md`, the permanent entry:

```markdown
# 2026-11-12-01: tidewatch, fixing the stale-forecast bug

## TL;DR
Stale forecasts fixed: the cache was keyed on date alone. One real bug is
left (tide heights off by one slot near midnight UTC). Next: reproduce it
with a failing test. Biggest risk: `--refresh` is untested against the real API.

## Start here
- `src/forecast/slots.ts` (`toSlot`, the date-boundary code): where the
  midnight bug most likely lives.
- `test/forecast/cache.test.ts`: the pattern to copy for the new test.
- Skip `src/cli/`: unchanged and unrelated.

## Commands that worked
- `npm test`: 41 passing, about 2 s.
- `npx tidewatch watch --station dover --refresh`: ran against the mock only.

## Tried and abandoned
- Per-request TTLs: the upstream API already sets cache headers, so this
  added code and changed nothing.

## What changed
- `src/forecast/cache.ts`: cache key now includes the station ID. It was
  keyed on date alone, so two stations on the same day shared one entry.
- `src/cli/watch.ts`: `--refresh` now bypasses the cache instead of
  silently ignoring it.
- `test/forecast/cache.test.ts`: new, 6 cases, including the two-station
  collision that caused the bug.

## Why
The stale forecasts weren't a network problem, which was the first guess.
Logging the key showed `2026-11-12` for both Dover and Harwich. Measured
cold vs warm: 840 ms vs 3 ms, so the cache is worth keeping and fixing.

## Decided, no code
- Not moving to a file-backed cache yet. Memory is fine at this size; revisit
  past ~50 stations.
- Ruled out per-request TTLs: the upstream API already sets cache headers.

## Still open
- Tide heights near midnight UTC are off by one slot. Reproduced once, not
  diagnosed. Probably the date-boundary code in `src/forecast/slots.ts`.
- `--refresh` is untested against the real API, only the mock.

## Discussed, unresolved
Whether `tidewatch` should expose a `--json` flag. No decision on the output
schema; deferred until the midnight bug is understood.

## Git state
On `main`, 1 commit ahead of `origin/main`. Source changes above are
committed locally and not pushed. Repo is public.
```

`HANDOFF.md`, regenerated each time:

````markdown
# Handoff

Last updated: 2026-11-12, after fixing the stale-forecast cache bug.
Based on: main@3f9c2ab

## Paste this to start the next session

```
Continue work on tidewatch. First read HANDOFF.md at the repo root, then
docs/dev-log/2026-11-12-01.md. Don't re-derive context, it's written down.

Nothing is blocking. Pick up with next-step 1 below.

Standing rules for this work: commit straight to main, no co-author
trailer, don't push without asking.

Before anything else, run `git status` and `git log --oneline 3f9c2ab..HEAD`.
If the repo has moved in ways HANDOFF.md doesn't mention, tell me first.

Then: reproduce the midnight-UTC off-by-one in src/forecast/slots.ts with a
failing test before changing anything.
```

## Status in one paragraph

The cache collision is fixed and covered by tests. One real bug remains
(midnight-UTC tide heights), reproduced once and not yet diagnosed.

## Immediate next step

1. Write a failing test for the midnight-UTC case, then fix `slots.ts`.
2. Try `--refresh` against the real API once.

## Read before proposing new work

`docs/dev-log/2026-11-12-01.md`
````

The wrap-up also appends a two-to-four sentence line to `INDEX.md` and, if you
say yes, commits both files.

## Install

**As a plugin** (inside Claude Code):

```
/plugin marketplace add manavpurswani/claude-wrap-up
/plugin install keepsession@claude-wrap-up
```

**Or copy the skill in directly**, which gives you the plain `/wrap-up` command:

```bash
git clone https://github.com/manavpurswani/claude-wrap-up
mkdir -p ~/.claude/skills
cp -R claude-wrap-up/skills/wrap-up ~/.claude/skills/
```

Restart Claude Code after installing.

## Use

At the end of a session worth resuming:

```
/keepsession:wrap-up
```

(If you copied the skill in directly instead of installing the plugin, the
command is the plain `/wrap-up`.)

Or just say "wrap up this session" or "write a handoff". Then, in the next
session, paste the prompt it gave you.

Add notes to steer it, for example
`/wrap-up emphasize the auth bug we didn't fix`.

**When not to use it:** after a small, self-contained fix. One entry per quick
task turns the log into noise. It's for sessions with real ground covered,
course corrections, or loose ends.

## Requirements

- Claude Code
- A git repository. It stops and tells you if there isn't one, because a log
  that isn't version-controlled has nowhere durable to live.
- Shell access, as in Claude Code. In a chat with no repo and no shell, it
  says so and stops.
- Optional: `python3` (for the secret scanner and verifier; without it Claude
  does the checks by reading) and the `gh` CLI (only if you ask it to look up
  whether a repo is public).

## Try it

No account or setup needed: open any git repository in Claude Code after
doing some work, and try one of these.

- `/keepsession:wrap-up`
- `wrap up this session, and emphasize the bug we didn't fix`
- `write a dev log entry and a handoff for the next session`

## Privacy and support

wrap-up collects nothing and has no server. Everything it writes goes into
your own repository, and the scripts only read the files they are given.
Questions, bugs and security concerns:
[open an issue](https://github.com/manavpurswani/claude-wrap-up/issues).

## What it runs, reads and sends

Everything is local and visible in this repo. There is no telemetry and no
server.

- **Writes:** only `docs/dev-log/` and `HANDOFF.md` in your repo, plus
  temporary drafts in a system temp folder that it deletes afterwards.
- **Reads:** your repo's git state and its recent dev-log entries and
  `HANDOFF.md`. It does not read Claude's memory, your chat history, or your
  `CLAUDE.md` files.
- **Runs:** `git` (status, log, diff, remote), and your own commit only after
  you approve it. It never pushes. It also runs two bundled Python scripts,
  `scripts/scan.py` and `scripts/verify.py`, which only read the files they
  are pointed at.
- **Network:** none. If you ask it to look up whether a repo is public, it
  runs `gh repo view` on your behalf; otherwise it just asks you. Nothing from
  your session is sent anywhere.

## What's in this repo

```
skills/wrap-up/
  SKILL.md                    the instructions Claude follows
  scripts/scan.py             secret and personal-detail scanner, run before saving
  scripts/test_scan.py        its tests (python3 -I scripts/test_scan.py)
  scripts/verify.py           checks the saved files, incl. that the log stayed append-only
  scripts/test_verify.py      its tests (python3 -I scripts/test_verify.py)
  assets/dev-log-readme.md    copied into docs/dev-log/README.md on first run
  assets/handoff-template.md  the shape of HANDOFF.md
.claude-plugin/               plugin and marketplace manifests
```

## License

MIT
