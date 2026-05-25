from fastapi import APIRouter
from backend.database.db import get_db

router = APIRouter(prefix="/api")


@router.get("/dashboard/summary")
async def get_summary():
    db = await get_db()
    try:
        row = await db.execute(
            "SELECT id, completed_at FROM scans WHERE status = 'completed' ORDER BY id DESC LIMIT 1"
        )
        scan = await row.fetchone()
        if not scan:
            return {
                "total_monthly_spend": 0,
                "month_over_month_change": 0,
                "total_potential_savings": 0,
                "resources_scanned": 0,
                "last_scan_time": None,
                "top_services": [],
            }

        scan_id = scan[0]
        last_scan_time = scan[1]

        # Total monthly spend
        row = await db.execute(
            "SELECT SUM(amount) FROM costs WHERE scan_id = ?", (scan_id,)
        )
        total = await row.fetchone()
        total_monthly_spend = round(total[0] or 0, 2)

        # Top services by cost
        cursor = await db.execute(
            "SELECT service, SUM(amount) as total FROM costs WHERE scan_id = ? GROUP BY service ORDER BY total DESC",
            (scan_id,),
        )
        top_services = [
            {"service": r[0], "total": round(r[1], 2)} for r in await cursor.fetchall()
        ]

        # Resource count
        row = await db.execute(
            "SELECT COUNT(*) FROM resources WHERE scan_id = ?", (scan_id,)
        )
        resources_scanned = (await row.fetchone())[0]

        # Potential savings from recommendations
        row = await db.execute(
            "SELECT SUM(estimated_savings) FROM recommendations WHERE scan_id = ? AND status = 'active'",
            (scan_id,),
        )
        savings = await row.fetchone()
        total_potential_savings = round(savings[0] or 0, 2)

        # Month-over-month change
        cursor = await db.execute(
            "SELECT date, SUM(amount) as daily FROM costs WHERE scan_id = ? GROUP BY date ORDER BY date",
            (scan_id,),
        )
        daily_costs = await cursor.fetchall()
        if len(daily_costs) > 1:
            mid = len(daily_costs) // 2
            first_half = sum(r[1] for r in daily_costs[:mid])
            second_half = sum(r[1] for r in daily_costs[mid:])
            if first_half > 0:
                mom_change = round(((second_half - first_half) / first_half) * 100, 1)
            else:
                mom_change = 0
        else:
            mom_change = 0

        return {
            "total_monthly_spend": total_monthly_spend,
            "month_over_month_change": mom_change,
            "total_potential_savings": total_potential_savings,
            "resources_scanned": resources_scanned,
            "last_scan_time": last_scan_time,
            "top_services": top_services,
        }
    finally:
        await db.close()
