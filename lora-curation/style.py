"""gameFarmling low-poly style for LoRA curation (Forge + Flux GGUF)."""

from __future__ import annotations

# Trained style LoRA (Forge: models/Lora/gf_lowpoly.safetensors).
TRIGGER_WORD = "gf_lowpoly"
GENERATION_LORA_TAGS = "<lora:gf_lowpoly:0.9>"
GENERATION_PROMPT_PREFIX = (
    f"{GENERATION_LORA_TAGS}, {TRIGGER_WORD}, ningraphix, ps1 game screenshot,"
)
GENERATION_LORA_TAG = GENERATION_LORA_TAGS

# Strong low-poly mesh + crisp stylized textures (avoid extreme poly-count wording).
MESH_STYLE = (
    "very low polygon mesh, extremely chunky blocky silhouette, "
    "few large geometric facets, highly optimized game model, minimal geometry"
)
TEXTURE_STYLE = (
    "crisp stylized hand-painted textures, rich clean color blocks, "
    "sharp material definition, painted PS1 textures on flat facets"
)
CHARACTER_BODY = (
    f"chibi proportions, big angular head, {MESH_STYLE}, {TEXTURE_STYLE}, "
    "flat shaded, crisp silhouette"
)

FELINE_EYE_LOCK = "feline cat eyes"

PROMPT_FRAMING = (
    "T-pose, full body, centered, plain solid light grey background, "
    "no scenery, no environment, no ground, empty background"
)

STYLE_NEGATIVE = (
    "high-poly, smooth subdivision, muddy textures, blurry textures, "
    "flat untextured plastic, muddy artifacts, broken geometry, extra limbs, "
    "cube body, box body, scenery, landscape, environment, sky, clouds, forest, grass, "
    "ground, floor, horizon, room, interior, outdoor, dungeon, castle, props, furniture, "
    "platform, gradient background, detailed background, blurry, watermark, text, "
    "round eyes, huge round eyes, anime round eyes, circular eyes, bug eyes"
)
MONSTER_NEGATIVE = STYLE_NEGATIVE

HOUSE_STYLE = PROMPT_FRAMING
STYLE_LOCK = "single character, full body, centered, no scenery"
