from app.services.analyzer import analyze_python
def review_code(source_code: str,language:str) ->dict:
    if language == "python":
        issues = analyze_python(source_code)
    else:
        issues = []
    return{
        "language":language,
        "summary":"Static analysis completed.",
        "issues":issues,
        "suggestions":[]
    }