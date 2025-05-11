import os, json, asyncio, datetime as dt
from google import genai
from google.genai import types

# re-use the client exactly like paper_service
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL_ID = "gemini-2.0-flash-lite"

_PROMPT = """
You are an AI research assistant.  The user has uploaded {n} paper titles
and their tag lists.  Return structured JSON with:
1. “trend_gaps” – up-trending or under-represented toxpics.
2. “recommendations” – up to 3 next papers to explore (title + why).
3. “assistant_cards” – 3 short cards (title, body) for dashboard display.

Respond **only** with JSON matching the provided schema.
"""

_SCHEM = genai.types.Schema(
    type = genai.types.Type.OBJECT,
    required = ["trend_gaps",
                "recommendations",
                "assistant_cards"],
    properties = {
        "trend_gaps": genai.types.Schema(
            type = genai.types.Type.ARRAY,
            items = genai.types.Schema(type=genai.types.Type.STRING),
        ),
        "recommendations": genai.types.Schema(
            type = genai.types.Type.ARRAY,
            items = genai.types.Schema(
                type=genai.types.Type.OBJECT,
                required=["title", "reason"],
                properties={
                    "title": genai.types.Schema(type=genai.types.Type.STRING),
                    "reason": genai.types.Schema(type=genai.types.Type.STRING),
                },
            ),
        ),
        "assistant_cards": genai.types.Schema(
            type = genai.types.Type.ARRAY,
            items = genai.types.Schema(
                type=genai.types.Type.OBJECT,
                required=["title", "body"],
                properties={
                    "title": genai.types.Schema(type=genai.types.Type.STRING),
                    "body": genai.types.Schema(type=genai.types.Type.STRING),
                },
            ),
        ),
    },
)

async def get_ai_analysis(papers: list[dict]) -> dict:
    """Call Gemini once, return structured JSON."""
    if not papers:
        return {"trend_gaps": [], "recommendations": [], "assistant_cards": []}

    titles = [p["title"] for p in papers]
    tags   = [p["metadata"].get("tags", []) for p in papers]

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=_PROMPT.format(n=len(papers))
                ),
                types.Part.from_text(
                    text=json.dumps({"titles": titles, "tags": tags})
                ),
            ],
        )
    ]

    cfg = types.GenerateContentConfig(
        temperature=0.8,
        max_output_tokens=4096,
        response_mime_type="application/json",
        response_schema=_SCHEM,
    )

    resp = await asyncio.to_thread(
        client.models.generate_content,
        model=MODEL_ID,
        contents=contents,
        config=cfg,
    )

    raw_json = resp.candidates[0].content.parts[0].text
    # safest: single attempt; fall back to {}
    try:
        return json.loads(raw_json)
    except Exception:
        return {"trend_gaps": [], "recommendations": [], "assistant_cards": []}
