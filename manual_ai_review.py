from app.services.ai_reviewer import review_with_ai


bad_code = """
password = "admin123"

def find_transactions(users, transactions):
    results = []

    for user in users:
        for transaction in transactions:
            if transaction["user_id"] == user["id"]:
                results.append(transaction)

    return results


def execute_user_input():
    user_input = input("Enter expression: ")
    return eval(user_input)


def divide(a, b):
    try:
        return a / b
    except:
        return None
"""


issues = review_with_ai(bad_code, "python")

print("\n=== AI CODE REVIEW ===\n")

if not issues:
    print("No issues found.")
else:
    for index, issue in enumerate(issues, start=1):
        severity = issue.get("severity")
        category = issue.get("category")

        print(f"Issue #{index}")
        print(f"Code: {issue.get('code')}")
        print(
            f"Severity: "
            f"{severity.value if hasattr(severity, 'value') else severity}"
        )
        print(
            f"Category: "
            f"{category.value if hasattr(category, 'value') else category}"
        )
        print(f"Message: {issue.get('message')}")
        print(f"Line: {issue.get('line')}")
        print(f"Explanation: {issue.get('explanation')}")
        print(f"Suggestion: {issue.get('suggestion')}")
        print("-" * 60)

print(f"\nTotal issues: {len(issues)}")