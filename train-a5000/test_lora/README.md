# Test `gf_lowpoly` — 12 images

## 1b) All 40 curation prompts (same as dataset v2)

```bash
cd ~/gpu-image-service
git pull
cd train-a5000
chmod +x server_cycle.sh test_lora/run_dataset_test.sh
./server_cycle.sh test dataset
# or:
cd test_lora && ./run_dataset_test.sh
```

Result: `test_lora/out_dataset/knight_v2.png`, `orc_v2.png`, … + `manifest.json`

Download:

```bash
scp -r ubuntu@SERVER:~/gpu-image-service/train-a5000/test_lora/out_dataset F:\fluxGenerationForLora\lora_test_40
```

Optional:

```bash
LORA=../output/gf_lowpoly/gf_lowpoly_000001500.safetensors ./run_dataset_test.sh --weight 0.9 --limit 4
```

## 1) On the GPU server — quick smoke (12 images)

Uses the **already downloaded FLUX** from training + LoRA in `output/` — **Forge not needed**.

```bash
cd ~/gpu-image-service
git pull
cd train-a5000/test_lora
chmod +x run_on_server.sh
./run_on_server.sh
```

Result: `train-a5000/test_lora/out/01_….png` … `12_….png`

Download to PC:

```bash
# from your PC (PowerShell / scp)
scp -r ubuntu@SERVER:~/gpu-image-service/train-a5000/test_lora/out F:\fluxGenerationForLora\lora_test_out
```

Optional: other LoRA path / strength:

```bash
./run_on_server.sh --lora ../output/gf_lowpoly/gf_lowpoly_000001250.safetensors --weight 0.85
./run_on_server.sh --limit 4   # quick smoke
```

Needs: `train-a5000/.ai-toolkit/.venv` and HF cache from training (same machine).

## 2) Later on this Windows PC (Forge)

```bat
cd F:\fluxGenerationForLora\gpu-image-service\train-a5000\test_lora
python test_gf_lowpoly.py
```

Forge must be up with `--api`, LoRA in `models\Lora\gf_lowpoly.safetensors`, Diffusion Low Bits = **Automatic (fp16 LoRA)**.

## Files

| File | Role |
|------|------|
| `test_prompts.json` | 12 subjects + gen settings |
| `run_dataset_test.sh` / `infer_dataset_prompts.py` | 40 prompts from `lora-curation/prompts.json` |
| `run_on_server.sh` / `infer_diffusers.py` | 12-prompt smoke test |
| `test_gf_lowpoly.py` | local Forge API test |
| `out/` | 12 smoke PNGs (gitignored) |
| `out_dataset/` | 40 dataset PNGs (gitignored) |
