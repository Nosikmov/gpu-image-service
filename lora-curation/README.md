# LoRA Style Curation

Сбор style LoRA для Reign of Devorio: 100 промптов → Comfy GPU → оценка в браузере → экспорт approved.

Репозиторий: **gpu-image-service**. Игровой репо эти скрипты не содержит.

Trigger word: **`gf_bestiary`**

## Быстрый старт

Из корня `gpu-image-service`:

```bash
python3 lora-curation/build_prompts.py          # при необходимости пересобрать prompts.json
python3 lora-curation/generate_batch_gpu.py --skip-existing --continue-on-error
python3 lora-curation/serve_reviewer.py --host 0.0.0.0 --port 8765
# http://127.0.0.1:8765/   A=approve  R=reject  M=maybe
python3 lora-curation/export_dataset.py
# → lora-curation/export/approved/
```

Или `bash lora-curation/start.sh`.

В игру (после оценки):

```bash
GAME_REPO=/opt/sites/gameFarmling python3 lora-curation/promote_to_game.py --approved-only
```

## Файлы

| Путь | В git |
|------|-------|
| `prompts.json`, скрипты, `reviewer.html` | да |
| `images/`, `ratings.json`, `manifest.json`, `export/` | нет |
