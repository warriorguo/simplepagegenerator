import json

from openai import AsyncOpenAI

from app.config import settings
from app.pipeline.prompts.intent_parser import INTENT_PARSER_SYSTEM
from app.schemas.pipeline import IntentResult


async def parse_intent(client: AsyncOpenAI, message: str, history: list[dict], memories_context: str = "") -> IntentResult:
    messages = [
        {"role": "system", "content": INTENT_PARSER_SYSTEM},
    ]
    if memories_context:
        messages.append({"role": "system", "content": memories_context})
    messages.extend([
        *history[-10:],  # Last 10 messages for context
        {"role": "user", "content": message},
    ])

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        temperature=0.1,
        **settings.max_tokens_param(500),
    )

    content = response.choices[0].message.content or "{}"
    # Strip markdown code fences if present
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

    try:
        data = json.loads(content)
        return IntentResult(**data)
    except (json.JSONDecodeError, ValueError):
        return IntentResult(
            intent_type="other",
            complexity="simple",
            affected_areas=[],
            summary=message,
        )
