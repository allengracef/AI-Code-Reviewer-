# AI Code Reviewer

[![Python](https://img.shields.io/badge/Python-3.13%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Groq](https://img.shields.io/badge/Groq-Llama--3.1--70B-orange.svg)](https://groq.com/)
[![Ruff](https://img.shields.io/badge/Ruff-Linter-black.svg)](https://github.com/astral-sh/ruff)

An automated, enterprise-grade AI-powered code review API. **AI Code Reviewer** combines static code analysis (Ruff for Python, pattern-based analysis for JavaScript) with state-of-the-art LLMs hosted on Groq to identify software defects, security vulnerabilities, performance bottlenecks, and architectural anti-patterns.

---

## 🚀 Key Features

- **🔐 User Authentication & JWT Security**: Full user lifecycle management with access/refresh tokens, password hashing, and Bearer token security.
- **⚡ Hybrid Code Review Pipeline**:
  - **Static Analysis**: Rapid, deterministic analysis using `ruff` for Python and AST/pattern checks for JavaScript.
  - **AI Analysis**: High-reasoning LLM reviews via Groq (`llama-3.1-70b-versatile`) covering security (XSS, injection, hardcoded secrets), complexity, edge cases, and maintainability.
- **🧠 Smart Finding Aggregation**: Automatic deduplication and normalization of issues identified by both static analysis tools and AI models.
- **💾 Review History & Database Persistence**: Saves all review sessions, summary metrics, and granular finding records with SQLAlchemy and SQLite/PostgreSQL support.
- **📄 Paginated API Endpoints**: Easily list, fetch detail, upload, and manage code review records per user.
- **⚡ High Performance**: Asynchronous request processing powered by FastAPI and Uvicorn.

---

## 🛠 Tech Stack

- **Framework**: FastAPI (Python 3.13+)
- **ORM / Database**: SQLAlchemy 2.0 (SQLite / PostgreSQL ready)
- **AI / LLM Engine**: Groq API (`llama-3.1-70b-versatile` / customizable)
- **Static Linters**: `ruff` (Python), Regex/Pattern Matcher (JavaScript)
- **Security**: PyJWT (`python-jose`), Passlib / Bcrypt password hashing
- **Dependency & Task Management**: [`uv`](https://github.com/astral-sh/uv)
- **Testing**: `pytest`, `httpx`

---

## 📂 Project Structure

```
AI-CodeReviwer/
├── app/
│   ├── api/                # FastAPI routers (auth, review)
│   │   ├── auth.py
│   │   └── review.py
│   ├── core/               # App configurations and security helpers
│   │   ├── config.py
│   │   └── security.py
│   ├── database.py         # SQLAlchemy engine and session initialization
│   ├── main.py             # FastAPI entrypoint and lifecycle events
│   ├── models.py           # Database models (User, ReviewRecord, IssueRecord)
│   ├── schemas/            # Pydantic schemas (requests/responses)
│   │   ├── auth.py
│   │   └── review.py
│   └── services/           # Core business logic
│       ├── aggregator.py   # Issue deduplication & merging
│       ├── ai_reviewer.py  # Groq AI review logic & retries
│       ├── analyzer.py     # Static analysis engines (ruff, js)
│       ├── auth.py         # Authentication service logic
│       ├── language.py     # Language detection by extension
│       └── review.py       # Review pipeline coordinator
├── tests/                  # Pytest test suite
│   ├── conftest.py
│   ├── test_aggregator.py
│   ├── test_ai_reviewer.py
│   ├── test_analyzer.py
│   ├── test_review.py
│   └── test_review_api.py
├── pyproject.toml          # UV project definition & dependencies
├── uv.lock                 # UV lockfile
└── README.md
```

---

## ⚙️ Environment Setup

Create a `.env` file in the root directory:

```env
# JWT Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Groq AI Configuration
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.1-70b-versatile
```

---

## 📦 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/allengracef/AI-Code-Reviewer-.git
   cd AI-Code-Reviewer-
   ```

2. **Install `uv` (if not already installed):**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install project dependencies:**
   ```bash
   uv sync
   ```

---

## 🏃 Running the Application

Start the local Uvicorn development server:

```bash
uv run uvicorn app.main:app --reload
```

The server will start at `http://localhost:8000`.

- **Swagger UI Interactive Docs**: `http://localhost:8000/docs`
- **ReDoc API Documentation**: `http://localhost:8000/redoc`

---

## 📡 API Reference

### Health Check
| Method | Endpoint | Auth | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | No | System health check endpoint |

### Authentication (`/api/v1/auth`)
| Method | Endpoint | Auth | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | No | Register a new user account |
| `POST` | `/api/v1/auth/login` | No | Authenticate and obtain JWT token pair |
| `POST` | `/api/v1/auth/refresh` | No | Refresh an access token using a refresh token |
| `GET` | `/api/v1/auth/me` | Yes | Get current user profile |

### Reviews (`/api/v1/reviews`)
| Method | Endpoint | Auth | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/reviews/upload` | Yes | Upload source code file for static & AI review |
| `GET` | `/api/v1/reviews/` | Yes | Get paginated review history of current user |
| `GET` | `/api/v1/reviews/{id}` | Yes | Fetch details and issues for a specific review |
| `DELETE` | `/api/v1/reviews/{id}` | Yes | Delete a review record |

---

## 💡 Example Usage

### 1. Register & Login

```bash
# Register User
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePassword123", "name": "Jane Doe"}'

# Login to get Access Token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePassword123"}'
```

*Response:*
```json
{
  "access_token": "eyJhbGciOiJIUzI1Ni...",
  "refresh_token": "eyJhbGciOiJIUzI1Ni...",
  "token_type": "bearer"
}
```

### 2. Upload File for Review

```bash
curl -X POST http://localhost:8000/api/v1/reviews/upload \
  -H "Authorization: Bearer <your_access_token>" \
  -F "file=@sample.py"
```

*Response Sample:*
```json
{
  "filename": "sample.py",
  "content_type": "text/x-python",
  "size": 184,
  "language": "python",
  "code": "...",
  "review": {
    "language": "python",
    "summary": "The code contains potential security issues with hardcoded secrets and eval usage.",
    "issues": [
      {
        "code": "SEC001",
        "source": "AI",
        "severity": "HIGH",
        "category": "SECURITY",
        "message": "Hardcoded password detected.",
        "line": 2,
        "column": 1,
        "explanation": "Credentials should not be stored directly in source code.",
        "suggestion": "Use environment variables or a secrets manager."
      }
    ],
    "suggestions": []
  }
}
```

---

## 🧪 Running Tests

Run the complete test suite using `pytest`:

```bash
uv run pytest
```

---

## 📄 License

This project is open-source and licensed under the [MIT License](LICENSE).
