"""Vendored Reign of Devorio art style for LoRA curation (no game-repo import)."""

from __future__ import annotations

HOUSE_STYLE = (
    "dark medieval fantasy RPG art, stylized hand-painted 2D, painterly textures, "
    "muted earthy palette, warm highlights, soft cinematic lighting, subtle shadows, "
    "refined shapes, not photoreal, cohesive game art style"
)

MONSTER_FRAMING = "one single creature, full body, centered, three quarter view"
MONSTER_STYLE_LOCK = (
    "dark medieval fantasy hand-painted illustration, classic RPG bestiary art, "
    "visible brushstrokes, muted earthy palette, semi-realistic, same look as fantasy NPC portrait"
)

MONSTER_VISUAL_EN: dict[str, str] = {
    "mob_main_1": "lime-green jelly slime blob, two small dark eyes, no limbs",
    "mob_main_2": "insect beetle bug, six legs, brown chitin carapace, mandibles, NOT humanoid",
    "mob_main_3": "gray feral rat beast, red eyes, long pink tail, on all fours",
    "mob_main_4": "green warty toad beast, bumpy skin, golden eyes, squat body",
    "wm_named_slime": "purple jelly slime blob, two eyes, small gold crown on top",
    "mob_mist_wraith": "pale gray swamp wraith, tattered hooded robes",
    "mob_mist_mosquito": "giant gray-red blood mosquito, long proboscis",
    "mob_mist_bogling": "brown mud bogling, squat muddy humanoid",
    "mob_mist_hydra": "green swamp hydra hatchling, two snake heads",
    "wm_mist_mother": "pale fog spirit woman, veiled gray mist dress",
    "wm_boss_titan": "stone-and-ember lava golem titan, cracked basalt body, magma veins",
    "mob_locb_cave_slime": "green mountain goblin, crude scrap armor",
    "mob_locb_amber_slime": "gray stone monitor lizard, rocky scales",
    "mob_locb_ash_hound": "gray granite guardian hound statue",
    "mob_stone_harpy": "brown-feathered mountain harpy, wings, talons",
    "wm_bone_warden": "white skeleton knight, horned skull helm",
    "mob_ash_slag": "orange molten slag slime blob, ash cinders",
    "mob_ash_burner": "smoldering charcoal ember humanoid",
    "mob_ash_golem": "bulky volcanic ash golem, dark rock",
    "mob_ash_salamander": "orange fire salamander, glowing scales",
    "wm_heat_overseer": "red-black demon foreman, dark iron armor",
    "mob_fang_scarab": "void-black shadow scarab beetle",
    "mob_fang_blade": "dark void wraith fused with living sword",
    "mob_fang_knight": "Rift Knight blackened plate armor",
    "mob_fang_herald": "mage purple robes with void staff",
    "wm_boss_varkan": "dragonoid boss violet abyss armor wings",
    "wm_event_wolf": "huge dark-fur alpha wolf, scarred muzzle",
}

MONSTER_NEGATIVE = (
    "cartoon, chibi, pixar, disney, anime, cute mascot, sticker, cel shaded, "
    "photorealistic, hyperrealistic, macro photo, wildlife photo, nature documentary, "
    "cgi, 3d render, octane, unreal engine, glossy plastic, "
    "character sheet, concept art, reference sheet, model sheet, turnaround, grid, 2x2, collage, "
    "multiple creatures, duplicate, blueprint, parchment, form, footer, text, labels, "
    "sky, trees, ground, floor, landscape, scenery, watermark, signature, UI"
)
