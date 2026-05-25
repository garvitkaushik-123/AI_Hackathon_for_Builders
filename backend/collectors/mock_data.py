import random
from datetime import datetime, timedelta


def _random_id(prefix: str) -> str:
    return f"{prefix}-{random.randint(10000000, 99999999):08x}"


def generate_ec2_instances() -> list[dict]:
    configs = [
        {"type": "t3.micro", "cpu": random.uniform(1, 4), "state": "running", "tag": "idle"},
        {"type": "t3.medium", "cpu": random.uniform(1, 5), "state": "running", "tag": "idle"},
        {"type": "m5.xlarge", "cpu": random.uniform(2, 4), "state": "running", "tag": "idle"},
        {"type": "m5.large", "cpu": random.uniform(8, 14), "state": "running", "tag": "oversized"},
        {"type": "c5.2xlarge", "cpu": random.uniform(10, 15), "state": "running", "tag": "oversized"},
        {"type": "t3.medium", "cpu": random.uniform(40, 65), "state": "running", "tag": "healthy"},
        {"type": "t3.large", "cpu": random.uniform(45, 70), "state": "running", "tag": "healthy"},
        {"type": "m5.large", "cpu": random.uniform(50, 68), "state": "running", "tag": "healthy"},
        {"type": "c5.xlarge", "cpu": random.uniform(55, 72), "state": "running", "tag": "healthy"},
        {"type": "t3.small", "cpu": random.uniform(35, 55), "state": "running", "tag": "healthy"},
    ]
    regions = ["us-east-1", "us-west-2", "eu-west-1"]
    cost_map = {
        "t3.micro": 7.59, "t3.small": 15.18, "t3.medium": 30.37,
        "t3.large": 60.74, "m5.large": 70.08, "m5.xlarge": 140.16,
        "c5.xlarge": 124.10, "c5.2xlarge": 248.20,
    }

    instances = []
    for cfg in configs:
        iid = _random_id("i")
        launch_days_ago = random.randint(30, 365)
        instances.append({
            "service": "ec2",
            "resource_id": iid,
            "resource_type": cfg["type"],
            "region": random.choice(regions),
            "metadata": {
                "state": cfg["state"],
                "launch_time": (datetime.utcnow() - timedelta(days=launch_days_ago)).isoformat(),
                "monthly_cost": cost_map.get(cfg["type"], 50.0),
                "tag": cfg["tag"],
            },
            "utilization": {
                "avg_cpu_percent": round(cfg["cpu"], 1),
                "network_in_gb": round(random.uniform(0.1, 50), 2),
                "network_out_gb": round(random.uniform(0.05, 20), 2),
            },
        })
    return instances


def generate_rds_instances() -> list[dict]:
    configs = [
        {"cls": "db.t3.medium", "engine": "postgresql", "cpu": random.uniform(35, 55),
         "conns": random.randint(10, 50), "multi_az": False, "tag": "healthy"},
        {"cls": "db.r5.large", "engine": "mysql", "cpu": random.uniform(5, 9),
         "conns": random.randint(1, 3), "multi_az": True, "tag": "oversized"},
        {"cls": "db.m5.xlarge", "engine": "postgresql", "cpu": random.uniform(0, 2),
         "conns": 0, "multi_az": False, "tag": "idle"},
        {"cls": "db.t3.medium", "engine": "mysql", "cpu": random.uniform(40, 60),
         "conns": random.randint(15, 40), "multi_az": False, "tag": "healthy"},
    ]
    cost_map = {"db.t3.medium": 49.06, "db.r5.large": 175.20, "db.m5.xlarge": 256.00}

    instances = []
    for cfg in configs:
        instances.append({
            "service": "rds",
            "resource_id": _random_id("db"),
            "resource_type": cfg["cls"],
            "region": "us-east-1",
            "metadata": {
                "engine": cfg["engine"],
                "multi_az": cfg["multi_az"],
                "monthly_cost": cost_map.get(cfg["cls"], 100.0),
                "tag": cfg["tag"],
            },
            "utilization": {
                "avg_cpu_percent": round(cfg["cpu"], 1),
                "connections": cfg["conns"],
            },
        })
    return instances


