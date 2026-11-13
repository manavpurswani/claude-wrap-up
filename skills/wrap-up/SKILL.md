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
  wrap-up, **never touched again** once written (one exception: removing a
  leaked secret, see step 7). If a later entry turns out to be wrong about
  something, a newer entry corrects it; the old one still sits there as-is. This is what makes "nothing is silently lost" true rather
  than a promise.
- **`HANDOFF.md`** at the repo root — a short, regenerated index into the
  above. Safe to overwrite completely every time, specifically *because* the
  dev-log underneath it isn't going anywhere — if this file is ever thin or
  wrong, nothing is actually lost, it's just less convenient to find.

Keep that distinction in mind throughout: anything going into `HANDOFF.md`
should also be traceable back to the dev-log entry, never only live in the
regenerated file.

Because the dev-log is permanent, **whatever goes into it is permanent too.**
Everything below is written into git, and git history is very hard to take
back, especially once pushed. Step 7 exists for that reason, and it is the
step not to skip.

## Steps

### 1. Find the repo — or repos

Work out which git repos this session actually touched. Don't assume it's
only the current directory: look at the files edited and the commands run
during the session. `git rev-parse --show-toplevel` (or `git -C <path> ...`
for a repo outside the current directory) finds the root of each.

- **One repo:** carry on with that one.
- **More than one:** every repo that got real work gets its own full
  wrap-up — its own entry, its own `INDEX.md` line, its own `HANDOFF.md`,
  its own privacy check and its own git audit. Repeat steps 2-8 for each.
  The session is one conversation but the record lives per-repo, so a
  session that touched two repos and logged only one has silently lost half
  of itself. If it's unclear whether a repo counts (a one-line config
  tweak, say), ask rather than guess.
- **None:** say so plainly and stop. A dev log for work that isn't
  version-controlled has no durable home to live in.

Keep each repo's entry about *that repo*. Where the two are related, end the
entry with a short cross-reference by repo name and entry filename ("the
matching change in `<other-repo>` is `2026-11-12-01.md` there") so someone
reading one can find the other. Don't duplicate a whole account into both,
and never use absolute paths for the cross-reference.

**Mixed visibility is a trap.** If one repo is private and the other public,
nothing from the private one's entry — names, internal details, anything —
may leak into the public one's cross-reference. Name the sibling and say
what kind of change it was; stop there.

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
  away. A repo with **no commits yet** makes `git log` and the upstream
  comparison fail with `fatal:` errors. That's an answer, not a problem:
  record "no commits yet", skip the comparison, and note that the wrap-up
  commit in step 9 would be the repo's first.
- **Whether the repo is public.** Find out, don't guess:
  `gh repo view --json visibility,isPrivate` works when `gh` is installed
  and signed in. Otherwise judge from `git remote -v` (a GitHub, GitLab or
  Bitbucket remote with no way to confirm is *unknown*, not private). Record
  one of three answers: **public**, **private**, or **unknown / no remote
  yet**. Treat unknown exactly like public — the entry can't be assumed
  private, and a local-only repo is one `git remote add` + `git push` away
  from being published, history included.

- **The base commit.** `git rev-parse --short HEAD` and the branch name, taken
  now, before the wrap-up's own commit exists. HANDOFF records it so a later
  session can tell whether the repo has moved since (step 6). In a repo with
  no commits there is none; write "no commits yet".

  When you write the git state into the entry, strip any credentials out of
  a remote URL first (`https://user:token@host/...` becomes
  `https://host/...`).

  If the repo is public or unknown, also run the scanner (step 7) over the
  existing `docs/dev-log/` and `HANDOFF.md`. Entries written before this
  check existed may already hold something, and finding that out now beats
  finding out from a stranger. If it hits, see "Entries already in the log"
  in step 7.

Also gather the **standing rules** for step 6 now, while you're reading —
see there.

### 5. Draft the entry — outside the repo

This is the part worth taking real time over — thin entries defeat the whole
point. Write the draft of `docs/dev-log/YYYY-MM-DD-NN.md`.

**Write for a reader who will act on this with an empty context, and who
pays for every file they open.** The entry is complete, but it is organized
so they can stop reading early and still start in the right place. Open
with a **TL;DR** of 3-5 lines (what state things are in, the next step, the
biggest risk), then cover, as applicable to what actually happened:

- **Start here** — the 3-5 files (with function names or line ranges) the
  next session should open first to do the next step, one line of *why* each,
  and anything it can safely skip. This is the highest-value section for the
  next session: exploration is where a cold start burns its budget.
- **Commands that worked** — the exact build, test, run and deploy commands
  used this session and what they showed ("`npm test`: 41 passing"). Only
  what was actually run; mark anything you didn't verify as unverified. It
  lets the next session confirm the baseline in seconds instead of
  rediscovering how the project runs.
- **Tried and abandoned** — approaches that failed and *why*, so they aren't
  retried. (Decisions that never produced code belong here or under
  "decisions" below, whichever fits.)
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
  that's diverged from where it's supposed to merge). Report it *excluding*
  the wrap-up's own files: the entry can't truthfully say whether it has
  been committed, since step 9 happens after it's written. Don't claim
  either way.

