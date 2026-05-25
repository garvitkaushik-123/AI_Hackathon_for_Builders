# Cloud Cost Optimization Agent — Design Spec

## Overview

An AI-powered web application that monitors AWS infrastructure, detects unnecessary costs, and provides intelligent optimization recommendations using Google Gemini. Built for DevOps teams who want visibility into cloud waste without digging through the AWS console.

**Target:** Hackathon project (AI Hackathon for Builders)

## Decisions

- **Cloud provider:** AWS only (mock data by default, live data via read-only credentials when available)
- **AI engine:** Google Gemini API (Gemini 2.5 Flash via `google-genai` SDK)
- **Backend:** Python FastAPI + SQLite + boto3
- **Frontend:** Next.js + Tailwind CSS + Recharts
- **Architecture:** Monolithic — single FastAPI process serving the API, Next.js frontend built separately
- **AWS services analyzed:** EC2, RDS, S3, EBS
- **No auth** — hackathon scope, assumes local/trusted network

---

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Next.js Frontend                   │
│  ┌───────────┐ ┌───────────┐ ┌────────────────────┐ │
│  │ Dashboard  │ │ Resources │ │  AI Chat / Ask     │ │
│  │ (Charts)  │ │ (Tables)  │ │  (Streaming)       │ │
│  └─────┬─────┘ └─────┬─────┘ └────────┬───────────┘ │
└────────┼──────────────┼────────────────┼─────────────┘
         │              │                │
         ▼              ▼                ▼
