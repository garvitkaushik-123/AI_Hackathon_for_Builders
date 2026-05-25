import asyncio
from datetime import datetime, timedelta, timezone
import boto3


SERVICE_NAME_MAP = {
    "Amazon Elastic Compute Cloud - Compute": "ec2",
    "Amazon Elastic Compute Cloud": "ec2",
    "EC2 - Other": "ec2",
    "Amazon Relational Database Service": "rds",
    "Amazon Simple Storage Service": "s3",
    "Amazon Elastic Block Store": "ebs",
}


def _collect(session: boto3.Session, region: str) -> list[dict]:
    ce = session.client("ce", region_name="us-east-1")  # Cost Explorer is global

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=30)

    response = ce.get_cost_and_usage(
        TimePeriod={
            "Start": start.strftime("%Y-%m-%d"),
            "End": now.strftime("%Y-%m-%d"),
        },
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )

    costs = []
    for result in response.get("ResultsByTime", []):
        date = result["TimePeriod"]["Start"]
        for group in result.get("Groups", []):
            aws_service = group["Keys"][0]
            amount = float(group["Metrics"]["UnblendedCost"]["Amount"])

            service = SERVICE_NAME_MAP.get(aws_service, "other")

            costs.append({
                "service": service,
                "date": date,
                "amount": round(amount, 2),
                "unit": "USD",
                "granularity": "DAILY",
            })

    return costs


async def collect_costs(session: boto3.Session, region: str) -> list[dict]:
    try:
        return await asyncio.to_thread(_collect, session, region)
    except Exception:
        return []
