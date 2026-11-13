---
name: wrap-up
description: Writes a complete, permanent account of the current work session into the project's own git repo (docs/dev-log/), so nothing is lost to context compaction, a new session starting cold, or a summary that quietly drops something. Use this whenever the user runs /wrap-up, or says things like "wrap up this session", "write a dev log entry", "create a handoff", "document what we did before I close this", "save our progress", or otherwise signals they're about to end a session they'll want to resume later with full context. This is explicitly USER-TRIGGERED ONLY — never invoke it proactively based on context length, a sense that the session "feels expensive" to keep going, or any other self-assessment. Only run it when the user actually asks.
---

# Wrap-up: the session's permanent record

A long session accumulates real context that's expensive to rebuild: bugs
found and fixed, measurements taken instead of assumed, directions tried and
abandoned, decisions made in conversation that never produced a commit. None
of that is in the git log. Most of it isn't even fully in a chat summary,
because summaries compress, and compression is exactly the thing that loses
the detail someone will need later. This skill writes it all down, once, in
the one place that's never allowed to shrink: the project's own repo.

## The two-file design, and why it's shaped this way

A single file that gets overwritten each session has a real failure mode: if
one regeneration is incomplete, whatever it dropped is gone, with no way to
tell what's missing. The fix isn't writing more carefully — it's making the
loss structurally impossible. So there are two files with different jobs:

- **`docs/dev-log/YYYY-MM-DD-NN.md`** — the actual record. One file per
  wrap-up, **never touched again** once written. If a later entry turns out
  to be wrong about something, a newer entry corrects it; the old one still
  sits there as-is. This is what makes "nothing is silently lost" true rather
  than a promise.
- **`HANDOFF.md`** at the repo root — a short, regenerated index into the
  above. Safe to overwrite completely every time, specifically *because* the
  dev-log underneath it isn't going anywhere — if this file is ever thin or
  wrong, nothing is actually lost, it's just less convenient to find.

Keep that distinction in mind throughout: anything going into `HANDOFF.md`
should also be traceable back to the dev-log entry, never only live in the
regenerated file.

## Steps

### 1. Find the repo

Walk up from the current directory to the nearest `.git`. If there isn't one,
say so plainly and stop — `git rev-parse --show-toplevel` is the easy way to
check. This convention is per-repo on purpose: a dev log for work that isn't
version-controlled has no durable home to live in.

### 2. Set up `docs/dev-log/` if this is the first wrap-up in this repo

