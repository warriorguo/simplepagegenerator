# Phaser 2D WebGame Option-First Exploration System

> AI-driven game prototyping system that generates runnable Phaser 3 candidates instead of asking clarifying questions.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [State Machine](#state-machine)
- [Core Flow](#core-flow)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Frontend Components](#frontend-components)
- [Template Catalog](#template-catalog)
- [AI Prompts](#ai-prompts)
- [Data Structures](#data-structures)
- [Design Principles](#design-principles)

---

## Overview

The Exploration System is the core interaction model for SimplePageGenerator's game prototyping workflow. Rather than asking users clarifying questions about their game idea, the system **decomposes ambiguity** and **generates 3-6 runnable Phaser 3 candidates** that users can preview, select, and iteratively refine. All conclusions are captured as **structured memory** that biases future explorations.

### Key Characteristics

- **Option-First**: No clarifying questions. Ambiguity is decomposed internally and explored through concrete, playable options.
- **Closed-Loop Memory**: Each exploration session produces structured conclusions that influence future sessions.
- **Template-Based**: Options are mapped to pre-built Phaser 3 templates (fully self-contained HTML, no external assets).
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
│      ├── ExplorePanel  → OptionCard[]                │
│      ├── IteratePanel  → HypothesisLedger            │
│      └── ExplorationMemoryPanel → MemoryNoteCard[]   │
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
│  Service: exploration_service.py                     │
│  ├── decompose_ambiguity()  ←── OpenAI GPT           │
│  ├── generate_options()     ←── OpenAI GPT           │
│  ├── iterate()              ←── OpenAI GPT           │
│  └── finish_exploration()   ←── OpenAI GPT           │
│                                                      │
│  Templates: phaser_demos.py (6 game templates)       │
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
│   ├── services/exploration_service.py # Business logic + AI orchestration
│   ├── routers/exploration.py         # FastAPI endpoints
│   └── templates/phaser_demos.py      # 6 Phaser 3 game templates
├── alembic/versions/
│   └── b2c3d4e5f6g7_add_exploration_tables.py

frontend/src/
├── types/exploration.ts               # TypeScript interfaces
├── api/exploration.ts                 # API client functions
├── store/index.ts                     # Zustand store (exploration slice)
├── components/exploration/
│   ├── ExplorePanel.tsx               # Input + ambiguity + options grid
│   ├── OptionCard.tsx                 # Single option card
│   ├── IteratePanel.tsx               # Iteration chat + hypothesis ledger
│   └── ExplorationMemoryPanel.tsx     # Memory notes viewer
├── pages/EditorPage.tsx               # Main page with tabs + preview
└── styles/exploration.css             # All exploration styles
```

---

## State Machine

The exploration lifecycle follows a strict state machine:

```
                 ┌────────────────────────┐
                 │         idle           │  (initial state)
                 └───────────┬────────────┘
                             │ POST /explore
                 ┌───────────▼────────────┐
                 │    explore_options      │  AI generates 3-6 options
                 └───────────┬────────────┘
                             │ user previews template
                 ┌───────────▼────────────┐
                 │      previewing        │  iframe shows template
                 └───────────┬────────────┘
                             │ POST /select_option
                 ┌───────────▼────────────┐
                 │      committed         │  template imported as ProjectVersion
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

| State | Description | Allowed Actions |
|---|---|---|
| `idle` | No active exploration | Start new exploration |
| `explore_options` | AI generated options, user is reviewing | Preview, Select |
| `previewing` | User is viewing a template in iframe (frontend-only) | Select, Preview another |
| `committed` | User selected an option, template imported | Iterate, Finish |
| `iterating` | User is modifying the game through iterations | Iterate more, Finish |
| `memory_writing` | AI is synthesizing session into memory (transient) | Wait |
| `stable` | Exploration complete, memory saved | Start new exploration |

---

## Core Flow

### 1. Explore: Generate Options

User describes a game idea. The system:

1. **Decomposes ambiguity** into 7 dimensions via GPT:
   - `gameplay_type`, `control_method`, `pace`, `goal_structure`, `difficulty`, `visual_complexity`, `platform`
2. **Retrieves memory context** from past explorations (last 5 notes + user preferences)
3. **Generates 3-6 options** via GPT, each mapped to a Phaser template
4. **Persists** session and options to database

```
User: "I want a fun mobile game"
                    │
         ┌──────────▼──────────┐
         │ Ambiguity Decompose │
         │ gameplay: [runner,   │
         │   clicker, puzzle]   │
         │ pace: [fast, idle]   │
         │ platform: [mobile]   │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │  Memory Retrieval   │
         │ "user prefers tap   │
         │  controls, fast     │
         │  pace games"        │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │  Generate Options   │
         │ opt_1: Endless Run  │
         │ opt_2: Tap Puzzle   │ ← recommended (matches memory)
         │ opt_3: Idle Clicker │
         └─────────────────────┘
```

### 2. Preview & Select

- User clicks **Preview** on an option → iframe loads the template HTML via `GET /exploration/preview/{template_id}`
- User clicks **Select** → template files are imported as a new `ProjectVersion`
- Hypothesis ledger is initialized with empty arrays
- State transitions to `committed`

### 3. Iterate

User requests code modifications in natural language:

1. Current version's files are loaded
2. GPT receives the code + user request and returns modified files
3. A new `ProjectVersion` is created (immutable versioning)
4. The user request is appended to `hypothesis_ledger.open_questions`
5. Preview refreshes automatically

### 4. Finish & Write Memory

When the user clicks "Finish Exploration":

1. GPT receives the full session data (user input, selected option, iterations, hypothesis ledger)
2. Generates a **structured memory** with: preferences, validated/rejected hypotheses, key decisions, pitfalls
3. Saves `ExplorationMemoryNote` to database
4. Updates `UserPreference` record (upsert)
5. State transitions to `stable`

The memory then influences all future explorations for this project.

---

## API Reference

All endpoints are under `/api/v1/projects/{project_id}`.

### POST `/explore`

Start a new exploration session.

**Request:**
```json
{
  "user_input": "I want a fast-paced mobile platformer with coins"
}
```

**Response:**
```json
{
  "session_id": 1,
  "ambiguity": {
    "gameplay_type": {
      "candidates": ["platformer","shooter","puzzle","runner","clicker","tower_defense"],
      "detected": ["platformer"]
    },
    "control_method": {
      "candidates": ["keyboard","touch_tap","touch_swipe","mouse_click","auto"],
      "detected": ["touch_tap"]
    },
    "pace": { "candidates": [...], "detected": ["fast"] },
    "goal_structure": { "candidates": [...], "detected": ["level_clear","high_score"] },
    "difficulty": { "candidates": [...], "detected": ["progressive"] },
    "visual_complexity": { "candidates": [...], "detected": ["moderate"] },
    "platform": { "candidates": [...], "detected": ["mobile"] }
  },
  "options": [
    {
      "option_id": "opt_1",
      "title": "Coin Rush Platformer",
      "core_loop": "Jump across platforms collecting coins before time runs out",
      "controls": "Tap left/right to move, tap up to jump",
      "mechanics": ["jumping", "collecting", "timer"],
      "engine": "Phaser",
      "template_id": "platformer_basic",
      "complexity": "medium",
      "mobile_fit": "good",
      "assumptions_to_validate": ["Touch controls feel responsive", "Timer adds urgency"],
      "is_recommended": true
    }
  ],
  "memory_influence": {
    "relevant_preferences": { "platform": "mobile", "pace": "fast" },
    "recurring_patterns": ["User prefers tap controls"],
    "warnings": ["Avoid complex multi-touch"],
    "suggested_direction_bias": { "input": "tap", "pace": "fast" }
  }
}
```

### POST `/select_option`

Select an option and import its template.

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

### POST `/iterate`

Apply a code modification.

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
      "title": "Fast Mobile Platformer Exploration",
      "summary": "Explored platformer options for mobile. Settled on tap-based controls with coin collecting.",
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
      "rejected_hypotheses": ["Swipe controls for movement"],
      "key_decisions": [
        {
          "decision": "Use tap instead of virtual joystick",
          "reason": "Simpler and more responsive",
          "evidence": "User preferred tap after trying both"
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

**Response:**
```json
{
  "session_id": 1,
  "state": "iterating",
  "selected_option_id": "opt_1",
  "iteration_count": 2,
  "hypothesis_ledger": {
    "validated": ["Tap controls work well"],
    "rejected": [],
    "open_questions": ["Add double-jump"]
  }
}
```

### GET `/exploration/memory_notes`

List all memory notes for this project.

**Response:** `MemoryNoteResponse[]`

### GET `/exploration/preview/{template_id}`

Returns raw HTML content for iframe preview. Used during the `previewing` state.

**Response:** `text/html` (the template's `index.html`)

---

## Database Schema

Migration: `b2c3d4e5f6g7_add_exploration_tables.py`

### exploration_sessions

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` PK | Auto-increment |
| `project_id` | `UUID` FK→projects.id | CASCADE delete |
| `user_input` | `TEXT` | Original game description |
| `ambiguity_json` | `JSONB` | 7-dimension decomposition |
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
| `confidence` | `FLOAT` | 0.0–1.0, default 0.8 |
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
- **Right panel**: Three tabs — Explore, Iterate, Memory
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
1. **Input**: Textarea + "Explore Options" button (Cmd/Ctrl+Enter shortcut)
2. **Ambiguity Display**: Detected dimensions shown as tags
3. **Memory Influence Banner**: Shows when past preferences biased option generation
4. **Options Grid**: Renders `OptionCard` for each generated option

### OptionCard (`components/exploration/OptionCard.tsx`)

Displays a single exploration option.

**Elements:**
- Recommended badge (conditional)
- Title + core loop description
- Details grid: Controls, Complexity (color-coded), Mobile Fit (color-coded)
- Mechanics tags
- Assumptions to validate (bulleted list)
- **Preview** button → sets `previewing` state, shows template in iframe
- **Select** button → calls `POST /select_option`, transitions to `committed`

### IteratePanel (`components/exploration/IteratePanel.tsx`)

Chat-like iteration interface after committing to an option.

**Sections:**
1. **Header**: Version badge (v1, v2...), selected option, "Finish Exploration" button
2. **Hypothesis Ledger**: Three collapsible lists — Validated (green), Rejected (red), Open (yellow)
3. **Iteration Log**: Timeline of user requests with timestamps
4. **Input**: Textarea + "Apply Change" button (Cmd/Ctrl+Enter shortcut)

### ExplorationMemoryPanel (`components/exploration/ExplorationMemoryPanel.tsx`)

Displays structured memory notes from completed explorations.

**Each MemoryNoteCard shows:**
- Title + confidence percentage (collapsed)
- Summary, tags (always visible)
- Expanded view:
  - User Preferences grid
  - Final Choice (option + reason)
  - Validated Hypotheses
  - Rejected Hypotheses
  - Key Decisions (decision + reason + evidence)
  - Pitfalls & Guards

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
ambiguity: Ambiguity | null
memoryInfluence: MemoryInfluence | null
isExploring: boolean                   // loading flag
activeTab: 'explore' | 'iterate' | 'memory'

// Actions
setExplorationState, setSessionId, setExplorationOptions,
setSelectedOptionId, setPreviewingTemplateId, setHypothesisLedger,
setIterationCount, setMemoryNotes, setAmbiguity, setMemoryInfluence,
setIsExploring, setActiveTab, resetExploration
```

---

## Template Catalog

Six pre-built Phaser 3 game templates in `backend/app/templates/phaser_demos.py`:

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
- `template_id`: Unique identifier used in API
- `title`, `core_loop`, `controls`: Descriptive metadata
- `mechanics`: Array of gameplay mechanics (e.g. `["jumping", "collecting"]`)
- `complexity`: `low` / `medium` / `high`
- `mobile_fit`: `excellent` / `good` / `fair` / `poor`
- `tags`: Categorization for search
- `files`: Array of `{file_path, file_type, content}` — complete HTML files

### Template Constraints

- All use **Phaser 3.60** from CDN (`https://cdn.jsdelivr.net/npm/phaser@3.60.0`)
- **No external assets** — all graphics rendered with Phaser primitives (rectangles, circles, text)
- Each template is a single `index.html` file
- Mobile-friendly with touch controls
- Complete game loops with win/lose conditions

---

## AI Prompts

Four system prompts drive the AI interactions:

### AMBIGUITY_DECOMPOSE_PROMPT

**Input**: User's game description (free text)
**Output**: JSON with 7 dimensions, each containing `candidates[]` and `detected[]`
**Purpose**: Structure the vague input into analyzable dimensions without asking the user

### OPTION_GENERATE_PROMPT

**Input**: Template IDs, memory context, ambiguity analysis, user input
**Output**: JSON array of 3-6 option objects
**Rules**:
- Options must differ significantly (not just parameter tweaks)
- Exactly one `is_recommended: true`
- Memory preferences bias recommendations
- Each option maps to a real template_id

### ITERATE_PROMPT

**Input**: Current file contents (truncated to 3000 chars/file), user's modification request
**Output**: JSON object mapping `file_path → new_content`
**Rules**:
- Minimal changes only
- Maintain Phaser structure
- Keep core game loop intact

### MEMORY_WRITER_PROMPT

**Input**: Full session data (user input, selected option, iterations, hypotheses, ambiguity)
**Output**: Structured `MemoryNoteContent` JSON
**Purpose**: Synthesize session into reusable structured knowledge

---

## Data Structures

### Ambiguity (7 dimensions)

```json
{
  "gameplay_type": { "candidates": ["platformer","shooter","puzzle","runner","clicker","tower_defense"], "detected": ["runner"] },
  "control_method": { "candidates": ["keyboard","touch_tap","touch_swipe","mouse_click","auto"], "detected": ["touch_tap"] },
  "pace": { "candidates": ["fast","medium","slow","idle"], "detected": ["fast"] },
  "goal_structure": { "candidates": ["high_score","level_clear","endless","economy","survival"], "detected": ["endless"] },
  "difficulty": { "candidates": ["easy","medium","hard","progressive"], "detected": ["progressive"] },
  "visual_complexity": { "candidates": ["minimal","moderate","rich"], "detected": ["moderate"] },
  "platform": { "candidates": ["mobile","desktop","both"], "detected": ["mobile"] }
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
  "title": "Mobile Platformer Exploration",
  "summary": "Explored 4 platformer variants. Settled on tap-based coin collector.",
  "user_preferences": {
    "platform": "mobile",
    "input": "tap",
    "pace": "fast",
    "session_length": "short",
    "difficulty": "progressive",
    "visual_density": "moderate"
  },
  "final_choice": {
    "option_id": "opt_2",
    "why": "Best mobile UX with tap controls"
  },
  "validated_hypotheses": ["Tap controls work well for platformers"],
  "rejected_hypotheses": ["Swipe-to-jump is unintuitive"],
  "key_decisions": [
    {
      "decision": "Use discrete tap zones instead of virtual joystick",
      "reason": "Lower latency and simpler mental model",
      "evidence": "User switched from joystick to tap after 1 iteration"
    }
  ],
  "pitfalls_and_guards": [
    "Avoid small tap targets (min 44px)",
    "Timer games can feel stressful on mobile"
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

### Memory Tags

Auto-extracted from memory content:
```json
["platform:mobile", "input:tap", "pace:fast", "chosen:opt_2"]
```

---

## Design Principles

1. **Explore phase never writes project code.** Options are read-only previews of existing templates. Only `select_option` commits code.

2. **Memory stores conclusions, not chat.** No raw conversation is persisted. Only structured, validated knowledge enters memory.

3. **Options must be meaningfully different.** Not parameter variations — different gameplay, input methods, or core loops.

4. **Iterations are versioned and rollbackable.** Every `iterate` call creates a new `ProjectVersion`. No destructive edits.

5. **Memory biases, never blocks.** Past preferences influence the `is_recommended` flag and option ordering, but all options remain available.

6. **Single-file templates.** Each Phaser game is a self-contained HTML file with no external dependencies beyond the Phaser CDN.

7. **Hypothesis tracking is lightweight.** The ledger accumulates user requests as `open_questions`. Validated/rejected status is determined at memory-writing time by AI.
