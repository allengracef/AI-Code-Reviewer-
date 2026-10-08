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
    # Evidence-Weighted Confidence & Risk Metrics
    risk_score: Optional[int] = None           # 0-100 Code Risk Score
    risk_level: Optional[str] = None           # Low | Moderate | High | Critical
    analysis_confidence: Optional[int] = None  # 0-100 Evidence-Weighted Confidence
    analysis_coverage: Optional[int] = None    # 0-100% Analysis Coverage
    detected_framework: Optional[str] = None   # Framework identifier
    confidence_breakdown: Optional[dict[str, Any]] = None  # 7-signal deterministic breakdown
    unknown_zones: Optional[list[str]] = None  # Factors reducing confidence
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
    filename: Optional[str] = None
    language: Optional[str] = None
    code: str


class GithubImportRequest(BaseModel):
    url: str