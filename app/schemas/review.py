from enum import Enum
from typing import Optional

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
    STYLE = "STYLE"


class IssueSource(str, Enum):
    STATIC_ANALYSIS = "STATIC_ANALYSIS"
    AI = "AI"


class ReviewIssue(BaseModel):
    code: Optional[str] = None
    source: IssueSource
    severity: Severity
    category: IssueCategory
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    explanation: Optional[str] = None
    suggestion: Optional[str] = None


class ReviewResult(BaseModel):
    language: str
    summary: str
    issues: list[ReviewIssue]
    suggestions: list[str]


class CodeFile(BaseModel):
    filename: str
    content_type: Optional[str] = None
    size: int
    code: str
    language: str
    review: ReviewResult