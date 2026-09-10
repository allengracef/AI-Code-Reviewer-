from typing import Any


def _word_set(message: str | None) -> set[str]:
    if not message:
        return set()
    return set(message.lower().split())


def _is_duplicate(
    issue: dict[str, Any],
    existing: dict[str, Any],
) -> bool:
    """
    Determine whether two findings represent the same issue.

    Two issues are considered duplicates when they share:
    - the same line number, AND
    - the same category, AND
    - message word overlap of at least 60 %

    The fuzzy message check handles AI paraphrasing the same
    underlying finding with different wording.
    """
    issue_line = issue.get("line")
    existing_line = existing.get("line")

    if issue_line is None or existing_line is None:
        return False

    if issue_line != existing_line:
        return False

    if issue.get("category") != existing.get("category"):
        return False

    a = _word_set(issue.get("message"))
    b = _word_set(existing.get("message"))

    if not a or not b:
        return False

    overlap = len(a & b) / max(len(a), len(b))
    return overlap >= 0.6


def aggregate_issues(
    static_issues: list[dict[str, Any]],
    ai_issues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Combine static-analysis and AI findings while removing duplicates.

    AI findings are preferred over static ones when they overlap because
    they contain richer explanations and actionable suggestions.
    """
    unique_issues: list[dict[str, Any]] = list(static_issues)

    for ai_issue in ai_issues:
        duplicate_index = next(
            (i for i, existing in enumerate(unique_issues) if _is_duplicate(ai_issue, existing)),
            None,
        )

        if duplicate_index is None:
            unique_issues.append(ai_issue)
        else:
            # Replace the static finding with the richer AI finding.
            unique_issues[duplicate_index] = ai_issue

    return unique_issues
