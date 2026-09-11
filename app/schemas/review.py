from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IssueCategory(str, Enum):
    BUG = "BUG"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    ARCHITECTURE = "ARCHITECTURE"
    READABILITY = "READABILITY"
    MAINTAINABILITY = "MAINTAINABILITY"
    BEST_PRACTICE = "BEST_PRACTICE"


class IssueSource(str, Enum):
    STATIC_ANALYSIS = "STATIC_ANALYSIS"
    AI = "AI"


class ReviewIssue(BaseModel):
    code: Optional[str] = None
    source: IssueSource
    severity: Severity
    category: IssueCategory
    message: str
    line: Optional[Any] = None
    column: Optional[int] = None
    explanation: Optional[str] = None
    suggestion: Optional[str] = None


class ReviewResult(BaseModel):
    language: str
    summary: str
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None
    refactored_code: Optional[str] = None
    issues: list[ReviewIssue]
    suggestions: list[str] = []


class CodeFile(BaseModel):
    filename: str
    content_type: Optional[str] = None
    size: int
    code: str
    language: str
    review: dict[str, Any]


class CodePasteRequest(BaseModel):
    filename: str = "snippet.py"
    language: Optional[str] = "python"
    code: str


class GithubImportRequest(BaseModel):
    url: str