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