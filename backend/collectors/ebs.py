import asyncio
import boto3


COST_MAP = {"gp3": 0.08, "gp2": 0.10, "io1": 0.125, "io2": 0.125, "st1": 0.045, "sc1": 0.015, "standard": 0.05}


def _collect(session: boto3.Session, region: str) -> list[dict]:
    ec2 = session.client("ec2", region_name=region)

    response = ec2.describe_volumes()
    volumes = []

    for vol in response.get("Volumes", []):
        vol_id = vol["VolumeId"]
        vol_type = vol["VolumeType"]
        size_gb = vol["Size"]
        iops = vol.get("Iops", 0)
        attached = len(vol.get("Attachments", [])) > 0

        monthly_cost = round(size_gb * COST_MAP.get(vol_type, 0.08), 2)

        tag = "healthy"
        if not attached:
            tag = "unattached"
        elif size_gb >= 500:
            tag = "oversized"

        volumes.append({
            "service": "ebs",
            "resource_id": vol_id,
            "resource_type": vol_type,
            "region": region,
            "metadata": {
                "size_gb": size_gb,
                "iops": iops,
                "attached": attached,
                "monthly_cost": monthly_cost,
                "tag": tag,
            },
            "utilization": {},
        })

    return volumes


async def collect_ebs(session: boto3.Session, region: str) -> list[dict]:
    try:
        return await asyncio.to_thread(_collect, session, region)
    except Exception:
        return []
