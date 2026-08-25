#!/usr/bin/env python3
"""KEYGEN — offline security suite. CS50P-compatible entry point."""

from __future__ import annotations

import sys

from core.generator import generate_password as _gen_pw
from core.generator import generate_pin as _gen_pin
from core.generator import fortify_password as _fortify
from core.passphrase import generate_passphrase as _gen_pp
from core.strength import analyze_generated, classify, observed_entropy


def generate_password(
    length: int = 16,
    uppercase: bool = True,
    lowercase: bool = True,
    digits: bool = True,
    symbols: bool = True,
    exclude_ambiguous: bool = False,
) -> str:
    """Top-level password generator (secrets-based)."""
    return _gen_pw(
        length=length,
        uppercase=uppercase,
        lowercase=lowercase,
        digits=digits,
        symbols=symbols,
        exclude_ambiguous=exclude_ambiguous,
    )


def generate_passphrase(word_count: int = 5, separator: str = "-") -> str:
    """Top-level passphrase generator (512-word list)."""
    return _gen_pp(word_count=word_count, separator=separator)


def calculate_strength(password: str, mode: str = "password") -> dict:
    """Return entropy bits, level, and crack-time estimate."""
    if mode == "passphrase":
        words = [w for w in password.replace(".", " ").replace("_", " ").replace("-", " ").split() if w]
        return analyze_generated(password, mode="passphrase", words=len(words))
    if mode == "pin":
        return analyze_generated(password, mode="pin")
    from core.strength import crack_time_label

    bits = observed_entropy(password)
    return {
        "bits": round(bits, 1),
        "level": classify(bits, password),
        "crack": crack_time_label(bits, password),
    }


def generate_pin(length: int = 6) -> str:
    return _gen_pin(length)


def fortify_password(password: str, extra: int = 8) -> str:
    return _fortify(password, extra)


def main() -> int:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QFont

    app = QApplication(sys.argv)
    app.setApplicationName("KEYGEN")
    app.setOrganizationName("KEYGEN")
    app.setApplicationDisplayName("KEYGEN")
    font = QFont("Segoe UI")
    font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    app.setFont(font)

    from app.main_window import MainWindow

    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
