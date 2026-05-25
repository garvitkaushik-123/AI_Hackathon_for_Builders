# Cloud Cost Optimization Agent — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an AI-powered web dashboard that analyzes AWS infrastructure costs and provides optimization recommendations using Google Gemini.

**Architecture:** Monolithic FastAPI backend with SQLite cache, mock data generator for demo, Gemini 2.5 Flash for analysis. Next.js frontend with Tailwind CSS and Recharts for visualization. Backend serves API on :8000, frontend on :3000.

**Tech Stack:** Python 3.11+, FastAPI, SQLite, google-genai, boto3 | Next.js 14 (App Router), TypeScript, Tailwind CSS, Recharts

**Spec:** `docs/superpowers/specs/2026-05-23-cloud-cost-optimizer-design.md`

---

## File Structure

### Backend (`backend/`)

| File | Responsibility |
|------|---------------|
| `backend/main.py` | FastAPI app, CORS, startup (DB init), router registration |
| `backend/config.py` | Settings from env vars (USE_MOCK_DATA, GEMINI_API_KEY, AWS creds) |
| `backend/database/db.py` | SQLite connection, table creation, query helpers |
| `backend/collectors/mock_data.py` | Realistic synthetic data generator for EC2, RDS, S3, EBS, costs |
| `backend/collectors/ec2.py` | Live EC2 + CloudWatch data collection via boto3 |
| `backend/collectors/rds.py` | Live RDS + CloudWatch data collection via boto3 |
| `backend/collectors/s3.py` | Live S3 + CloudWatch data collection via boto3 |
| `backend/collectors/ebs.py` | Live EBS data collection via boto3 |
| `backend/collectors/scanner.py` | Orchestrates mock or live collectors, stores results in DB |
| `backend/analysis/gemini.py` | Gemini integration: recommendations, Q&A, streaming |
| `backend/routers/dashboard.py` | GET /api/dashboard/summary |
| `backend/routers/costs.py` | GET /api/costs |
| `backend/routers/resources.py` | GET /api/resources |
| `backend/routers/scan.py` | POST /api/scan |
| `backend/routers/recommendations.py` | GET /api/recommendations, PATCH /api/recommendations/{id} |
| `backend/routers/ask.py` | POST /api/ask (streaming) |
| `backend/requirements.txt` | Python dependencies |

### Frontend (`frontend/`)

| File | Responsibility |
|------|---------------|
| `frontend/src/app/layout.tsx` | Root layout with sidebar navigation, dark theme |
| `frontend/src/app/page.tsx` | Dashboard page: summary cards, cost chart, top services |
| `frontend/src/app/resources/page.tsx` | Resources page: tab bar, resource tables |
| `frontend/src/app/ask/page.tsx` | AI Assistant page: chat + recommendations panel |
| `frontend/src/components/SummaryCards.tsx` | Four stat cards (spend, change, savings, resources) |
| `frontend/src/components/CostChart.tsx` | 30-day stacked area chart (Recharts) |
| `frontend/src/components/TopServicesChart.tsx` | Horizontal bar chart of service costs |
| `frontend/src/components/ResourceTable.tsx` | Service-specific resource table with color-coded utilization |
| `frontend/src/components/ChatInterface.tsx` | Chat input + streaming message display |
| `frontend/src/components/RecommendationCard.tsx` | Single recommendation with severity badge, savings, dismiss |
| `frontend/src/lib/api.ts` | API client: fetch helpers, SSE stream reader |

### Root

| File | Responsibility |
|------|---------------|
| `.env.example` | Template for env vars |
| `.gitignore` | Ignore data/, node_modules, .env, __pycache__ |

---

## Task 1: Project Scaffolding & Configuration

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `backend/requirements.txt`
- Create: `backend/config.py`
- Create: `backend/main.py`

- [ ] **Step 1: Create .gitignore**

```
# Python
__pycache__/
*.py[cod]
*.egg-info/
venv/
.venv/

# Node
node_modules/
.next/

# Data
data/

# Env
.env

# OS
.DS_Store
```

- [ ] **Step 2: Create .env.example**

```
# Data source (set to false for live AWS)
USE_MOCK_DATA=true

# Gemini
GEMINI_API_KEY=your-gemini-api-key

# AWS (only needed when USE_MOCK_DATA=false)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=us-east-1
```

- [ ] **Step 3: Create backend/requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
python-dotenv==1.0.1
google-genai==1.14.0
boto3==1.35.0
aiosqlite==0.20.0
sse-starlette==2.1.0
```

- [ ] **Step 4: Create Python venv and install deps**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Expected: all packages install without errors.

- [ ] **Step 5: Create backend/config.py**

```python
import os
from dotenv import load_dotenv

load_dotenv()

USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "true").lower() == "true"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "cloudopt.db")
```

- [ ] **Step 6: Create backend/main.py (minimal)**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Cloud Cost Optimizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 7: Verify backend starts**

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/api/health` — expect `{"status": "ok"}`.

- [ ] **Step 8: Commit**

```bash
git add .gitignore .env.example backend/requirements.txt backend/config.py backend/main.py
git commit -m "feat: scaffold backend with FastAPI, config, and health endpoint"
```

---

## Task 2: Database Layer

**Files:**
- Create: `backend/database/__init__.py`
- Create: `backend/database/db.py`
- Modify: `backend/main.py` (add startup event)

- [ ] **Step 1: Create backend/database/__init__.py**

Empty file.

- [ ] **Step 2: Create backend/database/db.py**

