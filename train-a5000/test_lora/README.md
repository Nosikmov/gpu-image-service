# Test `gf_lowpoly` — 12 images

## 1) On the GPU server (preferred first)

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
| `run_on_server.sh` / `infer_diffusers.py` | server test (diffusers) |
| `test_gf_lowpoly.py` | local Forge API test |
| `out/` | generated PNGs (gitignored) |
