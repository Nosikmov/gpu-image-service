"""Build exactly 100 curation prompts for style LoRA dataset collection."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from style import HOUSE_STYLE, MONSTER_FRAMING, MONSTER_STYLE_LOCK  # noqa: E402

STYLE_SUFFIX = (
    f"{MONSTER_STYLE_LOCK}, {HOUSE_STYLE}, {MONSTER_FRAMING}, "
    "single creature only, plain neutral gray background, no scenery, no text, no sheet"
)

LIGHTING_VARIANTS = (
    "soft warm torchlight",
    "cool moonlit highlights",
    "muted overcast daylight",
)

# Extra archetypes for style breadth (not all are in live seed yet).
GENERIC_CREATURES: list[tuple[str, str]] = [
    ("gen_dire_bear", "massive brown dire bear beast, scarred hide, roaring"),
    ("gen_cave_bat", "giant cave bat, leathery wings spread, fanged"),
    ("gen_iron_crab", "iron-plated dungeon crab, rusted pincers"),
    ("gen_moss_treant", "small moss treant sapling, root feet, glowing eyes"),
    ("gen_ice_wisp", "pale blue ice wisp spirit, floating orb core"),
    ("gen_flame_imp", "small red flame imp demon, pointed tail, mischievous grin"),
    ("gen_bone_hound", "skeletal hound beast, ribcage visible, glowing eye sockets"),
    ("gen_swamp_leech", "giant black swamp leech, segmented body, suckers"),
    ("gen_crystal_golem", "small crystal golem, amethyst shards, chunky limbs"),
    ("gen_poison_spider", "large toxic green spider, dripping fangs, hairy legs"),
    ("gen_storm_eel", "electric storm eel serpent, crackling scales"),
    ("gen_grave_gargoyle", "stone gargoyle beast, crouched wings, weathered"),
    ("gen_fungal_shambler", "fungal shambler humanoid, mushroom cap head, spores"),
    ("gen_sand_scorpion", "giant sand scorpion, chitin armor, raised tail"),
    ("gen_frost_wolf", "white frost wolf, icy breath, thick fur"),
    ("gen_magma_snail", "magma snail beast, shell of cooled rock, lava trail"),
    ("gen_void_moth", "void purple giant moth, dust wings, alien antennae"),
    ("gen_rust_automaton", "rusty clockwork automaton scout, gears exposed"),
    ("gen_amber_wasp", "giant amber wasp, translucent wings, stinger"),
    ("gen_bog_turtle", "armored bog turtle beast, moss shell, snapping jaw"),
    ("gen_shadow_stag", "shadow black stag beast, antlers of smoke"),
    ("gen_coal_elemental", "coal elemental humanoid, ember cracks, hunched"),
    ("gen_plague_rat_king", "plague rat king beast, crown of bone, swollen"),
    ("gen_thorn_lizard", "thorn-covered lizard beast, spiked back"),
    ("gen_abyss_fish", "abyssal deep fish monster, bioluminescent lure"),
    ("gen_cinder_bat", "cinder ash bat, ember wing membranes"),
    ("gen_mire_ooze", "dark mire ooze puddle beast, bubbles, single eye"),
    ("gen_rune_golem", "rune-carved stone golem fragment, glowing sigils"),
    ("gen_hollow_knight", "hollow black knight specter, tattered cape, no face"),
    ("gen_vine_serpent", "vine serpent beast, thorny coils, yellow eyes"),
    ("gen_slate_gryphon", "slate gray gryphon hatchling, small wings"),
    ("gen_blood_fly", "oversized blood-red horsefly beast, compound eyes"),
    ("gen_quartz_beetle", "quartz crystal beetle, faceted shell"),
    ("gen_peat_worm", "giant peat worm, segmented pink-gray body"),
    ("gen_ember_fox", "ember orange fox spirit beast, flame tail tips"),
    ("gen_slate_crab", "slate rock crab guardian, barnacle patches"),
    ("gen_mist_serpent", "mist gray sea serpent head, fog trailing"),
    ("gen_iron_boar", "iron-tusked war boar, bristled hide"),
    ("gen_obsidian_raven", "obsidian feather raven beast, glowing red eyes"),
    ("gen_sulfur_slime", "yellow sulfur slime blob, toxic fumes, no limbs"),
    ("gen_grave_rose", "walking grave rose plant monster, thorny stem legs"),
    ("gen_dust_wraith", "dust brown wraith silhouette, tattered strips"),
    ("gen_copper_wyrmling", "copper wyrmling dragon, small wings, fierce"),
    ("gen_lichen_troll", "small lichen-covered cave troll, hunched"),
    ("gen_night_mantis", "night black praying mantis beast, blade arms"),
    ("gen_ash_vulture", "ash gray vulture beast, ragged wings, hunched"),
]


def _entry(
    entry_id: str,
    prompt: str,
    *,
    category: str,
    monster_id: str | None = None,
    variant: str | None = None,
) -> dict[str, Any]:
    return {
        "id": entry_id,
        "prompt": prompt,
        "category": category,
        "monster_id": monster_id,
        "variant": variant,
    }


def build_prompt_pack() -> list[dict[str, Any]]:
    from style import MONSTER_VISUAL_EN

    entries: list[dict[str, Any]] = []

    for monster_id, visual in MONSTER_VISUAL_EN.items():
        entries.append(
            _entry(
                f"cat_{monster_id}",
                f"{visual}, {STYLE_SUFFIX}",
                category="catalog",
                monster_id=monster_id,
                variant="base",
            )
        )

    for idx, (monster_id, visual) in enumerate(MONSTER_VISUAL_EN.items()):
        light = LIGHTING_VARIANTS[idx % len(LIGHTING_VARIANTS)]
        entries.append(
            _entry(
                f"var_{monster_id}",
                f"{visual}, {light}, {STYLE_SUFFIX}",
                category="catalog_variant",
                monster_id=monster_id,
                variant=light,
            )
        )

    need = 100 - len(entries)
    if need > len(GENERIC_CREATURES):
        raise RuntimeError(f"Need {need} generic prompts but only {len(GENERIC_CREATURES)} defined")

    for entry_id, visual in GENERIC_CREATURES[:need]:
        entries.append(
            _entry(
                entry_id,
                f"{visual}, {STYLE_SUFFIX}",
                category="generic",
                variant="base",
            )
        )

    if len(entries) != 100:
        raise RuntimeError(f"Expected 100 prompts, got {len(entries)}")

    return entries


def write_prompt_pack(path: Path) -> list[dict[str, Any]]:
    pack = build_prompt_pack()
    payload = {
        "version": 1,
        "count": len(pack),
        "style_suffix": STYLE_SUFFIX,
        "trigger_word_suggestion": "gf_bestiary",
        "entries": pack,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return pack
