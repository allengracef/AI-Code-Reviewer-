from unittest.mock import MagicMock, patch

import pytest

from app.services.ai_reviewer import review_with_ai
import app.services.ai_reviewer

@pytest.fixture(autouse=True)
def reset_groq_client():
    app.services.ai_reviewer._groq_client = None


def mock_groq_response(content: str):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = content

    return mock_response


def test_ai_reviewer_returns_list():
    source_code = """
def add(a, b):
    return a + b
"""

    mock_response = mock_groq_response("[]")

    with patch("app.services.ai_reviewer.Groq") as mock_groq:
        mock_groq.return_value.chat.completions.create.return_value = mock_response

        result = review_with_ai(source_code, "python")

    assert isinstance(result, dict)
    assert result["issues"] == []


def test_ai_reviewer_accepts_different_languages():
    source_code = """
public class Test {
}
"""

    mock_response = mock_groq_response("[]")

    with patch("app.services.ai_reviewer.Groq") as mock_groq:
        mock_groq.return_value.chat.completions.create.return_value = mock_response

        result = review_with_ai(source_code, "java")

    assert isinstance(result, dict)
    assert result["issues"] == []


def test_ai_reviewer_rejects_invalid_json():
    source_code = """
def add(a, b):
    return a + b
"""

    mock_response = mock_groq_response("this is not json")

    with patch("app.services.ai_reviewer.Groq") as mock_groq:
        mock_groq.return_value.chat.completions.create.return_value = mock_response

        with pytest.raises(RuntimeError, match="invalid JSON"):
            review_with_ai(source_code, "python")


def test_ai_reviewer_rejects_non_list_json():
    source_code = """
def add(a, b):
    return a + b
"""

    mock_response = mock_groq_response('{"severity": "HIGH"}')

    with patch("app.services.ai_reviewer.Groq") as mock_groq:
        mock_groq.return_value.chat.completions.create.return_value = mock_response

        with pytest.raises(RuntimeError, match="JSON array"):
            review_with_ai(source_code, "python")


def test_ai_reviewer_rejects_invalid_issue_structure():
    source_code = """
def add(a, b):
    return a + b
"""

    invalid_issue = """
[
    {
        "severity": "HIGH"
    }
]
"""

    mock_response = mock_groq_response(invalid_issue)

    with patch("app.services.ai_reviewer.Groq") as mock_groq:
        mock_groq.return_value.chat.completions.create.return_value = mock_response

        with pytest.raises(
            RuntimeError,
            match="invalid issue structure"
        ):
            review_with_ai(source_code, "python")


def test_ai_reviewer_validates_real_findings():
    source_code = """
password = "admin123"

def calculate(users, transactions):
    for user in users:
        for transaction in transactions:
            print(user, transaction)

    return eval(input())
"""

    ai_response = """
[
    {
        "code": "SEC001",
        "source": "AI",
        "severity": "HIGH",
        "category": "SECURITY",
        "message": "Hardcoded password detected.",
        "line": 2,
        "column": 1,
        "explanation": "Credentials should not be stored directly in source code.",
        "suggestion": "Use environment variables or a secrets manager."
    },
    {
        "code": "SEC002",
        "source": "AI",
        "severity": "CRITICAL",
        "category": "SECURITY",
        "message": "Use of eval() with user-controlled input.",
        "line": 10,
        "column": 12,
        "explanation": "eval() can execute arbitrary Python code supplied by an attacker.",
        "suggestion": "Avoid eval() and use a safe parser for the expected input."
    },
    {
        "code": "PERF001",
        "source": "AI",
        "severity": "MEDIUM",
        "category": "PERFORMANCE",
        "message": "Nested loops may result in O(n²) time complexity.",
        "line": 5,
        "column": 5,
        "explanation": "Every user is compared with every transaction.",
        "suggestion": "Consider indexing or using a dictionary/set to avoid unnecessary comparisons."
    }
]
"""

    mock_response = mock_groq_response(ai_response)

    with patch("app.services.ai_reviewer.Groq") as mock_groq:
        mock_groq.return_value.chat.completions.create.return_value = mock_response

        result = review_with_ai(source_code, "python")

    assert isinstance(result, dict)
    issues = result["issues"]
    assert len(issues) == 3

    assert all(
        issue["source"] == "AI"
        for issue in issues
    )

    assert issues[0]["severity"] == "HIGH"
    assert issues[0]["category"] == "SECURITY"

    assert issues[1]["severity"] == "CRITICAL"
    assert issues[1]["category"] == "SECURITY"

    assert issues[2]["severity"] == "MEDIUM"
    assert issues[2]["category"] == "PERFORMANCE"