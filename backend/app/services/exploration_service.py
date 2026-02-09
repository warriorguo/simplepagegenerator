import json
import uuid
from typing import Any

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.exploration import (
    ExplorationSession, ExplorationOption, ExplorationMemoryNote, UserPreference
)
from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.models.project_file import ProjectFile


# ─── Prompts ────────────────────────────────────────────────

AMBIGUITY_DECOMPOSE_PROMPT = """You are a game design ambiguity analyzer. Given a user's vague game idea description, decompose it into structured ambiguity dimensions.

Output a JSON object with these keys:
{
  "gameplay_type": {"candidates": ["platformer","shooter","puzzle","runner","clicker","tower_defense","other"], "detected": ["..."]},
  "control_method": {"candidates": ["keyboard","touch_tap","touch_swipe","mouse_click","auto"], "detected": ["..."]},
  "pace": {"candidates": ["fast","medium","slow","idle"], "detected": ["..."]},
  "goal_structure": {"candidates": ["high_score","level_clear","endless","economy","survival"], "detected": ["..."]},
  "difficulty": {"candidates": ["easy","medium","hard","progressive"], "detected": ["..."]},
  "visual_complexity": {"candidates": ["minimal","moderate","rich"], "detected": ["..."]},
  "platform": {"candidates": ["mobile","desktop","both"], "detected": ["..."]}
}

For each dimension, "detected" should list the most likely values based on the input.
If ambiguous, list multiple candidates in "detected".
Always return valid JSON only, no markdown."""


OPTION_GENERATE_PROMPT = """You are a Phaser game option generator. Based on the ambiguity analysis and available templates, generate 3-6 differentiated game options.

Available template IDs: {template_ids}

Memory context (user preferences from past explorations):
{memory_context}

Ambiguity analysis:
{ambiguity_json}

User input: "{user_input}"

Generate options as a JSON array. Each option must be:
{{
  "option_id": "opt_<number>",
  "title": "...",
  "core_loop": "...",
  "controls": "...",
  "mechanics": ["..."],
  "engine": "Phaser",
  "template_id": "<one of the available template IDs>",
  "complexity": "low|medium|high",
  "mobile_fit": "good|fair|poor",
  "assumptions_to_validate": ["..."],
  "is_recommended": true/false
}}

Rules:
- Options must differ significantly (different gameplay or input method)
- Not just parameter tweaks
- Exactly one should be marked is_recommended=true
- If memory shows preferences, bias recommendations toward them
- 3-6 options total
- Return valid JSON array only, no markdown."""


MEMORY_WRITER_PROMPT = """You are a structured memory writer for game exploration sessions.

Given the exploration session data, write a structured conclusion.

Session data:
- User input: "{user_input}"
- Selected option: {selected_option}
- Iteration count: {iteration_count}
- Hypothesis ledger: {hypothesis_ledger}
- Ambiguity analysis: {ambiguity_json}

Generate a JSON object:
{{
  "title": "...",
  "summary": "2-3 sentence summary of what was explored and concluded",
  "user_preferences": {{
    "platform": "mobile|desktop|both",
    "input": "tap|keyboard|swipe|click",
    "pace": "fast|medium|slow|idle",
    "session_length": "short|medium|long",
    "difficulty": "easy|medium|hard",
    "visual_density": "minimal|moderate|rich"
  }},
  "final_choice": {{
    "option_id": "...",
    "why": "reason the user chose this direction"
  }},
  "validated_hypotheses": ["things confirmed to work"],
  "rejected_hypotheses": ["things that didn't work or user rejected"],
  "key_decisions": [
    {{"decision": "...", "reason": "...", "evidence": "..."}}
  ],
  "pitfalls_and_guards": ["warnings for future explorations"],
  "confidence": 0.0-1.0
}}

Return valid JSON only, no markdown."""


