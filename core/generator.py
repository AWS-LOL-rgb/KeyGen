"""Cryptographically secure password / PIN / fortifier generation."""

from __future__ import annotations

import secrets
import string

UPPER = string.ascii_uppercase
LOWER = string.ascii_lowercase
DIGITS = string.digits
SYMBOLS = "!@#$%^&*"
AMBIGUOUS = set("0Oo1lI|")


class GeneratorError(ValueError):
    """Raised when generation parameters are invalid."""


def _pool(
    uppercase: bool,
    lowercase: bool,
    digits: bool,
    symbols: bool,
    exclude_ambiguous: bool,
) -> tuple[str, list[str]]:
    classes: list[str] = []
    if uppercase:
        classes.append(UPPER)
    if lowercase:
        classes.append(LOWER)
    if digits:
        classes.append(DIGITS)
    if symbols:
        classes.append(SYMBOLS)
    if not classes:
        raise GeneratorError("Enable at least one character category.")

    def filt(s: str) -> str:
        if not exclude_ambiguous:
            return s
        return "".join(ch for ch in s if ch not in AMBIGUOUS)

    filtered = [filt(c) for c in classes]
    if any(len(c) == 0 for c in filtered):
        raise GeneratorError("Ambiguous exclusion emptied a selected category.")
    pool = "".join(filtered)
    if not pool:
        raise GeneratorError("Character pool is empty.")
    return pool, filtered


def generate_password(
    length: int = 16,
    uppercase: bool = True,
    lowercase: bool = True,
    digits: bool = True,
    symbols: bool = True,
    exclude_ambiguous: bool = False,
) -> str:
    """Generate a password using secrets. Each enabled class appears at least once."""
    if length < 4 or length > 64:
        raise GeneratorError("Password length must be between 4 and 64.")
    pool, classes = _pool(uppercase, lowercase, digits, symbols, exclude_ambiguous)
    if length < len(classes):
        raise GeneratorError(
            f"Length {length} is too short for {len(classes)} character classes."
        )
    chars: list[str] = [secrets.choice(cls) for cls in classes]
    remaining = length - len(chars)
    chars.extend(secrets.choice(pool) for _ in range(remaining))
    # Fisher–Yates with secrets
    for i in range(len(chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        chars[i], chars[j] = chars[j], chars[i]
    return "".join(chars)


def generate_pin(length: int = 6) -> str:
    if length < 4 or length > 16:
        raise GeneratorError("PIN length must be between 4 and 16.")
    return "".join(secrets.choice(DIGITS) for _ in range(length))


def fortify_password(password: str, extra: int = 8) -> str:
    """Append cryptographically random mixed characters to strengthen a password."""
    if not password:
        raise GeneratorError("Enter a password to fortify.")
    extra = max(4, min(24, extra))
    suffix = generate_password(
        length=extra,
        uppercase=True,
        lowercase=True,
        digits=True,
        symbols=True,
        exclude_ambiguous=False,
    )
    return password + suffix


def count_classes(password: str) -> dict[str, int]:
    return {
        "upper": sum(1 for c in password if c in UPPER),
        "lower": sum(1 for c in password if c in LOWER),
        "digits": sum(1 for c in password if c in DIGITS),
        "symbols": sum(1 for c in password if c not in string.ascii_letters + string.digits),
    }
