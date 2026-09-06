from typing import Any


def _normalize_message(message: str | None) -> str:
    if not message:
        return ""

    return " ".join(message.lower().split())


def _is_duplicate(
    issue: dict[str, Any],
    existing: dict[str, Any],
) -> bool:
    """
    Determine whether two findings represent the same issue.
    """

    issue_line = issue.get("line")
    existing_line = existing.get("line")

    if issue_line is None or existing_line is None:
        return False

    if issue_line != existing_line:
        return False

    issue_category = issue.get("category")
    existing_category = existing.get("category")

    if issue_category != existing_category:
        return False

    issue_message = _normalize_message(issue.get("message"))
    existing_message = _normalize_message(existing.get("message"))

    return issue_message == existing_message


def aggregate_issues(
    static_issues: list[dict[str, Any]],
    ai_issues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Combine static-analysis and AI findings while removing duplicates.

    AI findings are preferred when they duplicate static findings because
    they usually contain a more useful explanation and suggestion.
    """

    unique_issues: list[dict[str, Any]] = []

    for issue in static_issues:
        unique_issues.append(issue)

    for ai_issue in ai_issues:
        duplicate_index = None

        for index, existing_issue in enumerate(unique_issues):
            if _is_duplicate(ai_issue, existing_issue):
                duplicate_index = index
                break

        if duplicate_index is None:
            unique_issues.append(ai_issue)
        else:
            unique_issues[duplicate_index] = ai_issue

    return unique_issues