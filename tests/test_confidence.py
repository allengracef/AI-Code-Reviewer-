"""
Unit tests for Evidence-Weighted Code Confidence & Risk Analysis.
"""

from app.services.confidence import (
    _eval_code_context,
    _eval_dependency_resolution,
    _eval_framework_detection,
    _eval_rule_agreement,
    _eval_syntax_parsing,
    _eval_test_evidence,
    _eval_type_information,
    compute_evidence_confidence,
    compute_risk_score,
)


def test_syntax_parsing_clean_python():
    code = "def add(a: int, b: int) -> int:\n    return a + b\n"
    pts, unknowns, parsed, total = _eval_syntax_parsing(code, "python")
    assert pts == 20
    assert len(unknowns) == 0
    assert parsed == total


def test_syntax_parsing_broken_python():
    code = "def broken(:\n    pass\n"
    pts, unknowns, parsed, total = _eval_syntax_parsing(code, "python")
    assert pts < 20
    assert len(unknowns) > 0
    assert "syntax error" in unknowns[0].lower()


def test_syntax_parsing_js_eval_penalty():
    code = "function test(input) {\n    return eval(input);\n}\n"
    pts, unknowns, parsed, total = _eval_syntax_parsing(code, "javascript")
    assert pts < 20
    assert any("eval()" in u for u in unknowns)


def test_type_information_python_typed():
    code = "from typing import List\ndef process(items: List[str]) -> int:\n    return len(items)\n"
    pts, unknowns = _eval_type_information(code, "python")
    assert pts == 15
    assert len(unknowns) == 0


def test_type_information_python_untyped():
    code = "def process(items):\n    return len(items)\n"
    pts, unknowns = _eval_type_information(code, "python")
    assert pts < 15
    assert any("untyped" in u.lower() for u in unknowns)


def test_dependency_resolution_stdlib():
    code = "import json\nimport sys\nimport os\n"
    pts, unknowns = _eval_dependency_resolution(code, "python")
    assert pts == 15
    assert len(unknowns) == 0


def test_dependency_resolution_unresolved():
    code = "import internal_security_module\n"
    pts, unknowns = _eval_dependency_resolution(code, "python")
    assert pts < 15
    assert any("internal_security_module" in u for u in unknowns)


def test_framework_detection_fastapi():
    code = "from fastapi import FastAPI\napp = FastAPI()\n"
    pts, unknowns, name = _eval_framework_detection(code, "python")
    assert pts == 10
    assert "FastAPI" in name


def test_framework_detection_spring_boot():
    code = "import org.springframework.stereotype.Service;\n@Service\npublic class AppService {}\n"
    pts, unknowns, name = _eval_framework_detection(code, "java")
    assert pts == 10
    assert "Spring Boot" in name


def test_test_evidence_detection():
    code = "def test_login():\n    assert login('admin', '123') == True\n"
    pts, unknowns = _eval_test_evidence(code, "python")
    assert pts == 10
    assert len(unknowns) == 0


def test_risk_score_calculation():
    issues = [
        {"severity": "CRITICAL", "category": "SECURITY"},
        {"severity": "HIGH", "category": "BUG"},
    ]
    risk, level = compute_risk_score(issues, time_complexity="O(n^2)")
    assert risk > 50
    assert level in ("High", "Critical")


def test_compute_evidence_confidence_deterministic_total():
    code = """from typing import List
from fastapi import FastAPI
import sqlite3

app = FastAPI()

def list_users(limit: int = 10) -> List[str]:
    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM users LIMIT ?", (limit,))
        return [r[0] for r in cursor.fetchall()]
"""
    result = compute_evidence_confidence(
        source_code=code,
        language="python",
        static_issues=[],
        ai_issues=[],
        combined_issues=[],
    )

    assert "risk_score" in result
    assert "analysis_confidence" in result
    assert "analysis_coverage" in result
    assert "confidence_breakdown" in result
    assert "unknown_zones" in result
    assert 0 <= result["analysis_confidence"] <= 100
    assert 0 <= result["analysis_coverage"] <= 100
    assert 0 <= result["risk_score"] <= 100

    # Ensure weights in breakdown sum to 100%
    total_weight = sum(item["weight"] for item in result["confidence_breakdown"].values())
    assert total_weight == 100
