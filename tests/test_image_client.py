"""Tests for the image generation client."""
from unittest.mock import patch, MagicMock
from src.integrations.image_client import generate_image, IMAGE_DIR
import os


class TestImageClient:
    @patch("src.integrations.image_client._client")
    def test_generates_image_with_b64(self, mock_client):
        import base64
        fake_image = base64.b64encode(b"fake png data").decode()

        mock_response = MagicMock()
        mock_response.data = [MagicMock(url=None, b64_json=fake_image, revised_prompt="enhanced prompt")]
        mock_client.images.generate.return_value = mock_response

        result = generate_image("test prompt")
        assert "local_path" in result
        assert result["local_path"].endswith(".png")
        assert "revised_prompt" in result

        # Clean up
        if os.path.exists(result["local_path"]):
            os.remove(result["local_path"])

    @patch("src.integrations.image_client._client")
    def test_generates_image_with_url(self, mock_client):
        mock_response = MagicMock()
        mock_response.data = [MagicMock(url="https://example.com/img.png", b64_json=None, revised_prompt="prompt")]
        mock_client.images.generate.return_value = mock_response

        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(content=b"fake image bytes")
            result = generate_image("test prompt")

        assert "local_path" in result
        # Clean up
        if os.path.exists(result.get("local_path", "")):
            os.remove(result["local_path"])

    @patch("src.integrations.image_client._client")
    def test_handles_api_error(self, mock_client):
        mock_client.images.generate.side_effect = Exception("API Error")
        result = generate_image("test")
        assert "error" in result
        assert "API Error" in result["error"]

    @patch("src.integrations.image_client._client")
    def test_handles_no_image_data(self, mock_client):
        mock_response = MagicMock()
        mock_response.data = [MagicMock(url=None, b64_json=None)]
        mock_client.images.generate.return_value = mock_response

        result = generate_image("test")
        assert "error" in result

    def test_image_dir_exists(self):
        assert os.path.isdir(IMAGE_DIR)