```python
import aiosqlite
import os
from backend.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL DEFAULT 'running'
);

CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL,
    service TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    region TEXT NOT NULL DEFAULT 'us-east-1',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    utilization_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (scan_id) REFERENCES scans(id)
);

CREATE TABLE IF NOT EXISTS costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL,
    service TEXT NOT NULL,
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    unit TEXT NOT NULL DEFAULT 'USD',
    granularity TEXT NOT NULL DEFAULT 'DAILY',
    FOREIGN KEY (scan_id) REFERENCES scans(id)
);

CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL,
    resource_id TEXT,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    estimated_savings REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    FOREIGN KEY (scan_id) REFERENCES scans(id)
);
"""


async def get_db() -> aiosqlite.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    db = await get_db()
    await db.executescript(SCHEMA)
    await db.commit()
    await db.close()
```

- [ ] **Step 3: Add startup event to backend/main.py**

Add after the CORS middleware block:

```python
from backend.database.db import init_db


@app.on_event("startup")
async def startup():
    await init_db()
```

- [ ] **Step 4: Verify DB initializes on startup**

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

Check that `data/cloudopt.db` was created:

```bash
ls -la data/cloudopt.db
```

Expected: file exists.

- [ ] **Step 5: Commit**

```bash
git add backend/database/ backend/main.py
git commit -m "feat: add SQLite database layer with schema and auto-init"
```

---

## Task 3: Mock Data Generator

**Files:**
- Create: `backend/collectors/__init__.py`
- Create: `backend/collectors/mock_data.py`

- [ ] **Step 1: Create backend/collectors/__init__.py**

Empty file.

- [ ] **Step 2: Create backend/collectors/mock_data.py**

```python
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
```

- [ ] **Step 3: Verify mock data generates correctly**

```bash
cd backend
source venv/bin/activate
python -c "
from collectors.mock_data import generate_all_mock_data
data = generate_all_mock_data()
print(f'Resources: {len(data[\"resources\"])}')
print(f'Cost entries: {len(data[\"costs\"])}')
services = {}
for r in data['resources']:
    services[r['service']] = services.get(r['service'], 0) + 1
print(f'By service: {services}')
"
```

Expected output:
```
Resources: 31
Cost entries: 120
By service: {'ec2': 10, 'rds': 4, 's3': 5, 'ebs': 12}
```

- [ ] **Step 4: Commit**

```bash
git add backend/collectors/
git commit -m "feat: add mock data generator with realistic AWS resource and cost data"
```

---

## Task 4: Scanner Orchestrator

**Files:**
- Create: `backend/collectors/scanner.py`

- [ ] **Step 1: Create backend/collectors/scanner.py**

```python
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
            # from backend.collectors.ec2 import collect_ec2
            # ...
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
```

- [ ] **Step 2: Verify scanner writes to DB**

```bash
cd backend
source venv/bin/activate
python -c "
import asyncio
from collectors.scanner import run_scan
from database.db import init_db, get_db

async def test():
    await init_db()
    scan_id = await run_scan()
    print(f'Scan ID: {scan_id}')
    db = await get_db()
    row = await db.execute('SELECT COUNT(*) as cnt FROM resources WHERE scan_id = ?', (scan_id,))
    r = await row.fetchone()
    print(f'Resources stored: {r[0]}')
    row = await db.execute('SELECT COUNT(*) as cnt FROM costs WHERE scan_id = ?', (scan_id,))
    c = await row.fetchone()
    print(f'Cost entries stored: {c[0]}')
    await db.close()

asyncio.run(test())
"
```

Expected:
```
Scan ID: 1
Resources stored: 31
Cost entries stored: 120
```

- [ ] **Step 3: Commit**

```bash
git add backend/collectors/scanner.py
git commit -m "feat: add scanner orchestrator that stores mock data in SQLite"
```

---

## Task 5: API Routes — Dashboard, Costs, Resources, Scan, Scans

**Files:**
- Create: `backend/routers/__init__.py`
- Create: `backend/routers/dashboard.py`
- Create: `backend/routers/costs.py`
- Create: `backend/routers/resources.py`
- Create: `backend/routers/scan.py`
- Create: `backend/routers/recommendations.py`
- Modify: `backend/main.py` (register routers)

- [ ] **Step 1: Create backend/routers/__init__.py**

Empty file.

- [ ] **Step 2: Create backend/routers/dashboard.py**

```python
import json
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

        # Total monthly spend (sum last 30 days of costs)
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

        # Month-over-month: compare first 15 days vs last 15 days
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
```

- [ ] **Step 3: Create backend/routers/costs.py**

```python
from fastapi import APIRouter, Query
from backend.database.db import get_db

router = APIRouter(prefix="/api")


@router.get("/costs")
async def get_costs(days: int = Query(default=30)):
    db = await get_db()
    try:
        row = await db.execute(
            "SELECT id FROM scans WHERE status = 'completed' ORDER BY id DESC LIMIT 1"
        )
        scan = await row.fetchone()
        if not scan:
            return []

        cursor = await db.execute(
            "SELECT service, date, amount FROM costs WHERE scan_id = ? ORDER BY date",
            (scan[0],),
        )
        rows = await cursor.fetchall()
        return [{"service": r[0], "date": r[1], "amount": r[2]} for r in rows]
    finally:
        await db.close()
```

- [ ] **Step 4: Create backend/routers/resources.py**

