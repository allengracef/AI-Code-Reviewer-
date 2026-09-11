"""
Comprehensive tests for the review service pipeline.
Covers Python, JavaScript, Java review_code() calls with mocked AI reviewer.
"""
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
    assert len(result["issues"]) >= 3


def test_review_code_clean_java():
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
    assert result["issues"] == []


def test_review_code_javascript():
    source_code = """
function run(input) {
    var x = eval(input);
    console.log(x);
    return x;
}
"""
    result = review_code(source_code, "javascript")

    assert isinstance(result, dict)
    assert result["language"] == "javascript"
    assert isinstance(result["issues"], list)
    assert len(result["issues"]) > 0


def test_review_code_javascript_clean():
    source_code = """
function add(a, b) {
    return a + b;
}
"""
    result = review_code(source_code, "javascript")

    assert isinstance(result, dict)
    assert result["language"] == "javascript"
    assert isinstance(result["issues"], list)
    # No static issues expected for clean JS
    assert len(result["issues"]) == 0


def test_review_code_result_keys():
    """The result must always contain all required keys."""
    result = review_code("x = 1", "python")

    assert "language" in result
    assert "summary" in result
    assert "time_complexity" in result
    assert "space_complexity" in result
    assert "refactored_code" in result
    assert "issues" in result


def test_review_code_issues_are_dicts():
    """Each issue in the issues list must be a dictionary."""
    source_code = """
import sys

def bad():
    unused = 42
"""
    result = review_code(source_code, "python")

    for issue in result["issues"]:
        assert isinstance(issue, dict)
        assert "message" in issue
        assert "source" in issue
        assert "severity" in issue
        assert "category" in issue