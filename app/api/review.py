from fastapi import APIRouter,UploadFile,File,HTTPException
from app.schemas.review import CodeFile

router = APIRouter()

@router.post("/upload",response_model = CodeFile)
async def upload_code(file:UploadFile = File(...)):
    contents = await file.read()
    try:
        source_code = contents.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="THe uploaded file must be a valid UTF-8 text file."
        )

    return {
        "filename":file.filename,
        "content_type":file.content_type,
        "size": len(contents),
        "code":source_code
    }