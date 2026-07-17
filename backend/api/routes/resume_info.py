from fastapi import APIRouter

from resume import resume_filename

router = APIRouter()


@router.get("/resume-info")
async def resume_info():
    name = resume_filename()
    return {"loaded": name is not None, "filename": name}
