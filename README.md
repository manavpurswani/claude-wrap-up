# wrap-up

A Claude Code skill for ending a long session without losing anything.

Run `/wrap-up` before you close a session you'll want to come back to. Claude
writes down everything that happened (what changed, why, what was decided,
what's still broken) into your project's own git repo, checks what's actually
committed and pushed, and hands you a short prompt to paste into the next
session so it starts with full context instead of from zero.

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

1. Reads the existing handoff and recent log entries, so it adds to the
   record instead of repeating it.
2. **Audits git for real:** uncommitted work, missing remotes, unpushed
   branches, branches that look merged but aren't. It reports what's true,
   not what seems likely.
3. Writes the new entry: concrete file paths, the reasoning behind non-obvious
   changes, decisions that never produced code, open bugs, and conversations
   that didn't resolve.
4. Adds one line to `docs/dev-log/INDEX.md`.
5. Rewrites `HANDOFF.md`, including a **continuation prompt**: a block of text
   you paste as the first message of your next session. It names the one
   question that needs answering first (or says nothing is blocking) and the
   concrete next step.
6. Shows you that prompt in chat, so you don't have to go and open a file.

It only runs when you ask. It never triggers itself because a session "feels
long".

## Install

**As a plugin** (inside Claude Code):

```
/plugin marketplace add manavpurswani/claude-wrap-up
/plugin install wrap-up@claude-wrap-up
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
/wrap-up
```

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

## What's in this repo

```
skills/wrap-up/
  SKILL.md                    the instructions Claude follows
  assets/dev-log-readme.md    copied into docs/dev-log/README.md on first run
  assets/handoff-template.md  the shape of HANDOFF.md
.claude-plugin/               plugin and marketplace manifests
```

## License

MIT
