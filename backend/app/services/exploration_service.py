import json
import time
import uuid
from collections import deque
from typing import Any

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

# ─── Debug Log ─────────────────────────────────────────────
# In-memory ring buffer of recent OpenAI calls (max 50)
_debug_log: deque[dict] = deque(maxlen=50)
from app.models.exploration import (
    ExplorationSession, ExplorationOption, ExplorationMemoryNote, UserPreference
)
from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.models.project_file import ProjectFile


# ─── Prompts ────────────────────────────────────────────────

# Stage A: Requirement Decomposer — user request → implementation dimensions
STAGE_A_DECOMPOSER_PROMPT = """You are an implementation-oriented requirement decomposer for Phaser web games.

Given the user's request, identify the design decisions where ambiguity exists.
Do NOT propose solutions yet.

Reference dimensions (use these as a guide, but ONLY include ones that are actually ambiguous):
- controls: keyboard, mouse_click, touch_tap, touch_drag, virtual_joystick, auto, single_key
- presentation: 2d_topdown, side_scroller, isometric, minimal_2d
- core_loop: move_dodge_shoot, jump_collect, match_clear, click_upgrade, build_defend, run_avoid
- goals: high_score, level_clear, endless_survival, economy_growth, time_attack
- progression: infinite, levels, missions, freeform
- systems: physics, collision, simple_ai, projectiles, grid, economy, spawner
- platform: mobile, desktop, both
- tone: exciting, relaxing, tense, cute, retro, minimal

Output JSON only:

{{
  "summary": "one-sentence restatement of what the user wants",
  "dimensions": {{
    "<dimension_name>": {{
      "candidates": ["option_a", "option_b"],
      "confidence": "high|med|low",
      "signals": ["quotes or inferences from user text"]
    }}
  }},
  "hard_constraints": ["things the user explicitly required or excluded"],
  "open_questions": [
    {{"dimension": "...", "question": "...", "why_it_matters": "..."}}
  ]
}}

Rules:
- ONLY include dimensions where real ambiguity exists (2+ plausible candidates).
  If the user's intent is clear for a dimension, do NOT include it — put it in hard_constraints instead.
- If the request is very specific, you may output just 1-2 dimensions. If it is very vague, output more.
  There is no minimum or maximum — let the actual ambiguity decide.
- Each included dimension must have 2-4 candidates. More candidates = more ambiguity.
- You may use the reference dimensions above, or create custom ones if needed (e.g. "enemy_behavior", "scoring_model").
- "signals" are direct quotes or logical inferences from user text.
- You have access to a search_memory tool that can retrieve past exploration memories, design decisions, and user preferences. Use it if you think prior context would help decompose the request.
- Return valid JSON only, no markdown."""


# Stage A (contextual): when a game already exists, decompose based on current state
STAGE_A_CONTEXTUAL_PROMPT = """You are an implementation-oriented requirement decomposer for Phaser web games.

The user already has an existing game. Given their new request and the current game code,
decompose the request into SPECIFIC implementation dimensions relevant to this change.

Do NOT use generic dimensions like "controls" or "platform" if they are already decided.
Instead, generate dimensions that capture the ACTUAL design decisions needed for this request.

Current game code:
{current_code}

Already-decided context:
{decided_context}

Output JSON only:

{{
  "summary": "one-sentence restatement of what the user wants to change/add",
  "locked": {{
    "description": "things already decided that should NOT change",
    "items": ["controls: touch_tap", "presentation: side_scroller", ...]
  }},
  "dimensions": {{
    "<specific_dimension_name>": {{
      "candidates": ["option_a", "option_b", "option_c"],
      "confidence": "high|med|low",
      "signals": ["quotes or inferences from user text"]
    }}
  }},
  "hard_constraints": ["things the user explicitly required or excluded"],
  "open_questions": [
    {{"dimension": "...", "question": "...", "why_it_matters": "..."}}
  ]
}}

Rules:
- ONLY include dimensions where real ambiguity exists (2+ plausible candidates).
  If something is obvious from context, do NOT create a dimension for it.
- If the request is very specific, you may output just 1 dimension. If it is vague, output more.
  There is no minimum or maximum — let the actual ambiguity decide.
- Each included dimension must have 2-4 candidates.
- Dimension names should be descriptive snake_case: e.g. "power_up_types", "boss_attack_pattern",
  "difficulty_curve", "spawn_frequency", "reward_structure", "animation_style".
- "locked" lists decisions already made in the existing game that should be preserved.
- Focus on implementation choices, not high-level design.
- You have access to a search_memory tool that can retrieve past exploration memories, design decisions, and user preferences. Use it if prior decisions or patterns would help decompose the request.
- Return valid JSON only, no markdown."""


