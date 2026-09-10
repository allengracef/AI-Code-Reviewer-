from app.services.aggregator import aggregate_issues
from app.services.analyzer import analyze_javascript, analyze_python
from app.services.ai_reviewer import review_with_ai


def review_code(source_code: str, language: str) -> dict:
    """
    Run static analysis (if available) and AI review for the given source code.

    Returns a dict with:
        language, summary, issues, suggestions
    """
    static_issues: list[dict] = []

    if language == "python":
        static_issues = analyze_python(source_code)
    elif language == "javascript":
        static_issues = analyze_javascript(source_code)

    ai_result = review_with_ai(source_code, language)
    ai_issues = ai_result["issues"]
    summary = ai_result["summary"]

    issues = aggregate_issues(static_issues, ai_issues)

    return {
        "language": language,
        "summary": summary,
        "issues": issues,
        "suggestions": [],
    }
