import os
import base64
from dotenv import load_dotenv
from openai import OpenAI
from src.core.config import config

load_dotenv()

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

IMAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "generated_images")
os.makedirs(IMAGE_DIR, exist_ok=True)


def generate_image(prompt: str) -> dict:
    """Generate an image using OpenAI. Returns dict with local path."""
    try:
        response = _client.images.generate(
            model=config["image"]["provider"],
            prompt=prompt,
            size=config["image"]["size"],
            quality=config["image"]["quality"],
            n=1,
        )

        image_data = response.data[0]
        filename = f"image_{abs(hash(prompt)) % 100000}.png"
        filepath = os.path.join(IMAGE_DIR, filename)

        # Handle both URL and b64_json responses
        if image_data.url:
            import requests
            img_response = requests.get(image_data.url)
            with open(filepath, "wb") as f:
                f.write(img_response.content)
        elif image_data.b64_json:
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(image_data.b64_json))
        else:
            return {"error": "No image data returned"}

        return {
            "local_path": filepath,
            "revised_prompt": getattr(image_data, "revised_prompt", prompt),
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    result = generate_image("A modern minimalist blog header about artificial intelligence, blue and white color scheme")
    print(result)