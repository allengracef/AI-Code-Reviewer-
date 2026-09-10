import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


# ── Python — ruff static analysis ────────────────────────────────────────────
def analyze_python(source_code: str) -> list[dict]:
    """Run ruff on a Python snippet and return normalized findings."""
    ruff_bin = Path(sys.executable).parent / "ruff"

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / "review.py"
        file_path.write_text(source_code, encoding="utf-8")

        result = subprocess.run(
            [str(ruff_bin), "check", str(file_path), "--output-format", "json"],
            capture_output=True,
            text=True,
        )

        if not result.stdout:
            return []

        issues = json.loads(result.stdout)
        return [
            {
                "code": issue["code"],
                "source": "STATIC_ANALYSIS",
                "severity": "LOW",
                "category": "STYLE",
                "message": issue["message"],
                "line": issue["location"]["row"],
                "column": issue["location"]["column"],
                "explanation": None,
                "suggestion": None,
            }
            for issue in issues
        ]


# ── JavaScript — pattern-based analysis ──────────────────────────────────────
_JS_PATTERNS: list[tuple[re.Pattern, str, str, str, str]] = [
    # (pattern, severity, category, message, suggestion)
    (
        re.compile(r"\beval\s*\(", re.MULTILINE),
        "HIGH", "SECURITY",
        "Use of eval() is a security risk — it executes arbitrary code.",
        "Replace eval() with a safer alternative such as JSON.parse() or a lookup table.",
    ),
    (
        re.compile(r"(?<![=!<>])==(?!=)", re.MULTILINE),
        "MEDIUM", "BUG",
        "Loose equality (==) performs type coercion and can produce unexpected results.",
        "Use strict equality (===) instead.",
    ),
    (
        re.compile(r"(?<![=!<>])!=(?!=)", re.MULTILINE),
        "MEDIUM", "BUG",
        "Loose inequality (!=) performs type coercion and can produce unexpected results.",
        "Use strict inequality (!==) instead.",
    ),
    (
        re.compile(r"^\s*var\s+", re.MULTILINE),
        "LOW", "BEST_PRACTICE",
        "var has function scope and is hoisted, which can lead to subtle bugs.",
        "Use const for values that don't change, or let for mutable bindings.",
    ),
    (
        re.compile(r"\bconsole\.(log|warn|error|debug)\s*\(", re.MULTILINE),
        "LOW", "BEST_PRACTICE",
        "console statement left in production code.",
        "Remove debug console statements before shipping, or use a structured logger.",
    ),
    (
        re.compile(r"\bdebugger\b", re.MULTILINE),
        "HIGH", "BEST_PRACTICE",
        "debugger statement found — this pauses execution in all browser dev tools.",
        "Remove all debugger statements before merging.",
    ),
    (
        re.compile(r"document\.write\s*\(", re.MULTILINE),
        "HIGH", "SECURITY",
        "document.write() can enable XSS attacks and breaks streaming HTML parsing.",
        "Use DOM manipulation methods such as textContent or innerHTML with sanitized input.",
    ),
    (
        re.compile(r"innerHTML\s*=\s*(?!\"\")", re.MULTILINE),
        "MEDIUM", "SECURITY",
        "Assigning to innerHTML with unsanitized input can cause XSS vulnerabilities.",
        "Sanitize input with DOMPurify, or use textContent for plain text.",
    ),
]


def analyze_javascript(source_code: str) -> list[dict]:
    """Run pattern-based static analysis on a JavaScript snippet."""
    findings: list[dict] = []
    lines = source_code.splitlines()

    for pattern, severity, category, message, suggestion in _JS_PATTERNS:
        for match in pattern.finditer(source_code):
            # Determine 1-based line number from match position.
            line_no = source_code[: match.start()].count("\n") + 1
            col_no = match.start() - source_code.rfind("\n", 0, match.start())
            findings.append(
                {
                    "code": None,
                    "source": "STATIC_ANALYSIS",
                    "severity": severity,
                    "category": category,
                    "message": message,
                    "line": line_no,
                    "column": col_no,
                    "explanation": None,
                    "suggestion": suggestion,
                }
            )

    return findings
