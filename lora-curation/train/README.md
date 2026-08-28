# Обучение style LoRA `gf_lowpoly` (Flux) на RTX 4070 12GB

Датасет: `lora-curation/export/approved/` — только **approve** после curation на **Flux fp8** (тот же стек, что генерация).

Конфиг: [`gf_lowpoly_flux_4070.yaml`](gf_lowpoly_flux_4070.yaml)  
Base: `black-forest-labs/FLUX.1-dev` (Ostris AI-Toolkit, qfloat8).

## Когда 64 approve

```bat
python lora-curation\export_dataset.py --caption-mode train
TRAIN_LORA.bat
```

LoRA: `F:\fluxGenerationForLora\ai-toolkit\output\gf_lowpoly\` → скопировать `.safetensors` в Forge `models\Lora\`.

Проверка в Forge (не в curation-батче): `<lora:gf_lowpoly:0.9>, gf_lowpoly, …` на `flux1-dev-fp8`.

## Git

| В репо (git) | Локально, не коммитить |
|---|---|
| `train/gf_lowpoly_flux_4070.yaml`, `export_dataset.py`, `TRAIN_LORA.bat` | `lora-curation/images/`, `ratings.json`, `export/approved/` |
| `style.py` (trigger `gf_lowpoly`) | `ai-toolkit/output/`, обученные `.safetensors` |

SDXL-конфиг `gf_lowpoly_sdxl_4070.yaml` — черновик эксперимента, **не использовать**.

## Если прошлая `gf_lowpoly` не дотянула

1. **Датасет** — только строгие approve; без SDXL/Q6_K картинок; один стиль (dual LoRA curation).
2. **Captions** — export пишет `gf_lowpoly, <промпт без LoRA-тегов>`. В тексте остаются `ningraphix, ps1 game screenshot` — это норм для style, но если шум — режь вручную или попроси упростить export.
3. **Steps** — попробуй checkpoint **1000** и **1500** (`save_every: 250`), не только последний.
4. **Rank** — при слабом стиле можно `linear: 32` (больше VRAM/RAM).
5. **Не смешивать** approve с разных base (Flux fp8 only).

## Параметры (4070 12GB)

| | |
|---|---|
| Base | FLUX.1-dev (HF) |
| Resolution | 512 |
| Steps | 1500 |
| LR | 1e-4 |
| Network | LoRA 16/16 |

Закрой Forge перед train. При OOM по RAM: `EXPAND_PAGEFILE_F.bat` (админ), reboot.
