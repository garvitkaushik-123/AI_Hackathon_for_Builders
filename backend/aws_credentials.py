from database.db import get_db
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION


async def get_aws_credentials() -> dict | None:
    """Resolve AWS credentials: DB settings > env vars > None."""
    # Check DB settings first (UI-provided)
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT key, value FROM settings WHERE key IN ('aws_access_key_id', 'aws_secret_access_key', 'aws_region')"
        )
        rows = await cursor.fetchall()
        db_settings = {r[0]: r[1] for r in rows}

        if db_settings.get("aws_access_key_id") and db_settings.get("aws_secret_access_key"):
            return {
                "access_key_id": db_settings["aws_access_key_id"],
                "secret_access_key": db_settings["aws_secret_access_key"],
                "region": db_settings.get("aws_region", "us-east-1"),
            }
    finally:
        await db.close()

    # Fall back to env vars
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        return {
            "access_key_id": AWS_ACCESS_KEY_ID,
            "secret_access_key": AWS_SECRET_ACCESS_KEY,
            "region": AWS_DEFAULT_REGION,
        }

    return None


async def is_mock_mode() -> bool:
    """Check if platform should use mock data."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT value FROM settings WHERE key = 'use_mock_data'"
        )
        row = await cursor.fetchone()
        if row:
            return row[0].lower() == "true"
    finally:
        await db.close()

    # Fall back to config
    from config import USE_MOCK_DATA
    return USE_MOCK_DATA
