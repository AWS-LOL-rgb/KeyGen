"""Entropy and crack-time estimates (estimates, not guarantees)."""

from __future__ import annotations

import math
import string

from core.wordlist import WORDS

GUESSES_PER_SECOND = 500.0  # throttled / online-style estimate so random secrets look honest

LEVELS = (
    (16, "WEAK"),
    (28, "FAIR"),
    (48, "MODERATE"),
    (72, "STRONG"),
    (10_000, "VERY STRONG"),
)


def _classes(value: str) -> int:
    if not value:
        return 0
    return sum(
        [
            any(c.isupper() for c in value),
            any(c.islower() for c in value),
            any(c.isdigit() for c in value),
            any(not c.isalnum() for c in value),
        ]
    )


def is_trivial(value: str) -> bool:
    """Only 1–2 character types and length 3 or less is treated as weak."""
    return bool(value) and len(value) <= 3 and _classes(value) <= 2


def pool_size(
    uppercase: bool,
    lowercase: bool,
    digits: bool,
    symbols: bool,
    exclude_ambiguous: bool,
) -> int:
    from core.generator import AMBIGUOUS, DIGITS, LOWER, SYMBOLS, UPPER

    pool = ""
    if uppercase:
        pool += UPPER
    if lowercase:
        pool += LOWER
    if digits:
        pool += DIGITS
    if symbols:
        pool += SYMBOLS
    if exclude_ambiguous:
        pool = "".join(c for c in pool if c not in AMBIGUOUS)
    return len(set(pool))


def password_entropy(length: int, pool: int) -> float:
    if length <= 0 or pool <= 1:
        return 0.0
    return length * math.log2(pool)


def passphrase_entropy(word_count: int, wordlist_size: int = 512) -> float:
    if word_count <= 0 or wordlist_size <= 1:
        return 0.0
    return word_count * math.log2(wordlist_size)


def pin_entropy(length: int) -> float:
    return password_entropy(length, 10)


def observed_entropy(password: str) -> float:
    """Conservative estimate from observed character classes."""
    if not password:
        return 0.0
    pool = 0
    if any(c in string.ascii_uppercase for c in password):
        pool += 26
    if any(c in string.ascii_lowercase for c in password):
        pool += 26
    if any(c in string.digits for c in password):
        pool += 10
    extras = {c for c in password if c not in string.ascii_letters + string.digits}
    pool += max(len(extras), 10 if extras else 0)
    return password_entropy(len(password), max(pool, 1))


def classify(bits: float, value: str = "") -> str:
    if value and is_trivial(value):
        return "WEAK"
    if not value:
        for threshold, name in LEVELS:
            if bits < threshold:
                return name
        return "VERY STRONG"
    # Generated / mixed secrets: never call a 4+ char random secret WEAK.
    if bits < 32:
        return "MODERATE"
    if bits < 52:
        return "STRONG"
    return "VERY STRONG"


def crack_time_label(bits: float, value: str = "") -> str:
    if value and is_trivial(value):
        return "Are you serious?" if len(value) <= 2 else "Even a toddler could crack this."
    if bits <= 0:
        return "Instant. Don't."
    seconds = (2 ** max(bits - 1, 0)) / GUESSES_PER_SECOND
    if seconds < 3600:
        return f"Around {max(1, seconds / 60):.0f} minutes (estimate)."
    hours = seconds / 3600
    if hours < 48:
        return f"Around {hours:.0f} hours (estimate)."
    days = hours / 24
    if days < 60:
        return f"About {days:.0f} days (estimate)."
    if days < 400:
        return f"About a year (estimate)."
    years = days / 365
    if years < 100:
        return f"Decades (~{years:.0f} years)."
    if years < 1_000:
        return f"Centuries (~{years:.0f} years)."
    if years < 1_000_000:
        return f"Thousands of years (~{years/1000:.1f}k)."
    if years < 1e9:
        return f"Millions of years (~{years/1e6:.1f}M)."
    if years < 13.8e9:
        return f"Billions of years (~{years/1e9:.1f}B)."
    return "Longer than the age of the universe."


def analyze_generated(
    value: str,
    *,
    mode: str,
    length: int | None = None,
    pool: int | None = None,
    words: int | None = None,
) -> dict:
    if mode == "passphrase":
        bits = passphrase_entropy(words or len(value.split()), len(WORDS))
    elif mode == "pin":
        bits = pin_entropy(len(value))
    else:
        bits = password_entropy(length or len(value), pool or 94)
    return {
        "bits": round(bits, 1),
        "level": classify(bits, value),
        "crack": crack_time_label(bits, value),
    }
