# Systema Naturae — agent entry point

This file exists so that any agent/assistant tool — not just ones that look
for `CLAUDE.md` specifically — has somewhere to start. The repo's real
instructions live in [`CLAUDE.md`](CLAUDE.md): project rules, policy
decisions (no LLM-generated taxonomy content, the bacteria/viruses hold,
the six-kingdom build), architecture, and commands. **Read it before doing
anything else here.** This file does not duplicate it — it just makes sure
you find it.

Second stop: [`docs/INDEX.md`](docs/INDEX.md), which tracks every doc in
`docs/` with a status (active/superseded/obsolete/historical) so you don't
build on a plan that already shipped or a snapshot that's gone stale.

## About to run or extend the import pipeline?

Read [`docs/import.md`](docs/import.md) section 11 and
[`docs/dataset-inbox.md`](docs/dataset-inbox.md) **first**. The "manually
run" part of this pipeline is mostly just watching it — the hard parts
(discovery, transform, apply, dedup) are already automated by
`scripts/pipelineOrchestrator.py`. Twice now (2026-10-22, 2026-10-25) an
agent session re-discovered and re-queued datasets this repo already holds
or already declined, because it didn't check `scripts/sources.py`'s
`manifest.json` / `docs/dataset-inbox.md` before registering what looked
like a new source. Don't be the third. `scripts/sourceQueue.py add` now
catches the obvious cases (matching key, DOI, or title-word-overlap against
the manifest) but it's a backstop, not a substitute for actually reading
the history.

If you get partway into a task here and can't find documentation for
something that feels like it should be documented — stop and look harder
(`docs/INDEX.md`, then `grep -ri` across `docs/`) before writing new
scripts or new process. This is a heavily-documented repo; the gap is far
more likely in your search than in the docs.
