"""gameFarmling low-poly / PS1 cat style for LoRA curation (Forge + Flux)."""

from __future__ import annotations

HOUSE_STYLE = (
    "ningraphix, ps1 game screenshot, low-poly mesh, flat shaded, crisp hard edges, "
    "chibi proportions, big angular head, neutral solid light grey background"
)

STYLE_LOCK = (
    "anthropomorphic cat, low-poly papercraft / PS1 game look, single character, "
    "full body, centered, no scenery, T-pose"
)

# Flux typically works best with empty or very light negatives.
STYLE_NEGATIVE = ""
MONSTER_NEGATIVE = STYLE_NEGATIVE

TRIGGER_WORD = "gf_lowpoly"

# Use trained LoRA to regenerate the curation set (v2), then retrain.
GENERATION_LORA_TAG = "<lora:gf_lowpoly:0.85>"
GENERATION_PROMPT_PREFIX = f"{GENERATION_LORA_TAG}, {TRIGGER_WORD}, ningraphix, ps1 game screenshot"
