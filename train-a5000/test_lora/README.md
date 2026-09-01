# Test LoRA on server

Use **`../cycle.sh`** — do not call scripts here directly unless debugging.

```bash
cd ~/gpu-image-service/train-a5000
chmod +x cycle.sh test_lora/run.sh
export TRAIN_NAME=gf_lowpoly_v2

./cycle.sh test forge          # 12 images, Forge fp8 -> out/
./cycle.sh test forge40        # 40 prompts -> out_forge_dataset/
./cycle.sh test slow --limit 4 # diffusers fallback (slow)
```

Requires Forge running (`lora-curation/deploy/start_forge.sh`).

Python entry points (used by `run.sh`):

| Script | Mode |
|--------|------|
| `test_gf_lowpoly.py` | forge |
| `test_forge_dataset.py` | forge40 |
| `infer_diffusers.py` | slow |
| `infer_dataset_prompts.py` | slow40 |

See [LORA.md](../../LORA.md).
