from app.services.analyzer import analyze_python


def test_analyze_python_detects_issues():
    source_code = """
import os
import typing

def test():
    unused_variable = 10
    return True
"""

    issues = analyze_python(source_code)

    assert isinstance(issues, list)
    assert len(issues) > 0


def test_analyze_python_clean_code():
    source_code = """
def add(a: int, b: int) -> int:
    return a + b
"""

    issues = analyze_python(source_code)

    assert isinstance(issues, list)