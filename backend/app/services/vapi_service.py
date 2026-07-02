import httpx
from app.config import settings

VAPI_BASE_URL = "https://api.vapi.ai"

async def create_outbound_call(
    customer_name: str,
    customer_phone: str,
    company_name: str,
    company_system_prompt: str,
    customer_id: str,
    company_id: str,
) -> dict:
    headers = {
        "Authorization": f"Bearer {settings.VAPI_API_KEY}",
        "Content-Type": "application/json",
    }

    dynamic_prompt = (
        f"{company_system_prompt}\n\n"
        f"You are calling {customer_name} on behalf of {company_name}. "
        f"Be friendly, professional, and concise. "
        f"Your goal is to qualify this lead by understanding their property needs. "
        f"Ask about whether they want to buy, sell, or rent, their budget, timeline, and preferred locations. "
        f"If they are interested, confirm their details and thank them warmly. "
        f"If they are not interested, thank them politely and end the call."
    )

    provider = "groq"
    model_name = "llama3-8b-8192"

    payload = {
        "phoneNumberId": settings.VAPI_PHONE_NUMBER_ID,
        "customer": {
            "number": customer_phone,
            "name": customer_name,
        },
        "assistant": {
            "firstMessage": (
                f"Hello {customer_name}! This is an AI assistant calling from {company_name}. "
                f"I hope I'm not catching you at a bad time. "
                f"I'm reaching out about an exciting opportunity. "
                f"Do you have a couple of minutes to chat?"
            ),
            "model": {
                "provider": provider,
                "model": model_name,
                "systemPrompt": dynamic_prompt,
            },
            "voice": {
                "provider": "deepgram",
                "voiceId": "asteria",
            },
            "serverUrl": settings.VAPI_WEBHOOK_URL,
            "endCallFunctionEnabled": True,
            "transcriber": {
                "provider": "deepgram",
                "model": "nova-2",
                "language": "en-US",
            },
        },
        "metadata": {
            "customer_id": customer_id,
            "company_id": company_id,
        },
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{VAPI_BASE_URL}/call",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()

async def get_call_details(call_id: str) -> dict:
    headers = {"Authorization": f"Bearer {settings.VAPI_API_KEY}"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{VAPI_BASE_URL}/call/{call_id}",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()
