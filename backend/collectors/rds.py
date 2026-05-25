import asyncio
from datetime import datetime, timedelta, timezone
import boto3


COST_MAP = {
    "db.t3.micro": 12.41, "db.t3.small": 24.82, "db.t3.medium": 49.06,
    "db.t3.large": 98.11, "db.m5.large": 125.18, "db.m5.xlarge": 256.00,
    "db.m5.2xlarge": 512.00, "db.r5.large": 175.20, "db.r5.xlarge": 350.40,
    "db.t2.micro": 12.41, "db.t2.small": 24.82, "db.t2.medium": 49.06,
}


def _collect(session: boto3.Session, region: str) -> list[dict]:
    rds = session.client("rds", region_name=region)
    cw = session.client("cloudwatch", region_name=region)

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=14)

    response = rds.describe_db_instances()
    instances = []

    for db_inst in response.get("DBInstances", []):
        db_id = db_inst["DBInstanceIdentifier"]
        db_class = db_inst["DBInstanceClass"]
        engine = db_inst["Engine"]
        multi_az = db_inst.get("MultiAZ", False)

        # Get CPU utilization
        avg_cpu = 0.0
        try:
            cpu_stats = cw.get_metric_statistics(
                Namespace="AWS/RDS",
                MetricName="CPUUtilization",
                Dimensions=[{"Name": "DBInstanceIdentifier", "Value": db_id}],
                StartTime=start,
                EndTime=now,
                Period=86400,
                Statistics=["Average"],
            )
            datapoints = cpu_stats.get("Datapoints", [])
            if datapoints:
                avg_cpu = round(
                    sum(d["Average"] for d in datapoints) / len(datapoints), 1
                )
        except Exception:
            pass

        # Get connections
        avg_conns = 0
        try:
            conn_stats = cw.get_metric_statistics(
                Namespace="AWS/RDS",
                MetricName="DatabaseConnections",
                Dimensions=[{"Name": "DBInstanceIdentifier", "Value": db_id}],
                StartTime=start,
                EndTime=now,
                Period=86400,
                Statistics=["Average"],
            )
            datapoints = conn_stats.get("Datapoints", [])
            if datapoints:
                avg_conns = round(
                    sum(d["Average"] for d in datapoints) / len(datapoints)
                )
        except Exception:
            pass

        tag = "healthy"
        if avg_cpu < 5 and avg_conns == 0:
            tag = "idle"
        elif avg_cpu < 15:
            tag = "oversized"

        instances.append({
            "service": "rds",
            "resource_id": db_id,
            "resource_type": db_class,
            "region": region,
            "metadata": {
                "engine": engine,
                "multi_az": multi_az,
                "monthly_cost": COST_MAP.get(db_class, 100.0),
                "tag": tag,
            },
            "utilization": {
                "avg_cpu_percent": avg_cpu,
                "connections": avg_conns,
            },
        })

    return instances


async def collect_rds(session: boto3.Session, region: str) -> list[dict]:
    try:
        return await asyncio.to_thread(_collect, session, region)
    except Exception:
        return []
