"""gameFarmling low-poly / PS1 cat style for LoRA curation (Forge + Flux)."""

from __future__ import annotations

HOUSE_STYLE = (
    "ningraphix, ps1 game screenshot, chunky low-poly, simple geometric forms, large clean flat facets, PS1 game character, flat shaded, crisp silhouette, limited detail, "
    "chibi proportions, big angular head, feline cat eyes, neutral solid light grey background"
)

STYLE_LOCK = (
    "anthropomorphic cat, chunky PS1 low-poly game look, single character, "
    "full body, centered, no scenery, T-pose"
)

# Light negatives help Flux avoid broken geometry when pushing low-poly.
STYLE_NEGATIVE = "high-poly, smooth subdivision, muddy artifacts, broken geometry, extra limbs"
MONSTER_NEGATIVE = STYLE_NEGATIVE

TRIGGER_WORD = "gf_lowpoly"

GENERATION_LORA_TAG = "<lora:gf_lowpoly:0.9>"
GENERATION_PROMPT_PREFIX = f"{GENERATION_LORA_TAG}, {TRIGGER_WORD}, ningraphix, ps1 game screenshot"
