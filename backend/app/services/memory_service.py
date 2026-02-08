import json
import uuid

from openai import AsyncOpenAI
from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.project_memory import ProjectMemory


async def generate_embedding(client: AsyncOpenAI, content: str) -> list[float]:
    """Generate embedding vector for text using OpenAI."""
    response = await client.embeddings.create(
        model=settings.openai_embedding_model,
        input=content[:8000],  # Truncate to avoid token limits
    )
    return response.data[0].embedding


async def create_memory(
    db: AsyncSession,
    client: AsyncOpenAI,
    project_id: uuid.UUID,
    content: str,
    source: str = "manual",
) -> ProjectMemory:
    embedding = await generate_embedding(client, content)
    memory = ProjectMemory(
        project_id=project_id,
        content=content,
        embedding=embedding,
        source=source,
    )
    db.add(memory)
    await db.commit()
    await db.refresh(memory)
    return memory


async def update_memory(
    db: AsyncSession,
    client: AsyncOpenAI,
    memory_id: int,
    project_id: uuid.UUID,
    content: str,
) -> ProjectMemory | None:
    result = await db.execute(
        select(ProjectMemory).where(
            ProjectMemory.id == memory_id,
            ProjectMemory.project_id == project_id,
        )
    )
    memory = result.scalar_one_or_none()
    if not memory:
        return None

    embedding = await generate_embedding(client, content)
    memory.content = content
    memory.embedding = embedding
    await db.commit()
    await db.refresh(memory)
    return memory


async def delete_memory(db: AsyncSession, memory_id: int, project_id: uuid.UUID) -> bool:
    result = await db.execute(
        delete(ProjectMemory).where(
            ProjectMemory.id == memory_id,
            ProjectMemory.project_id == project_id,
        )
    )
    await db.commit()
    return result.rowcount > 0


async def list_memories(db: AsyncSession, project_id: uuid.UUID) -> list[ProjectMemory]:
    result = await db.execute(
        select(ProjectMemory)
        .where(ProjectMemory.project_id == project_id)
        .order_by(ProjectMemory.created_at.desc())
    )
    return list(result.scalars().all())


async def search_memories(
    db: AsyncSession,
    client: AsyncOpenAI,
    project_id: uuid.UUID,
    query: str,
    limit: int = 10,
) -> list[ProjectMemory]:
    """Semantic search using pgvector cosine similarity."""
    query_embedding = await generate_embedding(client, query)
    # Use raw SQL for pgvector cosine distance operator
    result = await db.execute(
        text(
            "SELECT id, project_id, content, source, created_at, updated_at "
            "FROM project_memories "
            "WHERE project_id = :project_id AND embedding IS NOT NULL "
            "ORDER BY embedding <=> :embedding "
            "LIMIT :limit"
        ),
        {"project_id": project_id, "embedding": str(query_embedding), "limit": limit},
    )
    rows = result.fetchall()
    # Map back to ProjectMemory objects
    memories = []
    for row in rows:
        m = ProjectMemory(
            id=row.id,
            project_id=row.project_id,
            content=row.content,
            source=row.source,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        memories.append(m)
    return memories


async def get_relevant_memories_for_prompt(
    db: AsyncSession,
    client: AsyncOpenAI,
    project_id: uuid.UUID,
    query: str,
    max_chars: int | None = None,
) -> str:
    """Retrieve relevant memories formatted for prompt injection, budget-capped."""
    if max_chars is None:
        max_chars = settings.memory_max_injected_chars

    memories = await search_memories(db, client, project_id, query, limit=10)
    if not memories:
        return ""

    lines = []
    total_chars = 0
    for m in memories:
        line = f"- {m.content}"
        if total_chars + len(line) > max_chars:
            break
        lines.append(line)
        total_chars += len(line)

    if not lines:
        return ""

    return (
        "## Project Memory\n"
        "Relevant context from previous interactions:\n"
        + "\n".join(lines)
    )


MEMORY_EXTRACTION_PROMPT = """You are a memory extraction agent. Analyze the conversation and extract 0-5 memorable facts that would be useful for future interactions with this project.

Focus on:
- User preferences (colors, layout, themes, styles)
- Design decisions (canvas size, game mechanics, UI patterns)
- Technical constraints or requirements
- Project goals and purpose
- Specific configurations or settings the user wants

Do NOT extract:
- Generic facts about web development
- Things that are obvious from the code itself
- Temporary debugging information

Return a JSON array of strings. Each string should be a concise, standalone fact.
Return an empty array [] if there are no memorable facts worth extracting.

Example output: ["User prefers dark theme with neon colors", "Game uses 800x600 canvas", "Score should be displayed in top-right corner"]"""


async def extract_memories_from_conversation(
    client: AsyncOpenAI,
    message: str,
    history: list[dict],
    current_files: list[dict],
) -> list[str]:
    """Use AI to extract memorable facts from a conversation."""
    file_list = ", ".join(f["file_path"] for f in current_files)

    messages = [
        {"role": "system", "content": MEMORY_EXTRACTION_PROMPT},
        {"role": "user", "content": (
            f"Recent conversation (last 6 messages):\n"
            + "\n".join(
                f"{m['role']}: {m['content'][:500]}" for m in history[-6:]
            )
            + f"\n\nLatest user message: {message}"
            + f"\n\nProject files: {file_list}"
            + "\n\nExtract memorable facts as a JSON array of strings:"
        )},
    ]

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        temperature=0.1,
        max_tokens=500,
    )

    content = response.choices[0].message.content or "[]"
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

    try:
        facts = json.loads(content)
        if isinstance(facts, list):
            return [str(f) for f in facts[:5]]
    except json.JSONDecodeError:
        pass
    return []
