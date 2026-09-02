# LoRA weights (Git LFS)

Trained checkpoints for testing on a rented GPU **without re-training**.

## Files

Put checkpoints here:

```
loras/gf_lowpoly_v2/
  gf_lowpoly_v2.safetensors          # final (recommended for tests)
  gf_lowpoly_v2_000001000.safetensors
  gf_lowpoly_v2_000000750.safetensors
  ...
```

Bootstrap style LoRA (for Forge, same as curation) — copy from your PC Forge:

```
loras/bootstrap/
  lowpoly_flux.safetensors
  OOTN64_Krea2.safetensors
```

## Upload from old server (once)

**Windows** — edit `REMOTE` in `FETCH_LORAS.bat`, run it.

**Linux / macOS:**

```bash
mkdir -p loras/gf_lowpoly_v2
scp user@OLD_SERVER:~/gpu-image-service/train-a5000/output/gf_lowpoly_v2/*.safetensors loras/gf_lowpoly_v2/
```

Then commit with Git LFS (see below).

## Git LFS (required — files are ~165 MB each)

```bash
git lfs install
git lfs track "loras/**/*.safetensors"
git add .gitattributes loras/
git commit -m "Add gf_lowpoly_v2 LoRA checkpoints"
git push
```

## New server (3090)

```bash
git clone https://github.com/Nosikmov/gpu-image-service.git
cd gpu-image-service
git lfs install
git lfs pull

cd train-a5000
chmod +x cycle.sh
./cycle.sh setup-forge
# sync flux fp8 models from PC (sync_models.sh)

./cycle.sh install-loras
# start Forge, then:
export TRAIN_NAME=gf_lowpoly_v2
./cycle.sh test forge --limit 4
```
