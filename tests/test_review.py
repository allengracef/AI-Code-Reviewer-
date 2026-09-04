from app.services.review import review_code


def test_review_code_python():
    source_code = """
import os

def test():
    unused_variable = 10
    return True
"""

    result = review_code(source_code, "python")

    assert isinstance(result, dict)
    assert result["language"] == "python"
    assert result["summary"] == "Static analysis completed."
    assert isinstance(result["issues"], list)
    assert isinstance(result["suggestions"], list)
    assert len(result["issues"]) > 0


def test_review_code_unsupported_language():
    source_code = """
public class Test {
}
"""

    result = review_code(source_code, "java")

    assert isinstance(result, dict)
    assert result["language"] == "java"
    assert result["issues"] == []
    assert result["suggestions"] == []