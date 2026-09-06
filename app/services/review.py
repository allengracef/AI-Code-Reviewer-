from app.services.aggregator import aggregate_issues
from app.services.analyzer import analyze_python
from app.services.ai_reviewer import review_with_ai


def review_code(source_code: str, language: str) -> dict:
    static_issues = []

    if language == "python":
        static_issues = analyze_python(source_code)

    ai_issues = review_with_ai(source_code, language)

    issues = aggregate_issues(
        static_issues,
        ai_issues,
    )

    return {
        "language": language,
        "summary": "Code review completed.",
        "issues": issues,
        "suggestions": [],
    }