# Stage B: Branch Synthesizer — dimensions → 3-6 divergent branches
STAGE_B_BRANCH_PROMPT = """You are a branch synthesizer for Phaser web game prototyping.

Given decomposed implementation dimensions, generate 3-6 divergent design branches.
Each branch is one internally-consistent set of choices across all dimensions.

Memory context (user preferences from past explorations):
{memory_context}

Dimensions JSON:
{dimensions_json}

{locked_context}

Output JSON only:
{{
  "branches": [
    {{
      "branch_id": "B1",
      "name": "short catchy name",
      "picked": {{
        "<dimension_name>": "chosen value or [list of values]"
      }},
      "why_this_branch": ["reasons this combination is interesting"],
      "risks": ["what might not work"],
      "what_to_validate": ["key assumptions to test"]
    }}
  ]
}}

Rules:
- "picked" must include a choice for EVERY dimension key in the dimensions JSON.
- Branches MUST differ on at least 2 dimensions.
- Keep scope MVP-friendly: each branch should be prototypable with Phaser primitives, no external assets.
- If user implies true 3D, propose isometric/pseudo-3D alternatives.
- If memory context shows user preferences, make one branch aligned with those preferences.
- If there is a "locked" section in the dimensions, respect those decisions — do NOT change locked items.
- You have access to a search_memory tool that can retrieve past exploration memories and strategy paths. Use it if you want to check what worked or failed before.
- 3-6 branches total.
- Return valid JSON only, no markdown."""


# Stage C: Demo Mapper — branches → option cards with template_id
STAGE_C_MAPPER_PROMPT = """You are a demo mapper for Phaser web game prototyping.

Map each design branch to one runnable demo template from the catalog.
Choose the closest template; note small tweaks needed after selection.

Available templates (template_id → description):
{template_catalog}

Branches JSON:
{branches_json}

Output JSON only:
{{
  "options": [
    {{
      "option_id": "opt_1",
      "branch_id": "B1",
      "title": "display name",
      "core_loop": "what the player does every 5-30 seconds",
      "controls": "input method description",
      "mechanics": ["mechanic_1", "mechanic_2"],
      "engine": "Phaser",
      "template_id": "one of the available template IDs",
      "complexity": "low|medium|high",
      "mobile_fit": "good|fair|poor",
      "assumptions_to_validate": ["key hypotheses"],
      "is_recommended": false
    }}
  ],
  "recommended_option_id": "opt_?"
}}

Rules:
- 3-6 options, one per branch.
- Exactly one recommended option (set is_recommended=true on it AND fill recommended_option_id).
- Options must be runnable immediately from the template with zero to minimal tweaks.
- Prefer low/medium complexity templates during exploration.
- Return valid JSON only, no markdown."""


# Stage D: Code Customizer — template + option spec → customized game code
STAGE_D_CUSTOMIZER_PROMPT = """You are a Phaser 3 game code customizer.

You will receive:
1. A base template (complete HTML+JS Phaser game)
2. A game design spec describing the target game

Your job: rewrite the template code so it becomes the described game.
Keep the same Phaser boilerplate structure (CDN import, config, scene lifecycle).
Change the gameplay, controls, mechanics, visuals, text, and behavior to match the spec.

Game design spec:
- Title: {title}
- Core loop: {core_loop}
- Controls: {controls}
- Mechanics: {mechanics}
- Complexity: {complexity}
- Mobile fit: {mobile_fit}

User's original request: "{user_input}"

Base template code:
{template_code}

Rules:
- Output a JSON object mapping file_path to full file content: {{"index.html": "<!DOCTYPE html>..."}}
- The game MUST be fully playable with zero external assets (use Phaser primitives: rectangles, circles, text, graphics).
- Keep the CDN import: https://cdn.jsdelivr.net/npm/phaser@3.60.0/dist/phaser.min.js
- Maintain mobile support (touch controls, Scale.FIT).
- Write complete, working code — do NOT leave placeholders or TODOs.
- Match the core_loop and controls description as closely as possible.
- Keep it simple but fun — this is a prototype.
- Return valid JSON only, no markdown."""


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

