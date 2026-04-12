"""Unit tests for Nintendo transaction filtering logic used in fix_nintendo_category."""

import pytest


GAMES_UUID = "games-uuid-1234"
RAIFFEISEN_ACCOUNT_ID = "raiff-account-uuid"
OTHER_ACCOUNT_ID = "other-account-uuid"


def _make_tx(
    payee: str = "",
    income_account: str = RAIFFEISEN_ACCOUNT_ID,
    outcome_account: str = RAIFFEISEN_ACCOUNT_ID,
    tags: list[str] | None = None,
    deleted: bool = False,
) -> dict:
    """Helper to build a fake transaction dict for testing."""
    return {
        "payee": payee,
        "incomeAccount": income_account,
        "outcomeAccount": outcome_account,
        "tag": tags,
        "deleted": deleted,
        "outcome": 9.99,
        "income": 0.0,
        "date": "2026-03-01",
    }


def _should_update(tx: dict, raiffeisen_ids: set[str], category_uuid: str) -> bool:
    """Reproduce the filtering logic from fix_nintendo_category.py."""
    if tx["deleted"]:
        return False
    is_raiffeisen = (
        tx["incomeAccount"] in raiffeisen_ids or tx["outcomeAccount"] in raiffeisen_ids
    )
    if not is_raiffeisen:
        return False
    payee = (tx["payee"] or "").upper()
    if "NINTENDO" not in payee:
        return False
    existing_tags = tx["tag"] or []
    if category_uuid in existing_tags:
        return False
    return True


RAIFFEISEN_IDS = {RAIFFEISEN_ACCOUNT_ID}


def test_nintendo_transaction_without_tag_should_update():
    tx = _make_tx(payee="Nintendo")
    assert _should_update(tx, RAIFFEISEN_IDS, GAMES_UUID) is True


def test_nintendo_transaction_already_tagged_should_not_update():
    tx = _make_tx(payee="Nintendo", tags=[GAMES_UUID])
    assert _should_update(tx, RAIFFEISEN_IDS, GAMES_UUID) is False


def test_deleted_nintendo_transaction_should_not_update():
    tx = _make_tx(payee="Nintendo", deleted=True)
    assert _should_update(tx, RAIFFEISEN_IDS, GAMES_UUID) is False


def test_non_raiffeisen_nintendo_should_not_update():
    tx = _make_tx(
        payee="Nintendo",
        income_account=OTHER_ACCOUNT_ID,
        outcome_account=OTHER_ACCOUNT_ID,
    )
    assert _should_update(tx, RAIFFEISEN_IDS, GAMES_UUID) is False


def test_non_nintendo_raiffeisen_should_not_update():
    tx = _make_tx(payee="AMAZON")
    assert _should_update(tx, RAIFFEISEN_IDS, GAMES_UUID) is False


def test_nintendo_case_insensitive():
    tx = _make_tx(payee="nintendo switch online")
    assert _should_update(tx, RAIFFEISEN_IDS, GAMES_UUID) is True


def test_nintendo_with_other_existing_tags_should_update():
    tx = _make_tx(payee="Nintendo", tags=["some-other-tag"])
    assert _should_update(tx, RAIFFEISEN_IDS, GAMES_UUID) is True


def test_nintendo_on_income_raiffeisen_account():
    tx = _make_tx(
        payee="Nintendo",
        income_account=RAIFFEISEN_ACCOUNT_ID,
        outcome_account=OTHER_ACCOUNT_ID,
    )
    assert _should_update(tx, RAIFFEISEN_IDS, GAMES_UUID) is True
