"""gameFarmling low-poly style for LoRA curation (Forge + Flux)."""

from __future__ import annotations

import os

# Trained export / Ostris trigger
TRIGGER_WORD = "gf_lowpoly"

# CURATION_MODE:
#   bootstrap (default) — lowpoly_flux + OOTN64_Krea2 while building dataset v1
#   trained             — only gf_lowpoly.safetensors (round 2+ on server)
_CURATION_MODE = os.environ.get("CURATION_MODE", "bootstrap").strip().lower()

STYLE_LORA_NAME = "OOTN64_Krea2"

if _CURATION_MODE in ("trained", "round2", "gf_lowpoly"):
    GENERATION_LORA_TAGS = "<lora:gf_lowpoly:0.9>"
    GENERATION_PROMPT_PREFIX = (
        f"{GENERATION_LORA_TAGS}, {TRIGGER_WORD}, ps1 game screenshot,"
    )
elif _CURATION_MODE in ("lowpoly", "lowpoly_only"):
    GENERATION_LORA_TAGS = "<lora:lowpoly_flux:0.9>"
    GENERATION_PROMPT_PREFIX = (
        f"{GENERATION_LORA_TAGS}, {TRIGGER_WORD}, ps1 game screenshot,"
    )
else:
    GENERATION_LORA_TAGS = (
        f"<lora:lowpoly_flux:0.9> <lora:{STYLE_LORA_NAME}:0.9>"
    )
    GENERATION_PROMPT_PREFIX = (
        f"{GENERATION_LORA_TAGS}, {TRIGGER_WORD}, {STYLE_LORA_NAME}, ps1 game screenshot,"
    )

GENERATION_LORA_TAG = GENERATION_LORA_TAGS

# Dataset v2 — chunky low-poly, empty hands, detail in texture/costume.
SUBJECT_PREFIX = "a low-poly 3D character asset of"
CHARACTER_BODY = (
    "empty hands, open palms, clear hands visible, chibi proportions, big angular head, "
    "amber yellow feline cat eyes, expressive slanted cat eyes, chunky low-poly, simple geometric forms, large clean flat facets, "
    "PS1 game character, flat shaded, crisp silhouette, limited detail"
)
SLIME_CHARACTER_BODY = (
    "chibi proportions, chunky low-poly, simple geometric forms, large clean flat facets, "
    "PS1 game character, flat shaded, crisp silhouette, limited detail"
)
SLIME_ENTRY_IDS = frozenset({"green_slime", "red_slime", "yellow_slime", "slime"})

FELINE_EYE_LOCK = ""

PROMPT_FRAMING = (
    "T-pose, orthographic front view, neutral solid light grey background, "
    "no scenery, no environment, no ground, empty background"
)

STYLE_NEGATIVE = (
    "high-poly, smooth subdivision, muddy textures, blurry textures, "
    "flat untextured plastic, muddy artifacts, broken geometry, extra limbs, "
    "weapon, sword, staff, bow, shield, gun, dagger, axe, spear, scythe, "
    "holding object, props in hands, "
    "cube body, box body, scenery, landscape, environment, sky, clouds, forest, grass, "
    "ground, floor, horizon, room, interior, outdoor, dungeon, castle, furniture, "
    "platform, gradient background, detailed background, blurry, watermark, text, "
    "black dot eyes, solid black eyes, beady black eyes, pitch black eyes, "
    "identical round black eyes, black circular dot pupils, void black eyes, "
    "round eyes, huge round eyes, anime round eyes, circular eyes, bug eyes"
)
MONSTER_NEGATIVE = STYLE_NEGATIVE

HOUSE_STYLE = PROMPT_FRAMING
STYLE_LOCK = "single character, full body, centered, no scenery"
