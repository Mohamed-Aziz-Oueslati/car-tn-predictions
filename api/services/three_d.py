import asyncio
import os
import threading
import time
import uuid
from collections import deque
from typing import Optional

import httpx
from fastapi import File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from api.state import DOWNLOAD_DIR, KAGGLE_API_URL, kaggle_url

APP_3D_QUEUE_MAX = int(os.getenv("APP_3D_QUEUE_MAX", "4"))
APP_3D_STATUS_POLL_SEC = int(os.getenv("APP_3D_STATUS_POLL_SEC", "10"))
APP_3D_MAX_WAIT_SEC = int(os.getenv("APP_3D_MAX_WAIT_SEC", "3600"))
app_3d_queue = asyncio.Queue(maxsize=APP_3D_QUEUE_MAX)
app_3d_worker_task = None
app_3d_worker_lock = asyncio.Lock()
app_3d_jobs = {}
app_3d_jobs_lock = threading.Lock()


def _app_update_3d_job(job_id: str, payload: dict) -> None:
    with app_3d_jobs_lock:
        current = app_3d_jobs.get(job_id, {})
        if "created_at" not in current:
            current["created_at"] = time.time()
        current.update(payload)
        current["updated_at"] = time.time()
        app_3d_jobs[job_id] = current


def _app_get_3d_job(job_id: str):
    with app_3d_jobs_lock:
        return app_3d_jobs.get(job_id)


def _app_queue_position(job_id: str):
    try:
        queued_ids = [jid for jid, *_ in list(app_3d_queue._queue)]
        return queued_ids.index(job_id) + 1
    except ValueError:
        return None


def _app_remove_from_queue(job_id: str) -> None:
    try:
        app_3d_queue._queue = deque([item for item in app_3d_queue._queue if item[0] != job_id])
    except Exception:
        pass


def _app_finalize_3d_job(job_id: str, status: str, error: str | None = None) -> None:
    payload = {"status": status, "final": True, "ended_at": time.time()}
    if error:
        payload["error"] = error
    _app_update_3d_job(job_id, payload)
    _app_remove_from_queue(job_id)


async def _app_3d_worker_loop():
    while True:
        job_id, file_bytes, filename, content_type = await app_3d_queue.get()
        _app_update_3d_job(job_id, {"status": "submitting", "started_at": time.time()})
        try:
            submitted_ok = False
            files = {
                "file": (
                    filename or "upload",
                    file_bytes,
                    content_type or "application/octet-stream",
                )
            }
            try:
                async with httpx.AsyncClient(timeout=600.0) as client:
                    gen_resp = await client.post(kaggle_url("/generate"), files=files, params={"job_id": job_id})
                    gen_resp.raise_for_status()
                    gen_data = gen_resp.json()
                submitted_ok = True
                _app_update_3d_job(
                    job_id,
                    {
                        "status": gen_data.get("status", "queued"),
                        "submitted": True,
                        "submitted_at": time.time(),
                    },
                )
            except Exception as e:
                _app_update_3d_job(
                    job_id,
                    {
                        "status": "submit_error",
                        "error": str(e),
                        "submitted": False,
                        "submitted_at": time.time(),
                    },
                )
            poll_started = time.monotonic()
            error_count = 0
            while True:
                if APP_3D_MAX_WAIT_SEC >= 0 and (time.monotonic() - poll_started) >= APP_3D_MAX_WAIT_SEC:
                    _app_finalize_3d_job(job_id, "timeout")
                    break
                try:
                    async with httpx.AsyncClient(timeout=600.0) as client:
                        status_resp = await client.get(kaggle_url(f"/status/{job_id}"))
                        status_resp.raise_for_status()
                        status_data = status_resp.json()
                except Exception as e:
                    error_count += 1
                    _app_update_3d_job(
                        job_id,
                        {
                            "status": "status_error",
                            "error": str(e),
                            "status_error_count": error_count,
                        },
                    )
                    await asyncio.sleep(max(APP_3D_STATUS_POLL_SEC, 1))
                    continue

                status = status_data.get("status")
                error_count = 0
                _app_update_3d_job(job_id, {"status": status, "last_status": status_data})

                if status == "not_found" and not submitted_ok:
                    _app_finalize_3d_job(job_id, "failed_to_submit")
                    break

                if status == "failed":
                    _app_finalize_3d_job(job_id, "failed", status_data.get("error"))
                    break

                if status == "not_found":
                    _app_finalize_3d_job(job_id, "not_found")
                    break

                if status == "completed":
                    _app_finalize_3d_job(job_id, "completed")
                    break

                await asyncio.sleep(max(APP_3D_STATUS_POLL_SEC, 1))
        except Exception as e:
            _app_finalize_3d_job(job_id, "failed_to_submit", str(e))
        finally:
            app_3d_queue.task_done()


