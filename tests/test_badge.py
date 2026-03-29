from urllib.parse import urlparse
from src.core.badge import get_badge_url


def _assert_shields_url(url: str) -> None:
    """Assert that the URL is a valid shields.io badge URL."""
    parsed = urlparse(url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "img.shields.io"


class TestGetBadgeUrl:
    def test_wip_badge(self):
        url = get_badge_url("WIP")
        assert "WIP" in url
        _assert_shields_url(url)

    def test_passing_badge(self):
        url = get_badge_url("PASSING")
        assert "PASSING" in url
        _assert_shields_url(url)

    def test_bronze_badge(self):
        url = get_badge_url("BRONZE")
        assert "BRONZE" in url
        _assert_shields_url(url)

    def test_silver_badge(self):
        url = get_badge_url("SILVER")
        assert "SILVER" in url
        _assert_shields_url(url)

    def test_gold_badge(self):
        url = get_badge_url("GOLD")
        assert "GOLD" in url
        _assert_shields_url(url)

    def test_case_insensitive(self):
        assert get_badge_url("gold") == get_badge_url("GOLD")
        assert get_badge_url("bronze") == get_badge_url("BRONZE")

    def test_unknown_level_defaults_to_wip(self):
        url = get_badge_url("UNKNOWN_LEVEL")
        assert get_badge_url("WIP") == url

    def test_all_levels_return_different_urls(self):
        levels = ["WIP", "PASSING", "BRONZE", "SILVER", "GOLD"]
        urls = [get_badge_url(level) for level in levels]
        assert len(set(urls)) == len(levels)
