import json
from fastapi import APIRouter, Query
from database.db import get_db

router = APIRouter(prefix="/api")


@router.get("/resources")
async def get_resources(service: str = Query(default=None)):
    db = await get_db()
    try:
        row = await db.execute(
            "SELECT id FROM scans WHERE status = 'completed' ORDER BY id DESC LIMIT 1"
        )
        scan = await row.fetchone()
        if not scan:
            return []

        if service:
            cursor = await db.execute(
                "SELECT * FROM resources WHERE scan_id = ? AND service = ?",
                (scan[0], service),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM resources WHERE scan_id = ?", (scan[0],)
            )

        rows = await cursor.fetchall()
        return [
            {
                "id": r[0],
                "service": r[2],
                "resource_id": r[3],
                "resource_type": r[4],
                "region": r[5],
                "metadata": json.loads(r[6]),
                "utilization": json.loads(r[7]),
            }
            for r in rows
        ]
    finally:
        await db.close()