async def _ensure_app_3d_worker():
    global app_3d_worker_task
    async with app_3d_worker_lock:
        if app_3d_worker_task is None or app_3d_worker_task.done():
            app_3d_worker_task = asyncio.create_task(_app_3d_worker_loop())


async def startup_3d_queue():
    await _ensure_app_3d_worker()


async def process_image_to_3d(
    file: UploadFile = File(None),
    job_id: Optional[str] = None,
    wait: bool = False,
    download: bool = False,
    timeout_sec: int = 600,
    poll_interval: int = 10,
):
    if not KAGGLE_API_URL:
        raise HTTPException(status_code=503, detail="Kaggle API not configured")

    if file is None and not job_id:
        raise HTTPException(status_code=400, detail="Provide a file or job_id")

    if file is not None:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Empty file")

        job_id = job_id or str(uuid.uuid4())

        if app_3d_queue.full():
            raise HTTPException(status_code=429, detail="Queue is full. Try again later.")

        _app_update_3d_job(job_id, {"status": "queued_local", "queued_at": time.time()})
        await _ensure_app_3d_worker()
        try:
            app_3d_queue.put_nowait((job_id, file_bytes, file.filename, file.content_type))
        except asyncio.QueueFull:
            _app_update_3d_job(job_id, {"status": "rejected", "error": "Queue full"})
            raise HTTPException(status_code=429, detail="Queue is full. Try again later.")

        if not wait and not download:
            return {
                "job_id": job_id,
                "status": "queued",
                "position": _app_queue_position(job_id),
                "queue_size": app_3d_queue.qsize(),
                "next": f"/process-3d?job_id={job_id}",
            }

    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")

    local = _app_get_3d_job(job_id)
    if not local:
        return {"job_id": job_id, "status": "not_found"}

    deadline = time.monotonic() + max(timeout_sec, 0)
    while True:
        local = _app_get_3d_job(job_id) or {}
        status = local.get("status") or "tracking"

        if status == "failed_to_submit":
            raise HTTPException(status_code=502, detail=f"Submission failed: {local.get('error')}")

        if status == "failed":
            raise HTTPException(status_code=500, detail=f"Generation failed: {local.get('error')}")

        if status == "completed":
            if download or wait:
                download_deadline = time.monotonic() + max(timeout_sec, 0)
                last_error = None
                while True:
                    try:
                        async with httpx.AsyncClient(timeout=600.0) as client:
                            download_resp = await client.get(kaggle_url(f"/download/{job_id}"))
                        if download_resp.status_code == 200:
                            modelThreeD = str(DOWNLOAD_DIR / f"{job_id}.glb")
                            with open(modelThreeD, "wb") as f:
                                f.write(download_resp.content)

                            return FileResponse(
                                modelThreeD,
                                media_type="model/gltf-binary",
                                filename=f"{job_id}.glb",
                            )
                        last_error = f"Download not ready ({download_resp.status_code})"
                    except httpx.HTTPError as e:
                        last_error = str(e)

                    if timeout_sec >= 0 and time.monotonic() >= download_deadline:
                        return {"job_id": job_id, "status": "download_timeout", "error": last_error}

                    await asyncio.sleep(max(poll_interval, 1))

            return local.get("last_status") or {"job_id": job_id, "status": status}

        if not wait:
            response = {"job_id": job_id, "status": status}
            if status in {"queued_local", "submitting"}:
                response["position"] = _app_queue_position(job_id)
                response["queue_size"] = app_3d_queue.qsize()
            if local.get("last_status"):
                response["details"] = local.get("last_status")
            return response

        if timeout_sec >= 0 and time.monotonic() >= deadline:
            return {"job_id": job_id, "status": "timeout"}

        await asyncio.sleep(max(poll_interval, 1))


async def process_3d_in_progress(job_id: str):
    local = _app_get_3d_job(job_id)
    if not local:
        return {"job_id": job_id, "exists": False, "in_progress": False, "status": "not_found"}

    status = local.get("status")
    in_progress = status in {"queued_local", "submitting", "queued", "processing", "tracking", "submitted", "status_error"}
    payload = {"job_id": job_id, "exists": True, "in_progress": in_progress, "status": status}
    if status in {"queued_local", "submitting"}:
        payload["position"] = _app_queue_position(job_id)
        payload["queue_size"] = app_3d_queue.qsize()
    return payload
