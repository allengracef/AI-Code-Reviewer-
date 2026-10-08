"""
Evidence-Weighted Code Confidence & Risk Analysis Service
=========================================================

Calculates three core metrics:
  1. CODE RISK SCORE (0–100):
     Measures how risky/problematic the analyzed code is based on detected
     bugs, security vulnerabilities, code smells, complexity, and severity.

  2. ANALYSIS CONFIDENCE (0–100):
     Deterministic calculation using measurable signals (NOT an arbitrary LLM %):
       - Syntax / Parsing Success       20%
       - Rule Agreement                 20%
       - Type Information               15%
       - Dependency Resolution          15%
       - Code Context                   10%
       - Test Evidence                  10%
       - Language / Framework Detection 10%
       ------------------------------------
       Total                           100%

  3. ANALYSIS COVERAGE (0–100%):
     How much of the submitted code was analyzed reliably without opaque,
     dynamic, unparseable, or unresolvable zones.

  4. UNKNOWN CODE ZONE:
     Explicit list of factors and code sections that could NOT be confidently analyzed.
"""

from __future__ import annotations

import ast
import re
from typing import Any


# ── Standard Library & Known Modules Reference ────────────────────────────────

_PYTHON_STDLIB = {
    "abc", "argparse", "array", "ast", "asyncio", "base64", "collections",
    "contextlib", "copy", "csv", "dataclasses", "datetime", "decimal", "enum",
    "functools", "glob", "hashlib", "hmac", "html", "http", "importlib", "io",
    "itertools", "json", "logging", "math", "multiprocessing", "os", "pathlib",
    "pickle", "queue", "random", "re", "secrets", "shutil", "socket", "sqlite3",
    "ssl", "string", "subprocess", "sys", "tempfile", "threading", "time",
    "traceback", "typing", "unittest", "urllib", "uuid", "warnings", "weakref",
    "zipfile", "zlib",
}

_JS_STDLIB = {
    "fs", "path", "http", "https", "crypto", "os", "events", "util", "stream",
    "buffer", "url", "querystring", "child_process", "cluster", "assert",
    "zlib", "net", "tls", "timers", "dns", "readline", "process",
}

_JAVA_STDLIB_PREFIXES = (
    "java.lang", "java.util", "java.io", "java.nio", "java.net", "java.math",
    "java.time", "java.sql", "java.security", "java.concurrent", "javax.",
)

_KNOWN_FRAMEWORKS: dict[str, list[tuple[str, re.Pattern]]] = {
    "python": [
        ("FastAPI", re.compile(r"\b(?:FastAPI|APIRouter|Depends|HTTPException|status)\b")),
        ("Django", re.compile(r"\b(?:django|models\.Model|views|HttpResponse|urlpatterns)\b")),
        ("Flask", re.compile(r"\b(?:Flask|Blueprint|render_template|jsonify|request\.args)\b")),
        ("SQLAlchemy", re.compile(r"\b(?:declarative_base|sessionmaker|Mapped|mapped_column|Session)\b")),
        ("Pytest", re.compile(r"\b(?:pytest|fixture|mark\.parametrize)\b")),
    ],
    "javascript": [
        ("React", re.compile(r"\b(?:useState|useEffect|useContext|useMemo|useCallback|React|JSX)\b")),
        ("Express", re.compile(r"\b(?:express|Router|app\.get|app\.post|res\.json|req\.body)\b")),
        ("Next.js", re.compile(r"\b(?:NextResponse|NextRequest|getServerSideProps|getStaticProps)\b")),
        ("Vue", re.compile(r"\b(?:ref|reactive|computed|onMounted|defineComponent)\b")),
        ("Node.js", re.compile(r"\b(?:require\s*\(|module\.exports|process\.env)\b")),
        ("Jest/Vitest", re.compile(r"\b(?:describe|it|expect|test|beforeEach|afterEach)\b")),
    ],
    "java": [
        ("Spring Boot", re.compile(r"(?:@(?:RestController|Service|Repository|Autowired|GetMapping|PostMapping|SpringBootApplication)|org\.springframework|SpringBootApplication)")),
        ("Hibernate/JPA", re.compile(r"(?:@(?:Entity|Table|Id|GeneratedValue)|EntityManager|JpaRepository|javax\.persistence)")),
        ("JUnit", re.compile(r"(?:@(?:Test|BeforeEach|AfterEach)|org\.junit|assertEquals|assertNotNull)")),
        ("Servlet", re.compile(r"\b(?:HttpServlet|HttpServletRequest|HttpServletResponse)\b")),
    ],
}


