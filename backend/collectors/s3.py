import asyncio
from datetime import datetime, timedelta, timezone
import boto3


def _collect(session: boto3.Session, region: str) -> list[dict]:
    s3 = session.client("s3", region_name=region)
    cw = session.client("cloudwatch", region_name=region)

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=2)

    response = s3.list_buckets()
    buckets = []

    for bucket in response.get("Buckets", []):
        name = bucket["Name"]

        # Get bucket location
        try:
            loc = s3.get_bucket_location(Bucket=name)
            bucket_region = loc.get("LocationConstraint") or "us-east-1"
        except Exception:
            bucket_region = "us-east-1"

        # Get bucket size from CloudWatch
        size_gb = 0.0
        try:
            size_stats = cw.get_metric_statistics(
                Namespace="AWS/S3",
                MetricName="BucketSizeBytes",
                Dimensions=[
                    {"Name": "BucketName", "Value": name},
                    {"Name": "StorageType", "Value": "StandardStorage"},
                ],
                StartTime=start,
                EndTime=now,
                Period=86400,
                Statistics=["Average"],
            )
            datapoints = size_stats.get("Datapoints", [])
            if datapoints:
                latest = max(datapoints, key=lambda d: d["Timestamp"])
                size_gb = round(latest["Average"] / (1024 ** 3), 2)
        except Exception:
            pass

        # Get object count
        object_count = 0
        try:
            obj_stats = cw.get_metric_statistics(
                Namespace="AWS/S3",
                MetricName="NumberOfObjects",
                Dimensions=[
                    {"Name": "BucketName", "Value": name},
                    {"Name": "StorageType", "Value": "AllStorageTypes"},
                ],
                StartTime=start,
                EndTime=now,
                Period=86400,
                Statistics=["Average"],
            )
            datapoints = obj_stats.get("Datapoints", [])
            if datapoints:
                latest = max(datapoints, key=lambda d: d["Timestamp"])
                object_count = int(latest["Average"])
        except Exception:
            pass

        monthly_cost = round(size_gb * 0.023, 2)

        tag = "healthy"
        if size_gb > 100:
            tag = "optimize-class"
        if size_gb > 200:
            tag = "needs-lifecycle"

        buckets.append({
            "service": "s3",
            "resource_id": name,
            "resource_type": "bucket",
            "region": bucket_region,
            "metadata": {
                "size_gb": size_gb,
                "object_count": object_count,
                "storage_class": "STANDARD",
                "monthly_cost": monthly_cost,
                "tag": tag,
            },
            "utilization": {},
        })

    return buckets


async def collect_s3(session: boto3.Session, region: str) -> list[dict]:
    try:
        return await asyncio.to_thread(_collect, session, region)
    except Exception:
        return []