def generate_s3_buckets() -> list[dict]:
    buckets = [
        {"name": "prod-assets", "size_gb": 245.3, "objects": 184200,
         "storage_class": "STANDARD", "tag": "optimize-class"},
        {"name": "app-logs", "size_gb": 512.7, "objects": 2340000,
         "storage_class": "STANDARD", "tag": "needs-lifecycle"},
        {"name": "user-uploads", "size_gb": 89.1, "objects": 45600,
         "storage_class": "STANDARD", "tag": "optimize-class"},
        {"name": "backups", "size_gb": 1.2, "objects": 340,
         "storage_class": "STANDARD_IA", "tag": "healthy"},
        {"name": "static-site", "size_gb": 0.5, "objects": 1200,
         "storage_class": "STANDARD", "tag": "healthy"},
    ]
    cost_per_gb = {"STANDARD": 0.023, "STANDARD_IA": 0.0125}

    results = []
    for b in buckets:
        monthly_cost = round(b["size_gb"] * cost_per_gb.get(b["storage_class"], 0.023), 2)
        results.append({
            "service": "s3",
            "resource_id": b["name"],
            "resource_type": "bucket",
            "region": "us-east-1",
            "metadata": {
                "size_gb": b["size_gb"],
                "object_count": b["objects"],
                "storage_class": b["storage_class"],
                "monthly_cost": monthly_cost,
                "tag": b["tag"],
            },
            "utilization": {},
        })
    return results


def generate_ebs_volumes() -> list[dict]:
    configs = [
        {"type": "gp3", "size": 100, "iops": 3000, "attached": True, "tag": "healthy"},
        {"type": "gp3", "size": 50, "iops": 3000, "attached": True, "tag": "healthy"},
        {"type": "gp2", "size": 200, "iops": 600, "attached": True, "tag": "healthy"},
        {"type": "gp2", "size": 100, "iops": 300, "attached": False, "tag": "unattached"},
        {"type": "gp3", "size": 250, "iops": 3000, "attached": False, "tag": "unattached"},
        {"type": "io1", "size": 500, "iops": 10000, "attached": False, "tag": "unattached"},
        {"type": "gp3", "size": 500, "iops": 3000, "attached": True, "tag": "oversized"},
        {"type": "gp2", "size": 500, "iops": 1500, "attached": True, "tag": "oversized"},
        {"type": "gp3", "size": 30, "iops": 3000, "attached": True, "tag": "healthy"},
        {"type": "gp2", "size": 50, "iops": 150, "attached": True, "tag": "healthy"},
        {"type": "gp3", "size": 80, "iops": 3000, "attached": False, "tag": "unattached"},
        {"type": "io1", "size": 200, "iops": 5000, "attached": True, "tag": "healthy"},
    ]
    cost_map = {"gp3": 0.08, "gp2": 0.10, "io1": 0.125}

    volumes = []
    for cfg in configs:
        monthly_cost = round(cfg["size"] * cost_map.get(cfg["type"], 0.08), 2)
        volumes.append({
            "service": "ebs",
            "resource_id": _random_id("vol"),
            "resource_type": cfg["type"],
            "region": random.choice(["us-east-1", "us-west-2"]),
            "metadata": {
                "size_gb": cfg["size"],
                "iops": cfg["iops"],
                "attached": cfg["attached"],
                "monthly_cost": monthly_cost,
                "tag": cfg["tag"],
            },
            "utilization": {},
        })
    return volumes


def generate_cost_data() -> list[dict]:
    base_daily = {"ec2": 95, "rds": 35, "s3": 15, "ebs": 12}
    spike_day = random.randint(5, 10)
    costs = []

    for day_offset in range(30, 0, -1):
        date = (datetime.utcnow() - timedelta(days=day_offset)).strftime("%Y-%m-%d")
        for service, base in base_daily.items():
            variance = random.uniform(0.85, 1.15)
            amount = base * variance
            if day_offset == spike_day and service == "ec2":
                amount = base * 3.2
            trend_factor = 1 + (0.15 * (30 - day_offset) / 30)
            amount *= trend_factor
            costs.append({
                "service": service,
                "date": date,
                "amount": round(amount, 2),
                "unit": "USD",
                "granularity": "DAILY",
            })

    return costs


def generate_all_mock_data() -> dict:
    return {
        "resources": (
            generate_ec2_instances()
            + generate_rds_instances()
            + generate_s3_buckets()
            + generate_ebs_volumes()
        ),
        "costs": generate_cost_data(),
    }
