import json
from datetime import datetime, timezone

from database.db import get_db
from collectors.mock_data import generate_all_mock_data
from analysis.gemini import generate_recommendations
from config import USE_MOCK_DATA


async def run_scan() -> int:
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        cursor = await db.execute(
            "INSERT INTO scans (started_at, status) VALUES (?, ?)",
            (now, "running"),
        )
        scan_id = cursor.lastrowid

        if USE_MOCK_DATA:
            data = generate_all_mock_data()
        else:
            # Live collectors would go here
            data = generate_all_mock_data()

        for resource in data["resources"]:
            await db.execute(
                """INSERT INTO resources
                   (scan_id, service, resource_id, resource_type, region,
                    metadata_json, utilization_json, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    scan_id,
                    resource["service"],
                    resource["resource_id"],
                    resource["resource_type"],
                    resource["region"],
                    json.dumps(resource["metadata"]),
                    json.dumps(resource["utilization"]),
                    now,
                ),
            )

        for cost in data["costs"]:
            await db.execute(
                """INSERT INTO costs
                   (scan_id, service, date, amount, unit, granularity)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    scan_id,
                    cost["service"],
                    cost["date"],
                    cost["amount"],
                    cost["unit"],
                    cost["granularity"],
                ),
            )

        await db.commit()

        # Generate AI recommendations
        try:
            recs = await generate_recommendations(data["resources"], data["costs"])
            for rec in recs:
                await db.execute(
                    """INSERT INTO recommendations
                       (scan_id, resource_id, severity, title, description,
                        estimated_savings, status, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        scan_id,
                        rec.get("resource_id"),
                        rec["severity"],
                        rec["title"],
                        rec["description"],
                        rec.get("estimated_savings", 0),
                        "active",
                        now,
                    ),
                )
            await db.commit()
        except Exception:
            pass  # Scan data is still valid without AI recommendations

        await db.execute(
            "UPDATE scans SET completed_at = ?, status = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), "completed", scan_id),
        )
        await db.commit()
        return scan_id
    finally:
        await db.close()