Write as much as the session actually warrants. A long, eventful session
earns a long entry — compressing it for brevity defeats the one job this
file has. A short, narrow session earns a short entry; don't pad one out to
look thorough. Never go back and edit a previous entry to add something that
was missed — write a new one instead, even if it's small.

**Where to draft.** Put the drafts (this entry, the `INDEX.md` line, and the
`HANDOFF.md` from step 6) in a temporary directory outside the repo —
`mktemp -d` — not in `docs/dev-log/`. Nothing should touch the repo until
step 7 has passed.

### 6. Draft the index line and HANDOFF.md — including an actual continuation prompt

**The index line.** One line for `docs/dev-log/INDEX.md`, starting with the
entry's name (`2026-11-12-01: ...`) followed by a 2-4 sentence summary —
enough that someone scanning the index can tell if it's the one they need
without opening every file, and can find it once they do.

**HANDOFF.md.** Use `assets/handoff-template.md` as the shape (not a rigid
fill-in-the-blanks — adapt it, but keep the parts: a short status paragraph,
an immediate next-step list, a pointer to the latest dev-log entry, **and the
continuation prompt described below**). Keep the surrounding material brief
— its whole job is orientation, with the real detail living in the entry it
points to. If the git audit in step 4 turned up something that needs
attention before anything else (uncommitted work at real risk, no remote),
say so plainly near the top rather than burying it in the status paragraph.
Include a `Based on: <branch>@<short hash>` line (the base commit from step
4). Keep the whole file to roughly 60 lines and the continuation prompt to
about 15: every line of it is read at the start of every future session, so
detail that isn't needed *before* starting belongs in the entry, not here.

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

Standing rules for this work: <the rules from the paragraph below — or, if
there are none that apply, omit this line entirely>.

Before anything else, run `git status` and `git log --oneline <base hash>..HEAD`.
If the repo has moved in ways HANDOFF.md doesn't mention, tell me first.

