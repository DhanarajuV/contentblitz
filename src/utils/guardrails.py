import re


def validate_input(user_message: str) -> tuple[bool, str]:
    """Validate user input. Returns (is_valid, error_message)."""
    if not user_message or not user_message.strip():
        return False, "Please enter a message."

    if len(user_message) > 5000:
        return False, "Message too long. Please keep it under 5000 characters."

    if len(user_message.strip()) < 3:
        return False, "Message too short. Please provide more detail."

    return True, ""


def validate_output_quality(content: str, content_type: str = "blog") -> dict:
    """Check content quality. Returns dict with score and suggestions."""
    issues = []
    score = 100

    if not content or not content.strip():
        return {"score": 0, "issues": ["Empty content generated"], "pass": False}

    word_count = len(content.split())

    if content_type == "blog":
        if word_count < 300:
            issues.append(f"Blog too short ({word_count} words). Aim for 800-1500 words.")
            score -= 30
        if "##" not in content and "**" not in content:
            issues.append("Missing headers or formatting. Blogs need structure.")
            score -= 15
        if not re.search(r'https?://', content):
            issues.append("No source links found. Consider adding citations.")
            score -= 10

    elif content_type == "linkedin":
        if word_count > 400:
            issues.append(f"LinkedIn post too long ({word_count} words). Keep under 300 words.")
            score -= 20
        if "#" not in content:
            issues.append("Missing hashtags. LinkedIn posts need 8-12 hashtags.")
            score -= 15
        if "?" not in content:
            issues.append("No question found. End with a question to drive engagement.")
            score -= 10

    return {
        "score": max(score, 0),
        "issues": issues,
        "pass": score >= 60,
        "word_count": word_count,
    }


# Words/patterns that indicate potentially inappropriate content
_BLOCKED_PATTERNS = [
    r'\b(hate|kill|violence|terrorist)\b',
    r'\b(scam|fraud|illegal)\b',
    r'\b(explicit|pornograph)\b',
]


def check_content_safety(text: str) -> tuple[bool, str]:
    """Basic content safety check. Returns (is_safe, reason)."""
    text_lower = text.lower()

    for pattern in _BLOCKED_PATTERNS:
        if re.search(pattern, text_lower):
            return False, f"Content may contain inappropriate material. Please revise your request."

    return True, ""