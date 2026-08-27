# LoRA Style Curation (Forge + Flux)

Сбор style LoRA для **gameFarmling**: промпты low-poly / PS1 cat → Forge txt2img → оценка в браузере → экспорт approved.

Trigger word: **`gf_lowpoly`**

Стек генерации (как в ваших удачных PNG):

| Параметр | Значение |
|----------|----------|
| Model | `flux1-dev-fp8.safetensors` |
| LoRA | `Low_Poly_Papercraft:0.75`, `ningraphix:0.85` (в промпте) |
| Size | 512×512 |
| Steps | 20 |
| Sampler / Schedule | Euler / Simple |
| CFG / Distilled CFG | 1 / 3.5 |

Конфиг: [`forge_gen.json`](forge_gen.json). Промпты: [`promts-for-generate.txt`](promts-for-generate.txt) → `prompts.json`.

## Один файл (рекомендуется)

Дважды кликни **[`START_CURATION.bat`](../START_CURATION.bat)** в корне `gpu-image-service`.

Он поднимает Forge (если нужно), открывает http://127.0.0.1:8765/ и сам:
- генерирует недостающие картинки;
- при **Reject** перегенерирует (новый seed);
- подхватывает новые промпты из UI или из `promts-for-generate.txt`.

В UI: **A / R / M**, блок «Добавить промпт». Когда все approve →  

```bat
python lora-curation\export_dataset.py --caption-mode train
```

Обучение своей LoRA (`gf_lowpoly`) на RTX 4070: см. [`train/README.md`](train/README.md).

## Как передать промпты

1. Форма в UI («Добавить промпт»), или
2. Правка [`promts-for-generate.txt`](promts-for-generate.txt) (заголовок + строка промпта).

Авто-цикл сам пересоберёт `prompts.json` и сгенерирует картинку.

## Ручной режим

```bash
python lora-curation/build_prompts.py --variants 1
FORGE_URL=http://127.0.0.1:7860 python -u lora-curation/generate_batch_gpu.py --skip-existing
python lora-curation/serve_reviewer.py --host 127.0.0.1 --port 8765
python lora-curation/generate_batch_gpu.py --rejected-only
python lora-curation/export_dataset.py
```

## Развёртка на GPU-сервере

См. [`deploy/README.md`](deploy/README.md).

## Файлы

| Путь | В git |
|------|-------|
| `promts-for-generate.txt`, `prompts.json`, скрипты, `reviewer.html`, `forge_gen.json`, `auto_loop.py` | да |
| `images/`, `ratings.json`, `manifest.json`, `auto_status.json`, `export/` | нет |