# ── 1. Syntax / Parsing Analysis (Weight: 20%) ───────────────────────────────

def _eval_syntax_parsing(source_code: str, language: str) -> tuple[int, list[str], int, int]:
    """
    Evaluates whether the source code parses cleanly.
    Returns: (points_out_of_20, unknown_items, parsed_lines, total_lines)
    """
    lines = source_code.splitlines()
    total_lines = max(1, len(lines))
    unknowns: list[str] = []

    if not source_code.strip():
        return 0, ["Empty code payload"], 0, total_lines

    if language == "python":
        try:
            ast.parse(source_code)
            return 20, [], total_lines, total_lines
        except SyntaxError as e:
            err_line = e.lineno or 1
            unknowns.append(f"Python syntax error at line {err_line}: {e.msg}")
            # Estimate partial valid lines before the syntax error
            parsed_lines = max(0, err_line - 1)
            ratio = parsed_lines / total_lines
            points = max(2, int(ratio * 16))
            return points, unknowns, parsed_lines, total_lines

    elif language == "javascript":
        # Check brace, bracket, parenthesis balance & basic syntax markers
        pairs = {"{": "}", "(": ")", "[": "]"}
        stack: list[tuple[str, int]] = []
        is_balanced = True
        error_line = 1

        for idx, line in enumerate(lines, 1):
            # Simple quote strip for structural check
            cleaned = re.sub(r'(["\'])(?:(?=(\\?))\2.)*?\1', '', line)
            cleaned = re.sub(r'//.*$', '', cleaned)
            for char in cleaned:
                if char in pairs:
                    stack.append((char, idx))
                elif char in pairs.values():
                    if not stack or pairs[stack.pop()[0]] != char:
                        is_balanced = False
                        error_line = idx
                        break
            if not is_balanced:
                break

        if is_balanced and not stack:
            # Check for eval() or obfuscation that reduces parse confidence
            eval_matches = list(re.finditer(r"\beval\s*\(", source_code))
            if eval_matches:
                for m in eval_matches:
                    l_no = source_code[: m.start()].count("\n") + 1
                    unknowns.append(f"Dynamic code execution via eval() at line {l_no} obscures static AST")
                return 16, unknowns, int(total_lines * 0.85), total_lines
            return 20, [], total_lines, total_lines
        else:
            unknowns.append(f"JavaScript unclosed or unbalanced tokens near line {error_line}")
            parsed_lines = max(1, int(total_lines * 0.6))
            return 10, unknowns, parsed_lines, total_lines

    elif language == "java":
        # Check class / method declarations and matching braces
        has_class_or_method = bool(re.search(r"\b(?:class|interface|enum|public|private|protected)\b", source_code))
        open_b = source_code.count("{")
        close_b = source_code.count("}")

        if open_b == close_b and has_class_or_method:
            return 20, [], total_lines, total_lines
        elif abs(open_b - close_b) <= 1:
            if not has_class_or_method:
                unknowns.append("Java snippet is missing surrounding class wrapper context")
                return 16, unknowns, total_lines, total_lines
            return 17, [], total_lines, total_lines
        else:
            unknowns.append(f"Java unbalanced class braces (open: {open_b}, close: {close_b})")
            return 9, unknowns, max(1, int(total_lines * 0.5)), total_lines

    return 15, [], total_lines, total_lines


# ── 2. Rule Agreement (Weight: 20%) ──────────────────────────────────────────

