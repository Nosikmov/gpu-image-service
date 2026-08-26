# Train `gf_lowpoly` on Ubuntu + A5000 (one command)

Style LoRA for gameFarmling (Flux). Dataset: curated 512×512 PNGs + captions.  
Home PC (4070) is only for **inference** after you download the `.safetensors`.

## Server

- Ubuntu 22.04+
- NVIDIA driver (`nvidia-smi` works)
- ~1× **A5000 24GB** (or similar), **64GB RAM**
- ~80GB free disk (FLUX download + caches + output)
- Hugging Face account with access to [`FLUX.1-dev`](https://huggingface.co/black-forest-labs/FLUX.1-dev)

## One command

```bash
git clone <THIS_REPO_URL> gpu-image-service
cd gpu-image-service/train-a5000
export HF_TOKEN=hf_xxxxxxxxxxxxxxxx
chmod +x bootstrap.sh
./bootstrap.sh
```

That will:

1. Clone Ostris AI-Toolkit into `train-a5000/.ai-toolkit`
2. Install torch/CUDA + deps via toolkit manager
3. Login to Hugging Face
4. Train LoRA → `train-a5000/output/gf_lowpoly/`

Resume after crash / SSH drop: run the same `./bootstrap.sh` again (picks last checkpoint).  
Skip reinstall: `SKIP_INSTALL=1 ./bootstrap.sh`

Optional knobs:

```bash
STEPS=2000 BATCH=1 ./bootstrap.sh
```

## After training → home Forge

```bash
# on server
ls -lh output/gf_lowpoly/*.safetensors
```

Copy the best checkpoint to your PC:

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
