# Optional Windows tools (local 4070 train via AI-Toolkit)

Primary workflow: **train on 4090** (`train-a5000/cycle.sh`), test in Forge on 4070 or 4090.

These scripts are legacy helpers if you want to train locally on 4070 instead.

| Script | Purpose |
|--------|---------|
| `TRAIN_LORA.bat` | Ostris train on Windows |
| `SETUP_AI_TOOLKIT.bat` | Install ai-toolkit venv |
| `START_AI_TOOLKIT_UI.bat` | Toolkit web UI |
| `EXPAND_PAGEFILE_F.bat` | Pagefile for RAM-heavy FLUX train |
| `FIX_FLUX_LORAS.bat` | Copy LoRAs into Forge |
| `SETUP_SDXL_MODELS.bat` | SDXL model download helper |

See `LORA.md` for the main pipeline.
