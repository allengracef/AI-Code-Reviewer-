from fastapi import APIRouter,UploadFile,File

router = APIRouter()

@router.post("/upload")
async def upload_code(file:UploadFile = File(...)):
    contents = await file.read()

    return {
        "filename":file.filename,
        "content_type":file.content_type,
        "size": len(contents)
    }