ITERATE_PROMPT = """You are a Phaser game code modifier. Given the current game code and user's modification request, generate the updated complete file content.

Current files:
{current_files}

User request: "{user_input}"

Rules:
- Minimal changes only
- Keep Phaser structure consistent
- Maintain the game's core loop
- Only modify what the user asked for
- Return a JSON object mapping file_path to new content:
{{"index.html": "<!DOCTYPE html>..."}}

Return valid JSON only, no markdown."""


# ─── Helpers ────────────────────────────────────────────────

async def _call_openai_json(client: AsyncOpenAI, system: str, user: str) -> Any:
    """Call OpenAI and parse JSON response."""
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.7,
        max_tokens=4000,
    )
    content = response.choices[0].message.content or "{}"
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
    return json.loads(content)


# ─── Memory Retrieval ───────────────────────────────────────

async def get_memory_context(
    db: AsyncSession, project_id: uuid.UUID
) -> dict:
    """Retrieve relevant memory notes and user preferences for option biasing."""
    result = await db.execute(
        select(ExplorationMemoryNote)
        .where(ExplorationMemoryNote.project_id == project_id)
        .order_by(ExplorationMemoryNote.created_at.desc())
        .limit(5)
    )
    notes = list(result.scalars().all())

    result = await db.execute(
        select(UserPreference)
        .where(UserPreference.project_id == project_id)
        .order_by(UserPreference.updated_at.desc())
        .limit(1)
    )
    pref = result.scalar_one_or_none()

    context = {
        "relevant_preferences": pref.preference_json if pref else {},
        "recurring_patterns": [],
        "warnings": [],
        "suggested_direction_bias": None,
    }

    for note in notes:
        cj = note.content_json
        if isinstance(cj, dict):
            if cj.get("validated_hypotheses"):
                context["recurring_patterns"].extend(cj["validated_hypotheses"][:3])
            if cj.get("pitfalls_and_guards"):
                context["warnings"].extend(cj["pitfalls_and_guards"][:3])
            if cj.get("user_preferences"):
                context["suggested_direction_bias"] = cj["user_preferences"]

    return context


# ─── Ambiguity Decomposer ──────────────────────────────────

async def decompose_ambiguity(
    client: AsyncOpenAI, user_input: str
) -> dict:
    """Decompose user input into ambiguity dimensions."""
    return await _call_openai_json(
        client, AMBIGUITY_DECOMPOSE_PROMPT, user_input
    )


# ─── Option Generator ──────────────────────────────────────

async def generate_options(
    client: AsyncOpenAI,
    user_input: str,
    ambiguity_json: dict,
    memory_context: dict,
    template_ids: list[str],
) -> list[dict]:
    """Generate 3-6 differentiated Phaser game options."""
    prompt = OPTION_GENERATE_PROMPT.format(
        template_ids=json.dumps(template_ids),
        memory_context=json.dumps(memory_context, indent=2),
        ambiguity_json=json.dumps(ambiguity_json, indent=2),
        user_input=user_input,
    )
    result = await _call_openai_json(client, prompt, user_input)
    if isinstance(result, list):
        return result
    return []


# ─── Explore ───────────────────────────────────────────────

