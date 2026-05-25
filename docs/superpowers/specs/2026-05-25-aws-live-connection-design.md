# AWS Live Connection — Design Spec

## Overview

Add the ability to connect the Cloud Cost Optimizer to a real AWS account with read-only access. Includes live boto3 collectors for EC2, RDS, S3, EBS, and Cost Explorer, a credential management system with UI and env var support, and user-facing IAM setup instructions.

## Decisions

- **Credential method:** IAM User with Access Keys (Approach A)
- **Credential input:** Both env vars and UI settings page, UI takes precedence
- **Credential storage:** SQLite `settings` table (acceptable for self-hosted tool)
- **Credential validation:** `sts:GetCallerIdentity` call on submission
- **Collector pattern:** Synchronous boto3 wrapped in `asyncio.to_thread()`, parallel execution
- **Failure handling:** Partial scans — failed collectors return empty list, scan continues

---

## IAM Policy

Users create a dedicated IAM user and attach this custom policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EC2ReadOnly",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "ec2:DescribeVolumeStatus"
      ],
      "Resource": "*"
    },
    {
      "Sid": "RDSReadOnly",
      "Effect": "Allow",
      "Action": [
        "rds:DescribeDBInstances"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3ReadOnly",
      "Effect": "Allow",
      "Action": [
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchReadOnly",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CostExplorerReadOnly",
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage"
      ],
      "Resource": "*"
    }
  ]
}
```

Minimal permissions — only the exact API calls the collectors use. No write access, no `s3:GetObject`, no wildcards.

---

## Live Collectors

### Shared Pattern

- Each collector is a standalone module returning the same data shape as `mock_data.py`
- Each has a single async function that wraps synchronous boto3 calls via `asyncio.to_thread()`
- Each accepts a boto3 session as parameter (created from user credentials)
- On failure, returns empty list — scanner logs the error and continues

### EC2 Collector (`collectors/ec2.py`)

- `ec2.describe_instances()` — all instances with type, state, launch time
- `cloudwatch.get_metric_statistics()` for `CPUUtilization` — 14-day average, 1-day period
- `cloudwatch.get_metric_statistics()` for `NetworkIn`, `NetworkOut` — 14-day sum
- Monthly cost estimated from instance type using hardcoded pricing lookup
- Returns: `[{service: "ec2", resource_id, resource_type, region, metadata, utilization}]`

### RDS Collector (`collectors/rds.py`)

- `rds.describe_db_instances()` — class, engine, multi-AZ, region
- CloudWatch `CPUUtilization` — 14-day average
- CloudWatch `DatabaseConnections` — 14-day average
- Monthly cost from instance class pricing lookup
- Returns: `[{service: "rds", ...}]`

### S3 Collector (`collectors/s3.py`)

- `s3.list_buckets()` — all bucket names
- `s3.get_bucket_location()` — region per bucket
- CloudWatch `BucketSizeBytes` (namespace `AWS/S3`, StorageType=`StandardStorage`) — latest value
- CloudWatch `NumberOfObjects` (StorageType=`AllStorageTypes`) — latest value
- Monthly cost estimated from size * $0.023/GB (Standard)
- Returns: `[{service: "s3", ...}]`

### EBS Collector (`collectors/ebs.py`)

- `ec2.describe_volumes()` — type, size, IOPS, state
- Attached status from `volume["Attachments"]` array (empty = unattached)
- Monthly cost from volume type pricing lookup
- Returns: `[{service: "ebs", ...}]`

### Cost Collector (`collectors/costs.py`)

- `ce.get_cost_and_usage()` — last 30 days, daily granularity, `GROUP_BY` service
- Maps AWS service names to short names:
  - "Amazon Elastic Compute Cloud - Compute" → "ec2"
  - "Amazon Relational Database Service" → "rds"
  - "Amazon Simple Storage Service" → "s3"
  - "Amazon Elastic Block Store" → "ebs"
  - Others grouped as "other"
- Returns: `[{service, date, amount, unit: "USD", granularity: "DAILY"}]`

### Scanner Integration

Update `scanner.py`:
- If credentials available and `use_mock_data=false`: create boto3 session from stored/env credentials, run all 5 live collectors in parallel via `asyncio.gather(asyncio.to_thread(...))`
- If any collector fails: log error, continue with remaining data, show warning in scan response
- If all collectors fail: return error to frontend

---

## Credential Management

### Settings Table

New SQLite table:

```sql
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

Keys: `aws_access_key_id`, `aws_secret_access_key`, `aws_region`, `use_mock_data`

### Credential Priority

1. UI-stored credentials (SQLite `settings` table) — highest
2. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`)
3. No credentials → mock mode

### Helper Function

`get_aws_credentials() -> dict | None` in a new `backend/aws_credentials.py`:
- Checks settings table first
- Falls back to env vars
- Returns `{access_key_id, secret_access_key, region}` or `None`

### API Endpoints

**GET /api/settings/aws**
- Returns: `{ connected: bool, region: str, account_id: str | null, use_mock_data: bool }`
- Never returns the secret key

**POST /api/settings/aws**
- Accepts: `{ access_key_id: str, secret_access_key: str, region: str }`
- Validates via `sts:GetCallerIdentity`
- On success: stores in DB, sets `use_mock_data=false`, returns `{ connected: true, account_id: str }`
- On failure: returns 400 with `{ error: "Invalid credentials" }`

**POST /api/settings/disconnect**
- Clears stored credentials from DB, sets `use_mock_data=true`
- Returns `{ connected: false }`

---

## Frontend Settings Page

### New Page: `/settings`

Added to sidebar navigation as "⚙️ Settings".

### Disconnected State

- Header: "Connect AWS Account"
- Collapsible IAM setup guide with:
  1. Step-by-step instructions (create IAM user, attach policy, generate keys)
  2. Copyable policy JSON block
- Form: Access Key ID input, Secret Access Key input, Region dropdown (default us-east-1)
- "Connect" button with loading state
- Error display for invalid credentials

### Connected State

- Green badge: "Connected to AWS Account XXXX-XXXX-XXXX"
- Region displayed
- "Disconnect" button (reverts to mock mode)
- "Run Scan with Live Data" link/button

### Error Handling

- Invalid credentials on connect → red error message below form
- Credentials revoked/expired during scan → dashboard shows "Credentials invalid — reconnect in Settings"

---

## Files Changed/Created

| File | Action | Purpose |
|------|--------|---------|
| `backend/collectors/ec2.py` | Create | Live EC2 + CloudWatch collector |
| `backend/collectors/rds.py` | Create | Live RDS + CloudWatch collector |
| `backend/collectors/s3.py` | Create | Live S3 + CloudWatch collector |
| `backend/collectors/ebs.py` | Create | Live EBS collector |
| `backend/collectors/costs.py` | Create | Live Cost Explorer collector |
| `backend/aws_credentials.py` | Create | Credential resolution (DB → env → none) |
| `backend/routers/settings.py` | Create | GET/POST /api/settings/aws, disconnect |
| `backend/collectors/scanner.py` | Modify | Wire live collectors when credentials present |
| `backend/database/db.py` | Modify | Add `settings` table to schema |
| `backend/main.py` | Modify | Register settings router |
| `frontend/src/app/settings/page.tsx` | Create | Settings page |
| `frontend/src/components/AWSSetupGuide.tsx` | Create | Collapsible IAM instructions |
| `frontend/src/app/layout.tsx` | Modify | Add Settings to sidebar nav |
| `frontend/src/lib/api.ts` | Modify | Add settings API functions |
