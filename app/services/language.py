LANGUAGE_MAP = {
    ".py": "python",
    ".java": "java",
    ".js": "javascript",
}
def detect_language(extension: str) ->str:
    return LANGUAGE_MAP[extension]