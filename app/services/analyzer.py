import json
import subprocess
import tempfile
from pathlib import Path


def analyze_python(source_code: str) -> list[dict]:
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / "review.py"

        file_path.write_text(
            source_code,
            encoding="utf-8"
        )

        result = subprocess.run(
            [
                "ruff",
                "check",
                str(file_path),
                "--output-format",
                "json",
            ],
            capture_output=True,
            text=True,
        )

        if not result.stdout:
            return []

        issues = json.loads(result.stdout)

        return [
            {
                "code": issue["code"],
                "severity":"LOW",
                "category":"STYLE",
                "message": issue["message"],
                "line": issue["location"]["row"],
                "column": issue["location"]["column"],
                "explanation":None,
                "suggestion":None,
            }
            for issue in issues
        ]