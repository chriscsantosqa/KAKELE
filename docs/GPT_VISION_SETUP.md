# GPT vision setup

## Implemented components
- `src/kakelebot/core/ai_vision.py`
- `src/kakelebot/infra/openai_compatible_vision_assistant.py`
- `src/kakelebot/core/session.py` visual analysis method
- `src/kakelebot/ai_diagnose.py` CLI command
- `settings.json` support for `ai_vision`

## Activation
Configure `settings.json` with an `ai_vision` section.

Example:

```json
{
  "runtime": {
    "debug": true,
    "log_level": "INFO",
    "active_profile": "default"
  },
  "ai_vision": {
    "enabled": true,
    "provider": "openai_compatible",
    "base_url": "https://api.openai.com",
    "endpoint_path": "/v1/chat/completions",
    "model": "FILL_MODEL_NAME",
    "api_key_env_var": "OPENAI_API_KEY",
    "timeout_seconds": 45.0,
    "allow_auto_apply_roi_suggestions": false
  }
}
```

## Environment variable
Set the key in the environment before running the command.

PowerShell example:

```powershell
$env:OPENAI_API_KEY="..."
```

## Command
Run:

```bash
kakelebot-ai-diagnose
```

## What it does
- captures the current game window
- captures life, mana and target ROI crops
- sends structured visual context to the configured AI provider
- prints JSON diagnosis with issues, suggested actions and suggested ROI values

## Recommended use
Use this for:
- screen diagnosis
- ROI suggestion
- OCR troubleshooting
- configuration help

Do not use this as the main real-time control loop.