def _eval_rule_agreement(
    static_issues: list[dict[str, Any]],
    ai_issues: list[dict[str, Any]],
    total_issues: list[dict[str, Any]],
) -> tuple[int, list[str]]:
    """
    Evaluates agreement between independent static analysis and AI findings.
    Returns: (points_out_of_20, unknown_items)
    """
    unknowns: list[str] = []

    if not static_issues and not ai_issues:
        # Both clean -> high agreement on code correctness
        return 20, []

    if static_issues and ai_issues:
        # Check category overlap
        static_cats = {i.get("category") for i in static_issues if i.get("category")}
        ai_cats = {i.get("category") for i in ai_issues if i.get("category")}
        overlap = static_cats & ai_cats

        if overlap:
            # Multi-rule confirmation
            return 20, []
        else:
            # Both found issues in different categories
            return 17, []

    if not static_issues and ai_issues:
        # AI found issues that standard linter didn't flag (semantic / architectural)
        # Check severity of AI findings
        high_critical = [i for i in ai_issues if i.get("severity") in ("HIGH", "CRITICAL")]
        if len(high_critical) > 3:
            unknowns.append("AI flagged severe findings without static linter rule confirmation")
            return 15, unknowns
        return 18, []

    if static_issues and not ai_issues:
        unknowns.append("Static linter flagged issues unconfirmed by semantic AI analysis")
        return 16, unknowns

    return 18, []


# ── 3. Type Information (Weight: 15%) ────────────────────────────────────────

def _eval_type_information(source_code: str, language: str) -> tuple[int, list[str]]:
    """
    Evaluates type certainty and explicit typing.
    Returns: (points_out_of_15, unknown_items)
    """
    unknowns: list[str] = []

    if language == "java":
        # Check for raw types like 'List' without generic <T>
        raw_types = re.findall(r"\b(?:List|Map|Set|ArrayList|HashMap|Collection)\s*(?!<)[a-zA-Z0-9_]+\s*[;=)]", source_code)
        if raw_types:
            unknowns.append(f"Raw type usage detected ({', '.join(raw_types[:2])}); missing generic type parameters")
            return 13, unknowns
        return 15, []

    elif language == "python":
        # Check for type annotations: 'def func(x: int) -> str:' or 'x: int = 5'
        has_return_types = bool(re.search(r"->\s*[a-zA-Z0-9_\[\], ]+:", source_code))
        has_param_types = bool(re.search(r":\s*(?:int|str|bool|float|list|dict|set|tuple|Any|Optional|List|Dict|Set|Union)\b", source_code))
        has_typing_import = bool(re.search(r"\b(?:from\s+typing\s+import|import\s+typing)\b", source_code))
        func_count = len(re.findall(r"^\s*def\s+", source_code, re.MULTILINE))

        if has_return_types and (has_param_types or has_typing_import):
            return 15, []
        elif has_param_types or has_return_types:
            if func_count > 2:
                unknowns.append("Partial Python type annotations: some function signatures lack complete type hints")
            return 13, unknowns
        else:
            if func_count > 0:
                unknowns.append("Untyped Python functions: missing explicit parameter/return type annotations")
                return 10, unknowns
            return 12, []

    elif language == "javascript":
        # Check for TypeScript / JSDoc / typed definitions
        has_ts_types = bool(re.search(r":\s*(?:string|number|boolean|any|void|object|[A-Z][a-zA-Z0-9_]*)\b", source_code))
        has_interfaces = bool(re.search(r"\b(?:interface|type)\s+[A-Z][a-zA-Z0-9_]*\s*=", source_code))
        has_jsdoc = bool(re.search(r"/\*\*[\s\S]*?@param[\s\S]*?\*/", source_code))

        if has_interfaces or (has_ts_types and has_jsdoc):
            return 15, []
        elif has_ts_types or has_jsdoc:
            return 13, []
        else:
            # Dynamically typed JS - normal, slight discount for missing contract hints
            unknowns.append("Dynamic JavaScript variables with no JSDoc or TypeScript contracts")
            return 11, unknowns

    return 12, []


# ── 4. Dependency Resolution (Weight: 15%) ────────────────────────────────────

