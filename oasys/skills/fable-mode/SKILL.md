---
name: fable-mode
description: >
  Enforces staged execution discipline on large tasks: a written stage plan,
  parallel delegation where the runtime supports it, a failable verification
  check at each stage, and a skeptical self-review before delivery. Trigger
  when the user explicitly asks ("do this thoroughly", "be systematic",
  "deep work mode") OR when the task objectively spans multiple
  files, multiple sources, or multiple sessions. Do NOT trigger on ordinary
  multi-step requests that a direct attempt handles fine. For a run pinned to a
  specific model, use fable-opus, fable-sonnet, or fable-haiku instead.
  Operational guardrails (verify-before-flag, warning batching, sed safety)
  live in the companion execution-guardrails skill and apply on every model
  regardless of whether this loop runs.
---

# Fable Mode

This skill encodes execution discipline for complex work: decompose before acting,
delegate where the runtime allows, verify with checks that can fail, self-critique
before delivery.

A note on what this is. The skill shapes the *procedure* a model follows. It does not
change the model's underlying capability. Coherence across long tasks and genuine
self-correction live in the weights, not in a prompt. On a model that already does
these well, the skill reinforces good habits. On a weaker model, it imposes structure
the model would otherwise skip, but it cannot lift the model's reasoning ceiling. Treat
this as a checklist, not a capability transplant.

## When NOT to use this

If a task has one obvious correct approach and fits in a single pass, do it directly and
skip this loop. Staging a trivial task wastes effort and buries the answer under
ceremony. This loop earns its cost only when a one-shot attempt would plausibly miss
something.

## Calibrate to the model running it

The loop's value inverts with model strength. When no Fable/Mythos-class model is
available, Opus is the frontier tier and every escalation path below resolves to it.
The escalation ladder is: Haiku → Sonnet → Opus → back to the user. Apply the loop at
the right intensity:

- **Frontier-tier models (latest Opus; Fable/Mythos class where available).** These
  plan, verify, and self-correct natively. Do NOT narrate the loop or write a formal
  stage map for tasks the model would handle cleanly anyway — that is ceremony. Apply
  only: (a) the failable-check standard from step 3 when producing artifacts, and
  (b) everything in the execution-guardrails skill. Write a full stage map only for
  genuinely multi-session or many-file work. Opus's characteristic gaps: self-review
  that trusts its own introspection, and scope growth mid-run — hold the external-
  artifact standard and the replan budget even when the plan feels obviously right.
- **Sonnet-tier.** Run the full loop. Sonnet plans decently but reliably skips step 3 —
  the check that can fail — and substitutes "looks right" review. Enforce step 3 hardest.
- **Haiku-tier.** Run the full loop with tightened checks: every stage gets a failable
  check, no stage may be marked unverified without naming what check was impossible and
  why. Haiku under time pressure skips verification entirely; the loop exists to prevent
  exactly that. Accept that the ceiling is unchanged — Haiku with a checklist is still
  Haiku. Escalate to Sonnet or Opus rather than looping when the task needs synthesis
  the checks can't substitute for.

If the model cannot tell which tier it is, assume Sonnet-tier and run the full loop.

## Core Loop

The loop is constant across domains. Only the verification artifact in step 3 changes by
domain (see Domain-specific patterns).

**1. Stage map (before touching anything)**
Write out the full stage plan before starting. Number the stages. Include a brief
expected output for each. This is how you avoid discovering at stage 7 that you made a
wrong assumption at stage 2. Update the map when what you learn invalidates what you
planned. The map is a living document, not a contract.

Each stage should produce one verifiable artifact. If a stage produces nothing checkable,
merge it with the next.

**Replan budget.** A living document is not an excuse to churn. Allow at most two full
replans per run. If a third structural replan seems necessary, stop — the task is
ambiguous at the requirements level, not the execution level. Surface the ambiguity to
the user and get a decision before burning more stages. Renumbering or splitting a single
stage does not count as a replan; reordering or rewriting the map does.

Example format:
```
Stage 1: [Name] → [Expected output]
Stage 2: [Name] → [Expected output]
...
```

**2. Delegate independent work (if the runtime supports it)**
First check whether subagent/Agent tooling exists in the current runtime. If it does
not (for example, a plain chat surface with no Agent tool), run the stages sequentially
and proceed to step 3.

If subagent tooling is available and stage N and stage M don't depend on each other,
spawn them concurrently. Each subagent should be briefed with: its specific task, what
it should produce, where to save outputs, and any relevant context from prior stages.

**Tier routing.** When the Agent tool exposes a `model` parameter, match the worker
tier to the stage's difficulty, not to habit: Sonnet for stage work that needs real
reasoning, Haiku for bulk mechanical work, the orchestrating model itself only for
synthesis no cheaper tier can verifiably do. Routing down-tier cuts cost as well as
time — expensive tokens should buy judgment, not file-shuffling.

Good delegation: "research X while I do Y", "process these 3 files", "verify this
independently". Bad delegation: splitting a single coherent thought just to use
subagents.

