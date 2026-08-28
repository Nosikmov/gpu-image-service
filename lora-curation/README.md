# LoRA Style Curation (Forge + Flux fp8)

Сбор style LoRA для **gameFarmling**: промпты low-poly + hand-painted textures → Forge txt2img → оценка в браузере → экспорт approved.

Trigger word **`gf_lowpoly`**.  
**Генерация:** обученная LoRA `<lora:gf_lowpoly:0.9>` (или dual Papercraft+ningraphix на старом пайплайне).

| Параметр | Значение |
|----------|----------|
| Model | `flux1-dev-fp8.safetensors` |
| LoRA | `gf_lowpoly:0.9` |
| Encoders | `ae`, `clip_l`, `t5xxl_fp8_e4m3fn` |
| Size | 512×512 |
| Steps | 20 |
| Sampler / Schedule | Euler / Simple |
| CFG / Distilled CFG | 1.0 / 3.5 |

**GPU server (4090):** [`SERVER_4090.md`](../SERVER_4090.md) + [`deploy/README.md`](deploy/README.md).

Конфиг: [`forge_gen.json`](forge_gen.json). Промпты: [`promts-for-generate.txt`](promts-for-generate.txt) → `prompts.json`.

## Один файл (рекомендуется)

Дважды кликни **[`START_CURATION.bat`](../START_CURATION.bat)** в корне `gpu-image-service`.

Forge поднимается с `webui-user.bat` (Flux fp8 flags), reviewer http://127.0.0.1:8765/, auto-loop: missing + reject redo.

## Ручной режим

```bash
python lora-curation/build_prompts.py --variants 1
set FORGE_DIR=F:\fluxGenerationForLora\stable-diffusion-webui-forge
FORGE_URL=http://127.0.0.1:7860 python -u lora-curation/generate_batch_gpu.py --no-skip-existing
python lora-curation/serve_reviewer.py --host 127.0.0.1 --port 8765
python lora-curation/export_dataset.py --caption-mode train
```

Обучение LoRA: [`train/README.md`](train/README.md) + **`TRAIN_LORA.bat`** (Flux).