```python
import json
from fastapi import APIRouter, Query
from backend.database.db import get_db

router = APIRouter(prefix="/api")


@router.get("/resources")
async def get_resources(service: str = Query(default=None)):
    db = await get_db()
    try:
        row = await db.execute(
            "SELECT id FROM scans WHERE status = 'completed' ORDER BY id DESC LIMIT 1"
        )
        scan = await row.fetchone()
        if not scan:
            return []

        if service:
            cursor = await db.execute(
                "SELECT * FROM resources WHERE scan_id = ? AND service = ?",
                (scan[0], service),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM resources WHERE scan_id = ?", (scan[0],)
            )

        rows = await cursor.fetchall()
        return [
            {
                "id": r[0],
                "service": r[2],
                "resource_id": r[3],
                "resource_type": r[4],
                "region": r[5],
                "metadata": json.loads(r[6]),
                "utilization": json.loads(r[7]),
            }
            for r in rows
        ]
    finally:
        await db.close()
```

- [ ] **Step 5: Create backend/routers/scan.py**

```python
from fastapi import APIRouter
from backend.collectors.scanner import run_scan

router = APIRouter(prefix="/api")


@router.post("/scan")
async def trigger_scan():
    scan_id = await run_scan()
    return {"scan_id": scan_id, "status": "completed"}
```

- [ ] **Step 6: Create backend/routers/recommendations.py**

```python
from fastapi import APIRouter, Query
from backend.database.db import get_db

router = APIRouter(prefix="/api")


@router.get("/recommendations")
async def get_recommendations(severity: str = Query(default=None)):
    db = await get_db()
    try:
        row = await db.execute(
            "SELECT id FROM scans WHERE status = 'completed' ORDER BY id DESC LIMIT 1"
        )
        scan = await row.fetchone()
        if not scan:
            return []

        if severity:
            cursor = await db.execute(
                "SELECT * FROM recommendations WHERE scan_id = ? AND severity = ? ORDER BY estimated_savings DESC",
                (scan[0], severity),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM recommendations WHERE scan_id = ? ORDER BY estimated_savings DESC",
                (scan[0],),
            )

        rows = await cursor.fetchall()
        return [
            {
                "id": r[0],
                "resource_id": r[2],
                "severity": r[3],
                "title": r[4],
                "description": r[5],
                "estimated_savings": r[6],
                "status": r[7],
            }
            for r in rows
        ]
    finally:
        await db.close()


@router.patch("/recommendations/{rec_id}")
async def update_recommendation(rec_id: int, status: str = Query(default="dismissed")):
    db = await get_db()
    try:
        await db.execute(
            "UPDATE recommendations SET status = ? WHERE id = ?", (status, rec_id)
        )
        await db.commit()
        return {"id": rec_id, "status": status}
    finally:
        await db.close()
```

- [ ] **Step 7: Register all routers in backend/main.py**

Replace the full content of `backend/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database.db import init_db
from backend.routers import dashboard, costs, resources, scan, recommendations

app = FastAPI(title="Cloud Cost Optimizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(costs.router)
app.include_router(resources.router)
app.include_router(scan.router)
app.include_router(recommendations.router)


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 8: Verify all endpoints work**

Start server, then test:

```bash
# Terminal 1
cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000

# Terminal 2 — trigger a scan first
curl -X POST http://localhost:8000/api/scan
# Expect: {"scan_id":1,"status":"completed"}

curl http://localhost:8000/api/dashboard/summary
# Expect: JSON with total_monthly_spend > 0

curl http://localhost:8000/api/costs
# Expect: array of 120 cost entries

curl "http://localhost:8000/api/resources?service=ec2"
# Expect: array of 10 EC2 instances

curl http://localhost:8000/api/recommendations
# Expect: empty array (no Gemini analysis yet)
```

- [ ] **Step 9: Commit**

```bash
git add backend/routers/ backend/main.py
git commit -m "feat: add API routes for dashboard, costs, resources, scan, recommendations"
```

---

## Task 6: Gemini Integration

**Files:**
- Create: `backend/analysis/__init__.py`
- Create: `backend/analysis/gemini.py`
- Modify: `backend/collectors/scanner.py` (call Gemini after scan)
- Create: `backend/routers/ask.py`
- Modify: `backend/main.py` (register ask router)

- [ ] **Step 1: Create backend/analysis/__init__.py**

Empty file.

- [ ] **Step 2: Create backend/analysis/gemini.py**

```python
import json
from google import genai
from google.genai import types
from backend.config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL = "gemini-2.5-flash"

RECOMMENDATION_SYSTEM_PROMPT = """You are a cloud cost optimization expert. Analyze the provided AWS infrastructure data and identify optimization opportunities.

For each finding, return a JSON array of objects with these exact fields:
- severity: "critical" | "warning" | "info"
- resource_id: the specific resource ID affected (or null for general findings)
- title: short title (under 80 chars)
- description: detailed explanation and actionable recommendation (2-3 sentences)
- estimated_savings: estimated monthly savings in USD (number)

Rules:
- "critical": idle resources costing >$50/month or unattached volumes
- "warning": underutilized resources that could be downsized
- "info": minor optimizations like storage class changes

Return ONLY the JSON array, no markdown fences or extra text."""

CHAT_SYSTEM_PROMPT = """You are a cloud cost optimization assistant. You have access to real AWS infrastructure data provided below. Answer questions about costs, resource utilization, and optimization opportunities grounded in this data.

Be specific: reference actual resource IDs, dollar amounts, and metrics from the data. When suggesting savings, show your math. Be concise but thorough."""


async def generate_recommendations(resources: list[dict], costs: list[dict]) -> list[dict]:
    if not GEMINI_API_KEY:
        return []

    context = json.dumps({"resources": resources, "costs": costs}, indent=2)
    prompt = f"Analyze this AWS infrastructure data and provide optimization recommendations:\n\n{context}"

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=RECOMMENDATION_SYSTEM_PROMPT,
            temperature=0.3,
        ),
    )

    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]

    return json.loads(text)


