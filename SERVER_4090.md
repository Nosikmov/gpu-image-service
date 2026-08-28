# RTX 4090 — curation + train `gf_lowpoly`

Полный цикл на одном арендованном сервере (Ubuntu 22.04+, **RTX 4090 24GB**):

1. **Forge + Flux** — быстрая генерация датасета (в ~3–5× быстрее 4070)
2. **Reviewer** — отбор картинок в браузере
3. **Ostris AI-Toolkit** — обучение LoRA v2 без возврата на домашний ПК

Домашний 4070 после этого только для финального теста в Forge.

---

## Требования

| | |
|---|---|
| GPU | RTX 4090 24GB (или A5000 24GB) |
| RAM | 32GB+ (64GB комфортнее для FLUX train) |
| Диск | ~100 GB свободно (FLUX ~24GB + Forge ~15GB + кэши) |
| HF | Аккаунт + доступ к [FLUX.1-dev](https://huggingface.co/black-forest-labs/FLUX.1-dev) |

---

## 0. Быстрый старт (копипаста)

```bash
# --- на чистом Ubuntu после nvidia-smi ---
sudo apt-get update && sudo apt-get install -y \
  git tmux curl rsync libgl1 libglib2.0-0 libsm6 libxext6 libxrender1

export REPO="$HOME/gpu-image-service"
export FORGE="$HOME/stable-diffusion-webui-forge"
export HF_TOKEN='hf_...'          # НОВЫЙ токен, не светить в чат
export HF_REPO_ID='YourName/gf-lowpoly'
export NTFY_TOPIC='gf-ready-YOUR_LONG_SECRET'   # опционально: пуш на телефон

# репозиторий
git clone https://github.com/Nosikmov/gpu-image-service.git "$REPO"
cd "$REPO"
git pull

# одноразовая подготовка ОС + Forge
bash lora-curation/deploy/setup_server.sh

# модели с домашнего ПК (см. раздел 2) ИЛИ вручную положить в Forge
```

Дальше — **два tmux-окна** (раздел 3 и 4).

---

## 1. Проверка GPU

```bash
nvidia-smi
# Driver 535+ recommended
```

---

## 2. Модели Forge (Flux fp8)

### Вариант A — rsync с Windows (рекомендуется)

На **домашнем ПК** (PowerShell / Git Bash), пути подставь свои:

```bash
export FORGE_SRC='F:/fluxGenerationForLora/stable-diffusion-webui-forge'
export REMOTE='user@YOUR_SERVER_IP'
export FORGE_DST='/home/user/stable-diffusion-webui-forge'

bash lora-curation/deploy/sync_models.sh
```

Копирует:

- `models/Stable-diffusion/flux1-dev-fp8.safetensors`
- `models/VAE/ae.safetensors`
- `models/text_encoder/clip_l.safetensors`
- `models/text_encoder/t5xxl_fp8_e4m3fn.safetensors`
- `models/Lora/gf_lowpoly.safetensors` (если есть — для генерации v1)

### Вариант B — скачать на сервере

FLUX fp8 и энкодеры — вручную в те же папки Forge (см. `lora-curation/forge_gen.json`).

---

## 3. Tmux: Forge (генерация)

```bash
tmux new -s forge
export FORGE="$HOME/stable-diffusion-webui-forge"
export FORGE_DIR="$FORGE"
bash "$HOME/gpu-image-service/lora-curation/deploy/start_forge.sh"
# Ctrl+B, D — отсоединиться
```

Проверка API (другой SSH):

```bash
curl -s http://127.0.0.1:7860/sdapi/v1/sd-models | head
```

В Forge UI: **Diffusion in Low Bits → Automatic (fp16 LoRA)** (важно для LoRA на Flux).

---

## 4. Tmux: Curation (батч + reviewer)

```bash
tmux new -s curate
cd ~/gpu-image-service
export FORGE_URL=http://127.0.0.1:7860
export FORGE_DIR="$HOME/stable-diffusion-webui-forge"

# полный цикл: build_prompts → generate → reviewer :8765
bash lora-curation/deploy/run_curation.sh
```

Или **auto-loop** (как START_CURATION.bat на Windows):

```bash
python3 lora-curation/auto_loop.py --port 8765 --forge http://127.0.0.1:7860
```

### Reviewer снаружи

```bash
# на сервере — открыть порт (осторожно, без пароля на reviewer)
sudo ufw allow 8765/tcp
```

Браузер: `http://SERVER_IP:8765/` → **A** approve / **R** reject.

### Экспорт approved

```bash
cd ~/gpu-image-service
python3 lora-curation/export_dataset.py --caption-mode train
bash train-a5000/sync_dataset.sh
```

---

## 5. Tmux: Обучение LoRA

```bash
tmux new -s train
cd ~/gpu-image-service/train-a5000
chmod +x bootstrap.sh

export HF_TOKEN='hf_...'
export HF_REPO_ID='YourName/gf-lowpoly'
export HF_PRIVATE=true
export NTFY_TOPIC='gf-ready-YOUR_LONG_SECRET'

./bootstrap.sh
# Ctrl+B, D
```

Повторный запуск без переустановки:

```bash
SKIP_INSTALL=1 ./bootstrap.sh
```

Только залить готовые веса на HF:

```bash
SKIP_INSTALL=1 UPLOAD_ONLY=1 ./bootstrap.sh
```

Чекпоинты: `train-a5000/output/gf_lowpoly/*.safetensors`

### Smoke-test LoRA (без Forge)

```bash
cd ~/gpu-image-service/train-a5000/test_lora
./run_on_server.sh
ls -lh out/*.png
```

Скачать на ПК: `scp -r user@server:~/gpu-image-service/train-a5000/test_lora/out ./`

---

## 6. После обучения → домашний Forge

```bash
# с сервера
scp user@server:~/gpu-image-service/train-a5000/output/gf_lowpoly/gf_lowpoly.safetensors \
  'F:/fluxGenerationForLora/stable-diffusion-webui-forge/models/Lora/'
```

Или скачать с Hugging Face, если задан `HF_REPO_ID`.

Промпт:

```text
<lora:gf_lowpoly:0.9>, gf_lowpoly, ningraphix, ps1 game screenshot, ...
```

---

## 7. Обновление репо на сервере

```bash
cd ~/gpu-image-service
git pull
python3 lora-curation/build_prompts.py
```

---

## Порты и firewall

| Порт | Сервис | Рекомендация |
|------|--------|--------------|
| 7860 | Forge UI+API | только localhost / SSH tunnel |
| 8765 | Reviewer | по необходимости наружу |
| 22 | SSH | ключи, не пароль root |

SSH-туннель для reviewer без открытия порта:

```bash
ssh -L 8765:127.0.0.1:8765 user@SERVER_IP
# браузер: http://127.0.0.1:8765/
```

---

## Troubleshooting

| Симптом | Решение |
|---------|---------|
| HF download 0B / зависание | `HF_HUB_DISABLE_XET=1` уже в bootstrap; перезапуск |
| OOM при train на 24GB | bootstrap уже: `low_vram`, no EMA, no samples |
| `libGL.so.1` | `sudo apt install libgl1` или `setup_server.sh` |
| Forge Connection refused | tmux `forge`, ждать загрузки модели 2–5 мин |
| LoRA не влияет | **Automatic (fp16 LoRA)** в Forge |
| git pull конфликт bootstrap | `git checkout -- train-a5000/bootstrap.sh && git pull` |

---

## Файлы в репо

```
lora-curation/deploy/
  setup_server.sh    # apt + clone Forge + webui-user.sh
  start_forge.sh     # запуск Forge
  run_curation.sh    # build → generate → reviewer
  sync_models.sh     # rsync Flux с Windows
  webui-user.sh      # --api --listen для Linux

train-a5000/
  bootstrap.sh       # train + HF upload + ntfy
  sync_dataset.sh    # export/approved → dataset/
  test_lora/         # diffusers smoke test
```

Windows-аналог curation: `START_CURATION.bat` в корне репо.
