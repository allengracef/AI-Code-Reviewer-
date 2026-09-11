"""
Comprehensive tests for the static analysis module.
Covers Python (ruff), JavaScript (pattern-based), and Java (pattern-based) analyzers.
"""
import pytest
from app.services.analyzer import analyze_python, analyze_javascript, analyze_java


# ── Python (ruff) ─────────────────────────────────────────────────────────────

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
    assert all(issue["source"] == "STATIC_ANALYSIS" for issue in issues)


def test_analyze_python_clean_code():
    source_code = """
def add(a: int, b: int) -> int:
    return a + b
"""
    issues = analyze_python(source_code)
    assert isinstance(issues, list)


def test_analyze_python_detects_unused_import():
    source_code = """
import os

def hello():
    return "hello"
"""
    issues = analyze_python(source_code)
    codes = [i["code"] for i in issues]
    assert any("F401" in c for c in codes)


def test_analyze_python_issue_structure():
    """Every issue must contain required fields."""
    source_code = """
import sys
x = 1
"""
    issues = analyze_python(source_code)
    for issue in issues:
        assert "source" in issue
        assert issue["source"] == "STATIC_ANALYSIS"
        assert "severity" in issue
        assert "category" in issue
        assert "message" in issue
        assert "line" in issue


def test_analyze_python_empty_code():
    issues = analyze_python("")
    assert isinstance(issues, list)


def test_analyze_python_syntax_error_code():
    """Ruff should still process a file with a syntax error."""
    source_code = """
def broken(:
    pass
"""
    issues = analyze_python(source_code)
    assert isinstance(issues, list)


# ── JavaScript ────────────────────────────────────────────────────────────────

def test_analyze_javascript_detects_eval():
    source_code = """
function run(input) {
    return eval(input);
}
"""
    issues = analyze_javascript(source_code)
    messages = [i["message"] for i in issues]
    assert any("eval()" in m for m in messages)


def test_analyze_javascript_detects_loose_equality():
    source_code = """
if (x == 5) {
    console.log("match");
}
"""
    issues = analyze_javascript(source_code)
    messages = [i["message"] for i in issues]
    assert any("==" in m or "Loose equality" in m for m in messages)


def test_analyze_javascript_detects_var():
    source_code = """
var count = 0;
function increment() {
    var x = count + 1;
    return x;
}
"""
    issues = analyze_javascript(source_code)
    messages = [i["message"] for i in issues]
    assert any("var" in m for m in messages)


def test_analyze_javascript_detects_console_log():
    source_code = """
function debug(data) {
    console.log(data);
    return data;
}
"""
    issues = analyze_javascript(source_code)
    messages = [i["message"] for i in issues]
    assert any("console" in m for m in messages)


def test_analyze_javascript_detects_debugger():
    source_code = """
function run() {
    debugger;
    return true;
}
"""
    issues = analyze_javascript(source_code)
    messages = [i["message"] for i in issues]
    assert any("debugger" in m for m in messages)


def test_analyze_javascript_detects_inner_html():
    source_code = """
document.getElementById("output").innerHTML = userInput;
"""
    issues = analyze_javascript(source_code)
    messages = [i["message"] for i in issues]
    assert any("innerHTML" in m for m in messages)


def test_analyze_javascript_clean_code():
    source_code = """
function add(a, b) {
    return a + b;
}
"""
    issues = analyze_javascript(source_code)
    assert isinstance(issues, list)
    assert len(issues) == 0


def test_analyze_javascript_issue_structure():
    source_code = "eval('dangerous');"
    issues = analyze_javascript(source_code)
    for issue in issues:
        assert issue["source"] == "STATIC_ANALYSIS"
        assert "severity" in issue
        assert "category" in issue
        assert "message" in issue
        assert "line" in issue
        assert "suggestion" in issue


# ── Java ──────────────────────────────────────────────────────────────────────

def test_analyze_java_detects_return_null():
    source_code = """
public class Repo {
    public String findUser(String id) {
        return null;
    }
}
"""
    issues = analyze_java(source_code)
    messages = [i["message"] for i in issues]
    assert any("null" in m for m in messages)


def test_analyze_java_detects_empty_catch():
    source_code = """
public class App {
    public void run() {
        try {
            doSomething();
        } catch (Exception e) {}
    }
}
"""
    issues = analyze_java(source_code)
    messages = [i["message"] for i in issues]
    assert any("catch" in m.lower() for m in messages)


def test_analyze_java_detects_system_out():
    source_code = """
public class App {
    public void log(String msg) {
        System.out.println(msg);
    }
}
"""
    issues = analyze_java(source_code)
    messages = [i["message"] for i in issues]
    assert any("System.out" in m for m in messages)


def test_analyze_java_detects_thread_sleep():
    source_code = """
public class Worker {
    public void run() throws InterruptedException {
        Thread.sleep(1000);
    }
}
"""
    issues = analyze_java(source_code)
    messages = [i["message"] for i in issues]
    assert any("Thread.sleep" in m for m in messages)


def test_analyze_java_detects_hardcoded_url():
    source_code = """
public class Config {
    private static final String BASE_URL = "https://api.example.com/v1";
}
"""
    issues = analyze_java(source_code)
    messages = [i["message"] for i in issues]
    assert any("URL" in m or "IP" in m or "Hardcoded" in m for m in messages)


def test_analyze_java_clean_code():
    source_code = """
public class Clean {
    public Optional<String> findUser(String id) {
        return Optional.of("user");
    }
}
"""
    issues = analyze_java(source_code)
    assert isinstance(issues, list)
    assert len(issues) == 0


def test_analyze_java_issue_structure():
    source_code = """
public class Bad {
    public String get() { return null; }
}
"""
    issues = analyze_java(source_code)
    for issue in issues:
        assert issue["source"] == "STATIC_ANALYSIS"
        assert "severity" in issue
        assert "category" in issue
        assert "message" in issue
        assert "line" in issue