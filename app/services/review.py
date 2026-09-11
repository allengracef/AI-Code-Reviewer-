from app.services.aggregator import aggregate_issues
from app.services.analyzer import analyze_java, analyze_javascript, analyze_python
from app.services.ai_reviewer import review_with_ai


def review_code(source_code: str, language: str) -> dict:
    """
    Run static analysis (if available) and AI review for the given source code.

    Returns a dict with:
        language, summary, time_complexity, space_complexity, refactored_code, issues
    """
    static_issues: list[dict] = []

    if language == "python":
        static_issues = analyze_python(source_code)
    elif language == "javascript":
        static_issues = analyze_javascript(source_code)
    elif language == "java":
        static_issues = analyze_java(source_code)

    ai_issues: list[dict] = []
    summary = "Static analysis completed."
    tc = None
    sc = None
    refactored = None

    try:
        ai_result = review_with_ai(source_code, language)
        ai_issues = ai_result.get("issues", [])
        summary = ai_result.get("summary", "Code review completed.")
        tc = ai_result.get("time_complexity")
        sc = ai_result.get("space_complexity")
        refactored = ai_result.get("refactored_code")
    except Exception as err:
        print(f"AI review warning/error: {err}")
        if static_issues:
            summary = f"Static analysis found {len(static_issues)} issues."
        else:
            summary = "Analysis completed."

    issues = aggregate_issues(static_issues, ai_issues)

    return {
        "language": language,
        "summary": summary,
        "time_complexity": tc,
        "space_complexity": sc,
        "refactored_code": refactored,
        "issues": issues,
    }