┌─────────────────────────────────────────────────────┐
│                  FastAPI Backend                      │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ /api/costs   │  │ /api/resources│ │ /api/ask   │ │
│  │ /api/summary │  │ /api/scan    │  │ (streaming)│ │
│  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘ │
│         │                 │                 │        │
│  ┌──────▼─────────────────▼──┐  ┌──────────▼──────┐ │
│  │   AWS Data Collector      │  │ Gemini Analysis  │ │
│  │   (boto3)                 │  │ (google-genai)   │ │
│  └──────┬────────────────────┘  └─────────────────┘ │
│         │                                            │
│  ┌──────▼──────┐                                     │
│  │   SQLite    │                                     │
│  │   (cache)   │                                     │
│  └─────────────┘                                     │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   AWS Account   │
│  (Read-only)    │
│  - Cost Explorer│
│  - CloudWatch   │
│  - EC2, RDS,    │
│    S3, EBS APIs │
└─────────────────┘
```

---

## Data Layer

### Data Source Strategy

The app supports two modes controlled by `USE_MOCK_DATA` env var (defaults to `true`):

- **Mock mode (`USE_MOCK_DATA=true`):** A mock data generator produces realistic AWS-shaped data. Default for development and demo.
- **Live mode (`USE_MOCK_DATA=false`):** Real boto3 calls to AWS APIs. Requires valid AWS credentials.

Both modes produce the same data shapes and feed into the same SQLite storage and Gemini analysis pipeline. Swapping is just a config change.

### Mock Data Generator

Generates realistic data for a fictional mid-size startup AWS account:

**EC2 (8-12 instances):**
- Mix of instance types (t3.micro, t3.medium, m5.large, m5.xlarge, c5.2xlarge)
- 2-3 idle instances (<5% CPU for 14 days) — clear optimization targets
- 1-2 oversized instances (large type, <15% CPU) — downsize candidates
- Rest healthy (40-70% CPU)
- Realistic launch dates, regions (us-east-1, us-west-2)

**RDS (3-4 instances):**
- Mix of db.t3.medium, db.r5.large, db.m5.xlarge
- 1 idle database (0 connections for 7+ days)
- 1 oversized (db.r5.large with <10% CPU)
- Engines: PostgreSQL, MySQL

**S3 (5-6 buckets):**
- Mix of sizes (100MB to 500GB)
- 1-2 buckets with all data in Standard that should be in Infrequent Access
- 1 bucket with no lifecycle policy and large size

**EBS (10-15 volumes):**
- 3-4 unattached volumes (clear waste)
- 1-2 oversized volumes (500GB provisioned, <10% used)
- Mix of gp3, gp2, io1 types

**Cost data (30 days):**
- Daily costs between $150-$250/day with realistic variance
- A noticeable spike (~$400) on one day (triggers "why did my bill spike?" scenario)
- Service breakdown: EC2 ~60%, RDS ~20%, S3 ~10%, EBS ~10%
- Month-over-month: current month trending 15% higher than previous

### Live Collectors (when USE_MOCK_DATA=false)

| Collector | AWS APIs Used | Data Captured |
|-----------|--------------|---------------|
| **EC2** | `describe_instances`, CloudWatch `CPUUtilization`, `NetworkIn/Out` | Instance type, state, launch time, avg CPU over 14 days, network activity |
| **RDS** | `describe_db_instances`, CloudWatch `CPUUtilization`, `DatabaseConnections` | Instance class, engine, multi-AZ, avg CPU, connection count over 14 days |
| **S3** | `list_buckets`, CloudWatch `BucketSizeBytes`, `NumberOfObjects` | Bucket size, object count, storage class distribution |
| **EBS** | `describe_volumes`, `describe_volume_status` | Volume type, size, IOPS, attached/unattached state, snapshot count |

Cost data via AWS Cost Explorer API: `get_cost_and_usage` for the last 30 days, daily granularity, grouped by service.

### Scan Flow

1. User clicks "Scan" (or first visit triggers it)
2. Mock generator or live collectors produce data (live mode uses `asyncio.gather` for parallel collection)
3. Results stored in SQLite with a timestamp
4. Subsequent page loads use cached data until the user rescans

---

## Gemini-Powered Analysis

### Three Modes

**1. Automated Recommendations (on scan)**

After each scan, the backend sends a structured summary of all resource/cost data to Gemini with a system prompt instructing it to identify idle/underutilized resources, oversized instances, cost anomalies, and optimization opportunities. Each finding includes severity (critical/warning/info), estimated monthly savings, and a specific actionable recommendation. Response requested as JSON.

**2. Interactive Q&A (chat)**

`/api/ask` accepts natural language questions. The backend injects current AWS data as context so Gemini answers grounded in real numbers. Streamed via SSE.

Example questions:
- "Why did my bill spike last Tuesday?"
- "Which EC2 instances should I downsize?"
- "What would I save by switching to reserved instances?"

**3. Cost Prediction**

User asks about future costs — Gemini analyzes the 30-day trend and resource trajectory to provide a natural-language forecast with reasoning.

### Integration Details

- Model: Gemini 2.5 Flash (fast, cost-effective)
- Streaming via `google-genai` SDK
- System prompt includes full resource/cost dataset as structured context
- Recommendations parsed as JSON server-side

---

## Database Schema (SQLite)

```sql
-- Scan metadata
scans (id, started_at, completed_at, status)

-- Raw resource data per scan
resources (id, scan_id, service, resource_id, resource_type,
           region, metadata_json, utilization_json, created_at)

-- Cost data per scan
costs (id, scan_id, service, date, amount, unit, granularity)

-- AI-generated recommendations per scan
recommendations (id, scan_id, resource_id, severity,
                 title, description, estimated_savings,
                 status, created_at)
```

- `metadata_json` and `utilization_json` are flexible JSON blobs per service type
- `recommendations.status` tracks dismissed/acknowledged state
- Each scan creates a fresh snapshot; old data kept for comparison
- SQLite file at `data/cloudopt.db`, gitignored
- Tables created on first run via startup script

---

## API Endpoints

```
GET  /api/dashboard/summary
     → Total monthly spend, top spending services, resource counts,
       total potential savings, last scan time

GET  /api/costs?days=30
     → Daily cost breakdown by service (for trend chart)

GET  /api/resources?service=ec2|rds|s3|ebs
     → List of resources with utilization data, filterable by service

POST /api/scan
     → Triggers new AWS data collection + Gemini analysis
     → Returns scan_id, streams progress via SSE

GET  /api/recommendations?severity=critical|warning|info
     → AI-generated optimization findings, filterable by severity

