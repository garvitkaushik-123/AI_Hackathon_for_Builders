from fastapi import APIRouter, Query
from backend.database.db import get_db

router = APIRouter(prefix="/api")


@router.get("/costs")
async def get_costs(days: int = Query(default=30)):
    db = await get_db()
    try:
        row = await db.execute(
            "SELECT id FROM scans WHERE status = 'completed' ORDER BY id DESC LIMIT 1"
        )
        scan = await row.fetchone()
        if not scan:
            return []

        cursor = await db.execute(
            "SELECT service, date, amount FROM costs WHERE scan_id = ? ORDER BY date",
            (scan[0],),
        )
        rows = await cursor.fetchall()
        return [{"service": r[0], "date": r[1], "amount": r[2]} for r in rows]
    finally:
        await db.close()