async def _call_openai_json(
    client: AsyncOpenAI, system: str, user: str, label: str = "", max_tokens: int = 4000
) -> Any:
    """Call OpenAI and parse JSON response. Logs to debug buffer."""
    t0 = time.time()
    entry: dict = {
        "label": label,
        "timestamp": t0,
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "raw_response": None,
        "parsed": None,
        "error": None,
        "duration_ms": 0,
    }
    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.7,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content or "{}"
        entry["raw_response"] = content
        entry["usage"] = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            "total_tokens": response.usage.total_tokens if response.usage else 0,
        }
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
        parsed = json.loads(content)
        entry["parsed"] = parsed
        return parsed
    except Exception as e:
        entry["error"] = str(e)
        raise
    finally:
        entry["duration_ms"] = round((time.time() - t0) * 1000)
        _debug_log.append(entry)


def get_debug_log() -> list[dict]:
    """Return all debug log entries."""
    return list(_debug_log)


def clear_debug_log() -> None:
    """Clear the debug log."""
    _debug_log.clear()


# ─── Memory Tool for OpenAI Function Calling ──────────────

MEMORY_TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "search_memory",
        "description": (
            "Search past exploration memories for relevant strategy paths, "
            "design decisions, user preferences, validated/rejected hypotheses, "
            "and lessons learned from previous game explorations."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "What to search for, e.g. 'runner game controls', "
                        "'power-up design patterns', 'mobile tap games', "
                        "'what was rejected before'"
                    ),
                },
                "filter_type": {
                    "type": "string",
                    "enum": ["all", "design_decision", "exploration_finish"],
                    "description": "Filter by memory type. 'all' returns everything.",
                },
            },
            "required": ["query"],
        },
    },
}


async def _search_memory_for_tool(
    db: AsyncSession, project_id: uuid.UUID, query: str, filter_type: str = "all"
) -> str:
    """Execute a memory search and return formatted results for the AI."""
    result = await db.execute(
        select(ExplorationMemoryNote)
        .where(ExplorationMemoryNote.project_id == project_id)
        .order_by(ExplorationMemoryNote.created_at.desc())
        .limit(20)
    )
    notes = list(result.scalars().all())

    # Also get user preferences
    result = await db.execute(
        select(UserPreference)
        .where(UserPreference.project_id == project_id)
        .order_by(UserPreference.updated_at.desc())
        .limit(1)
    )
    pref = result.scalar_one_or_none()

    query_lower = query.lower()
    matched = []
    for note in notes:
        cj = note.content_json
        if not isinstance(cj, dict):
            continue
        # Filter by type if specified
        if filter_type != "all" and cj.get("type") != filter_type:
            continue
        # Simple relevance: check if query terms appear in content
        note_text = json.dumps(cj).lower()
        if any(term in note_text for term in query_lower.split()):
            matched.append(cj)
        elif not query_lower.strip():
            matched.append(cj)

    # If no keyword match, return all (up to limit)
    if not matched:
        matched = [n.content_json for n in notes[:10] if isinstance(n.content_json, dict)]
        if filter_type != "all":
            matched = [m for m in matched if m.get("type") == filter_type]

    # Format results
    parts = []
    if pref:
        parts.append(f"User Preferences: {json.dumps(pref.preference_json)}")

    for i, m in enumerate(matched[:10]):
        entry = f"\n--- Memory #{i+1}: {m.get('title', 'Untitled')} ---"
        if m.get("summary"):
            entry += f"\nSummary: {m['summary']}"
        if m.get("type"):
            entry += f"\nType: {m['type']}"
        if m.get("selected_option"):
            entry += f"\nSelected: {json.dumps(m['selected_option'])}"
        if m.get("validated_hypotheses"):
            entry += f"\nValidated: {m['validated_hypotheses']}"
        if m.get("rejected_hypotheses"):
            entry += f"\nRejected: {m['rejected_hypotheses']}"
        if m.get("key_decisions"):
            entry += f"\nKey decisions: {json.dumps(m['key_decisions'])}"
        if m.get("pitfalls_and_guards"):
            entry += f"\nPitfalls: {m['pitfalls_and_guards']}"
        if m.get("dimensions"):
            entry += f"\nDimensions explored: {m['dimensions']}"
        if m.get("hard_constraints"):
            entry += f"\nConstraints: {m['hard_constraints']}"
        if m.get("user_preferences"):
            entry += f"\nPreferences: {json.dumps(m['user_preferences'])}"
        parts.append(entry)

    if not parts:
        return "No relevant memories found for this project."
    return "\n".join(parts)


