import asyncio
from datetime import datetime, timedelta, timezone
import boto3


COST_MAP = {
    "t3.micro": 7.59, "t3.small": 15.18, "t3.medium": 30.37,
    "t3.large": 60.74, "t3.xlarge": 121.47, "t3.2xlarge": 242.94,
    "m5.large": 70.08, "m5.xlarge": 140.16, "m5.2xlarge": 280.32,
    "m5.4xlarge": 560.64, "c5.large": 62.05, "c5.xlarge": 124.10,
    "c5.2xlarge": 248.20, "r5.large": 91.98, "r5.xlarge": 183.96,
    "t2.micro": 8.47, "t2.small": 16.94, "t2.medium": 33.87,
}


def _collect(session: boto3.Session, region: str) -> list[dict]:
    ec2 = session.client("ec2", region_name=region)
    cw = session.client("cloudwatch", region_name=region)

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=14)

    response = ec2.describe_instances()
    instances = []

    for reservation in response.get("Reservations", []):
        for inst in reservation.get("Instances", []):
            instance_id = inst["InstanceId"]
            instance_type = inst["InstanceType"]
            state = inst["State"]["Name"]

            if state == "terminated":
                continue

            # Get CPU utilization
            avg_cpu = 0.0
            try:
                cpu_stats = cw.get_metric_statistics(
                    Namespace="AWS/EC2",
                    MetricName="CPUUtilization",
                    Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
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

            # Get network in
            net_in_gb = 0.0
            try:
                net_stats = cw.get_metric_statistics(
                    Namespace="AWS/EC2",
                    MetricName="NetworkIn",
                    Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                    StartTime=start,
                    EndTime=now,
                    Period=86400 * 14,
                    Statistics=["Sum"],
                )
                datapoints = net_stats.get("Datapoints", [])
                if datapoints:
                    net_in_gb = round(datapoints[0]["Sum"] / (1024 ** 3), 2)
            except Exception:
                pass

            # Get network out
            net_out_gb = 0.0
            try:
                net_stats = cw.get_metric_statistics(
                    Namespace="AWS/EC2",
                    MetricName="NetworkOut",
                    Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                    StartTime=start,
                    EndTime=now,
                    Period=86400 * 14,
                    Statistics=["Sum"],
                )
                datapoints = net_stats.get("Datapoints", [])
                if datapoints:
                    net_out_gb = round(datapoints[0]["Sum"] / (1024 ** 3), 2)
            except Exception:
                pass

            # Determine tag
            tag = "healthy"
            if avg_cpu < 5:
                tag = "idle"
            elif avg_cpu < 20 and instance_type.startswith(("m5", "c5", "r5")):
                tag = "oversized"

            launch_time = inst.get("LaunchTime", now)
            if hasattr(launch_time, "isoformat"):
                launch_time = launch_time.isoformat()

            instances.append({
                "service": "ec2",
                "resource_id": instance_id,
                "resource_type": instance_type,
                "region": region,
                "metadata": {
                    "state": state,
                    "launch_time": launch_time,
                    "monthly_cost": COST_MAP.get(instance_type, 50.0),
                    "tag": tag,
                },
                "utilization": {
                    "avg_cpu_percent": avg_cpu,
                    "network_in_gb": net_in_gb,
                    "network_out_gb": net_out_gb,
                },
            })

    return instances


async def collect_ec2(session: boto3.Session, region: str) -> list[dict]:
    try:
        return await asyncio.to_thread(_collect, session, region)
    except Exception:
        return []
