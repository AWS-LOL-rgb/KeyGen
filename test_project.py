"""pytest suite for KEYGEN core functions."""

import string

import pytest

from core.generator import GeneratorError, generate_pin
from core.wordlist import WORDS
from project import calculate_strength, generate_passphrase, generate_password


def test_generate_password():
    pw = generate_password(16, True, True, True, True, False)
    assert len(pw) == 16
    assert any(c.isupper() for c in pw)
    assert any(c.islower() for c in pw)
    assert any(c.isdigit() for c in pw)
    assert any(c in "!@#$%^&*" for c in pw)

    pw8 = generate_password(8)
    assert len(pw8) == 8

    amb = generate_password(24, True, True, True, True, True)
    assert not any(c in "0Oo1lI|" for c in amb)

    with pytest.raises(GeneratorError):
        generate_password(16, False, False, False, False)

    with pytest.raises(GeneratorError):
        generate_password(3)

    with pytest.raises(GeneratorError):
        generate_password(80)

    a = generate_password(20)
    b = generate_password(20)
    assert a != b


def test_generate_passphrase():
    assert len(WORDS) == 512
    assert len(set(WORDS)) == 512
    pp = generate_passphrase(5, "-")
    parts = pp.split("-")
    assert len(parts) == 5
    assert all(w in WORDS for w in parts)

    spaced = generate_passphrase(4, " ")
    assert len(spaced.split(" ")) == 4

    with pytest.raises(ValueError):
        generate_passphrase(2)
    with pytest.raises(ValueError):
        generate_passphrase(20)
    with pytest.raises(ValueError):
        generate_passphrase(5, "/")


def test_calculate_strength():
    weak = calculate_strength("abc", "password")
    assert weak["level"] == "WEAK"
    assert weak["bits"] < 28

    strong = calculate_strength("A" * 20 + "a" * 20 + "1" * 10 + "!@#", "password")
    assert strong["bits"] > 40
    assert "level" in strong
    assert "crack" in strong

    pp = calculate_strength("able-about-above-abroad-absent-absorb", "passphrase")
    assert pp["bits"] == pytest.approx(6 * 9, abs=0.1)

    pin = calculate_strength("123456", "pin")
    assert pin["bits"] == pytest.approx(6 * 3.321928, abs=0.2)

    empty = calculate_strength("", "password")
    assert empty["bits"] == 0


def test_generate_pin():
    pin = generate_pin(6)
    assert len(pin) == 6
    assert pin.isdigit()
    with pytest.raises(GeneratorError):
        generate_pin(2)


def test_fortify_and_uniqueness():
    from project import fortify_password

    out = fortify_password("hello")
    assert out.startswith("hello")
    assert len(out) > 5
    with pytest.raises(GeneratorError):
        fortify_password("")
