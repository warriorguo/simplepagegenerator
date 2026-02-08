import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_thread import ChatThread
from app.models.chat_message import ChatMessage


async def get_or_create_thread(db: AsyncSession, project_id: uuid.UUID) -> ChatThread:
    result = await db.execute(
        select(ChatThread).where(ChatThread.project_id == project_id)
    )
    thread = result.scalar_one_or_none()
    if not thread:
        thread = ChatThread(project_id=project_id)
        db.add(thread)
        await db.flush()
    return thread


async def add_message(db: AsyncSession, thread_id: int, role: str, content: str) -> ChatMessage:
    msg = ChatMessage(thread_id=thread_id, role=role, content=content)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def get_messages(db: AsyncSession, project_id: uuid.UUID) -> list[ChatMessage]:
    result = await db.execute(
        select(ChatThread).where(ChatThread.project_id == project_id)
    )
    thread = result.scalar_one_or_none()
    if not thread:
        return []
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.thread_id == thread.id)
        .order_by(ChatMessage.created_at)
    )
    return list(result.scalars().all())


async def get_thread_messages_for_ai(db: AsyncSession, thread_id: int) -> list[dict]:
    """Get messages formatted for OpenAI API."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.thread_id == thread_id)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()
    return [
        {"role": msg.role if msg.role in ("user", "assistant", "system") else "assistant", "content": msg.content}
        for msg in messages
    ]
