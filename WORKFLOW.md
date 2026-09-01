# Итеративный пайплайн `gf_lowpoly`

Локально курация на **4070** → обучение и тест на **4090** → при необходимости **раунд 2** на той же машине.

**Да, итерация обычно даёт лучший результат**, чем один проход:

| Раунд | Генерация | Датасет | Результат |
|-------|-----------|---------|-----------|
| **0 (сейчас)** | `lowpoly_flux` + `OOTN64_Krea2` | 30–40 approve вручную | Bootstrap, учим «свой» стиль |
| **1** | обученная `gf_lowpoly` | отбор глаз/силуэта уже ближе к цели | Стабильнее стиль, меньше артефактов |
| **2** (опционально) | `gf_lowpoly_v2` | дочистка 10–20 картинок | Финальный polish |

После 2–3 раундов прирост падает — не зацикливайся.

---

## Фаза A — локально (4070), сейчас

```bat
START_CURATION.bat
```

Reviewer → **A** только хорошие (жёлтые глаза, силуэт, T-pose).

Когда готово (~30–40 approve):

```bat
EXPORT_FOR_TRAIN.bat
```

Создаёт `lora-curation\export\approved\` и копирует в `train-a5000\dataset\`.

Опционально — архив перед новым раундом:

```bat
STASH_IMAGES.bat
```

---

## Фаза B — залить датасет на 4090

В `train-a5000\push_dataset.bat` пропиши `REMOTE=root@IP_СЕРВЕРА`, затем:

```bat
push_dataset.bat
```

Или вручную:

```bash
scp -r train-a5000/dataset/* root@SERVER:~/gpu-image-service/train-a5000/dataset/
```

На сервере также:

```bash
cd ~/gpu-image-service && git pull
```

---

## Фаза C — обучение на 4090

```bash
tmux new -s train
cd ~/gpu-image-service/train-a5000
chmod +x bootstrap.sh server_cycle.sh

export HF_TOKEN='hf_...'
export HF_REPO_ID='YourName/gf-lowpoly'
export NTFY_TOPIC='gf-ready-SECRET'

./bootstrap.sh
# Ctrl+B D
```

Чекпоинт: `train-a5000/output/gf_lowpoly/gf_lowpoly.safetensors`

Повторное обучение (раунд 2) — другое имя:

```bash
TRAIN_NAME=gf_lowpoly_v2 STEPS=2000 ./bootstrap.sh
```

---

## Фаза D — smoke-test на 4090 (без Forge)

```bash
cd ~/gpu-image-service/train-a5000
./server_cycle.sh test
```

Картинки: `test_lora/out/*.png`

Скачать на ПК:

```bash
scp -r root@SERVER:~/gpu-image-service/train-a5000/test_lora/out ./lora_test_round1
```

---

## Фаза E — раунд 2: новый датасет на своей LoRA (на 4090)

После train v1:

```bash
cd ~/gpu-image-service
./train-a5000/server_cycle.sh round2
```

Скрипт:
1. Копирует `gf_lowpoly.safetensors` в Forge `models/Lora/`
2. Ставит `CURATION_MODE=trained` (только `<lora:gf_lowpoly:0.9>`)
3. Запускает curation (Forge + reviewer :8765)

Отбор → export на сервере:

```bash
python3 lora-curation/export_dataset.py --caption-mode train
bash train-a5000/sync_dataset.sh
TRAIN_NAME=gf_lowpoly_v2 ./train-a5000/bootstrap.sh
```

---

## Фаза F — забрать LoRA домой

```bash
scp root@SERVER:~/gpu-image-service/train-a5000/output/gf_lowpoly/gf_lowpoly.safetensors ^
  F:\fluxGenerationForLora\stable-diffusion-webui-forge\models\Lora\
```

Или с Hugging Face, если задан `HF_REPO_ID`.

Forge: **Automatic (fp16 LoRA)**, промпт:

```text
<lora:gf_lowpoly:0.9>, gf_lowpoly, ps1 game screenshot, ...
```

---

## Режимы генерации (`CURATION_MODE`)

| Значение | LoRA в промпте | Когда |
|----------|----------------|-------|
| `bootstrap` (default) | `lowpoly_flux` + `OOTN64_Krea2` | Сейчас на 4070 |
| `trained` | только `gf_lowpoly` | Раунд 2+ на сервере |
| `lowpoly_only` | только `lowpoly_flux` | Тест без PS1 LoRA |

Windows: `set CURATION_MODE=trained` перед `START_CURATION.bat`  
Linux: `export CURATION_MODE=trained`

---

## Файлы

| Файл | Назначение |
|------|------------|
| `EXPORT_FOR_TRAIN.bat` | export + sync в `train-a5000/dataset` |
| `push_dataset.bat` | scp датасета на сервер |
| `STASH_IMAGES.bat` | архив картинок перед новым раундом |
| `train-a5000/server_cycle.sh` | train / test / round2 на сервере |
| `train-a5000/bootstrap.sh` | Ostris FLUX LoRA train |
| `SERVER_4090.md` | установка Forge + tmux |
| `lora-curation/style.py` | `CURATION_MODE` переключатель |

---

## Чеклист перед первым train

- [ ] 30–40 approve в reviewer
- [ ] `EXPORT_FOR_TRAIN.bat` → N PNG в `train-a5000/dataset`
- [ ] `push_dataset.bat` или scp на сервер
- [ ] `HF_TOKEN` + лицензия FLUX.1-dev
- [ ] `git pull` на сервере
- [ ] `tmux` + `./bootstrap.sh`
- [ ] `./server_cycle.sh test` — глазами оценить v1
- [ ] Решить: достаточно v1 или раунд 2
