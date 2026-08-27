"""gameFarmling low-poly / PS1 cat style for LoRA curation (Forge + Flux)."""

from __future__ import annotations

# Shared style tokens already baked into each prompt in promts-for-generate.txt.
# Kept here for docs / future prompt builders.
HOUSE_STYLE = (
    "ningraphix, ps1 game screenshot, low-poly mesh, flat shaded, crisp hard edges, "
    "chibi proportions, big angular head, neutral solid light grey background"
)

# Lock default face eyes so the style LoRA does not invent a new eye each time.
# Special monsters (cyclops, doll buttons, slit reptile, etc.) may override in their prompt.
EYE_LOCK = (
    "identical paired low-poly cat eyes, two matching oval eyes, flat white sclera, "
    "same size simple black round pupils, symmetrical, no mismatched eyes"
)

STYLE_LOCK = (
    "anthropomorphic cat, low-poly papercraft / PS1 game look, single character, "
    "full body, centered, no scenery"
)

# Flux typically works best with empty or very light negatives.
STYLE_NEGATIVE = ""

# Back-compat alias for older scripts that imported MONSTER_NEGATIVE
MONSTER_NEGATIVE = STYLE_NEGATIVE

TRIGGER_WORD = "gf_lowpoly"
