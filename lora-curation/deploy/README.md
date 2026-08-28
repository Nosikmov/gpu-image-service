# Deploy: Forge Flux curation on GPU server (4090)

Полная инструкция: **[`SERVER_4090.md`](../../SERVER_4090.md)** в корне репо.

Кратко:

```bash
bash lora-curation/deploy/setup_server.sh          # Forge + deps
# sync models with sync_models.sh from Windows
tmux → bash lora-curation/deploy/start_forge.sh   # :7860 API
tmux → bash lora-curation/deploy/run_curation.sh  # generate + :8765 reviewer
python3 lora-curation/export_dataset.py --caption-mode train
bash train-a5000/sync_dataset.sh
cd train-a5000 && ./bootstrap.sh
```

## Скрипты

| Файл | Назначение |
|------|------------|
| `setup_server.sh` | apt, clone Forge, `webui-user.sh` |
| `start_forge.sh` | запуск Forge с `--api --listen` |
| `run_curation.sh` | build_prompts → generate → reviewer |
| `sync_models.sh` | rsync Flux fp8 с домашнего ПК |
| `webui-user.sh` | копируется в корень Forge |

## Модели (Flux)

См. `lora-curation/forge_gen.json`:

- `flux1-dev-fp8.safetensors`
- `ae.safetensors`, `clip_l.safetensors`, `t5xxl_fp8_e4m3fn.safetensors`
- `gf_lowpoly.safetensors` (опционально, для генерации на v1 LoRA)

## Порты

- `7860` — Forge (лучше только localhost / SSH tunnel)
- `8765` — reviewer
