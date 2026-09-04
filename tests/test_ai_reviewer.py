from app.services.ai_reviewer import review_with_ai


def test_ai_reviewer_returns_list():
    source_code = """
def add(a, b):
    return a + b
"""

    result = review_with_ai(source_code, "python")

    assert isinstance(result, list)


def test_ai_reviewer_accepts_different_languages():
    source_code = """
public class Test {
}
"""

    result = review_with_ai(source_code, "java")

    assert isinstance(result, list)