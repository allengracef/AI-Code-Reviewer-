"""
Comprehensive tests for the review REST API endpoints.
Covers /upload and /paste endpoints with various scenarios.
"""
from io import BytesIO
from unittest.mock import patch


_MOCK_AI_RESULT = {
    "summary": "Code review completed.",
    "time_complexity": "O(n)",
    "space_complexity": "O(1)",
    "refactored_code": None,
    "issues": [
        {
            "code": "SEC001",
            "source": "AI",
            "severity": "HIGH",
            "category": "SECURITY",
            "message": "Hardcoded password detected.",
            "line": 2,
            "column": 1,
            "explanation": "Credentials should not be stored in source code.",
            "suggestion": "Use an environment variable.",
        },
        {
            "code": "SEC002",
            "source": "AI",
            "severity": "CRITICAL",
            "category": "SECURITY",
            "message": "Use of eval() with user-controlled input.",
            "line": 6,
            "column": 12,
            "explanation": "eval() can execute arbitrary Python code.",
            "suggestion": "Use a safe parser instead.",
        },
    ],
}


# ── /upload ───────────────────────────────────────────────────────────────────

def test_upload_python_file(client):
    code = """
import os

def test():
    unused_variable = 10
    return True
"""
    response = client.post(
        "/api/v1/reviews/upload",
        files={"file": ("test.py", code.encode("utf-8"), "text/x-python")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.py"
    assert data["language"] == "python"
    assert data["review"]["language"] == "python"
    assert isinstance(data["review"]["issues"], list)
    assert len(data["review"]["issues"]) > 0


def test_upload_java_file(client):
    code = """
public class Example {
    public String find() { return null; }
}
"""
    with patch("app.services.review.review_with_ai", return_value=_MOCK_AI_RESULT):
        response = client.post(
            "/api/v1/reviews/upload",
            files={"file": ("Example.java", code.encode("utf-8"), "text/x-java")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "java"
    assert isinstance(data["review"]["issues"], list)


def test_upload_javascript_file(client):
    code = """
function run(x) {
    console.log(x);
    return eval(x);
}
"""
    with patch("app.services.review.review_with_ai", return_value=_MOCK_AI_RESULT):
        response = client.post(
            "/api/v1/reviews/upload",
            files={"file": ("app.js", code.encode("utf-8"), "text/javascript")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "javascript"


def test_upload_unsupported_file(client):
    response = client.post(
        "/api/v1/reviews/upload",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_unsupported_extension_csv(client):
    response = client.post(
        "/api/v1/reviews/upload",
        files={"file": ("data.csv", b"a,b,c", "text/csv")},
    )
    assert response.status_code == 400


def test_upload_runs_complete_review_pipeline(client):
    code = """
password = "admin123"

def test():
    unused_variable = 10
    return eval(input())
"""
    with patch("app.services.review.review_with_ai", return_value=_MOCK_AI_RESULT):
        response = client.post(
            "/api/v1/reviews/upload",
            files={"file": ("test.py", BytesIO(code.encode("utf-8")), "text/x-python")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.py"
    assert data["language"] == "python"
    assert data["code"] == code
    assert "review" in data
    assert data["review"]["summary"] == "Code review completed."
    assert isinstance(data["review"]["issues"], list)
    assert len(data["review"]["issues"]) > 0


def test_upload_response_contains_all_fields(client):
    """Verify all expected top-level and review sub-fields are present."""
    code = "x = 1\n"
    with patch("app.services.review.review_with_ai", return_value={
        "summary": "OK",
        "time_complexity": "O(1)",
        "space_complexity": "O(1)",
        "refactored_code": None,
        "issues": [],
    }):
        response = client.post(
            "/api/v1/reviews/upload",
            files={"file": ("script.py", code.encode("utf-8"), "text/x-python")},
        )

    assert response.status_code == 200
    data = response.json()
    assert "filename" in data
    assert "language" in data
    assert "size" in data
    assert "code" in data
    assert "review" in data
    review = data["review"]
    assert "language" in review
    assert "summary" in review
    assert "issues" in review


# ── /paste ────────────────────────────────────────────────────────────────────

def test_paste_python_code(client):
    payload = {
        "filename": "snippet.py",
        "language": "python",
        "code": "import os\n\ndef foo():\n    x = 10\n",
    }
    with patch("app.services.review.review_with_ai", return_value=_MOCK_AI_RESULT):
        response = client.post("/api/v1/reviews/paste", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "python"
    assert "review" in data


def test_paste_javascript_code(client):
    payload = {
        "filename": "app.js",
        "language": "javascript",
        "code": "var x = eval(input);\nconsole.log(x);\n",
    }
    with patch("app.services.review.review_with_ai", return_value=_MOCK_AI_RESULT):
        response = client.post("/api/v1/reviews/paste", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "javascript"


def test_paste_java_code(client):
    payload = {
        "filename": "Example.java",
        "language": "java",
        "code": "public class Example { public String get() { return null; } }",
    }
    with patch("app.services.review.review_with_ai", return_value=_MOCK_AI_RESULT):
        response = client.post("/api/v1/reviews/paste", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "java"


def test_paste_empty_code_returns_400(client):
    payload = {
        "filename": "snippet.py",
        "language": "python",
        "code": "   ",
    }
    response = client.post("/api/v1/reviews/paste", json=payload)
    assert response.status_code == 400


def test_paste_response_has_review_keys(client):
    payload = {
        "filename": "hello.py",
        "language": "python",
        "code": "print('hello')\n",
    }
    with patch("app.services.review.review_with_ai", return_value={
        "summary": "Looks fine.",
        "time_complexity": None,
        "space_complexity": None,
        "refactored_code": None,
        "issues": [],
    }):
        response = client.post("/api/v1/reviews/paste", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "review" in data
    assert "summary" in data["review"]
    assert "issues" in data["review"]


# ── Review listing ────────────────────────────────────────────────────────────

def test_list_reviews_returns_paginated_response(client):
    """GET /api/v1/reviews/ should return a paginated structure."""
    response = client.get("/api/v1/reviews/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data


def test_list_reviews_empty_for_new_user(client):
    """A fresh test user should have no reviews yet."""
    response = client.get("/api/v1/reviews/")
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_get_nonexistent_review_returns_404(client):
    """Requesting a review that doesn't exist should return 404."""
    response = client.get("/api/v1/reviews/99999")
    assert response.status_code == 404


def test_delete_nonexistent_review_returns_404(client):
    """Deleting a review that doesn't exist should return 404."""
    response = client.delete("/api/v1/reviews/99999")
    assert response.status_code == 404