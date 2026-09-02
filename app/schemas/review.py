from pydantic import BaseModel

class ReviewResult(BaseModel):
    language:str
    summary:str
    issues:list
    suggestions:list

class CodeFile(BaseModel):
    filename:str
    content_type:str
    size:int
    code:str
    language:str
    review:ReviewResult
