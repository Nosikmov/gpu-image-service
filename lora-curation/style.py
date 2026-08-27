"""gameFarmling low-poly / PS1 cat style for LoRA curation (Forge + Flux)."""

from __future__ import annotations

HOUSE_STYLE = (
    "ningraphix, ps1 game screenshot, extremely low-poly, very few polygons, chunky blocky mesh, large flat facets, minimal geometric detail, PS1 N64 game asset, flat shaded, hard silhouette edges, no smooth subdivision, no high-poly sculpt, "
    "chibi proportions, big angular head, feline cat eyes, neutral solid light grey background"
)

STYLE_LOCK = (
    "anthropomorphic cat, extremely low-poly PS1 game look, single character, "
    "full body, centered, no scenery, T-pose"
)

STYLE_NEGATIVE = ""
MONSTER_NEGATIVE = STYLE_NEGATIVE

TRIGGER_WORD = "gf_lowpoly"

GENERATION_LORA_TAG = "<lora:gf_lowpoly:0.95>"
GENERATION_PROMPT_PREFIX = f"{GENERATION_LORA_TAG}, {TRIGGER_WORD}, ningraphix, ps1 game screenshot"