Then: <the single most likely next action, stated concretely>.
```

That freshness check costs one command and catches the case where HANDOFF
is older than the repo (someone committed, another session ran, a branch
moved), which is exactly when trusting it blindly goes wrong. Omit it only
in a repo with no commits.

Fill this from what you actually just wrote — it should name the real next
step and the real open question for *this* repo, not a generic template. A
continuation prompt that doesn't orient someone with zero other context is
the one thing this step cannot afford to get wrong.

**Standing rules — pull them in, don't make the person retype them.** A new
session starts cold, and the rules someone has already stated are exactly
what it will get wrong first ("commit straight to main", "no co-author
trailer", "never push without asking"). Collect the ones that affect how
work gets done in *this repo* from:

- the repo's `CLAUDE.md` and the person's global `~/.claude/CLAUDE.md`,
- the memory index (`MEMORY.md`) and any feedback-type memories, if this
  session has them loaded or they sit in this project's folder under
  `~/.claude/projects/`,
- rules the person stated out loud during this very session.

Memory is stored **per project**, so a personal rule ("commit to main, no
co-author") may live only in a *different* project's memory and never reach
this one. If this project has no such rules but a sibling project's memory
holds an obviously personal, cross-project one (attribution, commit style),
don't silently apply it and don't silently skip it: ask once whether it
holds here too.

Include the ones that change what the next session would *do*: commit and
branch conventions, attribution and co-author lines, push and PR policy,
tooling or style constraints for this codebase. Keep it to a few lines,
paraphrased, each as a plain instruction. Leave out anything unrelated to
this repo, anything already obvious from the repo's own files, and anything
personal. Where sources disagree — a default attribution line versus the
person saying "no co-author" — the person's explicit rule wins; say that
rule, not the default.

These lines end up in a committed file, so they go through the step 7 check
like everything else. A rule that only makes sense by naming a private
detail gets stated without the detail.

### 7. Privacy check — before anything is saved

This is the most important step in the skill. Do not skip it, do not do it
after the files are in the repo, and do not wave it through because the
repo looks private.

**Run the scanner on every draft** — entry, index line, and HANDOFF:

```
python3 -I <this skill's directory>/scripts/scan.py <draft files...>
```

It flags credentials (API keys, tokens, private keys, passwords in URLs),
emails, phone numbers, and home-directory paths that expose an OS username.
Its output is masked on purpose. If `python3` isn't available, do the same
check by reading — the scanner is a convenience, not the requirement.

**Then read the drafts yourself for what a pattern can't see** — the scanner
is a regex, not a reader. Look for: real names of people who aren't already
public in the project, employer or client names, internal hostnames and
URLs, account or customer IDs, health, money, location or family details,
and anything from the conversation the person shared in confidence. Also
check that you didn't paste in anything from a `.env`, a config, or a
terminal where a secret was visible.

**What to do with each finding:**

| Finding | Public or unknown repo | Private repo |
|---|---|---|
| Credential / key / token (`secret`, `possible-secret`) | Remove. Refer to it by name ("the `STRIPE_KEY` env var"), never by value. | Same. Secrets don't belong in a log even a private one. |
| Email, phone, home path, personal detail | Remove, or generalize ("the maintainer's email", `~/project`). | Keep only if the entry genuinely needs it; otherwise generalize anyway. |

A redaction must not gut the entry. Replace the value, keep the fact: "the
deploy failed because `API_TOKEN` was expired" is useful, the token itself is
not. Never replace a secret with a "partially masked" copy — a half-shown
key is still a leaked key.

**If a real secret appears in the draft, it also appeared in the session** —
in a pasted log, a file read, a command. Tell the person plainly, by name
not value, that it should be treated as exposed and rotated. Do not just
silently scrub it from the log and move on.

Re-run the scanner after fixing. Only when it's clean (or every remaining
hit is something you've deliberately judged fine, such as a documentation
example) move to step 8. Tell the person what you redacted and why in the
final report; never redact silently.

**Entries already in the log.** "Never edited" has exactly one exception:
a secret or personal detail that has already landed in an old entry. Leaving
it in place just to keep the rule would be keeping the rule at the cost of
its purpose. So:

1. Tell the person what and where (file and line, never the value).
2. With their go-ahead, replace only the offending text in place with
   `[redacted: <what it was>]`, and touch nothing else in that file.
3. Say in the *new* entry what was redacted and why, so the edit is on the
   record.
4. Say plainly that **git history still holds the old text** (`git log -p`),
   and that a pushed secret should be treated as exposed and rotated.
   Rewriting history is the person's decision. Don't do it unasked.

### 8. Save the drafts

Copy the drafts into place: the entry to `docs/dev-log/YYYY-MM-DD-NN.md`,
the line appended to `docs/dev-log/INDEX.md`, and the handoff over
`HANDOFF.md`. Use the final scanned text — don't regenerate it.

Two mechanical details that have bitten: make sure `INDEX.md` ends in a
newline *before* appending (otherwise the new line glues onto the last one;
`tail -c1 docs/dev-log/INDEX.md` shows it), and delete the temporary draft
directory once everything is in place.

Then run the verifier from the repo root:

```
python3 -I <this skill's directory>/scripts/verify.py
```

It checks, mechanically, what this skill promises: no unfilled
`{{placeholders}}`, the entry is named correctly and appears in the index,
HANDOFF points at it and carries a fenced prompt that names it and a base
commit that exists, **no existing entry or index line was changed or
deleted** (except a `[redacted: ...]` replacement), and a final scanner pass
over everything written. Fix every `ERROR` before going on; a `WARN` is worth
reading but doesn't block. If `python3` isn't available, check those same
things by hand.

### 9. Offer to commit — just the wrap-up files

A log that exists only in a working tree can still be lost to a stray
`git checkout .`, a deleted folder, or a clone that never had it. So finish
by offering to commit it. **Offer; don't just do it.** Plenty of people have
rules about commits (branch policy, signing, no co-author lines, no commits
without review), and a wrap-up isn't a license to override them. Check the
standing rules you gathered in step 6 for commit conventions first and follow
them in the message and branch.

If they say yes:

0. **Check who the commit will be authored as.** A commit carries the git
   config email permanently. Compare `git config user.email` with the author
   of the repo's existing commits (`git log -3 --format=%ae`). In a public or
   unknown repo, if the repo's history uses a noreply address (or a different
   one) and the config would introduce a new, personal-looking address, stop
   and tell the person before committing: that email would be published with
   the history. Don't change their git config unasked; offer to commit with
   the address the repo already uses.
1. Confirm step 8's `verify.py` passed on the files exactly as they now sit
   in the repo; if anything has changed since, run it again. It includes the
   final scanner pass over what's actually about to be committed.
2. Stage only the wrap-up's own files:
   `git add -- docs/dev-log HANDOFF.md`
3. Commit with an explicit pathspec so anything else that happened to be
   staged is left alone (this is tested: an unrelated pre-staged file stays
   staged and out of the commit):
   `git commit -m "wrap-up: <short summary>" -- docs/dev-log HANDOFF.md`
4. Don't push. Say that it's committed locally and not pushed; pushing is a
   separate decision, and doubly so for a public repo.

If they say no, leave the files in place, and say plainly that the log is
currently uncommitted and not safe against loss. With more than one repo,
ask once for all of them, and commit each in its own repo. If a hook or an
unrelated problem makes the commit fail, report exactly what failed; don't
retry with the hook bypassed.

### 10. Tell the user what happened

Report back concisely: what was written and where, per repo. Say what the
privacy check found and changed, and whether the repo is public, private or
unknown. If the git audit found anything worth knowing — meaningful
uncommitted work, no remote, a branch not actually merged where it looks like
it should be — say that out loud in the conversation too, not only in the
file. That's exactly the kind of thing someone shouldn't have to go looking
for.

**Also show the continuation prompt directly in the chat response** — one
per repo if there were several — not only inside `HANDOFF.md`. The person who
just ran this skill is often the one who wants to copy it right now, and
making them go open a file for the one thing they'll need in sixty seconds
defeats the purpose.