def _eval_dependency_resolution(source_code: str, language: str) -> tuple[int, list[str]]:
    """
    Evaluates imported modules and checks for unresolved or dynamic imports.
    Returns: (points_out_of_15, unknown_items)
    """
    unknowns: list[str] = []

    if language == "python":
        # Extract all imports
        import_names: list[str] = []
        for match in re.finditer(r"^\s*(?:import\s+([a-zA-Z0-9_., ]+)|from\s+([a-zA-Z0-9_.]+)\s+import)", source_code, re.MULTILINE):
            mod1, mod2 = match.groups()
            if mod1:
                for part in mod1.split(","):
                    part = part.strip().split()[0].split(".")[0]
                    if part:
                        import_names.append(part)
            if mod2:
                import_names.append(mod2.split(".")[0])

        if not import_names:
            return 15, []

        unresolved: list[str] = []
        for mod in set(import_names):
            if mod not in _PYTHON_STDLIB and not mod.startswith("."):
                # Common 3rd party frameworks we understand
                if mod not in ("fastapi", "pydantic", "sqlalchemy", "requests", "httpx", "flask", "django", "pytest", "numpy", "pandas", "dotenv", "jwt", "groq"):
                    unresolved.append(mod)

        # Dynamic __import__ or importlib detection
        if re.search(r"\b(?:__import__|importlib\.import_module)\s*\(", source_code):
            unknowns.append("Dynamic import mechanism detected; modules loaded at runtime are unresolved")
            return 10, unknowns

        if unresolved:
            unknowns.append(f"External/custom modules without local package context: {', '.join(unresolved[:3])}")
            return 12, unknowns

        return 15, []

    elif language == "javascript":
        require_matches = re.findall(r"require\s*\(['\"]([^'\"]+)['\"]\)", source_code)
        import_matches = re.findall(r"import\s+.*?from\s+['\"]([^'\"]+)['\"]", source_code)
        all_deps = set(require_matches + import_matches)

        # Check for dynamic require(variable)
        if re.search(r"require\s*\([^'\"\)]+\)", source_code):
            unknowns.append("Dynamic require() with variable parameter obscures static dependency graph")
            return 10, unknowns

        unresolved_js = [d for d in all_deps if not d.startswith(".") and d not in _JS_STDLIB and d not in ("react", "react-dom", "express", "axios", "lucide-react", "gsap", "vite", "next")]
        if unresolved_js:
            unknowns.append(f"External npm packages without package.json lockfile context: {', '.join(unresolved_js[:3])}")
            return 12, unknowns

        return 15, []

    elif language == "java":
        java_imports = re.findall(r"import\s+([a-zA-Z0-9_.]+);", source_code)
        unresolved_java: list[str] = []
        for imp in java_imports:
            if not any(imp.startswith(prefix) for prefix in _JAVA_STDLIB_PREFIXES):
                if not any(imp.startswith(p) for p in ("org.springframework", "org.junit", "org.slf4j", "com.google")):
                    unresolved_java.append(imp.split(".")[-1])

        if unresolved_java:
            unknowns.append(f"External Java dependencies outside standard library: {', '.join(unresolved_java[:2])}")
            return 12, unknowns

        return 15, []

    return 13, []


# ── 5. Code Context (Weight: 10%) ─────────────────────────────────────────────

def _eval_code_context(source_code: str, language: str) -> tuple[int, list[str]]:
    """
    Evaluates snippet completeness vs full module context.
    Returns: (points_out_of_10, unknown_items)
    """
    lines = source_code.splitlines()
    non_empty = [l for l in lines if l.strip() and not l.strip().startswith(("#", "//", "/*"))]
    line_count = len(non_empty)
    unknowns: list[str] = []

    has_imports = bool(re.search(r"\b(?:import|from|require|package)\b", source_code))
    has_functions_or_classes = bool(re.search(r"\b(?:def|class|function|const\s+[a-zA-Z0-9_]+\s*=|public\s+class)\b", source_code))

    if line_count < 10:
        unknowns.append(f"Short snippet ({line_count} lines): lack of surrounding project architecture limits contextual confidence")
        return 6, unknowns
    elif line_count < 25:
        if not has_imports:
            unknowns.append("Isolated snippet: missing module-level import definitions and global configuration")
            return 8, unknowns
        return 9, []
    else:
        if has_imports and has_functions_or_classes:
            return 10, []
        return 9, []


# ── 6. Test Evidence (Weight: 10%) ────────────────────────────────────────────

