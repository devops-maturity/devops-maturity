from src.core.badge import get_badge_url

_SHIELDS_IO_BADGE_PREFIX = "https://img.shields.io/badge/"


def test_badge_wip():
    url = get_badge_url("WIP")
    assert "WIP" in url
    assert url.startswith(_SHIELDS_IO_BADGE_PREFIX)


def test_badge_passing():
    url = get_badge_url("PASSING")
    assert "PASSING" in url
    assert url.startswith(_SHIELDS_IO_BADGE_PREFIX)


def test_badge_bronze():
    url = get_badge_url("BRONZE")
    assert "BRONZE" in url
    assert url.startswith(_SHIELDS_IO_BADGE_PREFIX)


def test_badge_silver():
    url = get_badge_url("SILVER")
    assert "SILVER" in url
    assert url.startswith(_SHIELDS_IO_BADGE_PREFIX)


def test_badge_gold():
    url = get_badge_url("GOLD")
    assert "GOLD" in url
    assert url.startswith(_SHIELDS_IO_BADGE_PREFIX)


def test_badge_case_insensitive():
    assert get_badge_url("gold") == get_badge_url("GOLD")
    assert get_badge_url("wip") == get_badge_url("WIP")


def test_badge_unknown_level_defaults_to_wip():
    url = get_badge_url("UNKNOWN")
    assert "WIP" in url
