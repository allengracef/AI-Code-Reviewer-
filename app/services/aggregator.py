from typing import Any


def _word_set(message: str | None) -> set[str]:
    if not message:
        return set()
    return set(message.lower().split())


def _extract_lines(val: Any) -> list[int]:
    if val is None:
        return []
    if isinstance(val, int):
        return [val]
    if isinstance(val, str):
        nums = []
        cleaned = val.replace("Lines", "").replace("Line", "").replace("L", "")
        for part in cleaned.split(","):
            part = part.strip()
            if part.isdigit():
                nums.append(int(part))
        return nums
    return []


def _is_duplicate_or_same_issue(
    issue: dict[str, Any],
    existing: dict[str, Any],
) -> bool:
    """
    Determine whether two findings represent the same issue concept,
    either on the same line or across different lines.
    """
    if issue.get("category") != existing.get("category"):
        return False

    a = _word_set(issue.get("message"))
    b = _word_set(existing.get("message"))

    if not a or not b:
        if issue.get("code") and existing.get("code"):
            return issue.get("code") == existing.get("code")
        return False

    overlap = len(a & b) / max(len(a), len(b))
    return overlap >= 0.55 or issue.get("message") == existing.get("message")


def aggregate_issues(
    static_issues: list[dict[str, Any]],
    ai_issues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Combine static-analysis and AI findings, deduplicate and group same issues
    across multiple lines into a single issue entry listing all affected line numbers.
    """
    all_raw_issues = list(static_issues) + list(ai_issues)
    grouped_issues: list[dict[str, Any]] = []

    for issue in all_raw_issues:
        match_index = next(
            (i for i, existing in enumerate(grouped_issues) if _is_duplicate_or_same_issue(issue, existing)),
            None,
        )

        if match_index is None:
            new_issue = dict(issue)
            lines = _extract_lines(new_issue.get("line"))
            new_issue["_lines"] = lines
            grouped_issues.append(new_issue)
        else:
            existing = grouped_issues[match_index]
            
            # Prefer AI finding metadata if existing is static and current is AI
            if existing.get("source") == "STATIC_ANALYSIS" and issue.get("source") == "AI":
                lines = existing.get("_lines", []) + _extract_lines(issue.get("line"))
                existing = dict(issue)
                existing["_lines"] = lines
                grouped_issues[match_index] = existing
            else:
                existing.get("_lines", []).extend(_extract_lines(issue.get("line")))
                if not existing.get("explanation") and issue.get("explanation"):
                    existing["explanation"] = issue.get("explanation")
                if not existing.get("suggestion") and issue.get("suggestion"):
                    existing["suggestion"] = issue.get("suggestion")

    # Format final line numbers and location summaries
    final_issues: list[dict[str, Any]] = []
    for issue in grouped_issues:
        lines = sorted(list(set(issue.pop("_lines", []))))
        if lines:
            if len(lines) == 1:
                issue["line"] = lines[0]
            else:
                formatted_lines = ", ".join(str(n) for n in lines)
                issue["line"] = formatted_lines
                loc_str = f"Found on lines: {formatted_lines}"
                exp = issue.get("explanation") or ""
                if loc_str not in exp:
                    issue["explanation"] = f"{exp}\n\n({loc_str})".strip() if exp else loc_str

        final_issues.append(issue)

    return final_issues