PATCH /api/recommendations/{id}
      → Dismiss or acknowledge a recommendation

POST /api/ask
     → Chat endpoint — accepts { "question": "..." }
     → Streams Gemini response via SSE

GET  /api/scans
     → History of past scans with summary stats
```

- All endpoints return JSON, prefixed with `/api/`
- SSE for streaming on `/api/scan` and `/api/ask`
- CORS enabled for Next.js dev server (localhost:3000 → localhost:8000)

---

## Frontend

### Pages

**1. Dashboard (`/`)**
- Summary cards: total monthly spend, month-over-month change, total potential savings, resources scanned
- Cost trend chart: 30-day stacked area chart of daily spend by service (Recharts)
- Top spending services: horizontal bar chart
- "Scan Now" button with progress indicator

**2. Resources (`/resources`)**
- Tab bar: EC2 | RDS | S3 | EBS
- Resource table per tab with service-specific columns:
  - EC2: Instance ID, Type, State, Avg CPU%, Network, Region, Monthly Est. Cost
  - RDS: DB ID, Class, Engine, Avg CPU%, Connections, Multi-AZ
  - S3: Bucket Name, Size, Objects, Storage Class
  - EBS: Volume ID, Type, Size, IOPS, Attached/Unattached
- Color-coded utilization: red (<5%), yellow (<20%), green (healthy)
- Click row to see Gemini's analysis of that resource

**3. AI Assistant (`/ask`)**
- Chat interface with streaming responses
- Suggested prompts sidebar
- Recommendations panel with severity badges and estimated savings
- Dismiss/acknowledge buttons per recommendation

### Shared Layout
- Sidebar navigation
- Dark theme
- Tailwind CSS

---

## Error Handling

**AWS API failures:**
- Partial scan on collector failure — warning banner shows which services couldn't be scanned
- Missing billing access — resource data displays without cost figures, prompt to enable billing

**Gemini API:**
- Unreachable/rate-limited — "Retry Analysis" button, resource/cost data still displays
- Streaming error — "Response interrupted — try again" in chat

**Empty states:**
- No scans → welcome screen with "Run Your First Scan"
- No recommendations → "Looking good! No optimization opportunities found."
- No resources for a tab → "No {service} resources found in this account."

**Data freshness:**
- "Last scanned: X minutes ago" timestamp on dashboard
- No automatic re-scanning — always user-initiated

---

## Configuration

- `USE_MOCK_DATA=true` (default) — use synthetic data; set to `false` for live AWS
- AWS credentials via env vars (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`) or default credential chain — only needed when `USE_MOCK_DATA=false`
- Gemini API key via `GEMINI_API_KEY` env var
- All config via `.env` file (gitignored), with `.env.example` committed

---

## Project Structure

```
./ (repo root)
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── collectors/
│   │   ├── mock_data.py     # Realistic synthetic data generator
│   │   ├── ec2.py           # Live AWS collector
│   │   ├── rds.py
│   │   ├── s3.py
│   │   └── ebs.py
│   ├── analysis/
│   │   └── gemini.py        # Gemini integration
│   ├── database/
│   │   └── db.py            # SQLite setup and queries
│   ├── routers/
│   │   ├── dashboard.py
│   │   ├── resources.py
│   │   ├── scan.py
│   │   ├── recommendations.py
│   │   └── ask.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx         # Dashboard
│   │   │   ├── resources/
│   │   │   │   └── page.tsx
│   │   │   └── ask/
│   │   │       └── page.tsx
│   │   ├── components/
│   │   │   ├── Layout.tsx
│   │   │   ├── CostChart.tsx
│   │   │   ├── ResourceTable.tsx
│   │   │   ├── RecommendationCard.tsx
│   │   │   ├── ChatInterface.tsx
│   │   │   └── SummaryCards.tsx
│   │   └── lib/
│   │       └── api.ts           # API client
│   ├── package.json
│   └── tailwind.config.ts
├── data/                        # SQLite DB (gitignored)
├── .env.example
├── .gitignore
└── README.md
```
