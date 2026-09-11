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
    assert result["summary"] == "Code review completed."
    assert isinstance(result["issues"], list)
    assert len(result["issues"]) > 0


def test_review_code_java():
    source_code = """
public class Example {
    public String findUser(String id) {
        return null;
    }

    public void run() {
        try {
            Thread.sleep(1000);
        } catch (InterruptedException e) {}

        System.out.println("done");
    }
}
"""

    result = review_code(source_code, "java")

    assert isinstance(result, dict)
    assert result["language"] == "java"
    # Static analysis should catch at least: return null, empty catch, Thread.sleep, System.out
    assert len(result["issues"]) >= 3


def test_review_code_clean_java():
    """Clean Java code should produce no static-analysis issues."""
    source_code = """
public class Clean {
    public Optional<String> findUser(String id) {
        return Optional.of("user");
    }
}
"""
    result = review_code(source_code, "java")

    assert isinstance(result, dict)
    assert result["language"] == "java"
    # AI is mocked to return [] in conftest, static analysis should also find nothing
    assert result["issues"] == []