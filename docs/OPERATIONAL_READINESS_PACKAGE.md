# Operational readiness package

## Objective
Consolidate the current path for controlled first usage.

## Current supported flow
- profile configuration
- ROI editing
- ROI/OCR preview refresh
- baseline adoption from current game window
- calibration snapshot save
- AI visual analysis from the UI
- AI ROI suggestion application with confirmation
- AI analysis history persistence and comparison

## Use only one baseline first
Fill before broader usage:
- Operating system: __________________
- Monitor resolution: __________________
- Windows scaling/DPI: __________________
- Game window mode: __________________
- Game resolution: __________________
- Game UI scale: __________________
- Keyboard layout: __________________
- First supported profile: __________________
- First supported preset: __________________

Rule:
Do not validate multiple environments at the same time.

## Required documents
- `docs/FIRST_USE_CHECKLIST.md`
- `docs/GPT_VISION_SETUP.md`
- `docs/USAGE_READINESS_AND_GPT_VISION_AGENT.md`

## First controlled usage flow
1. Prepare the environment.
2. Open the application.
3. Click `Adopt current window as baseline`.
4. Click `Refresh ROI/OCR preview`.
5. Adjust ROI if needed.
6. Click `Save ROI calibration`.
7. Click `Save calibration snapshot`.
8. Click `Analyze current screen with AI`.
9. Review summary, issues, detections and suggested ROIs.
10. Apply ROI suggestions only with confirmation.
11. Validate Start, Pause, Resume and Stop.
12. Run one short observed session only.

## AI usage rule
Use AI for:
- screen diagnosis
- ROI suggestion
- OCR troubleshooting
- screen state interpretation

Do not use AI as the main real-time execution loop.

## GO
Proceed with controlled usage only when:
- startup is stable
- preview is coherent
- ROI can be calibrated reliably
- stop and pause work
- the short observed run is acceptable

## NO-GO
Do not broaden usage when:
- the app crashes
- preview is unreliable in the chosen baseline
- stop or pause fail
- the session behavior is unsafe or incorrect

## Record after each run
- environment used
- profile used
- preset used
- whether preview was coherent
- whether AI analysis reported issues
- whether ROI suggestions changed the setup
- whether session controls worked
- blocker bugs
- non-blocker improvements

## Recommendation
The project is already viable for controlled first usage.
The correct direction now is stabilization, not deep refactoring.
