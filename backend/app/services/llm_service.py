import json
from openai import AsyncOpenAI
from app.config import settings

if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY not in ("", "your_gemini_api_key_here"):
    client = AsyncOpenAI(
        api_key=settings.GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    llm_model = settings.GEMINI_MODEL
    print(f"[LLM] Using Google Gemini AI endpoint with model: {llm_model}")
else:
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    llm_model = settings.OPENAI_MODEL
    print(f"[LLM] Using OpenAI endpoint with model: {llm_model}")

ANALYSIS_PROMPT = """You are an expert sales call analyst for a real estate agency.

Analyze the following call transcript and determine the outcome of the lead qualification call.

Transcript:
{transcript}

Summary (if available):
{summary}

Based on the conversation, determine:
1. The outcome: one of [QUALIFIED, NOT_INTERESTED, FAILED]
   - QUALIFIED: The customer showed genuine interest in buying, selling, or renting a property
   - NOT_INTERESTED: The customer clearly expressed they are not interested
   - FAILED: The call failed to connect, was too short to determine, or the customer hung up immediately
2. Your confidence in this determination (0.0 to 1.0)
3. Your reasoning (2-3 sentences max)

IMPORTANT: If you are not confident (confidence < 0.7), set outcome to NEEDS_REVIEW so a human can review.

Respond ONLY with valid JSON in this exact format:
{{
  "outcome": "QUALIFIED|NOT_INTERESTED|FAILED|NEEDS_REVIEW",
  "confidence": 0.0-1.0,
  "reasoning": "Your brief reasoning here"
}}"""

async def analyze_call_transcript(transcript: str, summary: str = "") -> dict:
    prompt = ANALYSIS_PROMPT.format(
        transcript=transcript or "No transcript available.",
        summary=summary or "No summary available.",
    )

    try:
        response = await client.chat.completions.create(
            model=llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert call analyst. Always respond with valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        result = json.loads(raw)

        outcome = result.get("outcome", "NEEDS_REVIEW")
        confidence = float(result.get("confidence", 0.5))
        reasoning = result.get("reasoning", "")

        if confidence < 0.7 and outcome not in ("FAILED",):
            outcome = "NEEDS_REVIEW"

        return {
            "outcome": outcome,
            "confidence": confidence,
            "reasoning": reasoning,
        }

    except Exception as e:
        print(f"[LLM] Error analyzing transcript: {e}")
        return {
            "outcome": "NEEDS_REVIEW",
            "confidence": 0.0,
            "reasoning": f"LLM analysis failed: {str(e)}",
        }
