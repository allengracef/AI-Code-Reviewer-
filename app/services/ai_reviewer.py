import json
from typing import Any

from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.schemas.review import ReviewIssue

_groq_client: Groq | None = None


def _get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        if not settings.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not configured.")
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
    return _groq_client


def _strip_markdown_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def review_with_ai(source_code: str, language: str) -> dict[str, Any]:
    """
    Review source code using a Groq-hosted AI model.

    Returns a dict with keys:
        - "summary": str  — a concise overall assessment
        - "issues": list[dict]  — validated issue dicts
    """
    client = _get_groq_client()

    prompt = (
        "You are a senior software engineer performing a rigorous code review.\n\n"
        f"Review the following {language} source code.\n\n"

        "Your job is to identify meaningful problems that could affect:\n"
        "- Correctness and bugs\n"
        "- Security\n"
        "- Performance and algorithmic complexity\n"
        "- Architecture and design\n"
        "- Readability\n"
        "- Maintainability\n"
        "- Reliability and error handling\n"
        "- Best practices\n\n"

        "IMPORTANT RULES:\n"
        "1. Do not report trivial formatting or lint issues.\n"
        "2. Do not duplicate issues that a standard linter would detect.\n"
        "3. Only report an issue when you can explain why it is a real problem.\n"
        "4. Consider the actual behavior of the code, not just individual lines.\n"
        "5. Look for edge cases and failure scenarios.\n"
        "6. Look for inefficient algorithms such as unnecessary O(n²) operations.\n"
        "7. Look for hardcoded secrets, credentials, or sensitive information.\n"
        "8. Look for unsafe input handling and security vulnerabilities.\n"
        "9. Look for incorrect error handling and resource management.\n"
        "10. Look for design choices that make the code difficult to maintain.\n"
        "11. Do not invent problems that are not supported by the code.\n"
        "12. If the code is good, return an empty issues array instead of inventing issues.\n\n"

        "Severity guidelines:\n"
        "- LOW: Minor issue with limited impact.\n"
        "- MEDIUM: Real issue that should be addressed.\n"
        "- HIGH: Serious bug, security problem, or performance issue.\n"
        "- CRITICAL: Severe security vulnerability or issue that could cause "
        "major damage or system failure.\n\n"

        "Category guidelines:\n"
        "- BUG: Incorrect behavior or logic error.\n"
        "- SECURITY: Security vulnerability or unsafe handling of data.\n"
        "- PERFORMANCE: Inefficient computation, memory usage, or resource usage.\n"
        "- ARCHITECTURE: Structural or design problem.\n"
        "- READABILITY: Code that is unnecessarily difficult to understand.\n"
        "- MAINTAINABILITY: Code that will be difficult to modify or extend.\n"
        "- BEST_PRACTICE: Violation of an important engineering practice.\n\n"

        "Return ONLY valid JSON — no Markdown, no prose outside the JSON.\n\n"

        "Return a single JSON object with exactly these keys:\n"
        '  "summary": a concise 1-3 sentence overall assessment of the code quality.\n'
        '  "time_complexity": Big O notation for time complexity (if applicable, e.g., "O(n^2)").\n'
        '  "space_complexity": Big O notation for space complexity (if applicable, e.g., "O(1)").\n'
        '  "refactored_code": a fully refactored, better structured version of the code resolving the issues (omit if the code is already perfect).\n'
        '  "issues": an array of issue objects.\n\n'
        
        "Each issue object must contain exactly these fields:\n"
        "- code\n"
        "- severity\n"
        "- category\n"
        "- message\n"
        "- line\n"
        "- column\n"
        "- explanation\n"
        "- suggestion\n\n"

        "Do NOT include a source field — the application assigns it.\n\n"

        "Allowed severity values: LOW, MEDIUM, HIGH, CRITICAL\n"
        "Allowed category values: BUG, SECURITY, PERFORMANCE, ARCHITECTURE, "
        "READABILITY, MAINTAINABILITY, BEST_PRACTICE\n\n"

        "Example response shape:\n"
        '{"summary": "Overall the code is...", "time_complexity": "O(n)", "space_complexity": "O(1)", "refactored_code": "def func():\\n    pass", "issues": [...]}\n\n'

        "Source code:\n\n"
        f"{source_code}"
    )

    response = _get_groq_client().chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional code-review AI. "
                    "Always return valid JSON and nothing else."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.1,
        timeout=60,
    )

    content = response.choices[0].message.content or ""
    content = _strip_markdown_fences(content)

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("The AI returned invalid JSON.") from exc

    if isinstance(data, list):
        issues_raw = data
        summary = "Code review completed."
        tc, sc, refactored = None, None, None
    elif isinstance(data, dict):
        if "issues" not in data:
            raise RuntimeError("The AI response 'issues' must be a JSON array.")
        issues_raw = data["issues"]
        summary = data.get("summary", "Code review completed.")
        tc = data.get("time_complexity")
        sc = data.get("space_complexity")
        refactored = data.get("refactored_code")
    else:
        raise RuntimeError("Unexpected AI response shape.")

    if not isinstance(issues_raw, list):
        raise RuntimeError("The AI response 'issues' must be a JSON array.")

    for issue in issues_raw:
        if isinstance(issue, dict):
            issue["source"] = "AI"

    try:
        validated = [ReviewIssue.model_validate(issue) for issue in issues_raw]
    except Exception as exc:
        raise RuntimeError("The AI returned an invalid issue structure.") from exc

    return {
        "summary": summary,
        "time_complexity": tc,
        "space_complexity": sc,
        "refactored_code": refactored,
        "issues": [issue.model_dump() for issue in validated],
    }
