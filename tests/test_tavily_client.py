"""Tests for the Tavily integration client."""
from unittest.mock import patch, MagicMock
from src.integrations.tavily_client import search


class TestTavilySearch:
    @patch("src.integrations.tavily_client._client")
    def test_returns_formatted_results(self, mock_client):
        mock_client.search.return_value = {
            "results": [
                {"title": "Test Article", "url": "https://example.com", "content": "Some content here"},
                {"title": "Another Article", "url": "https://example2.com", "content": "More content"},
            ]
        }
        result = search("test query")
        assert "[1] Test Article" in result
        assert "https://example.com" in result
        assert "[2] Another Article" in result

    @patch("src.integrations.tavily_client._client")
    def test_no_results(self, mock_client):
        mock_client.search.return_value = {"results": []}
        result = search("obscure query")
        assert result == "No results found."

    @patch("src.integrations.tavily_client._client")
    def test_respects_max_results(self, mock_client):
        mock_client.search.return_value = {"results": []}
        search("test", max_results=3)
        mock_client.search.assert_called_with("test", max_results=3)

    @patch("src.integrations.tavily_client._client")
    def test_passes_days_filter(self, mock_client):
        mock_client.search.return_value = {"results": [
            {"title": "T", "url": "http://x.com", "content": "c"}
        ]}
        search("test", days=7)
        mock_client.search.assert_called_with("test", max_results=5, days=7)

    @patch("src.integrations.tavily_client._client")
    def test_no_days_filter_when_none(self, mock_client):
        mock_client.search.return_value = {"results": []}
        search("test", days=None)
        mock_client.search.assert_called_with("test", max_results=5)

    @patch("src.integrations.tavily_client._client")
    def test_content_truncated(self, mock_client):
        long_content = "x" * 500
        mock_client.search.return_value = {
            "results": [{"title": "T", "url": "http://x.com", "content": long_content}]
        }
        result = search("test")
        # Content should be truncated to 300 chars
        assert len(result) < 500

    @patch("src.integrations.tavily_client._client")
    def test_fallback_without_days(self, mock_client):
        # First call with days returns nothing, second without days returns results
        mock_client.search.side_effect = [
            {"results": []},
            {"results": [{"title": "Found", "url": "http://x.com", "content": "data"}]},
        ]
        result = search("test", days=30)
        assert "[1] Found" in result
        assert mock_client.search.call_count == 2
