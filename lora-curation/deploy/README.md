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

Models: see `lora-curation/forge_gen.json`.
