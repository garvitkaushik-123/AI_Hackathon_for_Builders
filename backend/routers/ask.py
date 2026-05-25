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
