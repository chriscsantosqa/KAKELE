# First use checklist

## Objective
Use the software for the first time with the lowest possible risk.

This checklist is intended for:
- initial operator validation
- environment preparation
- first calibration
- first controlled execution
- go/no-go decision

---

## Supported baseline for first validation
Before first use, freeze one baseline only.

Fill this before running:
- Operating system: __________________
- Monitor resolution: __________________
- Windows DPI/scaling: __________________
- Game window mode: __________________
- Game resolution: __________________
- Game UI scale: __________________
- Keyboard layout: __________________
- Selected profile: __________________
- Selected preset: __________________

Rule:
Do not validate multiple environments at the same time.

---

## Pre-run environment checklist
Mark each item before opening the bot.

- [ ] Game opens correctly
- [ ] Correct account/character is selected
- [ ] Game window is visible and not minimized
- [ ] Game window resolution matches the planned baseline
- [ ] Windows scaling/DPI is the expected one
- [ ] Keyboard layout is the expected one
- [ ] No other application is stealing the same hotkeys
- [ ] Operator knows the emergency stop hotkey
- [ ] Operator knows how to close the app safely

If any item fails, do not continue.

---

## App startup checklist
After opening the app:

- [ ] App starts without crash
- [ ] Main window renders correctly
- [ ] Selected profile is visible
- [ ] Current preset is visible
- [ ] Buttons are clickable
- [ ] No immediate error is shown in output/log area

If startup fails, stop and fix before testing runtime behavior.

---

## Profile validation checklist
Before calibration:

- [ ] Correct profile is selected
- [ ] Hotkeys are filled
- [ ] Healing thresholds are filled
- [ ] Polling/cooldown values are filled
- [ ] Combat options are coherent with the intended playstyle
- [ ] Continuous mode is intentionally on or off

Blocking rule:
Do not test with partially empty hotkeys or inconsistent combat settings.

---

## First calibration workflow
Run exactly in this order.

### Step 1 - Load or choose profile
- [ ] Load the profile that will be tested
- [ ] Confirm profile name shown in UI

### Step 2 - Adopt baseline
- [ ] Open the game in the intended window state
- [ ] Click `Adopt current window as baseline`
- [ ] Confirm the app reports the current resolution correctly

Expected result:
The profile baseline now matches the current game window.

### Step 3 - Refresh preview
- [ ] Click `Refresh ROI/OCR preview`
- [ ] Confirm preview refresh does not fail
- [ ] Confirm life/mana/target areas show meaningful data

### Step 4 - Adjust ROI if needed
- [ ] Adjust life ROI if the crop is wrong
- [ ] Adjust mana ROI if the crop is wrong
- [ ] Adjust target ROI if the crop is wrong
- [ ] Refresh preview after each relevant change

### Step 5 - Save ROI calibration
- [ ] Click `Save ROI calibration`
- [ ] Confirm save succeeded

### Step 6 - Save calibration snapshot
- [ ] Click `Save calibration snapshot`
- [ ] Confirm snapshot was created

Expected result:
You now have a reproducible calibration state for the current baseline.

---

## Preview acceptance criteria
Do not proceed to session execution unless these are true:

- [ ] Resolution validation says the current window matches the profile
- [ ] Life ROI is positioned correctly
- [ ] Mana ROI is positioned correctly
- [ ] Target ROI is positioned correctly or intentionally accepted
- [ ] Life OCR is not obviously broken
- [ ] Mana OCR is not obviously broken
- [ ] Target status is understandable

If OCR is empty or unstable:
- recheck resolution
- recheck ROI crop
- recheck in-game UI scale
- recheck visual contrast and game state

---

## Session control checklist
Before first live execution:

- [ ] Start button works
- [ ] Pause button works
- [ ] Resume button works
- [ ] Stop button works
- [ ] Global start/stop hotkey works
- [ ] Global pause/resume hotkey works

Blocking rule:
Do not run longer tests if stop and pause were not validated first.

---

## Controlled first run
Run the first test in a short and controlled window.

Recommended first run:
- duration: short
- operator watching continuously
- no multitasking during the run
- stop immediately on unexpected behavior

Checklist:
- [ ] Session starts without crash
- [ ] Status changes correctly
- [ ] Diagnostics update during execution
- [ ] No repeated obvious wrong action occurs
- [ ] Pause works during execution
- [ ] Resume works during execution
- [ ] Stop works immediately

---

## Post-run validation
After first run:

- [ ] Output/log area contains useful messages
- [ ] No unhandled error occurred
- [ ] OCR values looked plausible during the run
- [ ] Target detection behavior looked plausible
- [ ] Healing behavior looked plausible
- [ ] Combat behavior looked plausible for the selected preset
- [ ] No unsafe repeated key spam occurred

Record findings:
- Observed issue: __________________
- Expected behavior: __________________
- Suspected cause: __________________
- Reproducible? Yes / No

---

## Go / no-go decision

## GO when all are true
- [ ] Startup is stable
- [ ] Calibration can be completed
- [ ] Preview is coherent
- [ ] Stop/pause/resume work
- [ ] First short run is stable
- [ ] No blocker bug was observed

## NO-GO when any are true
- [ ] App crashes
- [ ] Resolution validation is inconsistent
- [ ] OCR is unusable
- [ ] ROI cannot be calibrated reliably
- [ ] Stop/pause fails
- [ ] Runtime behavior is unsafe or clearly incorrect

---

## Minimum blocker list before broader use
These are blockers for wider usage:
- startup crash
- corrupted profile save/load
- non-working stop command
- baseline adoption failure
- persistent resolution mismatch on correct environment
- unusable preview/OCR in the baseline environment

---

## Recommended first operator report
After the first controlled usage, record:
- environment used
- profile used
- preset used
- whether calibration succeeded
- whether session controls worked
- whether OCR was stable
- whether runtime actions were acceptable
- blocker bugs
- non-blocker improvements

---

## Next action after first use
Choose only one path:

### If GO
- keep the same baseline
- run a second controlled session
- log defects only
- avoid new refactors

### If NO-GO
- fix only blockers
- retest the same baseline
- do not expand scope yet

---

## Practical rule
For now, stability is more valuable than feature expansion.

Do not add new broad functionality before the first baseline is proven usable.
