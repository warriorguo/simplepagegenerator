import uuid

from fastapi import APIRouter, Depends, HTTPException
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_openai_client
from app.schemas.memory import MemoryCreate, MemoryUpdate, MemorySearch, MemoryResponse
from app.services import memory_service

router = APIRouter(prefix="/api/v1/projects/{project_id}/memories", tags=["memories"])


@router.get("", response_model=list[MemoryResponse])
async def list_memories(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await memory_service.list_memories(db, project_id)


@router.post("", response_model=MemoryResponse)
async def create_memory(
    project_id: uuid.UUID,
    data: MemoryCreate,
    db: AsyncSession = Depends(get_db),
    client: AsyncOpenAI = Depends(get_openai_client),
):
    return await memory_service.create_memory(db, client, project_id, data.content, source="manual")


@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    project_id: uuid.UUID,
    memory_id: int,
    data: MemoryUpdate,
    db: AsyncSession = Depends(get_db),
    client: AsyncOpenAI = Depends(get_openai_client),
):
    memory = await memory_service.update_memory(db, client, memory_id, project_id, data.content)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@router.delete("/{memory_id}", status_code=204)
async def delete_memory(
    project_id: uuid.UUID,
    memory_id: int,
    db: AsyncSession = Depends(get_db),
):
    deleted = await memory_service.delete_memory(db, memory_id, project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")


@router.post("/search", response_model=list[MemoryResponse])
async def search_memories(
    project_id: uuid.UUID,
    data: MemorySearch,
    db: AsyncSession = Depends(get_db),
    client: AsyncOpenAI = Depends(get_openai_client),
):
    return await memory_service.search_memories(db, client, project_id, data.query, data.limit)