def _eval_test_evidence(source_code: str, language: str) -> tuple[int, list[str]]:
    """
    Detects embedded or accompanying test suites & assertion evidence.
    Returns: (points_out_of_10, unknown_items)
    """
    unknowns: list[str] = []

    # Patterns indicating unit tests or test assertions
    has_test_funcs = bool(re.search(r"(?:def\s+test_\w*|@Test|describe\s*\(|it\s*\(|test\s*\()", source_code))
    has_assertions = bool(re.search(r"(?:\bassert\b|assertEquals|assertNotNull|assertTrue|expect\s*\(|assertThat)", source_code))
    has_test_framework = bool(re.search(r"\b(?:pytest|unittest|junit|jest|vitest|mocha|chai)\b", source_code, re.IGNORECASE))

    if has_test_funcs and has_assertions:
        return 10, []
    elif has_test_funcs or has_assertions or has_test_framework:
        return 8, []
    else:
        # Standard implementation code without inline tests
        unknowns.append("No inline test assertions or test runner suites detected in the analyzed snippet")
        return 6, unknowns


# ── 7. Language / Framework Detection (Weight: 10%) ──────────────────────────

def _eval_framework_detection(source_code: str, language: str) -> tuple[int, list[str], str]:
    """
    Identifies language + framework and checks if specialized rules apply.
    Returns: (points_out_of_10, unknown_items, detected_framework_name)
    """
    unknowns: list[str] = []
    framework_list = _KNOWN_FRAMEWORKS.get(language, [])
    detected: list[str] = []

    for name, pattern in framework_list:
        if pattern.search(source_code):
            detected.append(name)

    if detected:
        framework_str = f"{language.capitalize()} + {', '.join(detected[:2])}"
        return 10, [], framework_str
    else:
        framework_str = f"{language.capitalize()} (Core / Standard)"
        return 8, [], framework_str


# ── Code Risk Score Calculation (0–100) ──────────────────────────────────────

def compute_risk_score(
    issues: list[dict[str, Any]],
    time_complexity: str | None = None,
    space_complexity: str | None = None,
) -> tuple[int, str]:
    """
    Calculates a 0–100 Code Risk Score based on severity penalties,
    issue categories (Security, Bug, Architecture), and complexity.
    """
    if not issues and not time_complexity:
        return 5, "Low"

    base_risk = 0
    severity_weights = {
        "CRITICAL": 30,
        "HIGH":     18,
        "MEDIUM":    8,
        "LOW":       3,
    }

    category_multipliers = {
        "SECURITY":     1.3,
        "BUG":          1.2,
        "PERFORMANCE":  1.0,
        "ARCHITECTURE": 1.0,
        "BEST_PRACTICE": 0.8,
        "MAINTAINABILITY": 0.8,
        "READABILITY":  0.7,
    }

    for issue in issues:
        sev = str(issue.get("severity", "LOW")).upper()
        cat = str(issue.get("category", "BEST_PRACTICE")).upper()
        sev_pts = severity_weights.get(sev, 3)
        cat_mult = category_multipliers.get(cat, 1.0)
        base_risk += sev_pts * cat_mult

    # Complexity risk penalty
    if time_complexity:
        tc = time_complexity.lower()
        if "n^3" in tc or "n!" in tc or "2^n" in tc:
            base_risk += 15
        elif "n^2" in tc:
            base_risk += 8

    risk_score = min(100, max(0, round(base_risk)))

    if risk_score <= 20:
        level = "Low"
    elif risk_score <= 45:
        level = "Moderate"
    elif risk_score <= 70:
        level = "High"
    else:
        level = "Critical"

    return risk_score, level


# ── Main Evidence-Weighted Confidence Engine ──────────────────────────────────