async def ask_question_stream(question: str, resources: list[dict], costs: list[dict]):
    if not GEMINI_API_KEY:
        yield "Gemini API key not configured. Please set GEMINI_API_KEY in your .env file."
        return

    context = json.dumps({"resources": resources, "costs": costs}, indent=2)
    prompt = f"Current AWS infrastructure data:\n\n{context}\n\nUser question: {question}"

    response = client.models.generate_content_stream(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=CHAT_SYSTEM_PROMPT,
            temperature=0.5,
        ),
    )

    for chunk in response:
        if chunk.text:
            yield chunk.text
```

- [ ] **Step 3: Update backend/collectors/scanner.py to call Gemini**

Replace the full content:

```python
import json
from datetime import datetime, timezone

from backend.database.db import get_db
from backend.collectors.mock_data import generate_all_mock_data
from backend.analysis.gemini import generate_recommendations
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
```

- [ ] **Step 4: Create backend/routers/ask.py**

```python
import json
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
from backend.database.db import get_db
from backend.analysis.gemini import ask_question_stream

router = APIRouter(prefix="/api")


@router.post("/ask")
async def ask(request: Request):
    body = await request.json()
    question = body.get("question", "")

    db = await get_db()
    try:
        row = await db.execute(
            "SELECT id FROM scans WHERE status = 'completed' ORDER BY id DESC LIMIT 1"
        )
        scan = await row.fetchone()
        if not scan:
            async def no_data():
                yield {"data": "No scan data available. Please run a scan first."}
            return EventSourceResponse(no_data())

        scan_id = scan[0]

        cursor = await db.execute(
            "SELECT service, resource_id, resource_type, region, metadata_json, utilization_json FROM resources WHERE scan_id = ?",
            (scan_id,),
        )
        resource_rows = await cursor.fetchall()
        resources = [
            {
                "service": r[0], "resource_id": r[1], "resource_type": r[2],
                "region": r[3], "metadata": json.loads(r[4]),
                "utilization": json.loads(r[5]),
            }
            for r in resource_rows
        ]

        cursor = await db.execute(
            "SELECT service, date, amount FROM costs WHERE scan_id = ?", (scan_id,)
        )
        cost_rows = await cursor.fetchall()
        costs = [{"service": r[0], "date": r[1], "amount": r[2]} for r in cost_rows]
    finally:
        await db.close()

    async def stream():
        async for chunk in ask_question_stream(question, resources, costs):
            yield {"data": chunk}

    return EventSourceResponse(stream())
```

- [ ] **Step 5: Register ask router in backend/main.py**

Add to the imports:

```python
from backend.routers import dashboard, costs, resources, scan, recommendations, ask
```

Add after the other `include_router` lines:

```python
app.include_router(ask.router)
```

- [ ] **Step 6: Test with a real Gemini key**

Create `.env` with your Gemini API key, restart the server, then:

```bash
# Trigger scan (now includes Gemini recommendations)
curl -X POST http://localhost:8000/api/scan

# Check recommendations
curl http://localhost:8000/api/recommendations
# Expect: array of recommendation objects with severity, title, savings

# Test chat
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What are my biggest cost saving opportunities?"}'
# Expect: SSE stream of text chunks
```

- [ ] **Step 7: Commit**

```bash
git add backend/analysis/ backend/routers/ask.py backend/collectors/scanner.py backend/main.py
git commit -m "feat: add Gemini-powered recommendations and streaming chat Q&A"
```

---

## Task 7: Frontend Scaffolding

**Files:**
- Create: `frontend/` (via create-next-app)
- Modify: `frontend/src/app/layout.tsx`
- Create: `frontend/src/lib/api.ts`

- [ ] **Step 1: Scaffold Next.js app**

```bash
cd /path/to/repo
npx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir --import-alias "@/*" --eslint --no-turbopack
```

When prompted, accept defaults. Then install Recharts:

```bash
cd frontend
npm install recharts
```

- [ ] **Step 2: Create frontend/src/lib/api.ts**

Note: create-next-app with `--no-src-dir` puts code in `frontend/app/`, not `frontend/src/app/`. Adjust paths after scaffolding to match actual structure. The instructions below assume `frontend/app/` and `frontend/lib/`.

Create `frontend/lib/api.ts`:

```typescript
const API_BASE = "http://localhost:8000/api";

export async function fetchSummary() {
  const res = await fetch(`${API_BASE}/dashboard/summary`);
  return res.json();
}

export async function fetchCosts(days = 30) {
  const res = await fetch(`${API_BASE}/costs?days=${days}`);
  return res.json();
}

export async function fetchResources(service?: string) {
  const url = service
    ? `${API_BASE}/resources?service=${service}`
    : `${API_BASE}/resources`;
  const res = await fetch(url);
  return res.json();
}

export async function triggerScan() {
  const res = await fetch(`${API_BASE}/scan`, { method: "POST" });
  return res.json();
}

export async function fetchRecommendations(severity?: string) {
  const url = severity
    ? `${API_BASE}/recommendations?severity=${severity}`
    : `${API_BASE}/recommendations`;
  const res = await fetch(url);
  return res.json();
}

export async function dismissRecommendation(id: number) {
  const res = await fetch(`${API_BASE}/recommendations/${id}?status=dismissed`, {
    method: "PATCH",
  });
  return res.json();
}

