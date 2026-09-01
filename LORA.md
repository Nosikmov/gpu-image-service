# gf_lowpoly — LoRA pipeline

**4070 (Windows):** курация + экспорт  
**4090 (Linux):** обучение + быстрые тесты (Forge fp8)

---

## Launchers (минимум)

### Windows (4070)

| Файл | Действие |
|------|----------|
| `CURATE.bat` | Forge + reviewer :8765 |
| `EXPORT.bat` | approve → `train-a5000/dataset/` |
| `PUSH.bat` | scp датасета на сервер |
| `PULL_LORA.bat` | скачать LoRA с сервера в Forge |
| `STASH.bat` | архив картинок перед новым раундом |

### Linux (4090)

| Файл | Действие |
|------|----------|
| `train-a5000/cycle.sh` | train / test / setup-forge / round2 |
| `train-a5000/bootstrap.sh` | Ostris train (вызывается из cycle) |
| `lora-curation/deploy/setup_server.sh` | Forge + deps (один раз) |
| `lora-curation/deploy/start_forge.sh` | запуск Forge API :7860 |
| `lora-curation/deploy/sync_models.sh` | модели fp8 с ПК |
| `lora-curation/deploy/run_curation.sh` | batch + reviewer (round2) |

### Тесты на 4090

```bash
cd ~/gpu-image-service/train-a5000
chmod +x cycle.sh test_lora/run.sh

export TRAIN_NAME=gf_lowpoly_v2

./cycle.sh test forge          # 12 img, fp8, ~2-3 min
./cycle.sh test forge40        # 40 prompts
./cycle.sh test slow --limit 4 # diffusers fallback (~60s/img)
```

---

## Цикл

```
CURATE.bat → EXPORT.bat → git push / PUSH.bat
    → cycle.sh train → cycle.sh test forge → правки → repeat
```

### 1. Курация (4070)

```bat
CURATE.bat
```

Reviewer `http://127.0.0.1:8765/` — **A** approve (~40 шт).

Round 2 только своей LoRA:

```bat
set CURATION_MODE=trained
CURATE.bat
```

### 2. Экспорт

```bat
EXPORT.bat
```

### 3. На сервер

```bash
git pull
cd train-a5000
export HF_TOKEN=hf_...
export TRAIN_NAME=gf_lowpoly_v2
./cycle.sh train
```

### 4. Тест на 4090 (fp8)

Первый раз:

```bash
./cycle.sh setup-forge
# с ПК: bash lora-curation/deploy/sync_models.sh
tmux → bash lora-curation/deploy/start_forge.sh
```

```bash
./cycle.sh test forge
./cycle.sh test forge40
```

### 5. Забрать LoRA

```bat
PULL_LORA.bat
```

---

## Env

| Переменная | Где |
|------------|-----|
| `HF_TOKEN` | train на 4090 |
| `TRAIN_NAME` | `gf_lowpoly`, `gf_lowpoly_v2`, … |
| `FORGE_DIR` | `~/stable-diffusion-webui-forge` |
| `CURATION_MODE=trained` | round 2 курация |

---

## Промпт (Forge)

Bootstrap (как датасет v1):

```text
<lora:lowpoly_flux:0.9> <lora:OOTN64_Krea2:0.9>, gf_lowpoly, ps1 game screenshot, ...
```

После train:

```text
<lora:gf_lowpoly:1.0>, gf_lowpoly, ps1 game screenshot, extremely low-poly, chunky blocky mesh, ...
```

Forge: **flux1-dev-fp8**, **Automatic (fp16 LoRA)**.

---

## Структура

```
lora-curation/     промпты, генерация, reviewer, export
train-a5000/       dataset, bootstrap, cycle.sh, test_lora/
tools/win/         опционально: локальный train на 4070
```

HTTP ComfyUI-сервис (`app/`, `scripts/`) — отдельный модуль, см. README.md.