async def explore(
    db: AsyncSession,
    client: AsyncOpenAI,
    project_id: uuid.UUID,
    user_input: str,
    template_ids: list[str],
) -> dict:
    """Full explore flow: decompose -> memory -> generate options -> persist."""
    ambiguity = await decompose_ambiguity(client, user_input)
    memory_ctx = await get_memory_context(db, project_id)
    options = await generate_options(
        client, user_input, ambiguity, memory_ctx, template_ids
    )

    session = ExplorationSession(
        project_id=project_id,
        user_input=user_input,
        ambiguity_json=ambiguity,
        state="explore_options",
    )
    db.add(session)
    await db.flush()

    option_responses = []
    for opt in options:
        db_opt = ExplorationOption(
            session_id=session.id,
            option_id=opt.get("option_id", f"opt_{len(option_responses)+1}"),
            title=opt.get("title", "Untitled"),
            core_loop=opt.get("core_loop", ""),
            controls=opt.get("controls", ""),
            mechanics=opt.get("mechanics", []),
            template_id=opt.get("template_id", ""),
            complexity=opt.get("complexity", "medium"),
            mobile_fit=opt.get("mobile_fit", "good"),
            assumptions_to_validate=opt.get("assumptions_to_validate", []),
            is_recommended=opt.get("is_recommended", False),
        )
        db.add(db_opt)
        option_responses.append(opt)

    await db.commit()
    await db.refresh(session)

    return {
        "session_id": session.id,
        "ambiguity": ambiguity,
        "options": option_responses,
        "memory_influence": memory_ctx if memory_ctx["relevant_preferences"] else None,
    }


# ─── Select Option ─────────────────────────────────────────