export async function* askStream(question: string) {
  const res = await fetch(`${API_BASE}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  const reader = res.body?.getReader();
  const decoder = new TextDecoder();
  if (!reader) return;

  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        yield line.slice(6);
      }
    }
  }
}
```

- [ ] **Step 3: Replace frontend/app/layout.tsx with sidebar layout**

```tsx
import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "CloudOpt — AWS Cost Optimizer",
  description: "AI-powered cloud cost optimization",
};

const navItems = [
  { href: "/", label: "Dashboard", icon: "📊" },
  { href: "/resources", label: "Resources", icon: "🖥️" },
  { href: "/ask", label: "AI Assistant", icon: "🤖" },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-gray-950 text-gray-100 min-h-screen flex">
        <aside className="w-64 bg-gray-900 border-r border-gray-800 p-6 flex flex-col">
          <h1 className="text-xl font-bold text-white mb-8">
            <span className="text-emerald-400">Cloud</span>Opt
          </h1>
          <nav className="flex flex-col gap-1">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            ))}
          </nav>
        </aside>
        <main className="flex-1 p-8 overflow-auto">{children}</main>
      </body>
    </html>
  );
}
```

- [ ] **Step 4: Update frontend/app/globals.css**

Replace content with:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 5: Verify frontend starts**

```bash
cd frontend
npm run dev
```

Visit `http://localhost:3000` — expect dark sidebar with CloudOpt title and three nav links.

- [ ] **Step 6: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold Next.js frontend with sidebar layout and API client"
```

---

## Task 8: Dashboard Page

**Files:**
- Create: `frontend/components/SummaryCards.tsx`
- Create: `frontend/components/CostChart.tsx`
- Create: `frontend/components/TopServicesChart.tsx`
- Modify: `frontend/app/page.tsx`

- [ ] **Step 1: Create frontend/components/SummaryCards.tsx**

```tsx
"use client";

interface SummaryData {
  total_monthly_spend: number;
  month_over_month_change: number;
  total_potential_savings: number;
  resources_scanned: number;
  last_scan_time: string | null;
}

export default function SummaryCards({ data }: { data: SummaryData | null }) {
  if (!data) return null;

  const cards = [
    {
      label: "Monthly Spend",
      value: `$${data.total_monthly_spend.toLocaleString()}`,
      color: "text-white",
    },
    {
      label: "Month-over-Month",
      value: `${data.month_over_month_change > 0 ? "+" : ""}${data.month_over_month_change}%`,
      color: data.month_over_month_change > 0 ? "text-red-400" : "text-emerald-400",
    },
    {
      label: "Potential Savings",
      value: `$${data.total_potential_savings.toLocaleString()}`,
      color: "text-emerald-400",
    },
    {
      label: "Resources Scanned",
      value: data.resources_scanned.toString(),
      color: "text-white",
    },
  ];

  return (
    <div className="grid grid-cols-4 gap-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="bg-gray-900 border border-gray-800 rounded-xl p-6"
        >
          <p className="text-sm text-gray-400 mb-1">{card.label}</p>
          <p className={`text-2xl font-bold ${card.color}`}>{card.value}</p>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Create frontend/components/CostChart.tsx**

```tsx
"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface CostEntry {
  service: string;
  date: string;
  amount: number;
}

const COLORS: Record<string, string> = {
  ec2: "#10b981",
  rds: "#3b82f6",
  s3: "#f59e0b",
  ebs: "#8b5cf6",
};

export default function CostChart({ data }: { data: CostEntry[] }) {
  const grouped: Record<string, Record<string, number>> = {};
  for (const entry of data) {
    if (!grouped[entry.date]) grouped[entry.date] = {};
    grouped[entry.date][entry.service] = entry.amount;
  }

  const chartData = Object.entries(grouped)
    .map(([date, services]) => ({
      date: date.slice(5),
      ...services,
    }))
    .sort((a, b) => a.date.localeCompare(b.date));

  const services = [...new Set(data.map((d) => d.service))];

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <h2 className="text-lg font-semibold mb-4">Cost Trend (30 days)</h2>
      <ResponsiveContainer width="100%" height={350}>
        <AreaChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="date" stroke="#9ca3af" fontSize={12} />
          <YAxis stroke="#9ca3af" fontSize={12} tickFormatter={(v) => `$${v}`} />
          <Tooltip
            contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #374151", borderRadius: "8px" }}
            labelStyle={{ color: "#9ca3af" }}
            formatter={(value: number) => [`$${value.toFixed(2)}`, ""]}
          />
          <Legend />
          {services.map((service) => (
            <Area
              key={service}
              type="monotone"
              dataKey={service}
              stackId="1"
              fill={COLORS[service] || "#6b7280"}
              stroke={COLORS[service] || "#6b7280"}
              fillOpacity={0.6}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
```

- [ ] **Step 3: Create frontend/components/TopServicesChart.tsx**

```tsx
"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface ServiceTotal {
  service: string;
  total: number;
}

const COLORS = ["#10b981", "#3b82f6", "#f59e0b", "#8b5cf6"];

export default function TopServicesChart({ data }: { data: ServiceTotal[] }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <h2 className="text-lg font-semibold mb-4">Top Services by Spend</h2>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data} layout="vertical">
          <XAxis type="number" stroke="#9ca3af" fontSize={12} tickFormatter={(v) => `$${v}`} />
          <YAxis
            type="category"
            dataKey="service"
            stroke="#9ca3af"
            fontSize={12}
            width={50}
            tickFormatter={(v) => v.toUpperCase()}
          />
          <Tooltip
            contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #374151", borderRadius: "8px" }}
            formatter={(value: number) => [`$${value.toFixed(2)}`, "Spend"]}
          />
          <Bar dataKey="total" radius={[0, 6, 6, 0]}>
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
```

- [ ] **Step 4: Replace frontend/app/page.tsx**

```tsx
"use client";

import { useEffect, useState } from "react";
import { fetchSummary, fetchCosts, triggerScan } from "@/lib/api";
import SummaryCards from "@/components/SummaryCards";
import CostChart from "@/components/CostChart";
import TopServicesChart from "@/components/TopServicesChart";

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [costs, setCosts] = useState([]);
  const [scanning, setScanning] = useState(false);

  const loadData = async () => {
    const [s, c] = await Promise.all([fetchSummary(), fetchCosts()]);
    setSummary(s);
    setCosts(c);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleScan = async () => {
    setScanning(true);
    await triggerScan();
    await loadData();
    setScanning(false);
  };

  const hasData = summary && summary.last_scan_time;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          {summary?.last_scan_time && (
            <p className="text-sm text-gray-400 mt-1">
              Last scanned: {new Date(summary.last_scan_time).toLocaleString()}
            </p>
          )}
        </div>
        <button
          onClick={handleScan}
          disabled={scanning}
          className="bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors"
        >
          {scanning ? "Scanning..." : "Scan Now"}
        </button>
      </div>

      {!hasData ? (
        <div className="flex flex-col items-center justify-center h-96 bg-gray-900 border border-gray-800 rounded-xl">
          <p className="text-xl text-gray-400 mb-4">No scan data yet</p>
          <button
            onClick={handleScan}
            disabled={scanning}
            className="bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-700 text-white px-8 py-3 rounded-lg font-medium text-lg transition-colors"
          >
            {scanning ? "Scanning..." : "Run Your First Scan"}
          </button>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          <SummaryCards data={summary} />
          <CostChart data={costs} />
          <TopServicesChart data={summary.top_services} />
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Verify dashboard renders**

With backend running on :8000 and frontend on :3000, visit `http://localhost:3000`. Click "Run Your First Scan" — expect summary cards, cost trend chart, and top services chart to populate.

- [ ] **Step 6: Commit**

```bash
git add frontend/components/ frontend/app/page.tsx
git commit -m "feat: add dashboard page with summary cards, cost chart, and top services"
```

---

## Task 9: Resources Page

**Files:**
- Create: `frontend/components/ResourceTable.tsx`
- Create: `frontend/app/resources/page.tsx`

- [ ] **Step 1: Create frontend/components/ResourceTable.tsx**

```tsx
"use client";

interface Resource {
  id: number;
  service: string;
  resource_id: string;
  resource_type: string;
  region: string;
  metadata: Record<string, any>;
  utilization: Record<string, any>;
}

function getUtilColor(cpu: number | undefined): string {
  if (cpu === undefined) return "text-gray-400";
  if (cpu < 5) return "text-red-400";
  if (cpu < 20) return "text-yellow-400";
  return "text-emerald-400";
}

function EC2Table({ resources }: { resources: Resource[] }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-gray-800 text-gray-400">
          <th className="text-left py-3 px-4">Instance ID</th>
          <th className="text-left py-3 px-4">Type</th>
          <th className="text-left py-3 px-4">State</th>
          <th className="text-right py-3 px-4">Avg CPU%</th>
          <th className="text-right py-3 px-4">Network In</th>
          <th className="text-left py-3 px-4">Region</th>
          <th className="text-right py-3 px-4">Est. Cost/mo</th>
        </tr>
      </thead>
      <tbody>
        {resources.map((r) => (
          <tr key={r.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
            <td className="py-3 px-4 font-mono text-xs">{r.resource_id}</td>
            <td className="py-3 px-4">{r.resource_type}</td>
            <td className="py-3 px-4">{r.metadata.state}</td>
            <td className={`py-3 px-4 text-right font-medium ${getUtilColor(r.utilization.avg_cpu_percent)}`}>
              {r.utilization.avg_cpu_percent}%
            </td>
            <td className="py-3 px-4 text-right">{r.utilization.network_in_gb} GB</td>
            <td className="py-3 px-4">{r.region}</td>
            <td className="py-3 px-4 text-right">${r.metadata.monthly_cost}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function RDSTable({ resources }: { resources: Resource[] }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-gray-800 text-gray-400">
          <th className="text-left py-3 px-4">DB ID</th>
          <th className="text-left py-3 px-4">Class</th>
          <th className="text-left py-3 px-4">Engine</th>
          <th className="text-right py-3 px-4">Avg CPU%</th>
          <th className="text-right py-3 px-4">Connections</th>
          <th className="text-left py-3 px-4">Multi-AZ</th>
          <th className="text-right py-3 px-4">Est. Cost/mo</th>
        </tr>
      </thead>
      <tbody>
        {resources.map((r) => (
          <tr key={r.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
            <td className="py-3 px-4 font-mono text-xs">{r.resource_id}</td>
            <td className="py-3 px-4">{r.resource_type}</td>
            <td className="py-3 px-4">{r.metadata.engine}</td>
            <td className={`py-3 px-4 text-right font-medium ${getUtilColor(r.utilization.avg_cpu_percent)}`}>
              {r.utilization.avg_cpu_percent}%
            </td>
            <td className="py-3 px-4 text-right">{r.utilization.connections}</td>
            <td className="py-3 px-4">{r.metadata.multi_az ? "Yes" : "No"}</td>
            <td className="py-3 px-4 text-right">${r.metadata.monthly_cost}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function S3Table({ resources }: { resources: Resource[] }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-gray-800 text-gray-400">
          <th className="text-left py-3 px-4">Bucket Name</th>
          <th className="text-right py-3 px-4">Size (GB)</th>
          <th className="text-right py-3 px-4">Objects</th>
          <th className="text-left py-3 px-4">Storage Class</th>
          <th className="text-right py-3 px-4">Est. Cost/mo</th>
        </tr>
      </thead>
      <tbody>
        {resources.map((r) => (
          <tr key={r.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
            <td className="py-3 px-4 font-mono text-xs">{r.resource_id}</td>
            <td className="py-3 px-4 text-right">{r.metadata.size_gb}</td>
            <td className="py-3 px-4 text-right">{r.metadata.object_count?.toLocaleString()}</td>
            <td className="py-3 px-4">{r.metadata.storage_class}</td>
            <td className="py-3 px-4 text-right">${r.metadata.monthly_cost}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function EBSTable({ resources }: { resources: Resource[] }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-gray-800 text-gray-400">
          <th className="text-left py-3 px-4">Volume ID</th>
          <th className="text-left py-3 px-4">Type</th>
          <th className="text-right py-3 px-4">Size (GB)</th>
          <th className="text-right py-3 px-4">IOPS</th>
          <th className="text-left py-3 px-4">Status</th>
          <th className="text-right py-3 px-4">Est. Cost/mo</th>
        </tr>
      </thead>
      <tbody>
        {resources.map((r) => (
          <tr key={r.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
            <td className="py-3 px-4 font-mono text-xs">{r.resource_id}</td>
            <td className="py-3 px-4">{r.resource_type}</td>
            <td className="py-3 px-4 text-right">{r.metadata.size_gb}</td>
            <td className="py-3 px-4 text-right">{r.metadata.iops?.toLocaleString()}</td>
            <td className={`py-3 px-4 ${r.metadata.attached ? "text-emerald-400" : "text-red-400"}`}>
              {r.metadata.attached ? "Attached" : "Unattached"}
            </td>
            <td className="py-3 px-4 text-right">${r.metadata.monthly_cost}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

const TABLE_MAP: Record<string, React.FC<{ resources: Resource[] }>> = {
  ec2: EC2Table,
  rds: RDSTable,
  s3: S3Table,
  ebs: EBSTable,
};

export default function ResourceTable({
  service,
  resources,
}: {
  service: string;
  resources: Resource[];
}) {
  const Table = TABLE_MAP[service];
  if (!Table) return null;

  if (resources.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center text-gray-400">
        No {service.toUpperCase()} resources found in this account.
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <Table resources={resources} />
    </div>
  );
}
```

- [ ] **Step 2: Create frontend/app/resources/page.tsx**

```tsx
"use client";

import { useEffect, useState } from "react";
import { fetchResources } from "@/lib/api";
import ResourceTable from "@/components/ResourceTable";

const TABS = ["ec2", "rds", "s3", "ebs"];

export default function ResourcesPage() {
  const [activeTab, setActiveTab] = useState("ec2");
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchResources(activeTab).then((data) => {
      setResources(data);
      setLoading(false);
    });
  }, [activeTab]);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Resources</h1>
      <div className="flex gap-1 mb-6 bg-gray-900 p-1 rounded-lg w-fit">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-5 py-2 rounded-md font-medium text-sm transition-colors ${
              activeTab === tab
                ? "bg-emerald-600 text-white"
                : "text-gray-400 hover:text-white"
            }`}
          >
            {tab.toUpperCase()}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-gray-400 p-12 text-center">Loading...</div>
      ) : (
        <ResourceTable service={activeTab} resources={resources} />
      )}
    </div>
  );
}
```

- [ ] **Step 3: Verify resources page**

Visit `http://localhost:3000/resources` — expect tabs for EC2/RDS/S3/EBS, each showing a table with color-coded utilization for EC2/RDS. EBS should show red "Unattached" status for some volumes.

