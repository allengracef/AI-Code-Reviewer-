# AI Code Reviewer

An AI-powered code review API that combines static analysis and Large Language Models to perform rigorous, automated code reviews.

## Features

- **Static Analysis**: Uses `ruff` to identify stylistic and basic linting issues in Python code.
- **AI Analysis**: Integrates with Groq (defaulting to `llama-3.1-70b-versatile`) to identify deep bugs, security vulnerabilities, performance bottlenecks, and architectural issues.
- **Smart Aggregation**: Automatically deduplicates findings between static analysis and AI, preferring AI findings for better explanations and actionable suggestions.
- **Async API**: Built with FastAPI for high-performance, non-blocking requests.

## Prerequisites

- Python 3.13 or higher
- [uv](https://github.com/astral-sh/uv) (for dependency management)
- A [Groq API Key](https://console.groq.com/)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/allengracef/AI-Code-Reviewer-.git
   cd AI-Code-Reviewer-
   ```

2. **Set up the environment:**
   Create a `.env` file in the project root and add your Groq API key:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_MODEL=llama-3.1-70b-versatile  # Optional: defaults to llama-3.1-70b-versatile
   ```

3. **Install dependencies:**
   ```bash
   uv sync
   ```

## Usage

**Start the development server:**
```bash
uv run uvicorn app.main:app --reload
```
The API will be available at `http://localhost:8000`. You can explore the interactive API documentation at `http://localhost:8000/docs`.

### API Endpoints

**`POST /api/v1/reviews/upload`**

Upload a source code file for review.

- **Request:** `multipart/form-data` with a `file` field containing the code file (e.g., `.py`, `.js`, `.java`).
- **Response:** A JSON object detailing the detected language and a list of review issues (categorized by severity, category, and line number).

## Testing

The project uses `pytest` for unit testing.
To run the test suite:
```bash
uv run pytest
```
