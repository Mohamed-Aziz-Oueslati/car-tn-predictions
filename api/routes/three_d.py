from typing import Optional

from fastapi import APIRouter, File, UploadFile

from api.services.three_d import process_3d_in_progress, process_image_to_3d

router = APIRouter()

@router.post("/process-3d")
async def process_3d_route(
    file: UploadFile = File(None),
    job_id: Optional[str] = None,
    wait: bool = False,
    download: bool = False,
    timeout_sec: int = 600,
    poll_interval: int = 10,
):
    return await process_image_to_3d(
        file=file,
        job_id=job_id,
        wait=wait,
        download=download,
        timeout_sec=timeout_sec,
        poll_interval=poll_interval,
    )

@router.get("/process-3d/in-progress")
async def process_3d_in_progress_route(job_id: str):
    return await process_3d_in_progress(job_id)