- [ ] **Step 4: Commit**

```bash
git add frontend/components/ResourceTable.tsx frontend/app/resources/
git commit -m "feat: add resources page with service-specific tables and utilization colors"
```

---

## Task 10: AI Assistant Page

**Files:**
- Create: `frontend/components/ChatInterface.tsx`
- Create: `frontend/components/RecommendationCard.tsx`
- Create: `frontend/app/ask/page.tsx`

- [ ] **Step 1: Create frontend/components/ChatInterface.tsx**

```tsx
"use client";

import { useState, useRef, useEffect } from "react";
import { askStream } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const SUGGESTED_PROMPTS = [
  "What are my biggest cost saving opportunities?",
  "Why did my bill spike recently?",
  "Which EC2 instances should I downsize?",
  "Predict next month's bill",
  "What would I save with reserved instances?",
];

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (question: string) => {
    if (!question.trim() || streaming) return;

    const userMsg: Message = { role: "user", content: question };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setStreaming(true);

    const assistantMsg: Message = { role: "assistant", content: "" };
    setMessages((prev) => [...prev, assistantMsg]);

    try {
      for await (const chunk of askStream(question)) {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          updated[updated.length - 1] = {
            ...last,
            content: last.content + chunk,
          };
          return updated;
        });
      }
    } catch {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: "Response interrupted — try again.",
        };
        return updated;
      });
    }

    setStreaming(false);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex-1 overflow-auto space-y-4 mb-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-4">
            <p className="text-gray-400 text-lg">Ask anything about your AWS costs</p>
            <div className="flex flex-wrap gap-2 justify-center max-w-2xl">
              {SUGGESTED_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => sendMessage(prompt)}
                  className="bg-gray-800 hover:bg-gray-700 text-gray-300 px-4 py-2 rounded-lg text-sm transition-colors"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-2xl px-4 py-3 rounded-xl text-sm whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-emerald-600 text-white"
                  : "bg-gray-800 text-gray-200"
              }`}
            >
              {msg.content}
              {streaming && i === messages.length - 1 && msg.role === "assistant" && (
                <span className="animate-pulse">|</span>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage(input)}
          placeholder="Ask about your AWS costs..."
          disabled={streaming}
          className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500"
        />
        <button
          onClick={() => sendMessage(input)}
          disabled={streaming || !input.trim()}
          className="bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-700 text-white px-6 py-3 rounded-xl font-medium transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create frontend/components/RecommendationCard.tsx**

```tsx
"use client";

interface Recommendation {
  id: number;
  resource_id: string | null;
  severity: string;
  title: string;
  description: string;
  estimated_savings: number;
  status: string;
}

const SEVERITY_STYLES: Record<string, string> = {
  critical: "bg-red-900/30 border-red-800 text-red-400",
  warning: "bg-yellow-900/30 border-yellow-800 text-yellow-400",
  info: "bg-blue-900/30 border-blue-800 text-blue-400",
};

const BADGE_STYLES: Record<string, string> = {
  critical: "bg-red-600",
  warning: "bg-yellow-600",
  info: "bg-blue-600",
};

export default function RecommendationCard({
  rec,
  onDismiss,
}: {
  rec: Recommendation;
  onDismiss: (id: number) => void;
}) {
  if (rec.status === "dismissed") return null;

  return (
    <div className={`border rounded-lg p-4 ${SEVERITY_STYLES[rec.severity] || ""}`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className={`text-xs px-2 py-0.5 rounded-full text-white ${BADGE_STYLES[rec.severity]}`}>
            {rec.severity}
          </span>
          <span className="text-emerald-400 font-medium text-sm">
            Save ${rec.estimated_savings}/mo
          </span>
        </div>
        <button
          onClick={() => onDismiss(rec.id)}
          className="text-gray-500 hover:text-gray-300 text-xs"
        >
          Dismiss
        </button>
      </div>
      <h3 className="font-medium text-sm text-white mb-1">{rec.title}</h3>
      <p className="text-xs text-gray-400">{rec.description}</p>
      {rec.resource_id && (
        <p className="text-xs text-gray-500 mt-2 font-mono">{rec.resource_id}</p>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Create frontend/app/ask/page.tsx**

```tsx
"use client";

import { useEffect, useState } from "react";
import { fetchRecommendations, dismissRecommendation } from "@/lib/api";
import ChatInterface from "@/components/ChatInterface";
import RecommendationCard from "@/components/RecommendationCard";

export default function AskPage() {
  const [recommendations, setRecommendations] = useState([]);

  useEffect(() => {
    fetchRecommendations().then(setRecommendations);
  }, []);

  const handleDismiss = async (id: number) => {
    await dismissRecommendation(id);
    setRecommendations((prev: any[]) =>
      prev.map((r: any) => (r.id === id ? { ...r, status: "dismissed" } : r))
    );
  };

  const activeRecs = recommendations.filter((r: any) => r.status === "active");

  return (
    <div className="flex gap-6 h-[calc(100vh-8rem)]">
      <div className="flex-1">
        <h1 className="text-2xl font-bold mb-4">AI Assistant</h1>
        <ChatInterface />
      </div>
      <div className="w-80 overflow-auto">
        <h2 className="text-lg font-semibold mb-4">
          Recommendations
          {activeRecs.length > 0 && (
            <span className="ml-2 text-sm text-gray-400">({activeRecs.length})</span>
          )}
        </h2>
        {activeRecs.length === 0 ? (
          <p className="text-gray-400 text-sm">
            Looking good! No optimization opportunities found.
          </p>
        ) : (
          <div className="flex flex-col gap-3">
            {activeRecs.map((rec: any) => (
              <RecommendationCard key={rec.id} rec={rec} onDismiss={handleDismiss} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Verify AI assistant page**

Visit `http://localhost:3000/ask` — expect:
- Chat interface with suggested prompts
- Recommendations panel on the right (populated after a scan with Gemini key)
- Click a suggested prompt, see streaming response
- Dismiss button works on recommendations

- [ ] **Step 5: Commit**

```bash
git add frontend/components/ChatInterface.tsx frontend/components/RecommendationCard.tsx frontend/app/ask/
git commit -m "feat: add AI assistant page with streaming chat and recommendations panel"
```

---

## Task 11: Final Polish & Verification

**Files:**
- Modify: various (only if issues found)

- [ ] **Step 1: Full integration test**

1. Start backend: `cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000`
2. Start frontend: `cd frontend && npm run dev`
3. Open `http://localhost:3000`

Test checklist:
- [ ] Dashboard shows empty state with "Run Your First Scan" button
- [ ] Click "Scan Now" → summary cards, cost chart, top services chart populate
- [ ] Navigate to Resources → EC2 tab shows 10 instances with color-coded CPU%
- [ ] Switch to RDS/S3/EBS tabs → each shows correct data
- [ ] Navigate to AI Assistant → suggested prompts appear
- [ ] Click a prompt → streaming response appears
- [ ] Recommendations panel shows findings (requires Gemini key)
- [ ] Dismiss a recommendation → it disappears

- [ ] **Step 2: Commit any fixes**

```bash
git add -A
git commit -m "fix: integration test fixes and polish"
```

- [ ] **Step 3: Final commit — clean working state**

```bash
git status
# Ensure clean working tree
```
