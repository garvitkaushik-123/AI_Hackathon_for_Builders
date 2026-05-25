from fastapi import APIRouter
from backend.collectors.scanner import run_scan

router = APIRouter(prefix="/api")


@router.post("/scan")
async def trigger_scan():
    scan_id = await run_scan()
    return {"scan_id": scan_id, "status": "completed"}