async def _call_openai_with_tools(
    client: AsyncOpenAI,
    db: AsyncSession,
    project_id: uuid.UUID,
    system: str,
    user: str,
    label: str = "",
    max_tokens: int = 4000,
) -> Any:
    """Call OpenAI with memory tool support. Handles tool call loop."""
    t0 = time.time()
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    entry: dict = {
        "label": label,
        "timestamp": t0,
        "model": settings.openai_model,
        "messages": list(messages),
        "tool_calls": [],
        "raw_response": None,
        "parsed": None,
        "error": None,
        "duration_ms": 0,
    }
    try:
        # First call with tools
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            tools=[MEMORY_TOOL_DEF],
            temperature=0.7,
            max_tokens=max_tokens,
        )
        msg = response.choices[0].message

        # Handle tool calls (up to 3 rounds)
        rounds = 0
        while msg.tool_calls and rounds < 3:
            rounds += 1
            messages.append(msg)
            for tc in msg.tool_calls:
                entry["tool_calls"].append({
                    "id": tc.id,
                    "function": tc.function.name,
                    "arguments": tc.function.arguments,
                })
                # Execute the tool
                args = json.loads(tc.function.arguments)
                tool_result = await _search_memory_for_tool(
                    db, project_id,
                    query=args.get("query", ""),
                    filter_type=args.get("filter_type", "all"),
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": tool_result,
                })
            # Continue the conversation
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                tools=[MEMORY_TOOL_DEF],
                temperature=0.7,
                max_tokens=max_tokens,
            )
            msg = response.choices[0].message

        content = msg.content or "{}"
        entry["raw_response"] = content
        entry["usage"] = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            "total_tokens": response.usage.total_tokens if response.usage else 0,
        }
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
        parsed = json.loads(content)
        entry["parsed"] = parsed
        return parsed
    except Exception as e:
        entry["error"] = str(e)
        raise
    finally:
        entry["duration_ms"] = round((time.time() - t0) * 1000)
        _debug_log.append(entry)


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


# ─── Stage A: Requirement Decomposer ──────────────────────

async def decompose_requirements(
    client: AsyncOpenAI,
    db: AsyncSession,
    project_id: uuid.UUID,
    user_input: str,
    current_code: dict[str, str] | None = None,
    decided_context: str | None = None,
) -> dict:
    """Stage A: Decompose user input into implementation dimensions.

    If current_code is provided (existing game), uses the contextual decomposer
    that generates specific dimensions. Otherwise uses the generic 8-dimension
    decomposer for initial game design.

    Uses _call_openai_with_tools so the model can search_memory for past decisions.
    """
    if current_code:
        # Contextual mode: game already exists
        code_summary = ""
        for fp, content in current_code.items():
            code_summary += f"--- {fp} ---\n{content[:3000]}\n\n"
        prompt = STAGE_A_CONTEXTUAL_PROMPT.format(
            current_code=code_summary,
            decided_context=decided_context or "No prior decisions recorded.",
        )
        return await _call_openai_with_tools(
            client, db, project_id, prompt, user_input, label="A:decompose(contextual)"
        )
    else:
        # Fresh mode: no existing game
        return await _call_openai_with_tools(
            client, db, project_id, STAGE_A_DECOMPOSER_PROMPT, user_input, label="A:decompose(fresh)"
        )


# ─── Stage B: Branch Synthesizer ──────────────────────────

