"""Normalize prompts into gf_lowpoly training / inference captions."""

from __future__ import annotations

import re

from style import FELINE_EYE_LOCK, SLIME_ENTRY_IDS, STYLE_NEGATIVE, TRIGGER_WORD

_LORA_TAG = re.compile(r"<lora:[^>]+>\s*", re.IGNORECASE)
_MULTI_COMMA = re.compile(r"\s*,\s*,+")
_BOOTSTRAP = re.compile(r"\b(?:OOTN64_Krea2|lowpoly_flux)\b,?\s*", re.IGNORECASE)

_OLD_EYE_PHRASES = (
    r"amber yellow feline cat eyes,?\s*",
    r"expressive slanted cat eyes,?\s*",
    r"expressive slanted feline cat eyes,?\s*",
    r"angular slanted feline cat eyes,?\s*",
    r"narrow cat pupils,?\s*",
    r"single large glowing eye in center of forehead,?\s*",
    r"\bfeline cat eyes\b,?\s*",
    r"\bcat eyes\b,?\s*",
)

_ENTRY_STRIP: dict[str, tuple[str, ...]] = {
    "bee": (r"cat face,?\s*",),
}


def clean_prompt_for_training(prompt: str) -> str:
    text = _LORA_TAG.sub("", prompt or "")
    text = _BOOTSTRAP.sub("", text)
    text = _MULTI_COMMA.sub(",", text)
    return text.strip(" ,\n\t")


def _strip_old_eyes(text: str) -> str:
    out = text
    for pat in _OLD_EYE_PHRASES:
        out = re.sub(pat, "", out, flags=re.IGNORECASE)
    return out


def normalize_training_caption(
    prompt: str,
    *,
    trigger: str = TRIGGER_WORD,
    entry_id: str | None = None,
    include_eye_lock: bool = True,
) -> str:
    """Build a training caption: no bootstrap LoRA tokens, one shared eye phrase."""
    cleaned = clean_prompt_for_training(prompt)
    for pat in _ENTRY_STRIP.get(entry_id or "", ()):
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)
    cleaned = _strip_old_eyes(cleaned)
    cleaned = _MULTI_COMMA.sub(",", cleaned).strip(" ,\n\t")

    if include_eye_lock and FELINE_EYE_LOCK:
        if FELINE_EYE_LOCK.lower() not in cleaned.lower():
            marker = "big angular head"
            idx = cleaned.lower().find(marker)
            if idx >= 0:
                insert_at = idx + len(marker)
                cleaned = f"{cleaned[:insert_at]}, {FELINE_EYE_LOCK}{cleaned[insert_at:]}"
            else:
                cleaned = f"{cleaned}, {FELINE_EYE_LOCK}" if cleaned else FELINE_EYE_LOCK

    if cleaned.lower().startswith(trigger.lower()):
        return cleaned
    return f"{trigger}, {cleaned}" if cleaned else trigger


def prompt_for_inference(prompt: str, *, entry_id: str | None = None) -> str:
    return normalize_training_caption(prompt, entry_id=entry_id)


def default_negative_prompt() -> str:
    return STYLE_NEGATIVE
