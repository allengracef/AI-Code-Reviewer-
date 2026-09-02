from fastapi import APIRouter,UploadFile,File,HTTPException
from app.schemas.review import CodeFile
ALLOWED_EXTENSIONS = {".py",".java",".js"}
MAX_FILE_SIZE = 25*1024*1024
from app.services.language import detect_language
from app.services.review import review_code

router = APIRouter()

@router.post("/upload",response_model = CodeFile)
async def upload_code(file:UploadFile = File(...)):
    filename = file.filename or ""
    extension = "." + filename.split(".")[-1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code =400,
            detail = f"Unsupported file type:{extension}"
        )
    contents = await file.read()
    if len(contents)>MAX_FILE_SIZE:
        raise HTTPException(
            status_code = 413,
            detail= "File size exceeds the maximum allowed size of 25 MB"
        )
    try:
        source_code = contents.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="THe uploaded file must be a valid UTF-8 text file."
        )
    language = detect_language(extension)

    review = review_code(source_code,language)

    return {
        "filename":file.filename,
        "content_type":file.content_type,
        "size": len(contents),
        "code":source_code,
        "language":language,
        "review":review
    }
