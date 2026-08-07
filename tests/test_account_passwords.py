"""Account password hashing and Intermediate login restore."""

from at_utility.passwords import (
    hash_password,
    unwrap_api_key,
    verify_password,
    wrap_api_key,
)


def test_password_roundtrip():
    stored = hash_password("correct-horse")
    assert verify_password("correct-horse", stored)
    assert not verify_password("wrong-horse", stored)


def test_api_key_wrap_roundtrip():
    secret = "unit-test-account-secret"
    raw = "sk-at-testkey_abcdefghijklmnopqrstuv"
    token = wrap_api_key(raw, secret)
    assert token != raw
    assert unwrap_api_key(token, secret) == raw
    assert unwrap_api_key(token, "other-secret") is None
