"""Passphrase generation from the 512-word list."""

from __future__ import annotations

import secrets

from core.wordlist import WORDS

SEPARATORS = ("-", " ", ".", "_")


def generate_passphrase(word_count: int = 5, separator: str = "-") -> str:
    if word_count < 3 or word_count > 12:
        raise ValueError("Passphrase must use between 3 and 12 words.")
    if separator not in SEPARATORS:
        raise ValueError("Unsupported separator.")
    chosen = [secrets.choice(WORDS) for _ in range(word_count)]
    return separator.join(chosen)
