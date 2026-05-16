from langchain_core.tools import tool
from src.agents.base_agent import BaseAgent
from src.core.config import config
from src.integrations.image_client import generate_image


@tool
def create_image(prompt: str) -> str:
    """Generate an image using AI. Provide a detailed, descriptive prompt.

    Args:
        prompt: Detailed image description including style, colors, composition, and mood.
    """
    result = generate_image(prompt)
    if "error" in result:
        return f"Image generation failed: {result['error']}"
    return f"Image generated successfully!\nSaved to: {result['local_path']}\nPrompt used: {result['revised_prompt']}"


class ImageAgent(BaseAgent):
    """Generates images with optimized prompts."""

    def __init__(self):
        system_prompt = f"""You are {config['app']['name']}'s Image Generation Agent.

Your role:
- Create high-quality images for blog posts, social media, and marketing
- Optimize user requests into detailed image generation prompts
- Use the create_image tool with enhanced prompts

Prompt optimization rules:
- Add style descriptors: "professional", "modern", "minimalist", "photorealistic"
- Specify composition: "centered", "wide shot", "close-up", "flat lay"
- Include color guidance: specific palette or mood-based colors
- Add lighting: "soft lighting", "natural light", "dramatic shadows"
- Mention format: "blog header", "social media post", "infographic style"
- Avoid text in images (AI struggles with text rendering)

When the user gives a vague request like "image for my blog about AI":
- Enhance it to: "A modern minimalist blog header illustration showing abstract neural network connections with a gradient from deep blue to teal, clean professional style, soft lighting, no text"

ALWAYS use the create_image tool — never just describe what an image could look like."""

        super().__init__(
            name="Image Generation Agent",
            system_prompt=system_prompt,
            tools=[create_image],
        )