async def select_option(
    db: AsyncSession,
    project_id: uuid.UUID,
    session_id: int,
    option_id: str,
    template_files: list[dict],
) -> dict:
    """Select an option: import template files, create version, transition state."""
    result = await db.execute(
        select(ExplorationSession).where(ExplorationSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise ValueError("Session not found")

    version = ProjectVersion(
        project_id=project_id,
        build_status="success",
    )
    db.add(version)
    await db.flush()

    for f in template_files:
        pf = ProjectFile(
            version_id=version.id,
            file_path=f["file_path"],
            content=f["content"],
            file_type=f.get("file_type", "text/html"),
        )
        db.add(pf)

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project:
        project.current_version_id = version.id
        project.status = "running"

    session.selected_option_id = option_id
    session.state = "committed"
    session.hypothesis_ledger = {
        "validated": [],
        "rejected": [],
        "open_questions": [],
    }

    await db.commit()

    return {
        "session_id": session.id,
        "option_id": option_id,
        "version_id": version.id,
        "state": session.state,
    }


# ─── Iterate ───────────────────────────────────────────────

async def iterate(
    db: AsyncSession,
    client: AsyncOpenAI,
    project_id: uuid.UUID,
    session_id: int,
    user_input: str,
) -> dict:
    """Iterate on the current version: modify code, create new version."""
    result = await db.execute(
        select(ExplorationSession).where(ExplorationSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise ValueError("Session not found")

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project or not project.current_version_id:
        raise ValueError("No current version")

    result = await db.execute(
        select(ProjectFile).where(ProjectFile.version_id == project.current_version_id)
    )
    current_files = list(result.scalars().all())

    files_context = {}
    for f in current_files:
        files_context[f.file_path] = f.content

    prompt = ITERATE_PROMPT.format(
        current_files=json.dumps(
            {fp: content[:3000] for fp, content in files_context.items()},
            indent=2
        ),
        user_input=user_input,
    )
    modifications = await _call_openai_json(client, prompt, user_input)

    new_version = ProjectVersion(
        project_id=project_id,
        build_status="success",
    )
    db.add(new_version)
    await db.flush()

    for fp, content in files_context.items():
        new_content = modifications.get(fp, content)
        pf = ProjectFile(
            version_id=new_version.id,
            file_path=fp,
            content=new_content,
            file_type="text/html" if fp.endswith(".html") else "application/javascript",
        )
        db.add(pf)

    project.current_version_id = new_version.id

    session.iteration_count += 1
    session.state = "iterating"

    ledger = session.hypothesis_ledger or {"validated": [], "rejected": [], "open_questions": []}
    ledger["open_questions"].append(user_input)
    session.hypothesis_ledger = ledger

    await db.commit()

    return {
        "session_id": session.id,
        "version_id": new_version.id,
        "iteration_count": session.iteration_count,
        "hypothesis_ledger": session.hypothesis_ledger,
        "state": session.state,
    }


# ─── Finish Exploration ────────────────────────────────────

async def finish_exploration(
    db: AsyncSession,
    client: AsyncOpenAI,
    project_id: uuid.UUID,
    session_id: int,
) -> dict:
    """Finish exploration: write structured memory from session."""
    result = await db.execute(
        select(ExplorationSession).where(ExplorationSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise ValueError("Session not found")

    selected_option = None
    if session.selected_option_id:
        result = await db.execute(
            select(ExplorationOption).where(
                ExplorationOption.session_id == session.id,
                ExplorationOption.option_id == session.selected_option_id,
            )
        )
        opt = result.scalar_one_or_none()
        if opt:
            selected_option = {
                "option_id": opt.option_id,
                "title": opt.title,
                "core_loop": opt.core_loop,
                "template_id": opt.template_id,
            }

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    stable_version_id = project.current_version_id if project else None

    prompt = MEMORY_WRITER_PROMPT.format(
        user_input=session.user_input,
        selected_option=json.dumps(selected_option),
        iteration_count=session.iteration_count,
        hypothesis_ledger=json.dumps(session.hypothesis_ledger),
        ambiguity_json=json.dumps(session.ambiguity_json),
    )
    memory_content = await _call_openai_json(client, prompt, "Generate structured memory")

    memory_content["refs"] = {
        "exploration_session_id": session.id,
        "stable_version_id": stable_version_id,
    }

    note = ExplorationMemoryNote(
        project_id=project_id,
        content_json=memory_content,
        tags=_extract_tags(memory_content),
        confidence=memory_content.get("confidence", 0.8),
        source_version_id=stable_version_id,
        source_session_id=session.id,
    )
    db.add(note)

    if memory_content.get("user_preferences"):
        result = await db.execute(
            select(UserPreference).where(UserPreference.project_id == project_id)
        )
        pref = result.scalar_one_or_none()
        if pref:
            pref.preference_json = memory_content["user_preferences"]
        else:
            pref = UserPreference(
                project_id=project_id,
                preference_json=memory_content["user_preferences"],
            )
            db.add(pref)

    session.state = "stable"

    await db.commit()
    await db.refresh(note)

    return {
        "session_id": session.id,
        "memory_note": {
            "id": note.id,
            "project_id": str(note.project_id),
            "content_json": note.content_json,
            "tags": note.tags,
            "confidence": note.confidence,
            "source_session_id": note.source_session_id,
            "created_at": note.created_at.isoformat(),
        },
        "state": session.state,
    }


def _extract_tags(content: dict) -> list[str]:
    """Extract tags from memory content."""
    tags = []
    prefs = content.get("user_preferences", {})
    if prefs.get("platform"):
        tags.append(f"platform:{prefs['platform']}")
    if prefs.get("input"):
        tags.append(f"input:{prefs['input']}")
    if prefs.get("pace"):
        tags.append(f"pace:{prefs['pace']}")
    choice = content.get("final_choice", {})
    if choice.get("option_id"):
        tags.append(f"chosen:{choice['option_id']}")
    return tags


# ─── Query Helpers ──────────────────────────────────────────

async def get_session_state(
    db: AsyncSession, session_id: int
) -> dict | None:
    """Get current session state."""
    result = await db.execute(
        select(ExplorationSession).where(ExplorationSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        return None
    return {
        "session_id": session.id,
        "state": session.state,
        "selected_option_id": session.selected_option_id,
        "iteration_count": session.iteration_count,
        "hypothesis_ledger": session.hypothesis_ledger,
    }


async def list_memory_notes(
    db: AsyncSession, project_id: uuid.UUID
) -> list[ExplorationMemoryNote]:
    """List all exploration memory notes for a project."""
    result = await db.execute(
        select(ExplorationMemoryNote)
        .where(ExplorationMemoryNote.project_id == project_id)
        .order_by(ExplorationMemoryNote.created_at.desc())
    )
    return list(result.scalars().all())