async def synthesize_branches(
    client: AsyncOpenAI,
    db: AsyncSession,
    project_id: uuid.UUID,
    dimensions_json: dict,
    memory_context: dict,
) -> list[dict]:
    """Stage B: Combine dimensions into 3-6 divergent branches.

    Uses _call_openai_with_tools so the model can search_memory for strategy paths.
    """
    # Extract locked context if present (from contextual decomposer)
    locked = dimensions_json.get("locked")
    locked_context = ""
    if locked:
        locked_context = f"Locked decisions (do NOT change these):\n{json.dumps(locked, indent=2)}"

    # Pass only the dimensions part to the branch synthesizer
    dims = dimensions_json.get("dimensions", dimensions_json)

    prompt = STAGE_B_BRANCH_PROMPT.format(
        memory_context=json.dumps(memory_context, indent=2),
        dimensions_json=json.dumps(dims, indent=2),
        locked_context=locked_context,
    )
    result = await _call_openai_with_tools(
        client, db, project_id, prompt, "Synthesize branches", label="B:branches"
    )
    if isinstance(result, dict) and "branches" in result:
        return result["branches"]
    if isinstance(result, list):
        return result
    return []


# ─── Stage C: Demo Mapper ────────────────────────────────

async def map_demos(
    client: AsyncOpenAI,
    branches: list[dict],
    template_catalog: list[dict],
) -> tuple[list[dict], str | None]:
    """Stage C: Map branches to template options. Returns (options, recommended_id)."""
    catalog_summary = [
        {
            "template_id": t["template_id"],
            "title": t["title"],
            "core_loop": t["core_loop"],
            "controls": t["controls"],
            "mechanics": t["mechanics"],
            "complexity": t["complexity"],
            "mobile_fit": t["mobile_fit"],
        }
        for t in template_catalog
    ]
    prompt = STAGE_C_MAPPER_PROMPT.format(
        template_catalog=json.dumps(catalog_summary, indent=2),
        branches_json=json.dumps(branches, indent=2),
    )
    result = await _call_openai_json(client, prompt, "Map branches to demos", label="C:mapper")
    options = []
    recommended_id = None
    if isinstance(result, dict):
        options = result.get("options", [])
        recommended_id = result.get("recommended_option_id")
    elif isinstance(result, list):
        options = result
    # Mark the recommended option
    if recommended_id:
        for opt in options:
            opt["is_recommended"] = (opt.get("option_id") == recommended_id)
    return options, recommended_id


# ─── Stage D: Code Customizer ────────────────────────────

async def customize_template(
    client: AsyncOpenAI,
    template_files: list[dict],
    option: dict,
    user_input: str,
) -> dict[str, str]:
    """Stage D: Customize template code to match the selected option's game design."""
    # Build template code context
    template_code = ""
    for f in template_files:
        template_code += f"--- {f['file_path']} ---\n{f['content']}\n\n"

    prompt = STAGE_D_CUSTOMIZER_PROMPT.format(
        title=option.get("title", ""),
        core_loop=option.get("core_loop", ""),
        controls=option.get("controls", ""),
        mechanics=json.dumps(option.get("mechanics", [])),
        complexity=option.get("complexity", "medium"),
        mobile_fit=option.get("mobile_fit", "good"),
        user_input=user_input,
        template_code=template_code,
    )
    result = await _call_openai_json(
        client, prompt, "Customize game code", label="D:customize", max_tokens=8000
    )
    if isinstance(result, dict):
        return result
    return {}


# ─── Explore (full pipeline A → B → C) ───────────────────

