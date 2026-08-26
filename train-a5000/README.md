# Train `gf_lowpoly` on Ubuntu + A5000 (one command)

Style LoRA for gameFarmling (Flux). Dataset: curated 512×512 PNGs + captions.  
Home PC (4070) is only for **inference** after you download the `.safetensors`.

## Server

- Ubuntu 22.04+
- NVIDIA driver (`nvidia-smi` works)
- `sudo` (bootstrap installs `libgl1` etc. for OpenCV on headless hosts)
- ~1× **A5000 24GB** (or similar), **64GB RAM**
- ~80GB free disk (FLUX download + caches + output)
- Hugging Face account with access to [`FLUX.1-dev`](https://huggingface.co/black-forest-labs/FLUX.1-dev)

If you already hit `libGL.so.1` / cv2 error:

```bash
sudo apt-get update && sudo apt-get install -y libgl1 libglib2.0-0 libsm6 libxext6 libxrender1
SKIP_INSTALL=1 ./bootstrap.sh
```

## One command (leave the PC — use tmux + auto-upload)

```bash
sudo apt-get update && sudo apt-get install -y tmux libgl1 libglib2.0-0 libsm6 libxext6 libxrender1
cd ~/gpu-image-service && git pull
cd train-a5000
tmux new -s train
```

Inside tmux (use a **new** HF token, never paste tokens into chat/git):

```bash
export HF_TOKEN='hf_...'
export HF_REPO_ID='YourHFName/gf-lowpoly'
export HF_PRIVATE=true
# phone push when done (no Telegram/Discord):
export NTFY_TOPIC='gf-ready-CHANGE_ME_long_secret_123'
chmod +x bootstrap.sh
./bootstrap.sh
# detach: Ctrl+B then D
```

**Notify setup (ntfy):**
1. App: [ntfy.sh](https://ntfy.sh) (Android/iOS) или в браузере `https://ntfy.sh/ТВОЙ_ТОПИК`
2. Подпишись на тот же секретный `NTFY_TOPIC`
3. По окончании обучения придёт пуш «gf_lowpoly DONE» (+ ссылка на HF, если задан `HF_REPO_ID`)

When training finishes, bootstrap **uploads** `.safetensors` to Hugging Face (если задан `HF_REPO_ID`) и шлёт ntfy.  
Server can be deleted after you downloaded the LoRA.

Already trained, only upload:

```bash
export HF_TOKEN='hf_...'
export HF_REPO_ID='YourHFName/gf-lowpoly'
SKIP_INSTALL=1 UPLOAD_ONLY=1 ./bootstrap.sh
```

Resume after crash / SSH drop (without tmux loss): same `./bootstrap.sh` again (picks last checkpoint).  
Skip reinstall: `SKIP_INSTALL=1 ./bootstrap.sh`

Optional knobs:

```bash
STEPS=2000 BATCH=1 ./bootstrap.sh
```

## After training → home Forge

If you did **not** set `HF_REPO_ID`, copy manually:

```bash
ls -lh output/gf_lowpoly/*.safetensors
```

Into:

`F:\fluxGenerationForLora\stable-diffusion-webui-forge\models\Lora\`

Prompt:

```text
<lora:gf_lowpoly:0.85>, gf_lowpoly, ningraphix, ps1 game screenshot, anthropomorphic cat mage, ...
```

## Refresh dataset (Windows)

After new approvals in the curator:

```bat
train-a5000\sync_dataset.bat
```

Then commit/push (or `scp -r train-a5000/dataset user@server:...`).

## Layout

```
train-a5000/
  bootstrap.sh          # Ubuntu entrypoint
  dataset/              # PNG + TXT (synced from lora-curation/export/approved)
  gf_lowpoly_a5000.yaml.template
  output/               # created on server (gitignored)
  .ai-toolkit/          # created on server (gitignored)
  .hf-cache/            # created on server (gitignored)
```

## Notes

- Config is tuned for **24GB VRAM + 64GB RAM** (`low_vram: false`, EMA on, sample every 250).
- Base model is still full `FLUX.1-dev` with **qfloat8** quant (Ostris) — not the Forge GGUF file.
- Do not commit HF tokens. Use `export HF_TOKEN=...` only on the server session.
