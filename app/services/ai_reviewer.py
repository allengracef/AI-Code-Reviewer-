import json
import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from app.schemas.review import ReviewIssue

load_dotenv()

_groq_client = None

def _get_groq_client():
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not configured.")
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def review_with_ai(source_code: str, language: str) -> list[dict[str, Any]]:
    """
    Review source code using a Groq-hosted AI model.
    """

    model = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    client = _get_groq_client()

    prompt = (
        "You are a senior software engineer performing a rigorous code review.\n\n"
        f"Review the following {language} source code.\n\n"

        "Your job is to identify meaningful problems that could affect:\n"
        "- Correctness and bugs\n"
        "- Security\n"
        "- Performance and algorithmic complexity\n"
        "- Architecture and design\n"
        "- Readability\n"
        "- Maintainability\n"
        "- Reliability and error handling\n"
        "- Best practices\n\n"

        "IMPORTANT RULES:\n"
        "1. Do not report trivial formatting or lint issues.\n"
        "2. Do not duplicate issues that a standard linter would detect.\n"
        "3. Only report an issue when you can explain why it is a real problem.\n"
        "4. Consider the actual behavior of the code, not just individual lines.\n"
        "5. Look for edge cases and failure scenarios.\n"
        "6. Look for inefficient algorithms such as unnecessary O(n²) operations.\n"
        "7. Look for hardcoded secrets, credentials, or sensitive information.\n"
        "8. Look for unsafe input handling and security vulnerabilities.\n"
        "9. Look for incorrect error handling and resource management.\n"
        "10. Look for design choices that make the code difficult to maintain.\n"
        "11. Do not invent problems that are not supported by the code.\n"
        "12. If the code is good, return an empty array instead of inventing issues.\n\n"

        "Severity guidelines:\n"
        "- LOW: Minor issue with limited impact.\n"
        "- MEDIUM: Real issue that should be addressed.\n"
        "- HIGH: Serious bug, security problem, or performance issue.\n"
        "- CRITICAL: Severe security vulnerability or issue that could cause "
        "major damage or system failure.\n\n"

        "Category guidelines:\n"
        "- BUG: Incorrect behavior or logic error.\n"
        "- SECURITY: Security vulnerability or unsafe handling of data.\n"
        "- PERFORMANCE: Inefficient computation, memory usage, or resource usage.\n"
        "- ARCHITECTURE: Structural or design problem.\n"
        "- READABILITY: Code that is unnecessarily difficult to understand.\n"
        "- MAINTAINABILITY: Code that will be difficult to modify or extend.\n"
        "- BEST_PRACTICE: Violation of an important engineering practice.\n\n"

        "Return ONLY valid JSON.\n"
        "Do not use Markdown.\n"
        "Do not include explanations outside the JSON array.\n\n"

        "Each issue must contain exactly these fields:\n"
        "- code\n"
        "- severity\n"
        "- category\n"
        "- message\n"
        "- line\n"
        "- column\n"
        "- explanation\n"
        "- suggestion\n\n"

        "Do NOT include a source field.\n"
        "The application will assign the source automatically.\n\n"

        "Allowed severity values: LOW, MEDIUM, HIGH, CRITICAL\n"
        "Allowed category values: BUG, SECURITY, PERFORMANCE, ARCHITECTURE, "
        "READABILITY, MAINTAINABILITY, BEST_PRACTICE\n\n"

        "If there are no meaningful issues, return exactly:\n"
        "[]\n\n"

        "Source code:\n\n"
        f"{source_code}"
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional code-review AI. "
                    "Always return valid JSON and nothing else."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.1,
    )

    content = response.choices[0].message.content

    if not content:
        return []

    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("The AI returned invalid JSON.") from exc

    if not isinstance(data, list):
        raise RuntimeError("The AI response must be a JSON array.")

    # The AI does not control the source value.
    # The backend assigns it because this finding came from the AI reviewer.
    for issue in data:
        if isinstance(issue, dict):
            issue["source"] = "AI"

    try:
        validated_issues = [
            ReviewIssue.model_validate(issue)
            for issue in data
        ]
    except Exception as exc:
        raise RuntimeError(
            "The AI returned an invalid issue structure."
        ) from exc

    return [
        issue.model_dump()
        for issue in validated_issues
    ]