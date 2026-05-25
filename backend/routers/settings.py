from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError

from database.db import get_db
from aws_credentials import get_aws_credentials


router = APIRouter(prefix="/api/settings")


class AWSCredentialsInput(BaseModel):
    access_key_id: str
    secret_access_key: str
    region: str = "us-east-1"


class AWSStatus(BaseModel):
    connected: bool
    source: str | None = None  # "env" | "ui" | None
    region: str | None = None
    account_id: str | None = None
    iam_user: str | None = None


def _validate_credentials(access_key_id: str, secret_access_key: str, region: str) -> dict:
    """Validate AWS credentials using STS GetCallerIdentity (read-only, always allowed)."""
    try:
        session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region,
        )
        sts = session.client("sts")
        identity = sts.get_caller_identity()
        return {
            "valid": True,
            "account_id": identity["Account"],
            "arn": identity["Arn"],
            "user_id": identity["UserId"],
        }
    except ClientError as e:
        return {"valid": False, "error": str(e)}
    except Exception as e:
        return {"valid": False, "error": str(e)}


@router.get("/aws", response_model=AWSStatus)
async def get_aws_status():
    """Get current AWS connection status."""
    # Check DB settings first
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT key, value FROM settings WHERE key IN ('aws_access_key_id', 'aws_secret_access_key', 'aws_region', 'aws_account_id', 'aws_iam_user')"
        )
        rows = await cursor.fetchall()
        db_settings = {r[0]: r[1] for r in rows}
    finally:
        await db.close()

    if db_settings.get("aws_access_key_id") and db_settings.get("aws_secret_access_key"):
        return AWSStatus(
            connected=True,
            source="ui",
            region=db_settings.get("aws_region", "us-east-1"),
            account_id=db_settings.get("aws_account_id"),
            iam_user=db_settings.get("aws_iam_user"),
        )

    # Check env vars
    from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        return AWSStatus(
            connected=True,
            source="env",
            region=AWS_DEFAULT_REGION,
        )

    return AWSStatus(connected=False)


@router.post("/aws")
async def connect_aws(creds: AWSCredentialsInput):
    """Validate and store AWS credentials."""
    # Validate credentials with STS
    result = _validate_credentials(creds.access_key_id, creds.secret_access_key, creds.region)

    if not result["valid"]:
        raise HTTPException(status_code=400, detail=f"Invalid credentials: {result['error']}")

    # Extract IAM user name from ARN
    arn = result.get("arn", "")
    iam_user = arn.split("/")[-1] if "/" in arn else arn

    # Store in DB
    db = await get_db()
    try:
        settings = {
            "aws_access_key_id": creds.access_key_id,
            "aws_secret_access_key": creds.secret_access_key,
            "aws_region": creds.region,
            "aws_account_id": result["account_id"],
            "aws_iam_user": iam_user,
            "use_mock_data": "false",
        }
        for key, value in settings.items():
            await db.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )
        await db.commit()
    finally:
        await db.close()

    return {
        "status": "connected",
        "account_id": result["account_id"],
        "iam_user": iam_user,
        "region": creds.region,
    }


@router.post("/disconnect")
async def disconnect_aws():
    """Remove stored AWS credentials and switch to mock mode."""
    db = await get_db()
    try:
        await db.execute(
            "DELETE FROM settings WHERE key IN ('aws_access_key_id', 'aws_secret_access_key', 'aws_region', 'aws_account_id', 'aws_iam_user')"
        )
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            ("use_mock_data", "true"),
        )
        await db.commit()
    finally:
        await db.close()

    return {"status": "disconnected"}
