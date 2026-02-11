# Phaser 2D WebGame Option-First Exploration System

> AI-driven game prototyping system that generates runnable Phaser 3 candidates instead of asking clarifying questions.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [AI Pipeline (5 Stages)](#ai-pipeline-5-stages)
- [State Machine](#state-machine)
- [Core Flow](#core-flow)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Frontend Components](#frontend-components)
- [Template Catalog](#template-catalog)
- [Data Structures](#data-structures)
- [Memory System](#memory-system)
- [Design Principles](#design-principles)

---

## Overview

The Exploration System is the core interaction model for SimplePageGenerator's game prototyping workflow. Rather than asking users clarifying questions about their game idea, the system **decomposes requirements into implementation dimensions**, **synthesizes divergent design branches**, **maps branches to runnable Phaser 3 templates**, and **customizes the code with AI** to produce a playable prototype matching the user's intent. All conclusions are captured as **structured memory** that biases future explorations.

### Key Characteristics

- **Option-First**: No clarifying questions. Ambiguity is decomposed internally and explored through concrete, playable options.
- **Adaptive Decomposer**: Stage A auto-detects context — uses generic 8 dimensions for a blank slate, or generates specific contextual dimensions when a game already exists.
- **4-Stage AI Pipeline**: Decompose → Branch → Map → Customize. Each stage has a dedicated prompt and debug logging.
- **AI-Customized Code**: Selecting an option doesn't just copy a preset demo — the template is rewritten by AI to match the specific game design.
- **AI-Powered Preview**: Clicking "Preview" runs Stage D+E to show an AI-customized game — not just the raw template. Results are cached in a generic `kv_cache` table (30-min TTL).
- **Self-Healing Preview**: Runtime errors in previewed games are automatically caught via injected `window.onerror`, sent back to AI for fixing, and the iframe reloads with corrected code (up to 2 fix attempts).
- **Memory Tool (Function Calling)**: Stage A and B can dynamically query past exploration memories via OpenAI tool use (`search_memory`), enabling the AI to recall strategy paths, design decisions, and lessons learned.
- **Dual-Layer Memory**: Design decisions are recorded immediately on select (confidence 0.6); comprehensive memory is written on finish (confidence 0.85). Future explorations benefit from both.
- **Closed-Loop Memory**: Each exploration session produces structured conclusions that influence future sessions.
- **Versioned Iterations**: Every code modification creates an immutable `ProjectVersion` that can be rolled back.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (React)                   │
│                                                      │
│  EditorPage                                          │
│  ├── PreviewPanel / Template iframe                  │
│  └── Tabs                                            │
│      ├── ExplorePanel  → Decomposition + OptionCard[]│
│      ├── IteratePanel  → HypothesisLedger            │
│      ├── ExplorationMemoryPanel → MemoryNoteCard[]   │
│      └── DebugPanel    → OpenAI call log             │
│                                                      │
│  Zustand Store (exploration state slice)              │
│  API Client (api/exploration.ts)                     │
└────────────────┬────────────────────────────────────┘
                 │  REST API
┌────────────────▼────────────────────────────────────┐
│                 Backend (FastAPI)                     │
│                                                      │
│  Router: /api/v1/projects/{project_id}/...           │
│  ├── POST /explore                                   │
│  ├── POST /select_option                             │
│  ├── POST /iterate                                   │
│  ├── POST /finish_exploration                        │
│  ├── POST /exploration/preview_option                │
│  ├── POST /exploration/fix_preview                   │
│  ├── GET  /exploration/preview_option/{s}/{o}        │
│  ├── GET  /exploration/state/{session_id}            │
│  ├── GET  /exploration/memory_notes                  │
│  └── GET  /exploration/preview/{template_id}         │
│                                                      │
│  Debug Router: /api/v1/debug/...                     │
│  ├── GET  /openai_log                                │
│  └── DELETE /openai_log                              │
│                                                      │
│  Service: exploration_service.py                     │
│  ├── Stage A: decompose_requirements()  ←── OpenAI+tools│
│  ├── Stage B: synthesize_branches()     ←── OpenAI+tools│
│  ├── Stage C: map_demos()               ←── OpenAI   │
│  ├── Stage D: generate_feel_spec()      ←── OpenAI   │
│  ├── Stage E: customize_template()      ←── OpenAI   │
│  ├── preview_option()     (D+E, cached) ←── OpenAI   │
│  ├── fix_preview()        (self-heal)   ←── OpenAI   │
│  ├── iterate()                          ←── OpenAI   │
│  └── finish_exploration()               ←── OpenAI   │
│                                                      │
│  Memory Tool: search_memory (OpenAI function calling)│
│  ├── _search_memory_for_tool()  → queries DB         │
│  └── _call_openai_with_tools()  → tool call loop     │
│                                                      │
│  Templates: phaser_demos.py (6 game templates)       │
│  Debug: _debug_log (in-memory ring buffer, max 50)   │
└────────────────┬────────────────────────────────────┘
                 │  SQLAlchemy async
┌────────────────▼────────────────────────────────────┐
│              PostgreSQL + pgvector                    │
│  Tables:                                             │
│  ├── exploration_sessions                            │
│  ├── exploration_options                             │
│  ├── exploration_memory_notes                        │
│  ├── user_preferences                                │
│  └── kv_cache (preview HTML cache, 30-min TTL)       │
└─────────────────────────────────────────────────────┘
```

### File Structure

```
backend/
├── app/
│   ├── models/exploration.py          # ORM models (4 tables)
│   ├── schemas/exploration.py         # Pydantic request/response schemas
│   ├── services/exploration_service.py # 4-stage AI pipeline + business logic
│   ├── routers/exploration.py         # FastAPI endpoints + debug router
│   └── templates/phaser_demos.py      # 6 Phaser 3 game templates
├── alembic/versions/
│   ├── b2c3d4e5f6g7_add_exploration_tables.py
│   └── c3d4e5f6g7h8_add_kv_cache_table.py

frontend/src/
├── types/exploration.ts               # TypeScript interfaces
├── api/exploration.ts                 # API client functions
├── store/index.ts                     # Zustand store (exploration slice)
├── components/exploration/
│   ├── ExplorePanel.tsx               # Input + decomposition + options grid
│   ├── OptionCard.tsx                 # Single option card
│   ├── IteratePanel.tsx               # Iteration chat + hypothesis ledger
│   ├── ExplorationMemoryPanel.tsx     # Memory notes viewer
│   └── DebugPanel.tsx                 # OpenAI call debug viewer
├── pages/EditorPage.tsx               # Main page with tabs + preview
└── styles/exploration.css             # All exploration styles
```

---

## AI Pipeline (5 Stages)

The explore flow chains five AI stages, each with a dedicated system prompt. Every OpenAI call is logged to an in-memory ring buffer (`deque(maxlen=50)`) accessible via the Debug tab.

Stage A and B use **OpenAI function calling** (`_call_openai_with_tools`) with a `search_memory` tool, allowing the AI to dynamically query past exploration memories during decomposition and branch synthesis. Stages C, D, and E use standard JSON calls (`_call_openai_json`).

```
User Input
    │
    ▼
┌───────────────────────────────────────────────────────┐
│ Stage A: Decomposer            decompose_requirements()│
│                                      (with tools)      │
│  ┌─ Fresh (no game code) ──┐  ┌─ Contextual ────────┐ │
│  │ Reference 8 dims, only  │  │ Reads current code + │ │
│  │ includes ambiguous ones │  │ past decisions       │ │
│  │ Label: A:decompose      │  │ Dynamic dimensions   │ │
│  │        (fresh)          │  │ + locked items       │ │
│  └─────────────────────────┘  │ Label: A:decompose   │ │
│                               │        (contextual)  │ │
│  🔧 search_memory tool        └──────────────────────┘ │
│  Dimension count driven by                             │
│  actual ambiguity (1 to N)     max_tokens: 4000        │
└───────────────────┬────────────────────────────────────┘
                    │ dimensions JSON (+ optional locked)
                    ▼
┌───────────────────────────────┐
│ Stage B: Branch Synth         │  synthesize_branches()
│ Dimensions + memory           │  (with tools)
│ + locked constraints          │  Label: "B:branches"
│ 🔧 search_memory tool         │  max_tokens: 4000
│ → 3-6 divergent branches      │
└─────────┬─────────────────────┘
          │ branches JSON
          ▼
┌───────────────────────────┐
│ Stage C: Demo Mapper      │  map_demos()
│ Branches + template       │  Label: "C:mapper"
│ catalog → option cards    │  max_tokens: 4000
└─────────┬─────────────────┘
          │ options JSON
          ▼
      (User previews / selects)
          │
          ▼
┌───────────────────────────┐
│ Stage D: Feel Spec Gen    │  generate_feel_spec()
│ Option spec + game-type   │  Label: "D:feel_spec"
│ defaults + user prefs     │  max_tokens: 4000
│ → feel micro-spec JSON    │
└─────────┬─────────────────┘
          │ feel_spec JSON
          ▼
┌───────────────────────────┐
│ Stage E: Code Customizer  │  customize_template()
│ Template code + option    │  Label: "E:customize"
│ spec + feel spec          │  max_tokens: 8000
│ → customized game code    │
└───────────────────────────┘

Stages D+E run on both Preview (cached, no state change) and Select (persisted as ProjectVersion).
```

### search_memory Tool (OpenAI Function Calling)

Stage A and B use `_call_openai_with_tools()` which provides a `search_memory` tool via OpenAI function calling. This allows the AI to **proactively query** past exploration memories during decomposition and branch synthesis.

**Tool definition** (`MEMORY_TOOL_DEF`):
```json
{
  "name": "search_memory",
  "parameters": {
    "query": "string — what to search for (e.g. 'runner game controls', 'mobile tap games')",
    "filter_type": "string — 'all' | 'design_decision' | 'exploration_finish'"
  }
}
```

**Handler** (`_search_memory_for_tool`):
1. Queries `ExplorationMemoryNote` (latest 20) + `UserPreference` from the database
2. Filters by `filter_type` if specified (matches `content_json.type`)
3. Keyword-matches query terms against note content
4. Returns formatted text with: user preferences, memory summaries, selected options, validated/rejected hypotheses, key decisions, pitfalls, dimensions, constraints

**Call loop**: Up to 3 tool call rounds per OpenAI request. Debug entries include `tool_calls` array with function name, arguments, and ID.

### Stage A: Requirement Decomposer (Dual-Mode)

Stage A **auto-detects context** at runtime. If the project already has game code (a `current_version_id` with files), the contextual decomposer is used. Otherwise, the fresh decomposer runs. Both modes have access to the `search_memory` tool for recalling past decisions.

#### Fresh Mode — `STAGE_A_DECOMPOSER_PROMPT`

**When**: First exploration, no existing game code.
**Label**: `A:decompose(fresh)`
**Input**: User's free-text game description
**Output**: JSON with `summary`, `dimensions` (only ambiguous ones), `hard_constraints`, `open_questions`

Uses **8 reference dimensions** as a guide, but **only includes those where real ambiguity exists** (2+ plausible candidates). Clear decisions go into `hard_constraints` instead. The prompt may also create custom dimensions beyond the reference set (e.g. `enemy_behavior`, `scoring_model`).

Reference dimensions:

| Dimension | Example Candidates | Purpose |
|---|---|---|
| `controls` | keyboard, mouse_click, touch_tap, touch_drag, virtual_joystick, auto, single_key | How the player interacts |
| `presentation` | 2d_topdown, side_scroller, isometric, minimal_2d | Visual perspective |
| `core_loop` | move_dodge_shoot, jump_collect, match_clear, click_upgrade, build_defend, run_avoid | The 5-30s repeating action |
| `goals` | high_score, level_clear, endless_survival, economy_growth, time_attack | What the player aims for |
| `progression` | infinite, levels, missions, freeform | How difficulty/content advances |
| `systems` | physics, collision, simple_ai, projectiles, grid, economy, spawner | Required subsystems |
| `platform` | mobile, desktop, both | Target device |
| `tone` | exciting, relaxing, tense, cute, retro, minimal | Emotional feel |

For a very specific request like "a mobile tap-to-jump endless runner", most dimensions are clear — only 1-2 ambiguous ones (e.g. `tone`, `goals`) would appear as dimensions, while the rest become `hard_constraints`. For a vague request like "a fun game", many dimensions would be expanded.

#### Contextual Mode — `STAGE_A_CONTEXTUAL_PROMPT`

**When**: Project already has game code (re-exploration after select/iterate).
**Label**: `A:decompose(contextual)`
**Input**: User's new request + current game code (truncated to 3000 chars/file) + decided context (selected option details, iteration history, validated/rejected hypotheses)
**Output**: JSON with `summary`, `locked`, `dimensions` (dynamic 3-8), `hard_constraints`, `open_questions`

Instead of re-analyzing generic dimensions that are already decided (controls, platform, etc.), generates **specific, actionable dimensions** relevant to the current request.

The number of dimensions depends on actual ambiguity — if the request is specific ("add a shield power-up that lasts 5 seconds"), only 1-2 dimensions may appear. If vague ("add power-ups and a boss fight"), more are generated.

Example: user has an existing endless runner and requests "add power-ups and a boss fight":

| Generated Dimension | Candidates | Why |
|---|---|---|
| `power_up_types` | speed_boost, shield, magnet, double_score | What power-ups to implement |
| `power_up_spawn` | random_interval, fixed_positions, after_milestones | When/where power-ups appear |
| `boss_attack_pattern` | projectile_barrage, charge_dash, area_denial | How the boss behaves |
| `boss_frequency` | every_500_points, every_60_seconds, after_3_waves | When bosses appear |

The `locked` field lists what's already decided and should not change:
```json
{
  "locked": {
    "description": "things already decided that should NOT change",
    "items": ["controls: touch_tap", "presentation: side_scroller", "core_loop: run_avoid"]
  }
}
```

#### Shared Dimension Format

Both modes produce dimensions with the same internal structure:
- **candidates**: 2-4 possible values (a dimension is only created when there are 2+ plausible options)
- **confidence**: `high` | `med` | `low` — how certain the AI is based on user text
- **signals**: Direct quotes or inferences from the user's text

Key principle: **dimension count follows ambiguity**. A very specific request may produce 1 dimension; a vague one may produce 8+. There is no fixed minimum or maximum.

Both modes also extract:
- **hard_constraints**: Things the user explicitly required or excluded (including clear decisions that don't need a dimension)
- **open_questions**: Ambiguities worth investigating, with `dimension`, `question`, `why_it_matters`

#### How Context Is Built

`_get_current_game_context()` gathers:
1. **Current game files** from the project's `current_version_id`
2. **Decided context** from the most recent `ExplorationSession`:
   - Selected option details (title, core_loop, controls, mechanics, complexity, mobile_fit)
   - Iteration count
   - Hypothesis ledger (validated, rejected items)

### Stage B: Branch Synthesizer

**Prompt**: `STAGE_B_BRANCH_PROMPT`
**Input**: Dimensions JSON + memory context (past preferences) + optional locked constraints
**Tool access**: `search_memory` — can query past strategy paths and lessons learned
**Output**: 3-6 divergent design branches

Each branch is one **internally-consistent set of choices** across all dimensions (whether the fixed 8 from fresh mode or the dynamic ones from contextual mode). Branches must differ on at least 2 dimensions.

Key behaviors:
- If **locked** constraints are present (contextual mode), branches respect those decisions and only vary on the new dimensions.
- If memory context shows user preferences, one branch is aligned with those preferences.

Branch structure:
```json
{
  "branch_id": "B1",
  "name": "Neon Dash Runner",
  "picked": {
    "controls": "single_key",
    "presentation": "side_scroller",
    "core_loop": "tap to jump over obstacles, collect coins",
    "goals": "high_score",
    "progression": "infinite",
    "systems": ["physics", "collision", "spawner"],
    "platform": "mobile",
    "tone": "exciting"
  },
  "why_this_branch": ["Simple controls maximize mobile accessibility"],
  "risks": ["May feel repetitive without progression"],
  "what_to_validate": ["Is endless mode engaging enough?"]
}
```

### Stage C: Demo Mapper

**Prompt**: `STAGE_C_MAPPER_PROMPT`
**Input**: Branches JSON + full template catalog metadata (not just IDs — includes title, core_loop, controls, mechanics, complexity, mobile_fit)
**Output**: 3-6 option cards, one per branch, each mapped to a template_id

The mapper picks the closest template for each branch, noting what tweaks will be needed. Exactly one option is marked `is_recommended: true`.

### Stage D: Feel/Control Spec Generator

**Prompt**: `STAGE_D_FEEL_SPEC_PROMPT`
**Label**: `D:feel_spec`
**Input**: Option spec (title, core_loop, controls, mechanics, complexity, mobile_fit) + game-type defaults (from `get_feel_priors()`) + user feel profile + user's original request
**Output**: JSON micro-spec defining game feel: movement model, jump model, input scheme, camera, bounds, visual feedback, tuning presets

Key behaviors:
- Starts from **game-type defaults** (loaded per template type) and deviates only with reason
- Respects **user feel profile** (e.g. style_tendency: tight/floaty/arcade, dislikes)
- Each section has a `notes` field explaining reasoning
- Omits irrelevant sections (no `jump_model` for a clicker)
- Values are realistic Phaser 3 numbers (pixels/sec, ms, 0-1 ratios)

### Stage E: Code Customizer

**Prompt**: `STAGE_E_CUSTOMIZER_PROMPT`
**Label**: `E:customize`
**Input**: Template source code + option spec + **feel micro-spec** (from Stage D) + user's original request
**Output**: JSON mapping file_path to customized file content

This stage runs during both **Preview** (cached in `kv_cache`, no state change) and **Select** (persisted as `ProjectVersion`). The AI rewrites the game code to:
- Match the described core loop and controls
- Apply the feel micro-spec values as a `const TUNING` config object
- Implement a Debug HUD showing tuning values
- Implement the specified mechanics
- Update title, colors, and gameplay behavior
- Maintain mobile support (touch controls, Scale.FIT)
- Use only Phaser primitives (no external assets)

Uses `max_tokens: 8000` to accommodate full game code output.

### Self-Healing Preview (fix_preview)

**Prompt**: `FIX_PREVIEW_PROMPT`
**Label**: `fix_preview`

When AI-generated preview code throws runtime errors:
1. Injected `window.onerror` handler in the served HTML catches errors (up to 5)
2. Errors are sent to the parent frame via `postMessage`
3. Frontend calls `POST /exploration/fix_preview` with the errors
4. AI receives the current code + error details and returns a fixed version
5. Cache is updated, iframe reloads

**Retry limit**: 2 fix attempts per preview (tracked in `kv_cache.meta_json.fix_attempts`).

Common fixes the AI handles:
- `this` context lost in standalone functions called from Phaser scene methods
- Null access on `body`, `input`, `activePointer`
- Phaser objects used before scene initialization

---

## State Machine

The exploration lifecycle follows a strict state machine:

```
                 ┌────────────────────────┐
                 │         idle           │  (initial state)
                 └───────────┬────────────┘
                             │ POST /explore (Stages A → B → C)
                 ┌───────────▼────────────┐
                 │    explore_options      │  3-6 options generated
                 └───────────┬────────────┘
                             │ user clicks Preview (POST /exploration/preview_option, Stage D+E)
                 ┌───────────▼────────────┐
                 │      previewing        │  iframe shows AI-customized game
                 └───────────┬────────────┘  (cached in kv_cache, self-healing errors)
                             │ POST /select_option (Stage D+E)
                 ┌───────────▼────────────┐
                 │      committed         │  AI-customized code saved
                 └───────────┬────────────┘
                             │ POST /iterate (repeatable)
                 ┌───────────▼────────────┐
             ┌──▶│      iterating         │  AI modifies code per request
             │   └───────────┬────────────┘
             │               │
             └───────────────┘ (loop)
                             │ POST /finish_exploration
                 ┌───────────▼────────────┐
                 │    memory_writing       │  AI synthesizes structured memory
                 └───────────┬────────────┘
                             │
                 ┌───────────▼────────────┐
                 │        stable          │  exploration complete
                 └────────────────────────┘
```

### State Descriptions

| State | Description | AI Stage | Allowed Actions |
|---|---|---|---|
| `idle` | No active exploration | — | Start new exploration |
| `explore_options` | Options generated, user reviewing | A+B+C ran | Preview, Select |
| `previewing` | User viewing AI-customized preview (Stage D+E, cached) | D+E ran (preview) | Select, Preview another |
| `committed` | User selected an option, AI-customized code saved | D ran | Iterate, Finish |
| `iterating` | User modifying game through iterations | Iterate prompt | Iterate more, Finish |
| `memory_writing` | AI synthesizing session into memory (transient) | Memory writer | Wait |
| `stable` | Exploration complete, memory saved | — | Start new exploration |

---

## Core Flow

### 1. Explore: Decompose → Branch → Map

User describes a game idea (or a modification to an existing one). The system auto-detects whether a game already exists and runs Stages A → B → C accordingly.

#### Example: Fresh Exploration (no existing game)

```
User: "I want a fast mobile game where you tap to jump over things"
                    │
         ┌──────────▼───────────┐
         │ Stage A (fresh)      │
         │ 8 generic dimensions:│
         │  controls: single_key│ (high, "tap to jump")
         │  presentation: side  │ (med)
         │  core_loop: run_avoid│ (high, "jump over things")
         │  platform: mobile    │ (high, "mobile game")
         │  tone: exciting      │ (med, "fast")
         │  ...                 │
         └──────────┬───────────┘
                    │
         ┌──────────▼───────────┐
         │ Stage B: Branches    │
         │ + Memory Context     │
         │                      │
         │ B1: Neon Dash Runner │ (side_scroller, single_key)
         │ B2: Sky Bounce       │ (2d_topdown, touch_tap)
         │ B3: Obstacle Swipe   │ (side_scroller, touch_drag)
         └──────────┬───────────┘
                    │
         ┌──────────▼───────────┐
         │ Stage C: Mapper      │
         │ B1 → runner_endless  │ ← recommended
         │ B2 → platformer     │
         │ B3 → runner_endless  │
         └──────────┬───────────┘
                    │
              Option Cards shown
```

#### Example: Contextual Exploration (game already exists)

```
Existing game: endless runner with tap-to-jump
User: "add power-ups and a boss fight"
                    │
         ┌──────────▼───────────────────┐
         │ Stage A (contextual)         │
         │ locked:                      │
         │   controls: touch_tap        │
         │   presentation: side_scroller│
         │   core_loop: run_avoid       │
         │ new dimensions:              │
         │   power_up_types (med)       │
         │   boss_attack_pattern (low)  │
         │   boss_frequency (low)       │
         │   difficulty_scaling (med)   │
         │   reward_feedback (low)      │
         └──────────┬───────────────────┘
                    │
         ┌──────────▼───────────┐
         │ Stage B: Branches    │
         │ (respects locked)    │
         │                      │
         │ B1: Shield & Charge  │ (shield powerup, dash boss)
         │ B2: Magnet Barrage   │ (magnet powerup, projectile boss)
         │ B3: Score Rush       │ (multiplier powerup, area boss)
         └──────────┬───────────┘
                    │
         ┌──────────▼───────────┐
         │ Stage C: Mapper      │
         │ All → runner_endless │ (same base template)
         └──────────┬───────────┘
                    │
              Option Cards shown
```

### 2. Preview & Select (with AI Customization + Design Decision Memory)

- User clicks **Preview** on an option → triggers **AI-powered preview generation**:
  1. Raw template is shown immediately in iframe (placeholder while loading)
  2. `POST /exploration/preview_option` runs Stage D (feel spec) + Stage E (code customizer)
  3. Result is cached in `kv_cache` (key: `preview:{session_id}:{option_id}`, TTL: 30 min)
  4. Iframe switches to the AI-customized game via `GET /exploration/preview_option/{session_id}/{option_id}`
  5. If runtime errors occur, the **self-healing loop** auto-fixes code (up to 2 attempts)
  6. Subsequent preview clicks on the same option load instantly from cache
  7. No project versions are created, no session state is changed
- User clicks **Select** → triggers **Stage D+E** again (independent generation) + **Design Decision Memory**:
  1. Template files are loaded
  2. Option spec (title, core_loop, controls, mechanics) is read from DB
  3. AI rewrites the template code to match the specific game design
  4. Customized code is saved as a new `ProjectVersion`
  5. **Design decision memory note** is written immediately (see below)
- Preview refreshes to show the **customized game**
- State transitions to `committed`

#### Design Decision Memory (on select)

A `design_decision` memory note is written to `ExplorationMemoryNote` immediately when an option is selected — **without waiting for the user to finish exploration**. This ensures that design decisions are preserved even if the user never clicks "Finish Exploration".

**Memory content** (`type: "design_decision"`, `confidence: 0.6`):
- `user_input`: The original request
- `decomposition_summary`: Stage A summary
- `dimensions`: List of dimension keys explored
- `hard_constraints`: From Stage A
- `locked`: From contextual decomposer (if applicable)
- `options_considered`: All options generated (ID, title, core_loop, controls, is_recommended)
- `selected_option`: Full spec of the chosen option + assumptions_to_validate
- `key_decisions`: What was selected and why

**Tags**: Include `type:design_decision` + standard extracted tags (platform, input, pace, chosen option).

This memory is queryable by the `search_memory` tool in future Stage A and B calls, allowing the AI to reference prior design decisions when decomposing new requests.

### 3. Iterate

User requests code modifications in natural language:

1. Current version's files are loaded
2. GPT receives the code + user request and returns modified files (`max_tokens: 8000`)
3. A new `ProjectVersion` is created (immutable versioning)
4. The user request is appended to `hypothesis_ledger.open_questions`
5. Preview refreshes automatically

### 4. Finish & Write Comprehensive Memory

When the user clicks "Finish Exploration":

1. GPT receives the full session data (user input, selected option, iterations, hypothesis ledger, decomposition)
2. Generates a **comprehensive structured memory** with: preferences, validated/rejected hypotheses, key decisions, pitfalls (`confidence: 0.85`)
3. Saves `ExplorationMemoryNote` to database
4. Updates `UserPreference` record (upsert)
5. State transitions to `stable`

This is the **second layer** of memory — complementing the `design_decision` note (confidence 0.6) written at select time. The finish-time memory has higher confidence because it incorporates iteration results and hypothesis validation.

Both memory types are queryable by the `search_memory` tool in future explorations and also feed into `get_memory_context()` for Stage B's static memory context.

---

## API Reference

All exploration endpoints are under `/api/v1/projects/{project_id}`.
Debug endpoints are under `/api/v1/debug`.

### POST `/explore`

Start a new exploration session. Runs Stages A → B → C.

**Request:**
```json
{
  "user_input": "I want a fast-paced mobile game where you tap to jump over obstacles"
}
```

**Response:**
```json
{
  "session_id": 1,
  "ambiguity": {
    "summary": "A fast-paced mobile game with tap-to-jump controls over obstacles",
    "dimensions": {
      "controls": {
        "candidates": ["touch_tap", "single_key"],
        "confidence": "high",
        "signals": ["tap to jump"]
      },
      "presentation": {
        "candidates": ["side_scroller", "minimal_2d"],
        "confidence": "med",
        "signals": ["jump over things implies side view"]
      },
      "core_loop": {
        "candidates": ["run_avoid", "jump_collect"],
        "confidence": "high",
        "signals": ["jump over obstacles"]
      },
      "goals": {
        "candidates": ["high_score", "endless_survival"],
        "confidence": "low",
        "signals": []
      },
      "progression": {
        "candidates": ["infinite"],
        "confidence": "med",
        "signals": ["no mention of levels"]
      },
      "systems": {
        "candidates": ["physics", "collision", "spawner"],
        "confidence": "med",
        "signals": ["obstacles implies collision + spawning"]
      },
      "platform": {
        "candidates": ["mobile"],
        "confidence": "high",
        "signals": ["mobile game"]
      },
      "tone": {
        "candidates": ["exciting", "retro"],
        "confidence": "med",
        "signals": ["fast-paced"]
      }
    },
    "hard_constraints": ["must be mobile", "must use tap controls"],
    "open_questions": [
      {
        "dimension": "goals",
        "question": "Should the game be endless or have level-based progression?",
        "why_it_matters": "Affects difficulty curve and replay value"
      }
    ]
  },
  "branches": [
    {
      "branch_id": "B1",
      "name": "Neon Dash Runner",
      "picked": {
        "controls": "single_key",
        "presentation": "side_scroller",
        "core_loop": "tap to jump over oncoming obstacles, earn points for distance",
        "goals": "high_score",
        "progression": "infinite",
        "systems": ["physics", "collision", "spawner"],
        "platform": "mobile",
        "tone": "exciting"
      },
      "why_this_branch": ["Classic runner feel, simple single-input"],
      "risks": ["May feel repetitive without variety"],
      "what_to_validate": ["Is tap timing satisfying?"]
    }
  ],
  "options": [
    {
      "option_id": "opt_1",
      "branch_id": "B1",
      "title": "Neon Dash Runner",
      "core_loop": "Tap to jump over obstacles, earn points for distance",
      "controls": "Single tap to jump",
      "mechanics": ["jumping", "obstacles", "scoring", "speed_increase"],
      "engine": "Phaser",
      "template_id": "runner_endless",
      "complexity": "low",
      "mobile_fit": "good",
      "assumptions_to_validate": ["Tap timing feels responsive"],
      "is_recommended": true
    }
  ],
  "memory_influence": {
    "relevant_preferences": { "platform": "mobile", "input": "tap" },
    "recurring_patterns": ["User prefers tap controls"],
    "warnings": ["Avoid complex multi-touch"],
    "suggested_direction_bias": { "input": "tap", "pace": "fast" }
  }
}
```

### POST `/select_option`

Select an option. Runs Stage D (AI code customization) to produce a playable prototype.

**Request:**
```json
{
  "session_id": 1,
  "option_id": "opt_1"
}
```

**Response:**
```json
{
  "session_id": 1,
  "option_id": "opt_1",
  "version_id": 5,
  "state": "committed"
}
```

The resulting `ProjectVersion` contains **AI-customized code** (not the raw template). The customizer adapts the template to match the option's core_loop, controls, mechanics, title, and the user's original request.

### POST `/iterate`

Apply a code modification via AI.

**Request:**
```json
{
  "session_id": 1,
  "user_input": "Make the player move faster and add a double-jump"
}
```

**Response:**
```json
{
  "session_id": 1,
  "version_id": 6,
  "iteration_count": 1,
  "hypothesis_ledger": {
    "validated": [],
    "rejected": [],
    "open_questions": ["Make the player move faster and add a double-jump"]
  },
  "state": "iterating"
}
```

### POST `/finish_exploration`

Finish exploration and write structured memory.

**Request:**
```json
{
  "session_id": 1
}
```

**Response:**
```json
{
  "session_id": 1,
  "memory_note": {
    "id": 1,
    "project_id": "uuid-here",
    "content_json": {
      "title": "Fast Mobile Runner Exploration",
      "summary": "Explored runner options for mobile. Settled on tap-to-jump with endless progression.",
      "user_preferences": {
        "platform": "mobile",
        "input": "tap",
        "pace": "fast",
        "session_length": "short",
        "difficulty": "progressive",
        "visual_density": "moderate"
      },
      "final_choice": { "option_id": "opt_1", "why": "Best match for mobile tap controls" },
      "validated_hypotheses": ["Tap controls feel responsive on mobile"],
      "rejected_hypotheses": ["Swipe controls for jumping"],
      "key_decisions": [
        {
          "decision": "Use single tap instead of swipe",
          "reason": "Lower latency and simpler input",
          "evidence": "User chose tap-based option"
        }
      ],
      "pitfalls_and_guards": ["Avoid small tap targets on mobile"],
      "refs": { "exploration_session_id": 1, "stable_version_id": 6 },
      "confidence": 0.85
    },
    "tags": ["platform:mobile", "input:tap", "pace:fast", "chosen:opt_1"],
    "confidence": 0.85,
    "source_session_id": 1,
    "created_at": "2026-02-09T12:00:00+00:00"
  },
  "state": "stable"
}
```

### POST `/exploration/preview_option`

Trigger AI-powered preview generation (Stage D+E). Results are cached in `kv_cache`.

**Request:**
```json
{
  "session_id": 1,
  "option_id": "opt_1"
}
```

**Response:**
```json
{
  "session_id": 1,
  "option_id": "opt_1",
  "preview_ready": true
}
```

Returns instantly from cache on subsequent calls (30-min TTL). Does not create project versions or change session state.

### GET `/exploration/preview_option/{session_id}/{option_id}`

Serve the cached AI-customized preview HTML. Returns `text/html` with an injected `window.onerror` handler that posts runtime errors to the parent frame via `postMessage`.

### POST `/exploration/fix_preview`

Fix runtime errors in cached AI preview code. AI receives the current code + errors and returns a corrected version.

**Request:**
```json
{
  "session_id": 1,
  "option_id": "opt_1",
  "errors": [
    { "message": "can't access property 'now', this.time is undefined", "line": 231, "col": 33, "stack": "..." }
  ]
}
```

**Response:**
```json
{
  "session_id": 1,
  "option_id": "opt_1",
  "fixed": true
}
```

Returns 400 if max fix attempts (2) exceeded.

### GET `/exploration/state/{session_id}`

Query current session state.

### GET `/exploration/memory_notes`

List all memory notes for this project.

### GET `/exploration/preview/{template_id}`

Returns raw template HTML content for iframe preview. Used as a placeholder while AI preview generates.

### GET `/api/v1/debug/openai_log`

Returns all recent OpenAI call debug entries (max 50, ring buffer). Each entry includes:
- `label`: Stage identifier (e.g. "A:decompose(fresh)", "A:decompose(contextual)", "B:branches", "C:mapper", "D:customize", "iterate")
- `timestamp`, `duration_ms`: Timing
- `model`: OpenAI model used
- `messages`: System + user messages sent (for tool-enabled calls, includes tool call/response messages)
- `tool_calls`: Array of tool invocations (present for Stage A and B), each with `id`, `function` name, `arguments`
- `raw_response`: Raw text from OpenAI (final response after tool calls)
- `parsed`: Parsed JSON result
- `usage`: Token counts (prompt, completion, total) — from the final round
- `error`: Error message if call failed

### DELETE `/api/v1/debug/openai_log`

Clear the debug log.

---

## Database Schema

Migrations: `b2c3d4e5f6g7_add_exploration_tables.py`, `c3d4e5f6g7h8_add_kv_cache_table.py`

### exploration_sessions

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` PK | Auto-increment |
| `project_id` | `UUID` FK→projects.id | CASCADE delete |
| `user_input` | `TEXT` | Original game description |
| `ambiguity_json` | `JSONB` | Stage A decomposition (ambiguous dimensions only, count varies; contextual mode adds locked) |
| `state` | `VARCHAR(30)` | State machine value, default `explore_options` |
| `selected_option_id` | `VARCHAR(100)` | Chosen option_id |
| `hypothesis_ledger` | `JSONB` | `{validated[], rejected[], open_questions[]}` |
| `iteration_count` | `INTEGER` | Default 0 |
| `created_at` | `TIMESTAMPTZ` | Auto |
| `updated_at` | `TIMESTAMPTZ` | Auto, updates on change |

### exploration_options

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` PK | Auto-increment |
| `session_id` | `INTEGER` FK→exploration_sessions.id | CASCADE delete |
| `option_id` | `VARCHAR(100)` | e.g. `opt_1` |
| `title` | `VARCHAR(255)` | Display name |
| `core_loop` | `TEXT` | Gameplay description |
| `controls` | `VARCHAR(255)` | Input method |
| `mechanics` | `JSONB` | Array of mechanics strings |
| `template_id` | `VARCHAR(100)` | References phaser_demos catalog |
| `complexity` | `VARCHAR(20)` | `low` / `medium` / `high` |
| `mobile_fit` | `VARCHAR(20)` | `good` / `fair` / `poor` |
| `assumptions_to_validate` | `JSONB` | Array of strings |
| `is_recommended` | `BOOLEAN` | Default false |
| `created_at` | `TIMESTAMPTZ` | Auto |

### exploration_memory_notes

Two types of memory notes are written:

| Type | When Written | Confidence | Content |
|---|---|---|---|
| `design_decision` | On select (Stage D) | 0.6 | Decomposition, all options, selected option, constraints |
| (finish-time) | On finish exploration | 0.85 | Preferences, validated/rejected hypotheses, key decisions, pitfalls |

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` PK | Auto-increment |
| `project_id` | `UUID` FK→projects.id | CASCADE delete |
| `content_json` | `JSONB` | Full `MemoryNoteContent` structure; `content_json.type` distinguishes memory types |
| `tags` | `JSONB` | Searchable tags, e.g. `["platform:mobile", "type:design_decision"]` |
| `confidence` | `FLOAT` | 0.0-1.0 (0.6 for design_decision, ~0.85 for finish-time) |
| `source_version_id` | `INTEGER` | The version at write time |
| `source_session_id` | `INTEGER` FK→exploration_sessions.id | SET NULL on delete |
| `created_at` | `TIMESTAMPTZ` | Auto |

### user_preferences

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` PK | Auto-increment |
| `project_id` | `UUID` FK→projects.id | CASCADE delete |
| `preference_json` | `JSONB` | `{platform, input, pace, session_length, difficulty, visual_density}` |
| `updated_at` | `TIMESTAMPTZ` | Auto, updates on change |

### kv_cache

Generic key-value cache table. Currently used for AI preview HTML caching. Reusable for other caching needs.

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` PK | Auto-increment |
| `cache_key` | `VARCHAR(255)` | Unique, indexed. Format: `preview:{session_id}:{option_id}` |
| `value_text` | `TEXT` | Cached content (HTML for previews) |
| `meta_json` | `JSONB` | Optional metadata: `{session_id, option_id, fix_attempts, last_errors}` |
| `expires_at` | `TIMESTAMPTZ` | TTL (30 min for previews). Null = no expiry |
| `created_at` | `TIMESTAMPTZ` | Auto |

---

## Frontend Components

### EditorPage (`pages/EditorPage.tsx`)

Main layout orchestrator. Split into:
- **Left panel**: Preview (switches between `PreviewPanel` and template iframe)
- **Right panel**: Four tabs — Explore, Iterate, Memory, Debug
- **Toolbar**: Version toggle + state badge (color-coded)

State badge colors:
| State | CSS Class | Color |
|---|---|---|
| `explore_options` / `previewing` | `exploring` | Blue |
| `committed` | `committed` | Green |
| `iterating` | `iterating` | Orange |
| `memory_writing` | `writing` | Purple |
| `stable` | `stable` | Teal |

Tab disable logic: **Iterate** tab is disabled until state reaches `committed` or beyond.

### ExplorePanel (`components/exploration/ExplorePanel.tsx`)

The entry point for new explorations.

**Sections:**
1. **Input Area**: Textarea + footer bar (keyboard shortcut hint + "Explore Options" button)
2. **Error Banner**: Shows API errors with dismiss button
3. **Decomposition Display** (after Stage A):
   - Summary text
   - **Already Decided** (contextual mode only): Green tag list of locked decisions
   - **Dimension Grid**: Dimension cards (only ambiguous ones, count varies), each showing:
     - Dimension name (formatted from snake_case)
     - Confidence badge (color-coded: green=high, yellow=med, red=low)
     - Candidate tags
     - Signal quotes
   - **Hard Constraints**: Tag-style display
   - **Open Questions**: Each with dimension, question text, and "why it matters"
4. **Memory Influence Banner**: Shows when past preferences biased option generation
5. **Options Grid**: Renders `OptionCard` for each generated option

### OptionCard (`components/exploration/OptionCard.tsx`)

Displays a single exploration option.

**Elements:**
- Recommended badge (conditional)
- Title + core loop description
- Details grid: Controls, Complexity (color-coded), Mobile Fit (color-coded)
- Mechanics tags
- Assumptions to validate (bulleted list)
- **Preview** button → triggers AI preview (Stage D+E), shows loading state ("Generating..."), switches to "Previewing" when ready. Self-heals runtime errors automatically.
- **Select** button → triggers Stage D+E (AI customization), transitions to `committed`

### IteratePanel (`components/exploration/IteratePanel.tsx`)

Chat-like iteration interface after committing to an option.

**Sections:**
1. **Header**: Version badge (v1, v2...), selected option, "Finish Exploration" button
2. **Hypothesis Ledger**: Three sections — Validated (green), Rejected (red), Open (yellow)
3. **Iteration Log**: Timeline of user requests and system responses with timestamps
4. **Input Area**: Textarea + footer bar (keyboard shortcut hint + "Apply Change" button)

### ExplorationMemoryPanel (`components/exploration/ExplorationMemoryPanel.tsx`)

Displays structured memory notes from completed explorations.

**Each MemoryNoteCard shows:**
- Title + confidence percentage (collapsed)
- Summary, tags (always visible)
- Expanded view: User Preferences grid, Final Choice, Validated/Rejected Hypotheses, Key Decisions, Pitfalls & Guards

### DebugPanel (`components/exploration/DebugPanel.tsx`)

Displays all OpenAI API interactions for debugging.

**Features:**
- Fetches from `GET /api/v1/debug/openai_log`
- Auto-refresh every 3 seconds
- Manual refresh + clear buttons
- Collapsible entries showing: label, model, duration, token counts, timestamp
- Expanded view: system prompt, user message, raw response, parsed JSON, usage breakdown, errors

### Zustand Store (exploration slice)

```typescript
// State
explorationState: ExplorationState     // 'idle' | 'explore_options' | ...
sessionId: number | null               // active session
explorationOptions: ExplorationOption[] // generated options
selectedOptionId: string | null         // chosen option
previewingTemplateId: string | null     // template in iframe
previewingOptionId: string | null       // option being AI-previewed
isPreviewLoading: boolean              // AI preview generation in progress
previewError: string | null            // preview error message
previewFixAttempts: number             // self-healing fix attempt count
hypothesisLedger: HypothesisLedger | null
iterationCount: number
memoryNotes: MemoryNote[]
ambiguity: Ambiguity | null            // Stage A decomposition
memoryInfluence: MemoryInfluence | null
isExploring: boolean                   // loading flag
activeTab: 'explore' | 'iterate' | 'memory' | 'debug'

// Actions
setExplorationState, setSessionId, setExplorationOptions,
setSelectedOptionId, setPreviewingTemplateId, setPreviewingOptionId,
setIsPreviewLoading, setPreviewError, setPreviewFixAttempts,
setHypothesisLedger, setIterationCount, setMemoryNotes,
setAmbiguity, setMemoryInfluence, setIsExploring, setActiveTab,
resetExploration
```

---

## Template Catalog

Six pre-built Phaser 3 game templates in `backend/app/templates/phaser_demos.py`.

These serve as **starting points** for Stage D customization — they are not shown to users as-is (except during raw preview).

| template_id | Title | Core Loop | Complexity | Mobile Fit |
|---|---|---|---|---|
| `platformer_basic` | Classic Platformer | Jump, collect coins, avoid falling | medium | good |
| `shooter_topdown` | Top-Down Shooter | Move, shoot enemies, survive waves | medium | fair |
| `puzzle_match` | Color Match Puzzle | Select adjacent same-color blocks | low | good |
| `runner_endless` | Endless Runner | Single-input jump over obstacles | low | good |
| `clicker_idle` | Idle Clicker | Click to earn, buy upgrades | low | good |
| `defense_tower` | Tower Defense | Place towers, defeat enemy waves | high | fair |

### Template Properties

Each template entry contains:
- `template_id`: Unique identifier used in API and Stage C mapping
- `title`, `core_loop`, `controls`: Descriptive metadata (fed to Stage C for matching)
- `mechanics`: Array of gameplay mechanics
- `complexity`: `low` / `medium` / `high`
- `mobile_fit`: `good` / `fair` / `poor`
- `tags`: Categorization
- `files`: Array of `{file_path, file_type, content}` — complete HTML files (fed to Stage D for customization)

### Template Constraints

- All use **Phaser 3.60** from CDN
- **No external assets** — all graphics rendered with Phaser primitives (rectangles, circles, text)
- Each template is a single `index.html` file
- Mobile-friendly with touch controls and `Scale.FIT`
- Complete game loops with win/lose conditions

---

## Data Structures

### Decomposition — Fresh Mode (Stage A output)

```json
{
  "summary": "A fast-paced mobile runner with tap-to-jump controls",
  "dimensions": {
    "controls": {
      "candidates": ["touch_tap", "single_key"],
      "confidence": "high",
      "signals": ["tap to jump"]
    },
    "presentation": {
      "candidates": ["side_scroller", "minimal_2d"],
      "confidence": "med",
      "signals": ["jump over implies side view"]
    },
    "core_loop": { "candidates": ["run_avoid"], "confidence": "high", "signals": ["jump over obstacles"] },
    "goals": { "candidates": ["high_score", "endless_survival"], "confidence": "low", "signals": [] },
    "progression": { "candidates": ["infinite"], "confidence": "med", "signals": [] },
    "systems": { "candidates": ["physics", "collision", "spawner"], "confidence": "med", "signals": [] },
    "platform": { "candidates": ["mobile"], "confidence": "high", "signals": ["mobile game"] },
    "tone": { "candidates": ["exciting"], "confidence": "med", "signals": ["fast-paced"] }
  },
  "hard_constraints": ["must be mobile", "must use tap controls"],
  "open_questions": [
    {
      "dimension": "goals",
      "question": "Should the game be endless or have levels?",
      "why_it_matters": "Affects replay value and difficulty curve"
    }
  ]
}
```

### Decomposition — Contextual Mode (Stage A output)

```json
{
  "summary": "Add power-ups and a boss fight to the existing endless runner",
  "locked": {
    "description": "things already decided that should NOT change",
    "items": [
      "controls: touch_tap",
      "presentation: side_scroller",
      "core_loop: run_avoid (tap to jump over obstacles)",
      "platform: mobile",
      "tone: exciting"
    ]
  },
  "dimensions": {
    "power_up_types": {
      "candidates": ["speed_boost", "shield", "magnet", "double_score"],
      "confidence": "low",
      "signals": ["user said power-ups but didn't specify types"]
    },
    "power_up_spawn": {
      "candidates": ["random_interval", "fixed_positions", "after_milestones"],
      "confidence": "low",
      "signals": []
    },
    "boss_attack_pattern": {
      "candidates": ["projectile_barrage", "charge_dash", "area_denial"],
      "confidence": "low",
      "signals": ["boss fight implies combat"]
    },
    "boss_frequency": {
      "candidates": ["every_500_points", "every_60_seconds", "after_3_waves"],
      "confidence": "low",
      "signals": []
    },
    "difficulty_scaling": {
      "candidates": ["faster_speed", "more_obstacles", "stronger_bosses"],
      "confidence": "med",
      "signals": ["existing game already has speed increase"]
    }
  },
  "hard_constraints": ["must keep existing tap-to-jump controls"],
  "open_questions": [
    {
      "dimension": "boss_attack_pattern",
      "question": "Should the boss block the runner path or attack from a distance?",
      "why_it_matters": "Affects whether boss fights interrupt the core running loop"
    }
  ]
}
```

### Branch (Stage B output)

```json
{
  "branch_id": "B1",
  "name": "Neon Dash Runner",
  "picked": {
    "controls": "single_key",
    "presentation": "side_scroller",
    "core_loop": "tap to jump over oncoming obstacles, earn points for distance",
    "goals": "high_score",
    "progression": "infinite",
    "systems": ["physics", "collision", "spawner"],
    "platform": "mobile",
    "tone": "exciting"
  },
  "why_this_branch": ["Classic runner feel, simple single-input"],
  "risks": ["May feel repetitive without variety"],
  "what_to_validate": ["Is tap timing satisfying?"]
}
```

### HypothesisLedger

```json
{
  "validated": ["Tap controls are responsive", "Coin sound effect improves satisfaction"],
  "rejected": ["Virtual joystick felt clunky"],
  "open_questions": ["Should we add a timer?", "Is double-jump too powerful?"]
}
```

### MemoryNoteContent

```json
{
  "title": "Mobile Runner Exploration",
  "summary": "Explored 4 runner variants. Settled on tap-based endless runner.",
  "user_preferences": {
    "platform": "mobile",
    "input": "tap",
    "pace": "fast",
    "session_length": "short",
    "difficulty": "progressive",
    "visual_density": "moderate"
  },
  "final_choice": {
    "option_id": "opt_1",
    "why": "Best mobile UX with tap controls"
  },
  "validated_hypotheses": ["Tap controls work well for runners"],
  "rejected_hypotheses": ["Swipe-to-jump is unintuitive"],
  "key_decisions": [
    {
      "decision": "Use single tap instead of swipe",
      "reason": "Lower latency and simpler mental model",
      "evidence": "User chose tap-based option over swipe variant"
    }
  ],
  "pitfalls_and_guards": [
    "Avoid small tap targets (min 44px)",
    "Endless games need visual variety to stay engaging"
  ],
  "refs": {
    "exploration_session_id": 3,
    "stable_version_id": 12
  },
  "confidence": 0.85
}
```

### DesignDecisionMemory (written on select, `type: "design_decision"`)

```json
{
  "title": "Design Decision: Neon Dash Runner",
  "summary": "User requested: \"fast mobile runner\". Decomposed into 3 dimensions. Selected \"Neon Dash Runner\" from 4 options.",
  "type": "design_decision",
  "user_input": "I want a fast mobile runner game",
  "decomposition_summary": "A fast-paced mobile runner with tap controls",
  "dimensions": ["controls", "presentation", "tone"],
  "hard_constraints": ["must be mobile", "must use tap controls"],
  "locked": null,
  "options_considered": [
    { "option_id": "opt_1", "title": "Neon Dash Runner", "core_loop": "tap to jump", "controls": "single tap", "is_recommended": true },
    { "option_id": "opt_2", "title": "Sky Bounce", "core_loop": "tap to fly", "controls": "hold to rise", "is_recommended": false }
  ],
  "selected_option": {
    "option_id": "opt_1",
    "title": "Neon Dash Runner",
    "core_loop": "tap to jump over obstacles",
    "controls": "single tap",
    "mechanics": ["jumping", "obstacles", "scoring"],
    "complexity": "low",
    "mobile_fit": "good",
    "assumptions_to_validate": ["Tap timing feels responsive"]
  },
  "user_preferences": {},
  "final_choice": { "option_id": "opt_1", "why": "Recommended by system" },
  "validated_hypotheses": [],
  "rejected_hypotheses": [],
  "key_decisions": [
    {
      "decision": "Selected Neon Dash Runner",
      "reason": "Core loop: tap to jump over obstacles",
      "evidence": "Controls: single tap, Complexity: low"
    }
  ],
  "pitfalls_and_guards": [],
  "refs": { "exploration_session_id": 1, "stable_version_id": 5 },
  "confidence": 0.6
}
```

### MemoryInfluence (returned during explore)

```json
{
  "relevant_preferences": { "platform": "mobile", "input": "tap", "pace": "fast" },
  "recurring_patterns": ["User prefers tap controls", "Fast-paced games chosen 3/4 times"],
  "warnings": ["Avoid complex multi-touch", "Timer games rejected twice"],
  "suggested_direction_bias": { "input": "tap", "pace": "fast" }
}
```

---

## Memory System

The exploration system has a **dual-layer memory architecture** and a **dynamic recall mechanism** via OpenAI function calling.

### Memory Layers

```
┌─────────────────────────────────────────────────────────┐
│                    Memory Sources                        │
│                                                          │
│  Layer 1: Design Decision (on select)                   │
│  ├── confidence: 0.6                                    │
│  ├── type: "design_decision"                            │
│  ├── Written immediately when user selects an option    │
│  ├── Contains: decomposition, all options, selected     │
│  │   option, constraints, locked context                │
│  └── Purpose: capture decisions even if user never      │
│      finishes exploration                               │
│                                                          │
│  Layer 2: Exploration Finish (on finish)                │
│  ├── confidence: 0.85                                   │
│  ├── type: (none — legacy format)                       │
│  ├── Written by AI memory writer at finish time         │
│  ├── Contains: preferences, validated/rejected          │
│  │   hypotheses, key decisions, pitfalls                │
│  └── Purpose: high-confidence, AI-synthesized lessons   │
│                                                          │
│  User Preferences (upsert on finish)                    │
│  └── Aggregated preferences: platform, input, pace,     │
│      session_length, difficulty, visual_density          │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    Memory Consumers                      │
│                                                          │
│  1. search_memory tool (dynamic, Stage A+B)             │
│     AI can query memories during decomposition and      │
│     branch synthesis via OpenAI function calling.       │
│     Keyword matching, filter by type, up to 3 rounds.   │
│                                                          │
│  2. get_memory_context() (static, Stage B)              │
│     Pre-fetches latest 5 notes + user preferences.      │
│     Passed as {memory_context} in Stage B prompt.       │
│     Extracts: recurring_patterns, warnings,             │
│     suggested_direction_bias.                            │
│                                                          │
│  3. ExplorationMemoryPanel (frontend)                    │
│     Displays all memory notes to the user.               │
└─────────────────────────────────────────────────────────┘
```

### search_memory Tool Flow

When Stage A or B is called via `_call_openai_with_tools()`:

1. OpenAI receives the system prompt (which mentions the tool is available) + the user message
2. If the AI decides prior context would help, it calls `search_memory` with a query
3. `_search_memory_for_tool()` queries the DB: latest 20 memory notes + user preferences
4. Results are keyword-matched and formatted as text, returned as a tool response
5. OpenAI processes the memory context and produces its JSON output
6. Loop repeats up to 3 rounds if the AI makes additional tool calls

Example: Fresh decomposition for "a mobile puzzle game"
```
AI → search_memory(query="puzzle game mobile", filter_type="all")
DB → Returns: design_decision for a previous puzzle game,
     user preferences (platform: mobile, input: tap)
AI → Uses this context to produce dimensions that avoid
     previously rejected approaches
```

---

## Design Principles

1. **4-stage pipeline, not chat.** The system never asks clarifying questions. It decomposes → branches → maps → customizes in a single flow.

2. **Decomposition adapts to context and ambiguity.** Dimension count is driven by actual ambiguity — a specific request may produce 1 dimension, a vague one may produce 8+. Fresh explorations use reference dimensions as a guide; re-explorations on existing games generate specific, actionable dimensions (e.g. `power_up_types`, `boss_frequency`) while locking already-decided choices. Clear decisions become `hard_constraints`, not dimensions.

3. **AI customizes code, not just selects templates.** Stage D rewrites the template to match the specific game design. Users see their game idea, not a generic demo.

4. **Branches must be meaningfully different.** Not parameter variations — branches differ on at least 2 dimensions. In contextual mode, branches explore the new design space while respecting locked constraints.

5. **Memory biases, never blocks.** Past preferences influence branch synthesis (Stage B) both statically (pre-fetched context) and dynamically (search_memory tool calls), but all branches remain available.

6. **Iterations are versioned and rollbackable.** Every `iterate` and `select_option` call creates a new `ProjectVersion`. No destructive edits.

7. **Dual-layer memory with progressive confidence.** Design decisions are captured immediately on select (confidence 0.6) to prevent information loss. Comprehensive, AI-synthesized conclusions are written at finish time (confidence 0.85). Both layers are queryable by the `search_memory` tool.

8. **Memory stores conclusions, not chat.** No raw conversation is persisted. Only structured, validated knowledge enters memory.

9. **Single-file templates.** Each Phaser game is a self-contained HTML file with no external dependencies beyond the Phaser CDN.

10. **Every AI call is observable.** All OpenAI interactions are logged to an in-memory ring buffer (max 50 entries) and visible in the Debug tab with full request/response details. Tool-enabled calls (Stage A, B) also log `tool_calls` with function name and arguments.

11. **Hypothesis tracking is lightweight.** The ledger accumulates user requests as `open_questions`. Validated/rejected status is determined at memory-writing time by AI.
