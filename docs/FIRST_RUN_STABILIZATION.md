# First-run stabilization workflow

## Objective
Guide the first real usage round after the current implementation phase.

This document exists to keep the next phase focused on:
- real defects
- reproducible evidence
- blocker isolation
- stabilization decisions

## Current rule
Do not expand scope before the first controlled usage round is completed.

Use the software in one baseline only.
Fix only what is proven to block or degrade that baseline.

## First-run sequence
Execute in this order:
1. Follow `docs/OPERATIONAL_READINESS_PACKAGE.md`.
2. Complete `docs/FIRST_USE_CHECKLIST.md`.
3. Run one short observed session.
4. Register every defect using the first-run bug template.
5. Classify each defect.
6. Fix blockers first.
7. Re-run on the same baseline.

## Severity classification

### Blocker
Use `Blocker` when any of the following happens:
- app crash
- UI freeze during core operation
- start, pause, resume, or stop does not work
- baseline adoption fails on the validated environment
- preview is unusable on the validated environment
- ROI calibration cannot be saved reliably
- runtime behavior is unsafe or clearly wrong

### High
Use `High` when:
- AI analysis is available but frequently misleading on the validated baseline
- OCR is unstable but still partially usable
- ROI suggestions are regularly poor but workaround exists
- messages are too weak to support diagnosis

### Medium
Use `Medium` when:
- friction exists but controlled usage is still possible
- comparison/history output is unclear
- visuals need polish but the core behavior works

### Low
Use `Low` when:
- cosmetic issue only
- wording issue only
- layout issue without operational impact

## Triage decision
For each defect, answer:
- Can the operator continue safely?
- Can the defect be reproduced?
- Does it happen only in the chosen baseline or everywhere?
- Is there a workaround?
- Does it affect runtime control, calibration, or diagnosis?

## Fixing order
Always fix in this order:
1. Stop/pause/resume/start failures
2. Crash and freeze
3. Resolution/baseline mismatch
4. Preview/OCR calibration failures
5. Runtime action errors
6. AI diagnosis quality issues
7. Non-blocking UX improvements

## Evidence required for each defect
Minimum evidence:
- baseline used
- profile used
- preset used
- steps to reproduce
- expected result
- actual result
- preview state
- AI analysis state if relevant
- screenshot or snapshot if available

## Retest rule
After a fix:
- retest the same baseline first
- do not switch environment during retest
- confirm whether the issue is resolved, reduced, or unchanged

## Exit criteria for stabilization phase
The phase can be considered stable for that baseline when:
- no blocker remains open
- preview is reliable
- ROI can be calibrated consistently
- start/pause/resume/stop are stable
- one short observed run and one follow-up run are acceptable

## Recommendation
At this point, new development should be driven by evidence from real usage, not by speculative expansion.