def compute_evidence_confidence(
    source_code: str,
    language: str,
    static_issues: list[dict[str, Any]],
    ai_issues: list[dict[str, Any]],
    combined_issues: list[dict[str, Any]],
    time_complexity: str | None = None,
    space_complexity: str | None = None,
) -> dict[str, Any]:
    """
    Performs full deterministic evidence analysis across all 7 signals.
    Returns:
      - risk_score (0-100) and risk_level
      - analysis_confidence (0-100)
      - analysis_coverage (0-100%)
      - confidence_breakdown: detailed scores & points per signal
      - unknown_zones: list of specific factors reducing confidence
      - detected_framework: e.g. "Python + FastAPI"
    """
    # 1. Syntax / Parsing (20%)
    pts_syntax, unk_syntax, parsed_lines, total_lines = _eval_syntax_parsing(source_code, language)

    # 2. Rule Agreement (20%)
    pts_rules, unk_rules = _eval_rule_agreement(static_issues, ai_issues, combined_issues)

    # 3. Type Information (15%)
    pts_types, unk_types = _eval_type_information(source_code, language)

    # 4. Dependency Resolution (15%)
    pts_deps, unk_deps = _eval_dependency_resolution(source_code, language)

    # 5. Code Context (10%)
    pts_context, unk_context = _eval_code_context(source_code, language)

    # 6. Test Evidence (10%)
    pts_tests, unk_tests = _eval_test_evidence(source_code, language)

    # 7. Framework Detection (10%)
    pts_framework, unk_framework, framework_name = _eval_framework_detection(source_code, language)

    # Total Confidence = sum of points across all 7 categories (0–100)
    final_confidence = min(100, max(0, pts_syntax + pts_rules + pts_types + pts_deps + pts_context + pts_tests + pts_framework))

    # Analysis Coverage (%) based on successfully parsed & inspected lines and resolution
    parse_ratio = parsed_lines / max(1, total_lines)
    dep_factor = pts_deps / 15.0
    coverage_pct = round(parse_ratio * (0.85 + (0.15 * dep_factor)) * 100)
    coverage_pct = min(100, max(5, coverage_pct))

    # Calculate Code Risk Score (0-100)
    risk_score, risk_level = compute_risk_score(combined_issues, time_complexity, space_complexity)

    # Compile Unknown Code Zone
    all_unknowns = unk_syntax + unk_rules + unk_types + unk_deps + unk_context + unk_tests + unk_framework

    # Compile Structured Breakdown
    breakdown = {
        "syntax_parsing": {
            "name": "Syntax & Parsing Success",
            "weight": 20,
            "points": pts_syntax,
            "max_points": 20,
            "status": "Verified" if pts_syntax >= 18 else "Partial" if pts_syntax >= 12 else "Failed",
            "details": f"{parsed_lines} of {total_lines} lines cleanly parsed",
        },
        "rule_agreement": {
            "name": "Static & AI Rule Agreement",
            "weight": 20,
            "points": pts_rules,
            "max_points": 20,
            "status": "Consistent" if pts_rules >= 18 else "Moderate",
            "details": f"{len(static_issues)} static findings, {len(ai_issues)} semantic AI findings",
        },
        "type_information": {
            "name": "Type Information Certainty",
            "weight": 15,
            "points": pts_types,
            "max_points": 15,
            "status": "Strong" if pts_types >= 14 else "Moderate" if pts_types >= 11 else "Weak",
            "details": "Static/annotated types" if pts_types >= 14 else "Inferred or dynamic types",
        },
        "dependency_resolution": {
            "name": "Dependency Resolution",
            "weight": 15,
            "points": pts_deps,
            "max_points": 15,
            "status": "Resolved" if pts_deps >= 14 else "Partial",
            "details": "Standard library & core framework imports mapped",
        },
        "code_context": {
            "name": "Code & Project Context",
            "weight": 10,
            "points": pts_context,
            "max_points": 10,
            "status": "Complete" if pts_context >= 9 else "Partial Context",
            "details": f"{total_lines} lines of code analyzed",
        },
        "test_evidence": {
            "name": "Test Suite & Assertion Evidence",
            "weight": 10,
            "points": pts_tests,
            "max_points": 10,
            "status": "Present" if pts_tests >= 8 else "No Inline Tests",
            "details": "Test runner & assertions verified" if pts_tests >= 8 else "No inline test suite in snippet",
        },
        "framework_detection": {
            "name": "Language & Framework Detection",
            "weight": 10,
            "points": pts_framework,
            "max_points": 10,
            "status": "Identified",
            "details": framework_name,
        },
    }

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "analysis_confidence": final_confidence,
        "analysis_coverage": coverage_pct,
        "detected_framework": framework_name,
        "confidence_breakdown": breakdown,
        "unknown_zones": all_unknowns,
    }
