import asyncio
import json
from datetime import datetime, timezone

import boto3

from database.db import get_db
from collectors.mock_data import generate_all_mock_data
from collectors.ec2 import collect_ec2
from collectors.rds import collect_rds
from collectors.s3 import collect_s3
from collectors.ebs import collect_ebs
from collectors.costs import collect_costs
from analysis.gemini import generate_recommendations
from aws_credentials import get_aws_credentials, is_mock_mode


async def _collect_live(credentials: dict) -> dict:
    """Run all live collectors against a real AWS account."""
    session = boto3.Session(
        aws_access_key_id=credentials["access_key_id"],
        aws_secret_access_key=credentials["secret_access_key"],
        region_name=credentials["region"],
    )
    region = credentials["region"]

    # Run all collectors in parallel
    ec2_task = collect_ec2(session, region)
    rds_task = collect_rds(session, region)
    s3_task = collect_s3(session, region)
    ebs_task = collect_ebs(session, region)
    costs_task = collect_costs(session, region)

    ec2_data, rds_data, s3_data, ebs_data, costs_data = await asyncio.gather(
        ec2_task, rds_task, s3_task, ebs_task, costs_task
    )

    resources = ec2_data + rds_data + s3_data + ebs_data
    return {"resources": resources, "costs": costs_data}


async def run_scan() -> int:
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        cursor = await db.execute(
            "INSERT INTO scans (started_at, status) VALUES (?, ?)",
            (now, "running"),
        )
        scan_id = cursor.lastrowid

        use_mock = await is_mock_mode()
        credentials = await get_aws_credentials()

        if not use_mock and credentials:
            data = await _collect_live(credentials)
        else:
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
