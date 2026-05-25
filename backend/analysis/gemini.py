import json
from google import genai
from google.genai import types
from backend.config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
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
    if not client:
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
    if not client:
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