Check whether `docs/dev-log/` exists. If not, create it and copy
`assets/dev-log-readme.md` (from this skill's own directory) to
`docs/dev-log/README.md` verbatim — don't rewrite it, it's already tuned.
Create `docs/dev-log/INDEX.md` too, with just the line:

```
Append-only — add a line when a new entry is written, never edit an existing line.
```

### 3. Pick the filename

Look at today's date and scan `docs/dev-log/` for existing
`YYYY-MM-DD-*.md` files from today. Use the next unused number
(`YYYY-MM-DD-01.md` if none exist yet today, `-02` if `-01` is already
there, and so on).

### 4. Read before writing

Before drafting the new entry, read what already exists so the entry adds to
it rather than repeating it:

- The repo's `HANDOFF.md`, if it exists — it has the last known status.
- The most recent 2-3 dev-log entries (or all of them, if there are fewer
  than five total) — enough to know what's already on the record, so this
  entry can say "since the last entry" instead of re-deriving the whole
  project from scratch.
- The actual git state: `git status`, `git log --oneline` (recent history),
  `git remote -v`, and whether the current branch has an upstream and is
  actually pushed (`git rev-list --left-right --count HEAD...@{u}` if there
  is one). **Report what's actually true, not what seems likely.** A repo can
  look fully committed while a prior session's work is still sitting
  uncommitted, or a remote can simply not exist — both are exactly the kind
  of thing this skill exists to catch and say out loud rather than assume
  away.

### 5. Write the entry

This is the part worth taking real time over — thin entries defeat the whole
point. Write `docs/dev-log/YYYY-MM-DD-NN.md` covering, as applicable to what
actually happened this session:

- **What changed**, concretely — real file paths, not just "updated the
  auth logic." Someone (or some future session) should be able to go
  straight to the right file from this description alone.
- **Why**, wherever the reasoning isn't obvious from a diff: a bug that was
  found and what actually caused it, a number that was measured rather than
  guessed, a tradeoff that was chosen over an alternative and why that one
  won.
- **Decisions that didn't produce code** — a direction that was proposed and
  ruled out, a question that got a real answer, a constraint that was
  discovered. These are exactly the things a `git log` can never show and a
  casual summary tends to drop first.
- **What's still open** — bugs not fixed, code paths that exist but were
  never actually exercised, anything deferred on purpose, with the reasoning
  for deferring it (not just "TODO").
- **What got discussed but not resolved.** A half-finished conversation
  about direction is real, valuable context — don't drop it just because it
  didn't land anywhere in the code yet.
- **The git state from step 4, reported honestly** — including anything
  concerning (uncommitted work of real size, no remote configured, a branch
  that's diverged from where it's supposed to merge).

Write as much as the session actually warrants. A long, eventful session
earns a long entry — compressing it for brevity defeats the one job this
file has. A short, narrow session earns a short entry; don't pad one out to
look thorough. Never go back and edit a previous entry to add something that
was missed — write a new one instead, even if it's small.

### 6. Update the index

Append one line to `docs/dev-log/INDEX.md` — a 2-4 sentence summary of the
new entry, enough that someone scanning the index can tell if it's the one
they need without opening every file.

### 7. Regenerate HANDOFF.md — including an actual continuation prompt

Use `assets/handoff-template.md` as the shape (not a rigid fill-in-the-blanks
— adapt it, but keep the parts: a short status paragraph, an immediate
next-step list, a pointer to the latest dev-log entry, **and the
continuation prompt described below**). Keep the surrounding material brief
— its whole job is orientation, with the real detail living in the entry it
points to. If the git audit in step 4 turned up something that needs
attention before anything else (uncommitted work at real risk, no remote),
say so plainly near the top rather than burying it in the status paragraph.

**The continuation prompt is not optional, and it is not the status
paragraph restated.** The point of this whole skill is starting a *new*
session cheaper than continuing a long one — that only works if there's an
actual block of text to paste as the first message in that new session. Put
it in its own clearly marked section, in a fenced code block so it's
trivially copyable, written as something someone would literally send, not
as documentation about the project:

```
Continue work on <repo/project name>. First read HANDOFF.md at the repo
root, then docs/dev-log/<latest entry filename> — don't re-derive context,
it's already written down.

<The one thing — if there is one — that genuinely needs a decision before
anything else happens. State it as a real, specific question, not "check
for issues." If nothing is blocking, say so explicitly instead of omitting
this: "Nothing is blocking — pick up with next-step 1 below.">

Then: <the single most likely next action, stated concretely>.
```

Fill this from what you actually just wrote in steps 5-7 — it should name
the real next step and the real open question for *this* repo, not a
generic template. A continuation prompt that doesn't orient someone with
zero other context is the one thing this step cannot afford to get wrong.

### 8. Tell the user what happened

Report back concisely: what was written and where. If the git audit found
anything worth knowing — meaningful uncommitted work, no remote, a branch
not actually merged where it looks like it should be — say that out loud in
the conversation too, not only in the file. That's exactly the kind of thing
someone shouldn't have to go looking for.

**Also show the continuation prompt directly in the chat response**, not
only inside `HANDOFF.md` — the person who just ran this skill is often the
one who wants to copy it right now, and making them go open a file for the
one thing they'll need in sixty seconds defeats the purpose.
