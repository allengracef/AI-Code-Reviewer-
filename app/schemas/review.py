from pydantic import BaseModel

class CodeFile(BaseModel):
    filename:str
    content_type:str
    size:int
    code:str