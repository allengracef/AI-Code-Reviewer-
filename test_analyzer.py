import os
import json
import time
from typing import List


def process_users(users: List[dict]):
    results = []

    for user in users:
        name = user.get("name")
        email = user.get("email")

        if name:
            print("Processing user:", name)

        if email:
            print("Email:", email)

        for other_user in users:
            if other_user.get("email") == email:
                results.append({
                    "name": name,
                    "email": email,
                    "duplicate": True
                })

    data = json.dumps(results)

    with open("users.json", "w") as file:
        file.write(data)

    password = os.getenv("PASSWORD")

    if password == "admin123":
        print("Admin access granted")

    start = time.time()

    total = 0
    for i in range(1000000):
        total += i

    elapsed = time.time() - start

    print("Processing took:", elapsed)
    print("Total:", total)

    return results


def calculate_average(numbers):
    total = 0

    for number in numbers:
        total += number

    if len(numbers) > 0:
        return total / len(numbers)

    return 0


def find_user(users, target_email):
    for user in users:
        if user["email"] == target_email:
            return user

    return None


users = [
    {"name": "John", "email": "john@example.com"},
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob", "email": "bob@example.com"},
]

process_users(users)

print(calculate_average([10, 20, 30]))

user = find_user(users, "alice@example.com")

if user:
    print(user)