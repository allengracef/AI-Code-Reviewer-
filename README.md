# BugLens 🔍⚡

[![Python](https://img.shields.io/badge/Python-3.13%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.1-646CFF.svg)](https://vitejs.dev/)
[![Groq](https://img.shields.io/badge/Groq-Llama--3.3--70B-orange.svg)](https://groq.com/)
[![Lucide](https://img.shields.io/badge/Lucide-Icons-F56565.svg)](https://lucide.dev/)

**BugLens** is an automated, enterprise-grade AI-powered code review application. It combines static code analysis (Ruff for Python, AST pattern analysis for JavaScript) with state-of-the-art LLMs hosted on Groq (`llama-3.3-70b-versatile`) to detect bugs, security vulnerabilities, performance bottlenecks, time/space complexity issues, and architectural anti-patterns.

---

## 🚀 Key Features

- **🔐 User Authentication & JWT Security**: Full user lifecycle management with access/refresh tokens, password hashing, and Bearer token security.
- **🎨 Glassmorphism UI & Modern Design**: Floating glass navigation bar, vibrant blue (`#2457FF`) and icy blue (`#E8F9FF`) theme, dark Mode UI, and high-performance Lucide icons.
- **✨ React Bits Animations**: Animated text entrances letter-by-letter (`<SplitText />`) and 3D folding hero titles (`<FoldText />`) powered by GSAP.
- **⚡ Multiple Code Review Input Modes**:
  - **File Upload**: Support for `.py`, `.js`, and `.java` files up to 25 MB.
  - **Paste Code**: Direct in-browser code editor to paste and inspect snippets on the fly.
- **📊 Detailed AI Code Analysis**:
  - **Granular Issue Categorization**: Critical, High, Medium, and Low severity findings for Security, Performance, Quality, and Architecture.
  - **Complexity Metrics**: Automatic extraction of Time Complexity ($\mathcal{O}(N)$) and Space Complexity ($\mathcal{O}(1)$).
  - **Suggested Refactoring**: Syntax-highlighted code blocks providing drop-in improved solutions.
  - **SVG Donut Summary Chart**: Visual breakdown of findings per review.
- **💾 History & Database Persistence**: Saves all review sessions, summary metrics, and granular findings using SQLAlchemy.

---

## 🛠 Tech Stack

### Frontend
- **Framework**: React 19 + Vite
- **Styling & Theme**: Custom CSS with Glassmorphism blur & radial blue glowing gradients
- **Icons**: Lucide Icons (`lucide-react`)
- **Animations**: GSAP + `@gsap/react` + React Bits (`<SplitText />`, `<FoldText />`, `<GradientWaves />`)
- **Routing & HTTP**: `react-router-dom`, `axios`

### Backend
- **Framework**: FastAPI (Python 3.13+)
- **AI / LLM Engine**: Groq API (`llama-3.3-70b-versatile`)
- **ORM / Database**: SQLAlchemy 2.0 (SQLite / PostgreSQL)
- **Static Linters**: `ruff` (Python), Regex/AST Pattern Matcher (JavaScript)
- **Security**: PyJWT (`python-jose`), Passlib / Bcrypt password hashing
- **Dependency & Package Manager**: [`uv`](https://github.com/astral-sh/uv)
- **Testing**: `pytest`, `httpx`

---

## 📂 Project Structure

```
AI-CodeReviwer/
├── app/
│   ├── api/                # FastAPI routers (auth, review)
│   │   ├── auth.py
│   │   └── review.py       # Upload, Paste, and History endpoints
│   ├── core/               # App configurations and security helpers
│   │   ├── config.py
│   │   └── security.py
│   ├── database.py         # SQLAlchemy engine and session initialization
│   ├── main.py             # FastAPI entrypoint
│   ├── models.py           # Database models (User, ReviewRecord, IssueRecord)
│   ├── schemas/            # Pydantic request/response schemas
│   │   ├── auth.py
│   │   └── review.py
│   └── services/           # Core business logic
│       ├── aggregator.py   # Issue deduplication & normalization
│       ├── ai_reviewer.py  # Groq AI review logic & prompt parsing
│       ├── analyzer.py     # Static linters (ruff, js)
│       ├── auth.py         # Authentication service logic
│       ├── language.py     # Language detection by file extension
│       └── review.py       # Review pipeline coordinator
├── frontend/               # React + Vite frontend application
│   ├── src/
│   │   ├── api/            # Axios API client
│   │   ├── components/     # Navbar, UploadPanel, ReviewList, SplitText, FoldText, GradientWaves
│   │   ├── context/        # AuthContext (JWT state management)
│   │   ├── pages/          # LandingPage, DashboardPage, LoginPage, RegisterPage
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── tests/                  # Pytest test suite
├── pyproject.toml          # Python UV project definition
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
GROQ_MODEL=llama-3.3-70b-versatile

# Database (defaults to SQLite; swap for PostgreSQL in production)
DATABASE_URL=sqlite:///./reviews.db
```

---

## 📦 Installation & Running

### 1. Backend Setup (FastAPI)

```bash
# Install dependencies using uv
uv sync

# Run backend development server (starts on http://localhost:8000)
uv run uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup (React + Vite)

```bash
cd frontend

# Install node packages
npm install

# Start Vite dev server (starts on http://localhost:5173)
npm run dev
```

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
| `POST` | `/api/v1/auth/refresh` | No | Refresh access token using refresh token |
| `GET` | `/api/v1/auth/me` | Yes | Get current user profile |

### Reviews (`/api/v1/reviews`)
| Method | Endpoint | Auth | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/reviews/upload` | Yes | Upload source code file for review |
| `POST` | `/api/v1/reviews/paste` | Yes | Review pasted code snippet directly |
| `GET` | `/api/v1/reviews/` | Yes | Get paginated review history of current user |
| `GET` | `/api/v1/reviews/{id}` | Yes | Fetch details and findings for a specific review |
| `DELETE` | `/api/v1/reviews/{id}` | Yes | Delete a review record |

---

## 🧪 Running Tests

Run the complete backend test suite using `pytest`:

```bash
uv run pytest
```

---

## 📄 License

This project is open-source and licensed under the [MIT License](LICENSE).
