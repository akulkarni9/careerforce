from fastapi import APIRouter, HTTPException, UploadFile, File

from resume import get_resume_info, save_resume, _extract_text

router = APIRouter()

_SUPPORTED = {"pdf", "docx"}


@router.get("/resume-info")
async def resume_info():
    return await get_resume_info()


@router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "No file provided.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in _SUPPORTED:
        raise HTTPException(400, f"Unsupported file type. Use: {', '.join(_SUPPORTED)}")

    data = await file.read()
    try:
        content = _extract_text(file.filename, data)
    except Exception as e:
        raise HTTPException(422, f"Could not extract text: {e}")

    await save_resume(file.filename, content)
    return {"loaded": True, "filename": file.filename}
