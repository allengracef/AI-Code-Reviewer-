from app.services.aggregator import aggregate_issues


def test_aggregate_issues_removes_duplicate_findings():
    static_issues = [
        {
            "code": "F821",
            "severity": "LOW",
            "source": "STATIC_ANALYSIS",
            "category": "STYLE",
            "message": "Undefined name `foo`",
            "line": 5,
            "column": 1,
            "explanation": None,
            "suggestion": None,
        }
    ]

    ai_issues = [
        {
            "code": "AI001",
            "severity": "MEDIUM",
            "source": "AI",
            "category": "STYLE",
            "message": "Undefined name `foo`",
            "line": 5,
            "column": 1,
            "explanation": "The variable is used before being defined.",
            "suggestion": "Define `foo` before using it.",
        }
    ]

    result = aggregate_issues(static_issues, ai_issues)

    assert len(result) == 1
    assert result[0]["code"] == "AI001"
    assert result[0]["explanation"] is not None
    assert result[0]["suggestion"] is not None


def test_aggregate_issues_keeps_different_findings():
    static_issues = [
        {
            "code": "F401",
            "severity": "LOW",
            "source": "STATIC_ANALYSIS",
            "category": "STYLE",
            "message": "Unused import",
            "line": 1,
            "column": 1,
            "explanation": None,
            "suggestion": None,
        }
    ]

    ai_issues = [
        {
            "code": "SEC001",
            "severity": "HIGH",
            "source": "AI",
            "category": "SECURITY",
            "message": "Hardcoded password detected.",
            "line": 3,
            "column": 1,
            "explanation": "Credentials should not be stored in source code.",
            "suggestion": "Use an environment variable.",
        }
    ]

    result = aggregate_issues(static_issues, ai_issues)

    assert len(result) == 2


def test_aggregate_issues_does_not_merge_same_line_different_categories():
    static_issues = [
        {
            "code": "STYLE001",
            "severity": "LOW",
            "source": "STATIC_ANALYSIS",
            "category": "STYLE",
            "message": "Problem detected.",
            "line": 5,
            "column": 1,
            "explanation": None,
            "suggestion": None,
        }
    ]

    ai_issues = [
        {
            "code": "SEC001",
            "severity": "HIGH",
            "source": "AI",
            "category": "SECURITY",
            "message": "Problem detected.",
            "line": 5,
            "column": 1,
            "explanation": "Security problem.",
            "suggestion": "Fix the security issue.",
        }
    ]

    result = aggregate_issues(static_issues, ai_issues)

    assert len(result) == 2


def test_aggregate_issues_keeps_findings_without_line_numbers():
    static_issues = [
        {
            "code": "STYLE001",
            "severity": "LOW",
            "source": "STATIC_ANALYSIS",
            "category": "STYLE",
            "message": "General style issue.",
            "line": None,
            "column": None,
            "explanation": None,
            "suggestion": None,
        }
    ]

    ai_issues = [
        {
            "code": "AI001",
            "severity": "MEDIUM",
            "source": "AI",
            "category": "STYLE",
            "message": "General style issue.",
            "line": None,
            "column": None,
            "explanation": "Additional explanation.",
            "suggestion": "Improve the style.",
        }
    ]

    result = aggregate_issues(static_issues, ai_issues)

    assert len(result) == 2