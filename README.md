# GPU Image Service

Production-oriented HTTP service for GPU image generation via **ComfyUI**, with a Redis job queue and FastAPI control plane.

Game / product servers call this API only. No game-specific domain logic lives here.

```
Client (game server)
    |
    |  POST /api/v1/generate   Authorization: Bearer <API_KEY>
    v
GPU Image Service (api)
    |
    +-- Redis queue (sequential)
    |
    +-- worker  -->  ComfyUI  -->  NVIDIA GPU
    |
    +-- /data/generated/YYYY/MM/<job_id>.webp
```

## 1. Server requirements

- Ubuntu 22.04+ (or compatible Linux)
- NVIDIA GPU with recent proprietary driver (A5000 24GB, RTX 3090/4090, etc.)
- CUDA-capable driver visible via `nvidia-smi`
- Docker Engine + Docker Compose v2
- NVIDIA Container Toolkit
- Disk for models (tens of GB) and generated images
- Outbound HTTPS to pull Docker images / ComfyUI deps on first build

## 2. Install NVIDIA driver

```bash
sudo apt update
sudo ubuntu-drivers autoinstall
sudo reboot
nvidia-smi
```

## 3. Install Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# re-login, then:
docker --version
docker compose version
```

## 4. NVIDIA Container Toolkit

Follow NVIDIA docs, or:

```bash
INSTALL_NVIDIA_TOOLKIT=1 ./scripts/install.sh
```

Verify:

```bash
./scripts/check-gpu.sh
# or:
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

## 5. Clone

```bash
git clone <repository-url> gpu-image-service
cd gpu-image-service
```

## 6. Configure `.env`

```bash
cp .env.example .env
# edit API_KEY to a long random secret shared with the game server
nano .env
```

Important variables:

| Variable | Purpose |
|----------|---------|
| `API_KEY` | Bearer token required on `/api/v1/*` |
| `MODELS_PATH` | Host path mounted as ComfyUI/models |
| `GENERATED_PATH` | Host path for WebP outputs |
| `ALLOWED_WORKFLOWS` | Comma list (e.g. `sdxl`) |
| `DEFAULT_MODEL` | Checkpoint filename under `checkpoints/` |
| `MAX_WIDTH` / `MAX_HEIGHT` / `MAX_STEPS` | Hard caps |
| `PRIVACY_MODE` | Avoid logging full prompts |
| `SAVE_PNG` | Also keep PNG alongside WebP |
| `CORS_ORIGINS` | `*` or comma-separated origins |

Bind the API only on a private network / VPN / firewall. Do not expose it to the public internet without TLS and network controls.

## 7. Install models

Models are **not** in Git. Layout:

```
data/models/          # or $MODELS_PATH
  checkpoints/
  loras/
  vae/
  controlnet/
```

Place at least:

```text
$MODELS_PATH/checkpoints/sd_xl_base_1.0.safetensors
```

Optional helper (you supply `MODEL_URL`):

```bash
MODEL_URL='https://…/sd_xl_base_1.0.safetensors' ./scripts/fetch-model.sh
```

On generate, missing models return a clear `422` error. API logs an error at startup if the default checkpoint is absent.

## 8. Start

```bash
./scripts/install.sh
./scripts/start.sh
```

Equivalent:

```bash
docker compose up -d --build
docker compose ps
```

Stop:

```bash
./scripts/stop.sh
```

## 9. Verify GPU

```bash
./scripts/check-gpu.sh
docker compose exec comfyui nvidia-smi
docker compose exec worker nvidia-smi
curl -s http://127.0.0.1:8080/health
curl -s http://127.0.0.1:8080/ready
```

`/ready` is ready only when Redis, ComfyUI, and the worker heartbeat are healthy.

## 10. API examples

```bash
export API_KEY='your-secret'
export HOST=http://127.0.0.1:8080

# enqueue
curl -sS -X POST "$HOST/api/v1/generate" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow": "sdxl",
    "prompt": "medieval fantasy goblin warrior",
    "negative_prompt": "blurry, low quality",
    "width": 768,
    "height": 768,
    "steps": 20,
    "cfg": 7,
    "seed": -1
  }'
# -> {"job_id":"...","status":"queued"}

# poll
curl -sS -H "Authorization: Bearer $API_KEY" \
  "$HOST/api/v1/jobs/<job_id>"

# download (when status=completed)
curl -sS -H "Authorization: Bearer $API_KEY" \
  -o out.webp "$HOST/api/v1/images/<image_id>"

# ops
curl -sS "$HOST/health"
curl -sS "$HOST/ready"
curl -sS "$HOST/metrics"
```

Allowed workflows are JSON files under `workflows/` (allowlisted via `ALLOWED_WORKFLOWS`). Clients cannot submit arbitrary ComfyUI graphs.

## 11. Logs

```bash
docker compose logs -f api worker comfyui
docker compose logs -f worker | grep job_
```

Job logs include `job_id`, `workflow`, duration, and status. With `PRIVACY_MODE=true`, full prompts are not logged. API keys are never logged.

## 12. Update via Git

```bash
./scripts/deploy.sh
```

This runs `git pull`, rebuilds images, and recreates containers. Named/host volumes for **models** and **generated** images are preserved.

## 13. Backup generated images

```bash
# host path from .env GENERATED_PATH (default ./data/generated)
rsync -a ./data/generated/ /backup/gpu-images/
# or tar
tar -czf generated-$(date +%F).tar.gz -C ./data generated
```

## 14. Troubleshooting

| Symptom | Check |
|---------|--------|
| `nvidia-smi` fails on host | Reinstall/reboot NVIDIA driver |
| GPU not visible in container | Install NVIDIA Container Toolkit; `docker info` shows nvidia |
| Compose build of ComfyUI slow/fails | Network, disk space, CUDA pip index |
| `/ready` comfyui=false | `docker compose logs comfyui`; wait for first boot |
| `/ready` worker=false | Worker crash loop; check model path / ComfyUI URL |
| Generate `422` model not found | File missing under `MODELS_PATH/checkpoints/` |
| `401` on API | `Authorization: Bearer` must match `API_KEY` |
| Jobs stuck in `processing` | Worker reclaim after `STUCK_JOB_TIMEOUT_SEC` |
| OOM on 24GB | Lower resolution/steps; one sequential worker by design |

Local tests (no GPU):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
docker compose config
```

## Layout

```text
gpu-image-service/
  app/                 # FastAPI + worker + services
  workflows/           # allowlisted ComfyUI API graphs
  lora-curation/       # dataset curation (see LORA.md)
  train-a5000/         # FLUX LoRA train + cycle.sh
  docker/              # ComfyUI Dockerfile
  scripts/             # install/start/stop/deploy
  tests/
  docker-compose.yml
  Dockerfile
  .env.example
```

## gf_lowpoly LoRA pipeline

See **[`LORA.md`](LORA.md)** — курация на 4070, train/test на 4090.

```bash
cd train-a5000
export HF_TOKEN=hf_...
chmod +x cycle.sh bootstrap.sh
./cycle.sh train
./cycle.sh test forge
```

## Extensibility (not implemented yet)

Stubs/notes under `app/ext/` for S3 storage and webhooks. Designed for later: multi-GPU workers, priority queues, batch jobs, cancel, retention TTL — without rewriting the HTTP contract.
