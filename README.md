# BugLens 🔍⚡
### Evidence-Weighted AI & Static Code Review Platform

[![Python](https://img.shields.io/badge/Python-3.13%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.1-646CFF.svg)](https://vitejs.dev/)
[![Groq](https://img.shields.io/badge/Groq-Llama--3.3--70B-orange.svg)](https://groq.com/)
[![Tests](https://img.shields.io/badge/Tests-74%20Passing-brightgreen.svg)](https://pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

**BugLens** is an automated, enterprise-grade AI-powered code review and risk analysis platform. It pairs deterministic static code analysis with state-of-the-art LLMs hosted on Groq (`llama-3.3-70b-versatile`) to detect security vulnerabilities, logic flaws, architectural anti-patterns, and runtime bottlenecks across **Python**, **JavaScript**, and **Java**.

---

## 🌟 Core Architecture & Metrics

Rather than generating arbitrary AI percentages, BugLens provides **three transparent, evidence-based metrics**:

```
┌───────────────────────────┬───────────────────────────────┬───────────────────────────────┐
│     CODE RISK SCORE       │      ANALYSIS CONFIDENCE      │       ANALYSIS COVERAGE       │
│         0 – 100           │            0 – 100            │           0 – 100%            │
│  Measures code defect &   │    Deterministic evidence-    │  Percentage of code verified  │
│     security severity     │     weighted reliability      │   + Unknown Zone Detection    │
└───────────────────────────┴───────────────────────────────┴───────────────────────────────┘
```

### 1. 🛡️ Code Risk Score (0–100)
Calculated from detected bugs, security vulnerabilities, code smells, and cyclomatic complexity:
- **Low Risk (0–20)**: Clean code meeting standard security and style guidelines.
- **Moderate Risk (21–45)**: Minor code smells or style warnings; safe for review.
- **High Risk (46–70)**: Potential security vulnerabilities or unhandled runtime exceptions.
- **Critical Risk (71–100)**: Severe security threats (e.g. `eval()`, hardcoded secrets, SQL injection, resource leaks).

---

### 2. 🔬 Evidence-Weighted Code Confidence (0–100)
A deterministic confidence calculation built on 7 measurable signals (totaling 100%):

| Signal | Weight | Evaluation Criteria |
| :--- | :---: | :--- |
| **Syntax / Parsing Success** | **20%** | Valid AST construction, syntax error penalties, dynamic `eval()` penalties |
| **Rule Agreement** | **20%** | Independent cross-verification between AST static analyzers and AI semantic findings |
| **Type Information** | **15%** | Static type annotations (`typing` in Python, TypeScript/JSDoc, static Java typing) |
| **Dependency Resolution** | **15%** | Standard library vs. unresolved external/third-party package imports |
| **Code Context** | **10%** | Snippet length, enclosing functions/classes, structural completeness |
| **Test Evidence** | **10%** | Presence of unit/integration test suites (pytest, unittest, Jest, JUnit) |
| **Framework Detection** | **10%** | Identification of framework idioms (FastAPI, Django, Flask, Express, React, Spring Boot) |

Every review includes an expandable **Evidence Breakdown** showing point-by-point contributions:
```
Parsing Success           +20 / 20
Rule Agreement            +20 / 20
Type Information          +15 / 15
Dependencies Resolved     +15 / 15
Code Context              +10 / 10
Test Evidence             +10 / 10
Framework Detected        +10 / 10
───────────────────────────────────
Final Confidence           100 / 100
```

---

### 3. 🗺️ Analysis Coverage & Unknown Code Zones
BugLens explicitly flags sections it could not analyze with 100% certainty:
- **Dynamic imports & runtime evaluations** (`eval()`, dynamic `require()`, reflection)
- **Unresolved external dependencies**
- **Incomplete or truncated snippets**

---

## 🚀 Key Features

- **⚡ 3 Review Input Modes**:
  - **File Upload**: Upload `.py`, `.js`, `.java` files up to 25 MB.
  - **Direct Paste**: Instant in-browser editor with automatic language and framework detection.
  - **GitHub URL Import**: Import any public GitHub file URL (`github.com/.../blob/...`) directly.
- **🤖 GitHub Bot & Webhook Integration**:
  - Automatically reviews Pull Requests and Pushes on connected repositories.
  - Posts inline code review comments on specific lines.
  - Posts comprehensive PR summaries and sets commit status checks (`success` / `failure`).
- **💡 Smart Refactoring & Complexity Analysis**:
  - Extracts Time Complexity ($\mathcal{O}(N)$) and Space Complexity ($\mathcal{O}(1)$).
  - Provides side-by-side, syntax-highlighted refactored solutions.
- **🔐 JWT Authentication & User Accounts**:
  - Secure registration, login, token refresh, and private review history persistence.
- **🎨 Glassmorphism Dashboard UI**:
  - Built with React 19, Tailwind/Vite, Lucide icons, and fluid animations.

---

## 🛠 Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.13+)
- **LLM Engine**: Groq API (`llama-3.3-70b-versatile`)
- **Static Analysis**: `ruff` (Python), JavaScript AST Rules, Java Pattern Matcher
- **Database**: SQLAlchemy 2.0 (SQLite / PostgreSQL)
- **Security**: JWT (`python-jose`), Passlib / Bcrypt
- **Testing**: `pytest`, `httpx` (74 automated tests)

### Frontend
- **Framework**: React 19 + Vite
- **Styling**: Glassmorphism dark mode with radial glows & CSS variables
- **Icons**: Lucide React (`lucide-react`)
- **Animations**: GSAP + React Bits (`<SplitText />`, `<FoldText />`)
- **Routing & HTTP**: `react-router-dom`, `axios`

---

## 📂 Project Structure

```
AI-CodeReviwer/
├── app/
│   ├── api/
│   │   ├── auth.py           # User registration, login, refresh tokens
│   │   ├── review.py         # File upload, paste, GitHub import, history
│   │   └── webhook.py        # GitHub App webhook receiver (PR & push events)
│   ├── core/
│   │   ├── config.py         # App settings & environment variables
│   │   └── security.py       # Password hashing & JWT generation
│   ├── database.py           # SQLAlchemy database session & engine
│   ├── main.py               # FastAPI application entrypoint
│   ├── models.py             # Database models (User, ReviewRecord, IssueRecord)
│   ├── schemas/              # Pydantic validation schemas
│   └── services/
│       ├── aggregator.py     # Deduplication & severity normalization
│       ├── ai_reviewer.py    # Groq LLaMA 3.3 reviewer & structured JSON parser
│       ├── analyzer.py       # Multi-language static linters (Python, JS, Java)
│       ├── auth.py           # Authentication service
│       ├── confidence.py     # Evidence-weighted confidence & risk engine
│       ├── github_bot.py     # GitHub App token exchange & review posting
│       ├── language.py       # Multi-mode language detection
│       └── review.py         # Unified analysis pipeline coordinator
├── frontend/
│   ├── src/
│   │   ├── api/              # Axios API client
│   │   ├── components/       # UI components (Navbar, UploadPanel, SplitText, etc.)
│   │   ├── context/          # AuthContext (JWT state management)
│   │   ├── pages/            # DashboardPage, LandingPage, LoginPage, RegisterPage
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── tests/                    # Pytest test suite (74 tests)
│   ├── test_aggregator.py
│   ├── test_ai_reviewer.py
│   ├── test_analyzer.py
│   ├── test_confidence.py
│   ├── test_review.py
│   └── test_review_api.py
├── pyproject.toml
└── README.md
```

---

## ⚙️ Environment Configuration

Create a `.env` file in the root directory:

```env
# JWT Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Groq AI Configuration
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Database (defaults to SQLite)
DATABASE_URL=sqlite:///./reviews.db

# GitHub App Integration (Optional for Bot)
GITHUB_APP_ID=123456
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here
GITHUB_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----"
```

---

## 📦 Getting Started

### 1. Backend Setup (FastAPI)

```bash
# Set up virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start backend server (starts on http://localhost:8000)
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup (React + Vite)

```bash
cd frontend

# Install node dependencies
npm install

# Start Vite dev server (starts on http://localhost:5173)
npm run dev
```

---

## 🧪 Running Tests

Execute the automated test suite with pytest:

```bash
pytest -v
```

```
============================= 74 passed in 14.16s ==============================
```

---

## 📡 API Reference

### Health Check
| Method | Endpoint | Auth | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/health` | None | Service health status check |

### Authentication (`/api/v1/auth`)
| Method | Endpoint | Auth | Description |
| :--- | :--- | :---: | :--- |
| `POST` | `/api/v1/auth/register` | None | Register a new user |
| `POST` | `/api/v1/auth/login` | None | Login and obtain JWT tokens |
| `POST` | `/api/v1/auth/refresh` | None | Refresh access token |
| `GET` | `/api/v1/auth/me` | Bearer | Get current user profile |

### Reviews (`/api/v1/reviews`)
| Method | Endpoint | Auth | Description |
| :--- | :--- | :---: | :--- |
| `POST` | `/api/v1/reviews/upload` | Bearer | Upload code file (`.py`, `.js`, `.java`) |
| `POST` | `/api/v1/reviews/paste` | Bearer | Review pasted code snippet directly |
| `POST` | `/api/v1/reviews/github` | Bearer | Fetch and review public GitHub file URL |
| `GET` | `/api/v1/reviews/` | Bearer | Get paginated user review history |
| `GET` | `/api/v1/reviews/{id}` | Bearer | Get full review result and issue details |
| `DELETE` | `/api/v1/reviews/{id}` | Bearer | Delete review record |

### GitHub Webhook (`/api/v1/webhook`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/webhook/github` | Receives GitHub PR and push events for automated reviews |

---

## 📄 License

This project is open-source and licensed under the [MIT License](LICENSE).
