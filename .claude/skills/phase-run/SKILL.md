---
name: phase-run
description: Execute exactly one pumplab build phase end to end (read status, build, test, report, commit). Use when the owner says "/phase-run N", "start phase N", "continue the phase" or "what's next".
argument-hint: "[phase-number]"
effort: high
---

# Run one pumplab phase

Target phase: $ARGUMENTS (if empty, read `README.md` status and pick the first phase not done).

## 1. Orient (always)
- Read `README.md` (status), `docs/BUILD_BRIEF.md` (the phase's scope and "done when"),
  `docs/assumptions.md`, and the previous phase report in `docs/phase-reports/`.
- `git pull --rebase` first. Run `uv run pytest -q`; if anything fails, fix that before new work.
- If the previous phase's "done when" is not met, stop and tell the owner what is missing.

## 2. Plan (short)
State in 3-6 bullets what you will build in this phase and which files. If anything needs
the owner (money, a signup, a decision that can't be undone, a key), ask ONE question and
stop. Otherwise continue without waiting.

## 3. Build
- Tests first for decoder, simulator, labeler math, risk manager and any PnL calculation.
- Only dependencies in `pyproject.toml`. Never third-party bot code. Never read `.env` or keys.
- Every on-chain number used comes from the data or `docs/assumptions.md` (with source + date).
- For long jobs (labeling, backtests) run them in the background and check results with real
  numbers; never estimate a result you can compute.

## 4. Independent check
For Phase 3 (simulator), Phase 4 (strategy results) and anything touching money or risk,
ask the `reviewer` subagent to review the diff and results before you call the phase done.
Fix what it finds or explain in the report why not.

## 5. Report and hand off
- Write `docs/phase-reports/phase-N.md`: built, results with numbers, open issues, next step.
- Update the status table in `README.md`.
- Commit (`Phase N: <summary>`) and `git push`.
- Reply to the owner in at most 8 lines: what's done, the key numbers, the one thing
  they need to do or decide (if any).

Stop at the phase boundary. Never start the next phase in the same run.
