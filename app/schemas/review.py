from pydantic import BaseModel
from typing import Optional

class ReviewIssue(BaseModel):
    code:Optional[str] = None
    severity:str
    category:str
    message:str
    line:Optional[int] = None
    column:Optional[int] = None
    explanation: Optional[str] = None
    suggestion:Optional[str] = None


class ReviewResult(BaseModel):
    language:str
    summary:str
    issues:list[ReviewIssue]
    suggestions:list[str]

class CodeFile(BaseModel):
    filename:str
    content_type: Optional[str] = None
    size:int
    code:str
    language:str
    review:ReviewResult
