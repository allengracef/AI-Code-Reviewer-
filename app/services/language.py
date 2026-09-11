LANGUAGE_MAP = {
    ".py": "python",
    ".java": "java",
    ".js": "javascript",
}


def detect_language(extension: str) -> str:
    """Return the canonical language name for a file extension."""
    return LANGUAGE_MAP[extension]