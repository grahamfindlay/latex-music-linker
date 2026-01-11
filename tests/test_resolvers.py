from unittest.mock import MagicMock, patch

from latex_music_linker.resolvers import smart_link_resolver


def test_smart_link_resolver_detects_not_found():
    """Should return None smartlink_url when song.link returns not-found."""
    mock_response = MagicMock()
    mock_response.url = "https://song.link/not-found"

    with patch("latex_music_linker.resolvers.requests.get", return_value=mock_response):
        result = smart_link_resolver("https://music.apple.com/us/album/123")

    assert result["smartlink_url"] is None
    assert "not-found" in result.get("error", "")


def test_smart_link_resolver_detects_not_found_with_trailing_path():
    """Should detect not-found even with variations in the URL path."""
    mock_response = MagicMock()
    mock_response.url = "https://odesli.co/not-found"

    with patch("latex_music_linker.resolvers.requests.get", return_value=mock_response):
        result = smart_link_resolver("https://music.apple.com/us/album/123")

    assert result["smartlink_url"] is None
    assert "not-found" in result.get("error", "")


def test_smart_link_resolver_success():
    """Should return smartlink_url on successful resolution."""
    mock_response = MagicMock()
    mock_response.url = "https://album.link/i/1833088041"

    with patch("latex_music_linker.resolvers.requests.get", return_value=mock_response):
        result = smart_link_resolver("https://music.apple.com/us/album/123")

    assert result["smartlink_url"] == "https://album.link/i/1833088041"
    assert "error" not in result
