# Usage readiness and GPT vision agent analysis

## Objective
Move the project from active refactoring to a safe initial usage phase, with focus on:
- functional validation
- calibration workflow
- operator usability
- controlled rollout
- future AI-assisted screen analysis

---

## Recommended stop point for refactoring
At this stage, the best strategy is to stop large structural changes in `main_window.py` and shift to stabilization.

Reason:
- the UI has already been modularized into multiple panels
- the remaining cleanup is mostly cosmetic and low business value
- further deep refactoring now increases regression risk before first real usage

Recommended rule for now:
- no more broad refactors before first operator validation round
- only allow bug fixes, validation improvements, and usage blockers

---

## Path to initial usable release

### 1. Define a usage baseline
Create one default tested profile for the first supported scenario:
- one screen resolution
- one UI scale
- one keyboard layout
- one set of hotkeys
- one healing/combat preset

Goal:
Avoid supporting many combinations before validating one stable path.

### 2. Freeze supported environment for first release
Document the exact baseline:
- Windows version
- game window mode
- game resolution
- in-game UI scale
- recommended keyboard layout
- minimum monitor DPI/scaling

Goal:
Reduce false negatives caused by environmental drift.

### 3. Validate the calibration workflow end to end
Mandatory operator flow:
1. open app
2. select profile
3. adopt current window baseline
4. adjust ROI
5. refresh preview
6. save ROI calibration
7. save calibration snapshot
8. run session

Expected result:
A new user must complete this without touching JSON manually.

### 4. Run a blocker-oriented validation pass
Before first use, validate at least these cases:
- app starts without crash
- profile save/load works
- preset apply works
- ROI preview refresh works
- baseline adoption works
- snapshot save/load works
- session start/pause/resume/stop works
- hotkeys work
- invalid values are blocked with clear messages
- resolution mismatch is surfaced clearly

### 5. Create a first operator guide
The software should have a simple guide with:
- what to configure first
- what each main button does
- how to identify resolution mismatch
- how to recalibrate ROI
- how to recover from bad OCR
- how to stop safely

### 6. Establish a controlled rollout
Use staged rollout:
- developer local validation
- one controlled operator user
- small live usage window
- defect log
- stabilization fixes

Do not jump directly to broad usage.

---

## What should be developed next before broad usage
Priority order:

### Priority A - must have
- startup checklist / environment validation screen
- clearer inline validation messages
- first-run wizard for profile and calibration
- usage guide in repo and optionally in-app
- basic execution log export

### Priority B - strongly recommended
- profile duplication action
- backup/export/import profile
- reset ROI to profile defaults
- OCR confidence hints in preview
- clearer status badges for target detection and resolution state

### Priority C - later
- advanced presets by class/playstyle
- richer analytics/history
- automation recommendation layer
- AI-assisted calibration

---

## GPT paid vision agent - feasibility analysis

## Short conclusion
Yes, it is technically feasible to use a paid GPT multimodal agent as an assistant for:
- reading the game screen
- explaining what it sees
- helping calibrate ROI
- identifying bars, labels, icons, and buttons
- generating suggested config values
- troubleshooting bad OCR or bad target detection

But it should **not** be the primary real-time control loop for the bot.

Best use:
- calibration assistant
- setup assistant
- troubleshooting assistant
- offline/near-real-time visual analyzer

Worst use:
- frame-by-frame live combat control loop
- high-frequency decision loop
- direct replacement for deterministic OCR/template logic

---

## Recommended architecture

### Recommended model of use
Keep the bot core deterministic:
- capture window
- crop ROI
- OCR / image rules
- decision engine
- hotkey execution

Add GPT vision as a parallel assistant layer:
- receive screenshot or cropped images on demand
- analyze UI state
- explain what is on screen
- recommend ROI positions and thresholds
- suggest fixes when preview/OCR fails

### Architecture split

#### Layer 1 - deterministic runtime
Responsible for:
- screen capture
- OCR
- template/icon checks
- target validation
- healing/combat decisions
- hotkey execution

#### Layer 2 - GPT vision assistant
Responsible for:
- identify health/mana bars visually
- identify likely target area
- explain visible buttons or icons
- detect if wrong game screen is open
- help create/update profile values
- answer operator questions about current screen

---

