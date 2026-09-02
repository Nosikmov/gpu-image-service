"""gameFarmling low-poly style for LoRA curation (Forge + Flux)."""

from __future__ import annotations

import os

# Trained export / Ostris trigger
TRIGGER_WORD = "gf_lowpoly"

# CURATION_MODE:
#   ningraphix (default) — Flux LoRA ningraphix-000031 for dataset generation
#   bootstrap            — lowpoly_flux + OOTN64_Krea2 (legacy dual LoRA)
#   trained              — only gf_lowpoly.safetensors (round 2+ on server)
_CURATION_MODE = os.environ.get("CURATION_MODE", "ningraphix").strip().lower()

STYLE_LORA_NAME = "ningraphix-000031"

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
elif _CURATION_MODE in ("bootstrap", "dual"):
    GENERATION_LORA_TAGS = "<lora:lowpoly_flux:0.9> <lora:OOTN64_Krea2:0.9>"
    GENERATION_PROMPT_PREFIX = (
        f"{GENERATION_LORA_TAGS}, {TRIGGER_WORD}, OOTN64_Krea2, ps1 game screenshot,"
    )
else:
    GENERATION_LORA_TAGS = f"<lora:{STYLE_LORA_NAME}:0.9>"
    GENERATION_PROMPT_PREFIX = (
        f"{GENERATION_LORA_TAGS}, {TRIGGER_WORD}, ningraphix, ps1 game screenshot,"
    )

GENERATION_LORA_TAG = GENERATION_LORA_TAGS

# Dataset v2 — chunky low-poly, empty hands, detail in texture/costume.
SUBJECT_PREFIX = "a low-poly 3D character asset of"

# Same phrase in every caption + at inference. Do not use "expressive" (invites variation).
FELINE_EYE_LOCK = (
    "identical paired amber yellow cat eyes, flat painted oval eyes, "
    "vertical slit pupils, same eye style on every character"
)

CHARACTER_BODY = (
    "empty hands, open palms, clear hands visible, chibi proportions, big angular head, "
    f"{FELINE_EYE_LOCK}, chunky low-poly, simple geometric forms, large clean flat facets, "
    "PS1 game character, flat shaded, crisp silhouette, limited detail"
)
SLIME_CHARACTER_BODY = (
    "chibi proportions, chunky low-poly, simple geometric forms, large clean flat facets, "
    f"{FELINE_EYE_LOCK}, "
    "PS1 game character, flat shaded, crisp silhouette, limited detail"
)
SLIME_ENTRY_IDS = frozenset({"green_slime", "red_slime", "yellow_slime", "slime"})

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