async def _get_current_game_context(
    db: AsyncSession, project_id: uuid.UUID
) -> tuple[dict[str, str] | None, str | None]:
    """Check if the project has existing game code. Returns (files_dict, decided_context) or (None, None)."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project or not project.current_version_id:
        return None, None

    result = await db.execute(
        select(ProjectFile).where(ProjectFile.version_id == project.current_version_id)
    )
    files = list(result.scalars().all())
    if not files:
        return None, None

    files_dict = {f.file_path: f.content for f in files}

    # Build decided context from the most recent exploration session
    result = await db.execute(
        select(ExplorationSession)
        .where(ExplorationSession.project_id == project_id)
        .order_by(ExplorationSession.created_at.desc())
        .limit(1)
    )
    session = result.scalar_one_or_none()
    decided_parts = []
    if session:
        if session.selected_option_id:
            opt_result = await db.execute(
                select(ExplorationOption).where(
                    ExplorationOption.session_id == session.id,
                    ExplorationOption.option_id == session.selected_option_id,
                )
            )
            opt = opt_result.scalar_one_or_none()
            if opt:
                decided_parts.append(f"Game: {opt.title}")
                decided_parts.append(f"Core loop: {opt.core_loop}")
                decided_parts.append(f"Controls: {opt.controls}")
                decided_parts.append(f"Mechanics: {', '.join(opt.mechanics) if isinstance(opt.mechanics, list) else opt.mechanics}")
                decided_parts.append(f"Complexity: {opt.complexity}")
                decided_parts.append(f"Mobile fit: {opt.mobile_fit}")
        if session.iteration_count > 0:
            decided_parts.append(f"Iterations done: {session.iteration_count}")
        if session.hypothesis_ledger:
            ledger = session.hypothesis_ledger
            if ledger.get("validated"):
                decided_parts.append(f"Validated: {', '.join(ledger['validated'][:5])}")
            if ledger.get("rejected"):
                decided_parts.append(f"Rejected: {', '.join(ledger['rejected'][:5])}")

    decided_context = "\n".join(decided_parts) if decided_parts else None
    return files_dict, decided_context


async def explore(
    db: AsyncSession,
    client: AsyncOpenAI,
    project_id: uuid.UUID,
    user_input: str,
    template_ids: list[str],
    template_catalog: list[dict] | None = None,
) -> dict:
    """Full explore pipeline: A:decompose → B:branches → C:mapper → persist."""
    # Check for existing game code
    current_code, decided_context = await _get_current_game_context(db, project_id)

    # Stage A: contextual if game exists, generic if fresh
    decomposition = await decompose_requirements(
        client, db, project_id, user_input,
        current_code=current_code,
        decided_context=decided_context,
    )

    # Memory retrieval
    memory_ctx = await get_memory_context(db, project_id)

    # Stage B
    branches = await synthesize_branches(client, db, project_id, decomposition, memory_ctx)

    # Stage C
    if template_catalog is None:
        from app.templates.phaser_demos import PHASER_DEMO_CATALOG
        template_catalog = PHASER_DEMO_CATALOG
    options, recommended_id = await map_demos(client, branches, template_catalog)

    # Persist
    session = ExplorationSession(
        project_id=project_id,
        user_input=user_input,
        ambiguity_json=decomposition,
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
        "ambiguity": decomposition,
        "branches": branches,
        "options": option_responses,
        "memory_influence": memory_ctx if memory_ctx["relevant_preferences"] else None,
    }


# ─── Select Option ─────────────────────────────────────────

async def select_option(
    db: AsyncSession,
    client: AsyncOpenAI,
    project_id: uuid.UUID,
    session_id: int,
    option_id: str,
    template_files: list[dict],
) -> dict:
    """Select an option: customize template with AI, create version, transition state."""
    result = await db.execute(
        select(ExplorationSession).where(ExplorationSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise ValueError("Session not found")

    # Get the option details for customization context
    opt_result = await db.execute(
        select(ExplorationOption).where(
            ExplorationOption.session_id == session_id,
            ExplorationOption.option_id == option_id,
        )
    )
    option_row = opt_result.scalar_one_or_none()
    option_spec = {}
    if option_row:
        option_spec = {
            "title": option_row.title,
            "core_loop": option_row.core_loop,
            "controls": option_row.controls,
            "mechanics": option_row.mechanics,
            "complexity": option_row.complexity,
            "mobile_fit": option_row.mobile_fit,
        }

    # Stage D: AI-customize the template code based on the option
    customized = await customize_template(
        client, template_files, option_spec, session.user_input
    )

    version = ProjectVersion(
        project_id=project_id,
        build_status="success",
    )
    db.add(version)
    await db.flush()

    # Use customized code if available, fallback to raw template
    for f in template_files:
        fp = f["file_path"]
        content = customized.get(fp, f["content"])
        pf = ProjectFile(
            version_id=version.id,
            file_path=fp,
            content=content,
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

    # Write design-decision memory note
    # Gather all options for this session to record what was available
    all_opts_result = await db.execute(
        select(ExplorationOption).where(ExplorationOption.session_id == session_id)
    )
    all_options = list(all_opts_result.scalars().all())
    options_summary = []
    for o in all_options:
        options_summary.append({
            "option_id": o.option_id,
            "title": o.title,
            "core_loop": o.core_loop,
            "controls": o.controls,
            "is_recommended": o.is_recommended,
        })

    decomposition = session.ambiguity_json or {}
    memory_content = {
        "title": f"Design Decision: {option_spec.get('title', option_id)}",
        "summary": (
            f"User requested: \"{session.user_input}\". "
            f"Decomposed into {len(decomposition.get('dimensions', {}))} dimensions. "
            f"Selected \"{option_spec.get('title', option_id)}\" from {len(all_options)} options."
        ),
        "type": "design_decision",
        "user_input": session.user_input,
        "decomposition_summary": decomposition.get("summary", ""),
        "dimensions": list(decomposition.get("dimensions", {}).keys()),
        "hard_constraints": decomposition.get("hard_constraints", []),
        "locked": decomposition.get("locked"),
        "options_considered": options_summary,
        "selected_option": {
            **option_spec,
            "option_id": option_id,
            "assumptions_to_validate": (
                option_row.assumptions_to_validate
                if option_row and option_row.assumptions_to_validate else []
            ),
        },
        "user_preferences": {},
        "final_choice": {
            "option_id": option_id,
            "why": (
                "Recommended by system" if option_row and option_row.is_recommended
                else "User selected manually"
            ),
        },
        "validated_hypotheses": [],
        "rejected_hypotheses": [],
        "key_decisions": [{
            "decision": f"Selected {option_spec.get('title', option_id)}",
            "reason": f"Core loop: {option_spec.get('core_loop', '')}",
            "evidence": f"Controls: {option_spec.get('controls', '')}, Complexity: {option_spec.get('complexity', '')}",
        }],
        "pitfalls_and_guards": [],
        "refs": {
            "exploration_session_id": session.id,
            "stable_version_id": version.id,
        },
        "confidence": 0.6,
    }

    note = ExplorationMemoryNote(
        project_id=project_id,
        content_json=memory_content,
        tags=_extract_tags(memory_content) + ["type:design_decision"],
        confidence=0.6,
        source_version_id=version.id,
        source_session_id=session.id,
    )
    db.add(note)

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
    modifications = await _call_openai_json(client, prompt, user_input, label="iterate", max_tokens=8000)

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
    memory_content = await _call_openai_json(client, prompt, "Generate structured memory", label="finish_exploration")

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


async def get_active_session_full(
    db: AsyncSession, project_id: uuid.UUID
) -> dict | None:
    """Get the most recent non-stable exploration session with its options."""
    result = await db.execute(
        select(ExplorationSession)
        .where(
            ExplorationSession.project_id == project_id,
            ExplorationSession.state != "stable",
        )
        .order_by(ExplorationSession.created_at.desc())
        .limit(1)
    )
    session = result.scalar_one_or_none()
    if not session:
        return None

    result = await db.execute(
        select(ExplorationOption)
        .where(ExplorationOption.session_id == session.id)
    )
    options = list(result.scalars().all())

    return {
        "session_id": session.id,
        "state": session.state,
        "user_input": session.user_input,
        "ambiguity": session.ambiguity_json,
        "options": [
            {
                "option_id": o.option_id,
                "title": o.title,
                "core_loop": o.core_loop,
                "controls": o.controls,
                "mechanics": o.mechanics if isinstance(o.mechanics, list) else [],
                "engine": "Phaser",
                "template_id": o.template_id,
                "complexity": o.complexity,
                "mobile_fit": o.mobile_fit,
                "assumptions_to_validate": o.assumptions_to_validate if isinstance(o.assumptions_to_validate, list) else [],
                "is_recommended": o.is_recommended,
            }
            for o in options
        ],
        "selected_option_id": session.selected_option_id,
        "hypothesis_ledger": session.hypothesis_ledger,
        "iteration_count": session.iteration_count,
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
