# Dev log — how this folder works

This is the **complete, append-only record** of work on this project across
Claude Code sessions. It exists because a long conversation eventually gets
summarized or a new session starts cold, and a summary — however careful — is
lossy by construction. This folder is the backstop: if something feels missing
from memory or from `HANDOFF.md`, it is not actually lost as long as it is
written here.

## The two files, and why they're different

**`HANDOFF.md`** (repo root) is a snapshot: where things stand right now, what
to do next. It gets **regenerated** at the end of a work session — overwritten,
not appended to. That's safe specifically *because* this folder exists: if a
regeneration ever drops something, the full history is still sitting here,
unaffected. `HANDOFF.md` is a convenience, not the record.

**`docs/dev-log/YYYY-MM-DD-NN.md`** (this folder) is the record. One file per
work session (NN increments if there's more than one in a day). **A dev-log
entry is never edited after the session it describes ends.** If something was
wrong or incomplete, a later entry corrects it — the old one stays as-is,
because that's what makes "nothing is silently lost" actually true rather than
a promise. `INDEX.md` is a one-line-per-entry list, also append-only.

**One exception:** if a secret (an API key, a token, a password) or a private
personal detail ever lands in an entry, it is removed in place and replaced
with `[redacted: what it was]`, and a newer entry records that this was done.
The log's purpose is to preserve context, not to hold credentials. Git history
still contains the old text, so anything that was pushed should be treated as
exposed and rotated.

## What goes in an entry

Not a chronological transcript — a complete account, organized for someone
(human or AI) who needs to pick the work back up with full context:

- **What changed**, specifically enough to find it in the code (file paths,
  not just descriptions)
- **Why**, when the reason isn't obvious from the diff — a bug that was fixed,
  a tradeoff that was chosen, a thing measured rather than assumed
- **What was decided**, including decisions that didn't produce code — a
  direction ruled out, a question answered, a constraint discovered
- **What's still open** — bugs not fixed, paths not tested, things deferred on
  purpose with the reasoning for deferring
- **What was discussed but not resolved** — this matters as much as the rest.
  A half-finished conversation is real context that's easy to lose if it
  never produced a commit.

## When to write one

At the end of a substantial session — not after every small fix. Triggered on
request (`/wrap-up`), not self-assessed mid-session.

## Relationship to the global memory system

Claude's own cross-session memory (outside this repo) still holds durable
facts, preferences and decisions that apply across *all* projects — it isn't
replaced by this. This folder is project-local, git-tracked, and the complete
record for *this* codebase specifically; the global memory should stay a
curated index that points here for detail, not a duplicate of it.
