"""
Comprehensive tests for the aggregator module.
Covers: deduplication, multi-line grouping, empty inputs, edge cases.
"""
from app.services.aggregator import aggregate_issues


def _make_issue(message, category, line, source="STATIC_ANALYSIS", severity="LOW",
                explanation=None, suggestion=None, code=None):
    return {
        "code": code,
        "source": source,
        "severity": severity,
        "category": category,
        "message": message,
        "line": line,
        "column": 1,
        "explanation": explanation,
        "suggestion": suggestion,
    }


# ── Basic deduplication ───────────────────────────────────────────────────────

def test_aggregate_issues_removes_duplicate_findings():
    static_issues = [_make_issue("Undefined name `foo`", "STYLE", 5, code="F821")]
    ai_issues = [_make_issue("Undefined name `foo`", "STYLE", 5, source="AI",
                             severity="MEDIUM", code="AI001",
                             explanation="Variable used before definition.",
                             suggestion="Define `foo` first.")]

    result = aggregate_issues(static_issues, ai_issues)

    assert len(result) == 1
    assert result[0]["source"] == "AI"
    assert result[0]["explanation"] is not None
    assert result[0]["suggestion"] is not None


def test_aggregate_issues_keeps_different_findings():
    static_issues = [_make_issue("Unused import", "STYLE", 1, code="F401")]
    ai_issues = [_make_issue("Hardcoded password.", "SECURITY", 3, source="AI",
                             severity="HIGH", code="SEC001",
                             explanation="Don't hardcode credentials.",
                             suggestion="Use env vars.")]

    result = aggregate_issues(static_issues, ai_issues)

    assert len(result) == 2


def test_aggregate_issues_does_not_merge_same_line_different_categories():
    static_issues = [_make_issue("Problem detected.", "STYLE", 5)]
    ai_issues = [_make_issue("Problem detected.", "SECURITY", 5, source="AI",
                             severity="HIGH",
                             explanation="Security problem.",
                             suggestion="Fix security issue.")]

    result = aggregate_issues(static_issues, ai_issues)

    assert len(result) == 2


def test_aggregate_issues_keeps_findings_without_line_numbers():
    static_issues = [_make_issue("General style issue.", "STYLE", None)]
    ai_issues = [_make_issue("General style issue.", "STYLE", None, source="AI",
                             severity="MEDIUM",
                             explanation="Additional explanation.",
                             suggestion="Improve the style.")]

    result = aggregate_issues(static_issues, ai_issues)

    assert len(result) == 1
    assert result[0]["source"] == "AI"


def test_aggregate_issues_groups_same_issue_across_different_lines():
    static_issues = [
        _make_issue("Undefined variable `x`", "BUG", 5, code="F821",
                    explanation="Not defined.", suggestion="Define it."),
        _make_issue("Undefined variable `x`", "BUG", 15, code="F821",
                    explanation="Not defined.", suggestion="Define it."),
    ]
    ai_issues = [
        _make_issue("Undefined variable `x`", "BUG", 25, source="AI",
                    severity="MEDIUM", code="AI002",
                    explanation="Variable `x` referenced without definition.",
                    suggestion="Initialize `x` beforehand.")
    ]

    result = aggregate_issues(static_issues, ai_issues)

    assert len(result) == 1
    assert result[0]["line"] == "5, 15, 25"
    assert "Found on lines: 5, 15, 25" in result[0]["explanation"]


# ── Empty and minimal inputs ──────────────────────────────────────────────────

def test_aggregate_empty_both():
    result = aggregate_issues([], [])
    assert result == []


def test_aggregate_only_static_issues():
    issues = [_make_issue("Unused variable", "BEST_PRACTICE", 3)]
    result = aggregate_issues(issues, [])
    assert len(result) == 1
    assert result[0]["source"] == "STATIC_ANALYSIS"


def test_aggregate_only_ai_issues():
    issues = [_make_issue("SQL injection risk", "SECURITY", 10, source="AI",
                          severity="CRITICAL", explanation="User input not sanitized.",
                          suggestion="Use parameterized queries.")]
    result = aggregate_issues([], issues)
    assert len(result) == 1
    assert result[0]["source"] == "AI"


# ── Multi-issue scenarios ─────────────────────────────────────────────────────

def test_aggregate_multiple_distinct_issues_preserved():
    static_issues = [
        _make_issue("Unused import", "BEST_PRACTICE", 1, code="F401"),
        _make_issue("Line too long", "BEST_PRACTICE", 42, code="E501"),
        _make_issue("Missing return type", "BEST_PRACTICE", 10, code="ANN201"),
    ]
    ai_issues = [
        _make_issue("Hardcoded secret", "SECURITY", 5, source="AI",
                    severity="HIGH", explanation="Secret exposed.", suggestion="Use env var.")
    ]

    result = aggregate_issues(static_issues, ai_issues)

    assert len(result) == 4


def test_aggregate_single_line_badge_when_one_occurrence():
    static_issues = [_make_issue("Missing error handling", "ARCHITECTURE", 7)]
    result = aggregate_issues(static_issues, [])

    assert len(result) == 1
    # Single occurrence → line stays as integer or single value, NOT a comma string
    assert "," not in str(result[0]["line"])


def test_aggregate_ai_explanation_carried_over_to_merged():
    """When a static issue is merged with an AI issue, the AI explanation is kept."""
    static_issues = [_make_issue("eval() usage", "SECURITY", 12, explanation=None)]
    ai_issues = [_make_issue("eval() usage", "SECURITY", 12, source="AI",
                             severity="HIGH",
                             explanation="eval() executes arbitrary code.",
                             suggestion="Use JSON.parse() or a safe alternative.")]

    result = aggregate_issues(static_issues, ai_issues)

    assert len(result) == 1
    assert result[0]["explanation"] == "eval() executes arbitrary code."
    assert result[0]["suggestion"] is not None


def test_aggregate_three_occurrences_same_issue():
    """Three identical issues on different lines are merged into one with all locations."""
    issues = [
        _make_issue("console.log found", "BEST_PRACTICE", n, code="JS001")
        for n in [3, 17, 34]
    ]
    result = aggregate_issues(issues, [])

    assert len(result) == 1
    assert result[0]["line"] == "3, 17, 34"
    assert "Found on lines: 3, 17, 34" in result[0]["explanation"]