import json
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from app.config import settings
from app.pipeline.prompts.builder import BUILDER_SYSTEM, build_builder_prompt
from app.pipeline.tools import TOOL_DEFINITIONS
from app.utils.sse import sse_token, sse_tool_call


async def execute_build(
    client: AsyncOpenAI,
    plan_json: str,
    current_files: list[dict],
    memories_context: str = "",
) -> AsyncGenerator[str | dict, None]:
    """Execute the build plan. Yields SSE events and file operations as dicts."""
    prompt = build_builder_prompt(plan_json, current_files, memories_context)

    messages = [
        {"role": "system", "content": BUILDER_SYSTEM},
        {"role": "user", "content": prompt},
    ]

    # Track files modified during build
    file_ops: list[dict] = []

    while True:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            temperature=0.1,
            **settings.max_tokens_param(16000),
        )

        choice = response.choices[0]
        message = choice.message

        if message.content:
            yield sse_token(message.content)

        if not message.tool_calls:
            break

        # Process tool calls
        messages.append(message.model_dump())

        for tc in message.tool_calls:
            fn_name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            yield sse_tool_call(fn_name, {"file_path": args.get("file_path", "")})

            if fn_name == "write_file":
                file_ops.append({
                    "action": "write",
                    "file_path": args["file_path"],
                    "content": args["content"],
                })
                result = f"File written: {args['file_path']}"
            elif fn_name == "delete_file":
                file_ops.append({
                    "action": "delete",
                    "file_path": args["file_path"],
                })
                result = f"File deleted: {args['file_path']}"
            else:
                result = f"Unknown tool: {fn_name}"

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

        if choice.finish_reason == "stop":
            break

    # Yield file operations as a special dict (not SSE)
    yield {"__file_ops__": file_ops}
