import json
from datetime import datetime, timezone

from backend.database.db import get_db
from backend.collectors.mock_data import generate_all_mock_data
from backend.config import USE_MOCK_DATA


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

        await db.execute(
            "UPDATE scans SET completed_at = ?, status = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), "completed", scan_id),
        )
        await db.commit()
        return scan_id
    finally:
        await db.close()
