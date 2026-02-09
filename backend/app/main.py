from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import projects, versions, files, chat, build, preview, publish, memories, exploration

app = FastAPI(title="SimplePageGenerator", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(versions.router)
app.include_router(files.router)
app.include_router(chat.router)
app.include_router(build.router)
app.include_router(preview.router)
app.include_router(publish.router)
app.include_router(memories.router)
app.include_router(exploration.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
