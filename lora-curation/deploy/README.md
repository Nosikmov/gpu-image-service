# Deploy: Forge on 4090

Full guide: **[`LORA.md`](../../LORA.md)**

```bash
cd ~/gpu-image-service/train-a5000
./cycle.sh setup-forge

# from Windows:
#   bash lora-curation/deploy/sync_models.sh

tmux new -s forge
bash lora-curation/deploy/start_forge.sh

export TRAIN_NAME=gf_lowpoly_v2
./cycle.sh test forge
```

| Script | Purpose |
|--------|---------|
| `setup_server.sh` | apt, clone Forge, `webui-user.sh` |
| `start_forge.sh` | Forge `--api --listen` :7860 |
| `run_curation.sh` | prompts → generate → reviewer :8765 |
| `sync_models.sh` | rsync Flux fp8 from PC |
| `forge_user.sh` | helper (sourced, not run directly) |
| `webui-user.sh` | copied into Forge root |

### Forge: `pkg_resources` / CLIP build fails (Ubuntu 24.04)

```bash
sudo apt-get install -y python3-setuptools python3-pip python3-dev build-essential
# optional but helps Forge:
sudo apt-get install -y python3.10 python3.10-venv

cd ~/stable-diffusion-webui-forge
bash ~/gpu-image-service/lora-curation/deploy/bootstrap_forge_venv.sh
bash ~/gpu-image-service/lora-curation/deploy/start_forge.sh
```

If still fails, pre-install CLIP manually:

```bash
cd ~/stable-diffusion-webui-forge
./venv/bin/pip install "setuptools==69.5.1" wheel
./venv/bin/pip install --no-build-isolation \
  git+https://github.com/openai/CLIP.git@d50d76daa670286dd6cacf3bcd80b5e4823fc8e1
./webui.sh
```