## Why GPT vision should not control the live loop
Main reasons:
- latency
- API cost
- instability under frequent calls
- dependence on network/service availability
- non-deterministic output format unless heavily constrained
- harder debugging versus rule-based image logic

For this project, GPT is valuable as a supervisor and calibration assistant, not as the main loop.

---

## Best GPT-assisted features to implement

### 1. Screen diagnosis mode
User clicks `Analyze screen with AI`.
The app sends:
- full screenshot
- cropped ROIs
- current profile values
- current OCR texts
- resolution and UI scale

Expected answer from GPT in strict JSON:
- whether health bar seems correctly selected
- whether mana bar seems correctly selected
- whether target area seems correct
- whether the game screen matches expected state
- suggested ROI adjustments
- likely cause of failure

### 2. Guided calibration assistant
Flow:
- user captures screen
- GPT identifies likely bar/icon/button areas
- app translates that into suggested ratios
- user reviews and applies

Use case:
Speeds up first calibration.

### 3. OCR troubleshooting assistant
When OCR returns empty or unstable text:
- send original crop
- send processed crop
- send OCR result
- ask GPT what is wrong

Expected output:
- bad crop
- low contrast
- wrong scaling
- text too small
- wrong region selected
- suggested preprocessing direction

### 4. Visual state classifier
Use GPT to classify broader states such as:
- in combat
- menu open
- wrong window focused
- login screen
- configuration screen
- dead character / special event screen

This is useful for fallback diagnosis, not for every loop cycle.

### 5. Config generation assistant
Input:
- screenshot
- class/playstyle
- preferred hotkeys
- desired healing threshold

Output:
- starter profile recommendation
- suggested combat preset
- explanation of values

---

## How to implement safely

### Input contract to GPT
Always send structured payload:
- profile metadata
- screen metadata
- OCR result
- image purpose
- expected output schema

### Output contract from GPT
Force strict JSON fields such as:
- `screen_state`
- `health_bar_detected`
- `mana_bar_detected`
- `target_area_detected`
- `issues`
- `recommended_actions`
- `suggested_roi_ratios`
- `confidence`

### Human-in-the-loop
Never auto-apply changes silently.
Always show:
- current value
- suggested value
- reason
- apply/reject action

### Rate limiting
Do not call GPT continuously.
Trigger only on:
- manual analysis request
- failed preview
- repeated OCR failure
- first-run calibration wizard

---

## Practical implementation options

### Option A - simplest and best first step
Add a manual button in the app:
- `Analyze current screen with AI`

Behavior:
- capture screenshot
- send to backend/service with GPT vision
- receive structured analysis
- show result in dedicated panel

This is the best first implementation.

### Option B - calibration wizard with AI
On first run:
- user opens wizard
- app captures screen
- GPT suggests ROIs and explains them
- user confirms
- app saves profile

High value, medium complexity.

### Option C - automatic fallback assistant
If preview fails N times:
- app offers AI diagnosis
- user chooses whether to run it

Good for support and troubleshooting.

---

## Risks and constraints
- recurring API cost
- dependence on internet access
- privacy considerations if screenshots leave machine
- possible mismatch if game visuals change a lot
- output variability if schema is weak
- slower operator flow if overused

Mitigation:
- call only on-demand
- redact nonessential areas if needed
- keep deterministic core local
- cache diagnostic sessions when useful

---

## Recommended implementation order for GPT assistant

### Phase 1
- manual button for AI screen analysis
- send full screenshot + ROIs + OCR
- render structured diagnosis in UI

### Phase 2
- AI-assisted ROI suggestions
- apply suggestion with confirmation

### Phase 3
- first-run AI calibration wizard

### Phase 4
- optional visual state classification fallback

---

## Recommendation for this project right now
Do this now:
1. stop large refactors
2. stabilize first usable release
3. validate one baseline environment
4. add operator guide
5. add log export
6. after first usage, implement `Analyze current screen with AI`

Do not do this now:
- replace OCR loop with GPT
- build fully autonomous vision-driven runtime control
- support many environments before first stable baseline

---

## Final recommendation
The software is at the right point to shift from structural refactoring to controlled usability hardening.

The GPT paid vision assistant is feasible and valuable, but only as an auxiliary intelligence layer.

Best immediate direction:
- prepare first usable build
- validate in one real environment
- collect failures
- then add AI-assisted diagnosis and calibration
