import uuid
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.pipeline.intent_parser import parse_intent
from app.pipeline.planner import create_plan
from app.pipeline.builder import execute_build
from app.pipeline.fix_agent import fix_errors
from app.services.build_service import validate_build
from app.services.version_service import create_version
from app.services.chat_service import get_or_create_thread, add_message
from app.services.memory_service import get_relevant_memories_for_prompt, extract_memories_from_conversation, create_memory
from app.utils.sse import sse_stage_change, sse_build_status, sse_token, sse_error, sse_done

MAX_FIX_RETRIES = 3


def apply_file_ops(current_files: list[dict], file_ops: list[dict]) -> list[dict]:
    """Apply file operations to current files and return updated file list."""
    files_map = {f["file_path"]: f for f in current_files}

    for op in file_ops:
        if op["action"] == "write":
            ext = op["file_path"].rsplit(".", 1)[-1] if "." in op["file_path"] else ""
            mime_map = {"html": "text/html", "css": "text/css", "js": "application/javascript"}
            files_map[op["file_path"]] = {
                "file_path": op["file_path"],
                "content": op["content"],
                "file_type": mime_map.get(ext, "text/plain"),
            }
        elif op["action"] == "delete":
            files_map.pop(op["file_path"], None)

    return list(files_map.values())


async def run_pipeline(
    client: AsyncOpenAI,
    db: AsyncSession,
    project_id: uuid.UUID,
    message: str,
    history: list[dict],
    current_files: list[dict],
) -> AsyncGenerator[str, None]:
    """Run the 4-stage prompt pipeline. Yields SSE-formatted events."""

    # Retrieve relevant memories for this message
    memories_context = ""
    try:
        memories_context = await get_relevant_memories_for_prompt(db, client, project_id, message)
    except Exception:
        pass  # Graceful degradation — continue without memories

    # Stage 1: Intent Parsing
    yield sse_stage_change("intent_parser")
    try:
        intent = await parse_intent(client, message, history, memories_context)
    except Exception as e:
        yield sse_error(f"Intent parsing failed: {e}")
        yield sse_done()
        return

    yield sse_token(f"Intent: {intent.intent_type} ({intent.complexity}) - {intent.summary}")

    # If it's just a question, answer directly without building
    if intent.intent_type == "question":
        yield sse_stage_change("responding")
        try:
            from app.config import settings
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for a web app/game generator. Answer the user's question about their project."},
                    *history[-10:],
                    {"role": "user", "content": message},
                ],
                temperature=0.7,
                **settings.max_tokens_param(1000),
            )
            answer = response.choices[0].message.content or ""
            yield sse_token(answer)
            # Save assistant response
            thread = await get_or_create_thread(db, project_id)
            await add_message(db, thread.id, "assistant", answer)
        except Exception as e:
            yield sse_error(f"Failed to respond: {e}")
        yield sse_done()
        return

    # Stage 2: Planning
    yield sse_stage_change("planner")
    try:
        plan = await create_plan(client, intent.model_dump_json(), current_files, memories_context)
    except Exception as e:
        yield sse_error(f"Planning failed: {e}")
        yield sse_done()
        return

    if not plan.files:
        yield sse_token("No file changes needed.")
        yield sse_done()
        return

    plan_summary = ", ".join(f"{f.action} {f.file_path}" for f in plan.files)
    yield sse_token(f"Plan: {plan_summary}")

    # Stage 3: Building
    yield sse_stage_change("builder")
    file_ops = []
    try:
        async for event in execute_build(client, plan.model_dump_json(), current_files, memories_context):
            if isinstance(event, dict) and "__file_ops__" in event:
                file_ops = event["__file_ops__"]
            elif isinstance(event, str):
                yield event
    except Exception as e:
        yield sse_error(f"Build execution failed: {e}")
        yield sse_done()
        return

    if not file_ops:
        yield sse_token("No file changes were made.")
        yield sse_done()
        return

    # Apply file operations
    updated_files = apply_file_ops(current_files, file_ops)

    # Stage 4: Validate + Fix loop
    yield sse_stage_change("validation")
    for attempt in range(MAX_FIX_RETRIES + 1):
        build_result = validate_build(updated_files)

        if build_result.success:
            yield sse_build_status(True)
            break
        else:
            yield sse_build_status(False, build_result.errors)

            if attempt < MAX_FIX_RETRIES:
                yield sse_stage_change("fix_agent")
                try:
                    async for event in fix_errors(client, build_result.errors, updated_files, memories_context):
                        if isinstance(event, dict) and "__file_ops__" in event:
                            fix_ops = event["__file_ops__"]
                            updated_files = apply_file_ops(updated_files, fix_ops)
                        elif isinstance(event, str):
                            yield event
                except Exception as e:
                    yield sse_error(f"Fix attempt failed: {e}")
                    break
                yield sse_stage_change("validation")

    # Save version with updated files
    try:
        thread = await get_or_create_thread(db, project_id)
        assistant_msg = await add_message(db, thread.id, "assistant", f"Built: {plan_summary}")
        version = await create_version(
            db,
            project_id,
            updated_files,
            source_message_id=assistant_msg.id,
            build_status="success" if build_result.success else "failed",
            build_log="\n".join(build_result.errors) if build_result.errors else None,
        )
        yield sse_done(version.id)

        # Auto-extract memories after successful build
        if build_result.success:
            try:
                facts = await extract_memories_from_conversation(client, message, history, updated_files)
                for fact in facts:
                    await create_memory(db, client, project_id, fact, source="auto")
            except Exception:
                pass  # Graceful degradation
    except Exception as e:
        yield sse_error(f"Failed to save version: {e}")
        yield sse_done()
