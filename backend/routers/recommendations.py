from fastapi import APIRouter, Query
from database.db import get_db

router = APIRouter(prefix="/api")


@router.get("/recommendations")
async def get_recommendations(severity: str = Query(default=None)):
    db = await get_db()
    try:
        row = await db.execute(
            "SELECT id FROM scans WHERE status = 'completed' ORDER BY id DESC LIMIT 1"
        )
        scan = await row.fetchone()
        if not scan:
            return []

        if severity:
            cursor = await db.execute(
                "SELECT * FROM recommendations WHERE scan_id = ? AND severity = ? ORDER BY estimated_savings DESC",
                (scan[0], severity),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM recommendations WHERE scan_id = ? ORDER BY estimated_savings DESC",
                (scan[0],),
            )

        rows = await cursor.fetchall()
        return [
            {
                "id": r[0],
                "resource_id": r[2],
                "severity": r[3],
                "title": r[4],
                "description": r[5],
                "estimated_savings": r[6],
                "status": r[7],
            }
            for r in rows
        ]
    finally:
        await db.close()


@router.patch("/recommendations/{rec_id}")
async def update_recommendation(rec_id: int, status: str = Query(default="dismissed")):
    db = await get_db()
    try:
        await db.execute(
            "UPDATE recommendations SET status = ? WHERE id = ?", (status, rec_id)
        )
        await db.commit()
        return {"id": rec_id, "status": status}
    finally:
        await db.close()
