import json

from openai import AsyncOpenAI

from app.config import settings
from app.pipeline.prompts.planner import PLANNER_SYSTEM, build_planner_prompt
from app.schemas.pipeline import PlanResult


async def create_plan(
    client: AsyncOpenAI,
    intent_json: str,
    current_files: list[dict],
    memories_context: str = "",
) -> PlanResult:
    prompt = build_planner_prompt(intent_json, current_files, memories_context)

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": PLANNER_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=1000,
    )

    content = response.choices[0].message.content or "{}"
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

    try:
        data = json.loads(content)
        return PlanResult(**data)
    except (json.JSONDecodeError, ValueError):
        return PlanResult(files=[], execution_order=[], notes="Failed to parse plan")
