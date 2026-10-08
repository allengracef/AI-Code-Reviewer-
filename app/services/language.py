import re
from typing import Optional

LANGUAGE_MAP = {
    ".py": "python",
    ".pyw": "python",
    ".java": "java",
    ".jav": "java",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "javascript",
    ".tsx": "javascript",
}

_JAVA_PATTERNS = [
    re.compile(r"\bpublic\s+(?:static\s+)?(?:void|class|interface|enum|int|String|boolean|double|float|long)\b"),
    re.compile(r"\bSystem\.out\.(?:print|println|printf)\b"),
    re.compile(r"\bimport\s+java\.[a-zA-Z0-9_.*]+;"),
    re.compile(r"\bpackage\s+[a-zA-Z0-9_.]+;"),
    re.compile(r"\b(?:private|protected|public)\s+[A-Z][a-zA-Z0-9_]*\s+[a-zA-Z0-9_]+\s*[;=(]"),
    re.compile(r"\bnew\s+[A-Z][a-zA-Z0-9_]*\s*\("),
    re.compile(r"\bthrows\s+[A-Z][a-zA-Z0-9_]*Exception\b"),
]

_JS_PATTERNS = [
    re.compile(r"\b(?:const|let|var)\s+[a-zA-Z0-9_$]+\s*="),
    re.compile(r"\bconsole\.(?:log|warn|error|info|debug)\s*\("),
    re.compile(r"\bfunction\s*[a-zA-Z0-9_$]*\s*\("),
    re.compile(r"\b(?:=>|===|!==)\b"),
    re.compile(r"\b(?:document|window|localStorage|sessionStorage)\b"),
    re.compile(r"\b(?:require\s*\(|module\.exports|export\s+default|export\s+const)\b"),
    re.compile(r"\basync\s+function\b"),
    re.compile(r"\bJSON\.(?:parse|stringify)\b"),
]

_PY_PATTERNS = [
    re.compile(r"^\s*def\s+[a-zA-Z0-9_]+\s*\(", re.MULTILINE),
    re.compile(r"^\s*class\s+[a-zA-Z0-9_]+(?:\([a-zA-Z0-9_.,\s]*\))?:", re.MULTILINE),
    re.compile(r"^\s*(?:import\s+[a-zA-Z0-9_]+|from\s+[a-zA-Z0-9_.]+\s+import)", re.MULTILINE),
    re.compile(r"\bprint\s*\(", re.MULTILINE),
    re.compile(r"^\s*elif\s+.*:", re.MULTILINE),
    re.compile(r"\bself\.[a-zA-Z0-9_]+\b"),
    re.compile(r"\b__init__\b"),
]


def detect_language_from_code(code: str) -> str:
    """Analyze code syntax to determine if it is Java, JavaScript, or Python."""
    if not code or not code.strip():
        return "python"

    java_score = sum(len(p.findall(code)) for p in _JAVA_PATTERNS)
    js_score = sum(len(p.findall(code)) for p in _JS_PATTERNS)
    py_score = sum(len(p.findall(code)) for p in _PY_PATTERNS)

    scores = {
        "java": java_score,
        "javascript": js_score,
        "python": py_score,
    }

    best_lang = max(scores, key=scores.get)
    if scores[best_lang] > 0:
        return best_lang

    return "python"


def detect_language(
    extension: Optional[str] = None,
    code: Optional[str] = None,
    explicit_language: Optional[str] = None,
) -> str:
    """
    Return canonical language name ('python', 'javascript', 'java').
    Prioritizes explicit language selection, followed by file extension,
    falling back to code content analysis.
    """
    if explicit_language:
        lang = explicit_language.strip().lower()
        if lang in ("python", "py"):
            return "python"
        if lang in ("javascript", "js", "ts", "typescript"):
            return "javascript"
        if lang in ("java",):
            return "java"

    if extension:
        ext = extension.lower() if extension.startswith(".") else f".{extension.lower()}"
        if ext in LANGUAGE_MAP:
            # If the extension is default .py but code is clearly JS or Java, auto-correct it
            if ext == ".py" and code:
                detected_from_code = detect_language_from_code(code)
                if detected_from_code in ("javascript", "java"):
                    return detected_from_code
            return LANGUAGE_MAP[ext]

    if code:
        return detect_language_from_code(code)

    return "python"