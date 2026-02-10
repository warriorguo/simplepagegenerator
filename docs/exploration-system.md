# Phaser 2D WebGame Option-First Exploration System

> AI-driven game prototyping system that generates runnable Phaser 3 candidates instead of asking clarifying questions.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [AI Pipeline (4 Stages)](#ai-pipeline-4-stages)
- [State Machine](#state-machine)
- [Core Flow](#core-flow)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Frontend Components](#frontend-components)
- [Template Catalog](#template-catalog)
- [Data Structures](#data-structures)
- [Design Principles](#design-principles)

---

## Overview

The Exploration System is the core interaction model for SimplePageGenerator's game prototyping workflow. Rather than asking users clarifying questions about their game idea, the system **decomposes requirements into 8 implementation dimensions**, **synthesizes divergent design branches**, **maps branches to runnable Phaser 3 templates**, and **customizes the code with AI** to produce a playable prototype matching the user's intent. All conclusions are captured as **structured memory** that biases future explorations.

### Key Characteristics

- **Option-First**: No clarifying questions. Ambiguity is decomposed internally and explored through concrete, playable options.
- **4-Stage AI Pipeline**: Decompose → Branch → Map → Customize. Each stage has a dedicated prompt and debug logging.
- **AI-Customized Code**: Selecting an option doesn't just copy a preset demo — the template is rewritten by AI to match the specific game design.
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
│  ├── GET  /exploration/state/{session_id}            │
│  ├── GET  /exploration/memory_notes                  │
│  └── GET  /exploration/preview/{template_id}         │
│                                                      │
│  Debug Router: /api/v1/debug/...                     │
│  ├── GET  /openai_log                                │
│  └── DELETE /openai_log                              │
│                                                      │
│  Service: exploration_service.py                     │
│  ├── Stage A: decompose_requirements()  ←── OpenAI   │
│  ├── Stage B: synthesize_branches()     ←── OpenAI   │
│  ├── Stage C: map_demos()               ←── OpenAI   │
│  ├── Stage D: customize_template()      ←── OpenAI   │
│  ├── iterate()                          ←── OpenAI   │
│  └── finish_exploration()               ←── OpenAI   │
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
│  └── user_preferences                                │
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
│   └── b2c3d4e5f6g7_add_exploration_tables.py

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

## AI Pipeline (4 Stages)

The explore flow chains four AI stages, each with a dedicated system prompt. Every OpenAI call is logged to an in-memory ring buffer (`deque(maxlen=50)`) accessible via the Debug tab.

```
User Input
    │
    ▼
┌───────────────────────────┐
│ Stage A: Decomposer       │  decompose_requirements()
│ User text → 8 dimensions  │  Label: "A:decompose"
│ + hard constraints        │  max_tokens: 4000
│ + open questions          │
└─────────┬─────────────────┘
          │ dimensions JSON
          ▼
┌───────────────────────────┐
│ Stage B: Branch Synth     │  synthesize_branches()
│ Dimensions + memory       │  Label: "B:branches"
│ → 3-6 divergent branches  │  max_tokens: 4000
└─────────┬─────────────────┘
          │ branches JSON
          ▼
┌───────────────────────────┐
│ Stage C: Demo Mapper      │  map_demos()
│ Branches + template       │  Label: "C:mapper"
│ catalog → option cards    │  max_tokens: 4000
└─────────┬─────────────────┘
          │ options JSON
          ▼
      (User selects)
          │
          ▼
┌───────────────────────────┐
│ Stage D: Code Customizer  │  customize_template()
│ Template code + option    │  Label: "D:customize"
│ spec → customized game    │  max_tokens: 8000
└───────────────────────────┘
```

### Stage A: Requirement Decomposer

**Prompt**: `STAGE_A_DECOMPOSER_PROMPT`
**Input**: User's free-text game description
**Output**: JSON with `summary`, `dimensions`, `hard_constraints`, `open_questions`

Decomposes the user's request into **8 implementation dimensions**:

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

Each dimension contains:
- **candidates**: 1-4 possible values (more = more ambiguity)
- **confidence**: `high` | `med` | `low` — how certain the AI is based on user text
- **signals**: Direct quotes or inferences from the user's text

Also extracts:
- **hard_constraints**: Things the user explicitly required or excluded
- **open_questions**: Ambiguities worth investigating, with `dimension`, `question`, `why_it_matters`

### Stage B: Branch Synthesizer

**Prompt**: `STAGE_B_BRANCH_PROMPT`
**Input**: Dimensions JSON + memory context (past preferences)
**Output**: 3-6 divergent design branches

Each branch is one **internally-consistent set of choices** across all 8 dimensions. Branches must differ on at least 2 major dimensions (controls / presentation / core_loop).

If memory context shows user preferences, one branch is aligned with those preferences.

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

### Stage D: Code Customizer

**Prompt**: `STAGE_D_CUSTOMIZER_PROMPT`
**Input**: Template source code + option spec (title, core_loop, controls, mechanics, complexity, mobile_fit) + user's original request
**Output**: JSON mapping file_path to customized file content

This stage runs when the user **selects** an option. Instead of copying the template verbatim, the AI rewrites the game code to:
- Match the described core loop and controls
- Implement the specified mechanics
- Update title, colors, and gameplay behavior
- Maintain mobile support (touch controls, Scale.FIT)
- Use only Phaser primitives (no external assets)

Uses `max_tokens: 8000` to accommodate full game code output.

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
                             │ user previews template
                 ┌───────────▼────────────┐
                 │      previewing        │  iframe shows raw template
                 └───────────┬────────────┘
                             │ POST /select_option (Stage D)
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
| `previewing` | User viewing raw template in iframe (frontend-only) | — | Select, Preview another |
| `committed` | User selected an option, AI-customized code saved | D ran | Iterate, Finish |
| `iterating` | User modifying game through iterations | Iterate prompt | Iterate more, Finish |
| `memory_writing` | AI synthesizing session into memory (transient) | Memory writer | Wait |
| `stable` | Exploration complete, memory saved | — | Start new exploration |

---

## Core Flow

### 1. Explore: Decompose → Branch → Map

User describes a game idea. The system runs Stages A → B → C:

```
User: "I want a fast mobile game where you tap to jump over things"
                    │
         ┌──────────▼───────────┐
         │ Stage A: Decomposer  │
         │ 8 dimensions:        │
         │  controls: single_key│ (high, "tap to jump")
         │  presentation: side  │ (med)
         │  core_loop: run_avoid│ (high, "jump over things")
         │  platform: mobile    │ (high, "mobile game")
         │  tone: exciting      │ (med, "fast")
         │  ...                 │
         │ hard_constraints:    │
         │  ["must be mobile"]  │
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

### 2. Preview & Select (with AI Customization)

- User clicks **Preview** on an option → iframe loads the raw template HTML via `GET /exploration/preview/{template_id}`
- User clicks **Select** → triggers **Stage D: Code Customizer**:
  1. Template files are loaded
  2. Option spec (title, core_loop, controls, mechanics) is read from DB
  3. AI rewrites the template code to match the specific game design
  4. Customized code is saved as a new `ProjectVersion`
- Preview refreshes to show the **customized game**, not the generic template
- State transitions to `committed`

### 3. Iterate

User requests code modifications in natural language:

1. Current version's files are loaded
2. GPT receives the code + user request and returns modified files (`max_tokens: 8000`)
3. A new `ProjectVersion` is created (immutable versioning)
4. The user request is appended to `hypothesis_ledger.open_questions`
5. Preview refreshes automatically

### 4. Finish & Write Memory

When the user clicks "Finish Exploration":

1. GPT receives the full session data (user input, selected option, iterations, hypothesis ledger, decomposition)
2. Generates a **structured memory** with: preferences, validated/rejected hypotheses, key decisions, pitfalls
3. Saves `ExplorationMemoryNote` to database
4. Updates `UserPreference` record (upsert)
5. State transitions to `stable`

The memory then influences Stage B (branch synthesis) in all future explorations for this project.

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

### GET `/exploration/state/{session_id}`

Query current session state.

### GET `/exploration/memory_notes`

List all memory notes for this project.

### GET `/exploration/preview/{template_id}`

Returns raw HTML content for iframe preview. Used during the `previewing` state (before selection). Returns `text/html`.

### GET `/api/v1/debug/openai_log`

Returns all recent OpenAI call debug entries (max 50, ring buffer). Each entry includes:
- `label`: Stage identifier (e.g. "A:decompose", "B:branches", "C:mapper", "D:customize", "iterate")
- `timestamp`, `duration_ms`: Timing
- `model`: OpenAI model used
- `messages`: System + user messages sent
- `raw_response`: Raw text from OpenAI
- `parsed`: Parsed JSON result
- `usage`: Token counts (prompt, completion, total)
- `error`: Error message if call failed

### DELETE `/api/v1/debug/openai_log`

Clear the debug log.

---

## Database Schema

Migration: `b2c3d4e5f6g7_add_exploration_tables.py`

### exploration_sessions

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` PK | Auto-increment |
| `project_id` | `UUID` FK→projects.id | CASCADE delete |
| `user_input` | `TEXT` | Original game description |
| `ambiguity_json` | `JSONB` | Stage A decomposition (8 dimensions + constraints + open questions) |
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

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` PK | Auto-increment |
| `project_id` | `UUID` FK→projects.id | CASCADE delete |
| `content_json` | `JSONB` | Full `MemoryNoteContent` structure |
| `tags` | `JSONB` | Searchable tags, e.g. `["platform:mobile"]` |
| `confidence` | `FLOAT` | 0.0-1.0, default 0.8 |
| `source_version_id` | `INTEGER` | The stable version at finish time |
| `source_session_id` | `INTEGER` FK→exploration_sessions.id | SET NULL on delete |
| `created_at` | `TIMESTAMPTZ` | Auto |

### user_preferences

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` PK | Auto-increment |
| `project_id` | `UUID` FK→projects.id | CASCADE delete |
| `preference_json` | `JSONB` | `{platform, input, pace, session_length, difficulty, visual_density}` |
| `updated_at` | `TIMESTAMPTZ` | Auto, updates on change |

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
   - **Dimension Grid**: 8 dimension cards, each showing:
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
- **Preview** button → shows raw template in iframe (pre-customization preview)
- **Select** button → triggers Stage D (AI customization), transitions to `committed`

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
hypothesisLedger: HypothesisLedger | null
iterationCount: number
memoryNotes: MemoryNote[]
ambiguity: Ambiguity | null            // Stage A decomposition
memoryInfluence: MemoryInfluence | null
isExploring: boolean                   // loading flag
activeTab: 'explore' | 'iterate' | 'memory' | 'debug'

// Actions
setExplorationState, setSessionId, setExplorationOptions,
setSelectedOptionId, setPreviewingTemplateId, setHypothesisLedger,
setIterationCount, setMemoryNotes, setAmbiguity, setMemoryInfluence,
setIsExploring, setActiveTab, resetExploration
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

### Decomposition (Stage A output)

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

## Design Principles

1. **4-stage pipeline, not chat.** The system never asks clarifying questions. It decomposes → branches → maps → customizes in a single flow.

2. **AI customizes code, not just selects templates.** Stage D rewrites the template to match the specific game design. Users see their game idea, not a generic demo.

3. **Branches must be meaningfully different.** Not parameter variations — branches differ on at least 2 major dimensions (controls, presentation, core_loop).

4. **Memory biases, never blocks.** Past preferences influence branch synthesis (Stage B), but all branches remain available.

5. **Iterations are versioned and rollbackable.** Every `iterate` and `select_option` call creates a new `ProjectVersion`. No destructive edits.

6. **Memory stores conclusions, not chat.** No raw conversation is persisted. Only structured, validated knowledge enters memory.

7. **Single-file templates.** Each Phaser game is a self-contained HTML file with no external dependencies beyond the Phaser CDN.

8. **Every AI call is observable.** All OpenAI interactions are logged to an in-memory ring buffer (max 50 entries) and visible in the Debug tab with full request/response details.

9. **Hypothesis tracking is lightweight.** The ledger accumulates user requests as `open_questions`. Validated/rejected status is determined at memory-writing time by AI.