Keep delegation one level deep by default: a spawned subagent runs its stages
sequentially rather than spawning its own subagents. Nesting multiplies cost and scatters
context — allow a second level only when a sub-part clearly needs its own fan-out.

**3. Verify with a check that can fail**
Each stage must define a pass condition that an external artifact satisfies. Acceptable
checks:
- a test that runs and passes
- a file or output that provably exists in the expected shape
- a source actually fetched and read, not assumed
- an output diffed against the stated spec

"I reviewed it and it looks right" is not a check. A model that would skip verification
will also pass its own introspection. If a stage genuinely has no failable check, say so
explicitly and mark its output as unverified so the gap is visible downstream.

The cost of catching an error at stage 3 is trivial; at stage 8 it is catastrophic.

If a fix at stage N invalidates a prior stage's output, re-run that stage's check before
continuing. The loop goes forward and backward.

**4. Self-critique before delivery**
Before presenting final output, read it as a skeptical reviewer would. Hunt for a real
weakness or limitation; if one exists, fix it or flag it to the user. If genuine checking
turns up nothing, say so plainly — do not manufacture a weakness to satisfy the ritual.
Step 3 is the check that can fail. Step 4 is the judgment call about what remains weak
after the check passes.

For high-stakes deliverables, and where the runtime supports subagents, spawn a fresh
verifier agent briefed only with the spec and the artifact — not your reasoning — and
have it run the checks cold. Fresh eyes cannot inherit your blind spots. A Haiku or
Sonnet verifier is usually enough; the checks are mechanical by design.

Verify-before-flag and warning batching rules for this step live in the
execution-guardrails skill and are mandatory.

---

## Domain-specific patterns

Each domain below is an instance of step 3: it names the failable check that fits the
work. The check must name the exact command, file, or comparison — "verified" without a
named artifact is a step-3 violation.

### Software engineering
- Read the entire relevant codebase section before writing a line. Failable check:
  list the files actually opened; any file the diff touches that isn't on the list is a
  gap.
- Write tests before (or alongside) implementation, not after.
- For large changes: plan the diff, then execute it.
- Failable check: named test command runs and passes; at least one error path exercised
  and its output shown, not just the happy path. A test suite that was never run does
  not count as passing.

### Research / knowledge work
- Gather sources before synthesizing. Do not write as you search.
- For each claim that matters: what's the evidence? what would falsify it?
- Distinguish confirmed facts from inferences; flag the latter explicitly.
- Failable check: every load-bearing claim maps to a source actually fetched and read
  in this run — URL or document named. A claim resting on training memory alone must be
  labeled as such. Absence of a web result is never itself a finding (see
  execution-guardrails and source-of-truth).

### Data analysis
- Understand the data shape before writing any analysis: row count, column list, and
  a sample printed, not assumed.
- State your hypothesis before computing, not after seeing the numbers.
- Failable check: quality assertions (null counts, duplicate keys, out-of-range values,
  total row count vs. source) run against the actual data with output shown. Any
  aggregate in the deliverable reconciles to a spot-checked raw slice — pick one
  subtotal and recompute it independently.

### Documents / spreadsheets / decks
- Build from the spec, then diff the artifact against the spec line by line.
- Failable check: open the produced file and read it back — every required section,
  number, and label confirmed present. For spreadsheets: subtotals recomputed from raw
  rows match the report; formats (currency, headers) spot-checked on the rendered file,
  not the generating code.

### Long-running / multi-session tasks
- Maintain a work log: decisions made, why, what was tried and failed.
- At the start of any continuation, re-read the work log before doing anything.
- Define done criteria upfront so you know when to stop.
- Failable check: done criteria are written and testable, not vibes; each continuation
  begins with a line confirming the log was re-read and naming any decision it changed.

---

## Operational rules

The always-on rules — verify-before-flag, the warning threshold, and find-and-replace
safety — now live in the companion **execution-guardrails** skill so they apply on every
model and every task, not only inside this loop. Follow them there. If that skill is
missing from the runtime, its three rules are restated in compressed form:

1. Never flag a problem that hasn't been confirmed present by a direct check. Absence of
   evidence is not the finding.
2. Batch minor concerns; at the threshold (default three, user-tunable), stop and surface
   all at once.
3. Anchor sed/substring replaces on word boundaries (`\bword\b`); grep for corrupted
   compounds after every pass.

---

## What this skill doesn't do

It doesn't make the underlying model smarter. Complex reasoning, novel synthesis, and
domain expertise still depend on the model. This skill shapes *how* a model works
through a problem: the approach, the discipline, the verification habits. It does not
change raw capability.

When a task is genuinely beyond the model's capability, flag it rather than producing
plausible-sounding wrong output. That flag must itself follow verify-before-flag: name
what was attempted and where it failed, not a vague appeal to difficulty. If a stronger
tier exists on the ladder, recommend it; at the top of the ladder, the gap goes to the
user.
