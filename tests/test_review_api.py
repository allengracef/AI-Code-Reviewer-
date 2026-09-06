from io import BytesIO
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_upload_python_file():
    code = """
import os

def test():
    unused_variable = 10
    return True
"""

    response = client.post(
        "/api/v1/reviews/upload",
        files={
            "file": (
                "test.py",
                code.encode("utf-8"),
                "text/x-python",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "test.py"
    assert data["language"] == "python"
    assert data["size"] == len(code.encode("utf-8"))
    assert data["review"]["language"] == "python"
    assert isinstance(data["review"]["issues"], list)
    assert len(data["review"]["issues"]) > 0


def test_upload_unsupported_file():
    response = client.post(
        "/api/v1/reviews/upload",
        files={
            "file": (
                "test.txt",
                b"hello world",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400


def test_upload_runs_complete_review_pipeline():
    code = """
password = "admin123"

def test():
    unused_variable = 10
    return eval(input())
"""

    ai_issues = [
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
    ]

    with patch(
        "app.services.review.review_with_ai",
        return_value=ai_issues,
    ):
        response = client.post(
            "/api/v1/reviews/upload",
            files={
                "file": (
                    "test.py",
                    BytesIO(code.encode("utf-8")),
                    "text/x-python",
                )
            },
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