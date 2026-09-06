import pytest
import app.services.ai_reviewer
from unittest.mock import patch

@pytest.fixture(autouse=True)
def reset_groq_client():
    app.services.ai_reviewer._groq_client = None

@pytest.fixture(autouse=True)
def mock_review_with_ai_in_review_tests(request):
    if "test_review.py" in request.node.nodeid:
        with patch("app.services.ai_reviewer.review_with_ai") as mock_review:
            mock_review.return_value = []
            yield mock_review
    else:
        yield
