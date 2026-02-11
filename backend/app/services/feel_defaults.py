"""Feel Defaults — game-type priors and cross-project user feel profile.

Provides two layers of "prior knowledge" for Stage D (Feel Spec Generator):

A) User-level feel profile (cross-project):
   Aggregated from all ExplorationMemoryNote records across all projects.
   Captures: style preference, device/input preferences, likes/dislikes,
   and numerical tuning tendencies from past feel_specs.

B) Game-type default tuning (cross-demo):
   Static baseline feel specs per game archetype, keyed by template_id.
   These are sensible starting points; the AI may deviate but should
   justify why.
"""
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exploration import ExplorationMemoryNote, UserPreference


# ─── Template → Game Type Mapping ─────────────────────────

TEMPLATE_TO_GAME_TYPE: dict[str, str] = {
    "platformer_basic": "platformer",
    "shooter_topdown": "topdown_shooter",
    "puzzle_match": "puzzle",
    "runner_endless": "runner",
    "clicker_idle": "clicker",
    "defense_tower": "tower_defense",
}


# ─── Game-Type Default Tuning ──────────────────────────────

GAME_TYPE_DEFAULTS: dict[str, dict[str, Any]] = {
    "runner": {
        "movement_model": {
            "type": "auto_scroll",
            "scroll_speed": 280,
            "max_speed": 450,
            "speed_increment": 0.3,
            "notes": "Auto-run; speed increases over time for rising tension",
        },
        "jump_model": {
            "enabled": True,
            "coyote_time_ms": 80,
            "jump_buffer_ms": 100,
            "jump_velocity": -520,
            "gravity": 1200,
            "notes": "High gravity for snappy arc; generous coyote + buffer for forgiveness",
        },
        "input": {
            "buffer_ms": 100,
            "mobile_scheme": "tap_zones",
            "touch_zone_min_px": 44,
            "key_map": {"jump": "Space/ArrowUp"},
            "notes": "Single-button game; entire screen is the tap zone",
        },
        "camera": {
            "mode": "fixed",
            "lerp": 0,
            "deadzone": [0, 0],
            "bounds": "none",
            "notes": "Fixed viewport — world scrolls past the player",
        },
        "bounds": {
            "world_bounds": True,
            "entity_clamp": True,
            "world_size": "infinite_scroll",
            "notes": "Player clamped to vertical bounds; obstacles spawn/despawn at edges",
        },
        "visual_feedback": {
            "hit_flash_ms": 100,
            "screen_shake": "light",
            "trail": "subtle",
            "score_popup": True,
            "notes": "Quick death flash + shake; trail for speed feel; score popups for milestones",
        },
        "tuning": {
            "expose_in_debug_hud": True,
            "presets": ["arcade", "tight", "floaty"],
            "default_preset": "arcade",
        },
    },

    "platformer": {
        "movement_model": {
            "type": "accel_drag",
            "accel": 2000,
            "max_speed": 350,
            "drag": 1500,
            "turn_smoothing": 0.0,
            "notes": "Responsive accel with moderate drag; instant direction change",
        },
        "jump_model": {
            "enabled": True,
            "coyote_time_ms": 100,
            "jump_buffer_ms": 120,
            "jump_velocity": -480,
            "gravity": 1000,
            "notes": "Moderate gravity for floatier jumps; generous forgiveness windows",
        },
        "input": {
            "buffer_ms": 100,
            "mobile_scheme": "virtual_buttons",
            "touch_zone_min_px": 48,
            "key_map": {"left": "A/ArrowLeft", "right": "D/ArrowRight", "jump": "Space/W/ArrowUp"},
            "notes": "3-button layout: left, right, jump; large touch targets",
        },
        "camera": {
            "mode": "follow_player",
            "lerp": 0.1,
            "deadzone": [200, 120],
            "bounds": "world",
            "notes": "Smooth follow with deadzone so small movements don't jitter the camera",
        },
        "bounds": {
            "world_bounds": True,
            "entity_clamp": True,
            "world_size": "extended",
            "notes": "World larger than screen; player + enemies clamped to bounds",
        },
        "visual_feedback": {
            "hit_flash_ms": 80,
            "screen_shake": "light",
            "trail": "none",
            "score_popup": True,
            "notes": "Flash on damage; popup on coin collect; no trail for precision feel",
        },
        "tuning": {
            "expose_in_debug_hud": True,
            "presets": ["arcade", "tight", "floaty"],
            "default_preset": "arcade",
        },
    },

    "topdown_shooter": {
        "movement_model": {
            "type": "accel_drag",
            "accel": 1800,
            "max_speed": 300,
            "drag": 1200,
            "turn_smoothing": 0.0,
            "notes": "8-directional movement; drag-based stopping for precise positioning",
        },
        "jump_model": {
            "enabled": False,
            "notes": "No jumping in top-down view",
        },
        "input": {
            "buffer_ms": 80,
            "mobile_scheme": "virtual_buttons",
            "touch_zone_min_px": 44,
            "key_map": {
                "up": "W/ArrowUp", "down": "S/ArrowDown",
                "left": "A/ArrowLeft", "right": "D/ArrowRight",
                "shoot": "Space/Mouse",
            },
            "notes": "WASD + mouse aim on desktop; virtual joystick + auto-aim on mobile",
        },
        "camera": {
            "mode": "follow_player",
            "lerp": 0.08,
            "deadzone": [100, 80],
            "bounds": "world",
            "notes": "Tight follow for aiming precision; small deadzone",
        },
        "bounds": {
            "world_bounds": True,
            "entity_clamp": True,
            "world_size": "extended",
            "notes": "Arena-sized world; all entities clamped",
        },
        "visual_feedback": {
            "hit_flash_ms": 60,
            "screen_shake": "medium",
            "trail": "subtle",
            "score_popup": True,
            "notes": "Punchy hit feedback; shake on damage; bullet trails for readability",
        },
        "tuning": {
            "expose_in_debug_hud": True,
            "presets": ["arcade", "tight", "floaty"],
            "default_preset": "tight",
        },
    },

    "puzzle": {
        "movement_model": {
            "type": "none",
            "notes": "No player movement — interaction is through clicking/tapping game objects",
        },
        "jump_model": {
            "enabled": False,
            "notes": "No jumping in puzzle games",
        },
        "input": {
            "buffer_ms": 50,
            "mobile_scheme": "touch_direct",
            "touch_zone_min_px": 44,
            "key_map": {"select": "Mouse/Touch"},
            "notes": "Direct object interaction; minimal input buffering",
        },
        "camera": {
            "mode": "fixed",
            "lerp": 0,
            "deadzone": [0, 0],
            "bounds": "none",
            "notes": "Fixed view — entire puzzle board visible at once",
        },
        "bounds": {
            "world_bounds": True,
            "entity_clamp": True,
            "world_size": "screen",
            "notes": "Everything fits on screen",
        },
        "visual_feedback": {
            "hit_flash_ms": 0,
            "screen_shake": "none",
            "trail": "none",
            "score_popup": True,
            "notes": "Match animations and score popups; no combat-style feedback",
        },
        "tuning": {
            "expose_in_debug_hud": True,
            "presets": ["relaxed", "timed", "competitive"],
            "default_preset": "relaxed",
        },
    },

    "clicker": {
        "movement_model": {
            "type": "none",
            "notes": "No movement — core interaction is clicking/tapping a target",
        },
        "jump_model": {
            "enabled": False,
            "notes": "No jumping in clicker games",
        },
        "input": {
            "buffer_ms": 0,
            "mobile_scheme": "touch_direct",
            "touch_zone_min_px": 60,
            "key_map": {"click": "Mouse/Touch"},
            "notes": "Every tap counts; large touch target; no buffering needed",
        },
        "camera": {
            "mode": "fixed",
            "lerp": 0,
            "deadzone": [0, 0],
            "bounds": "none",
            "notes": "Fixed single-screen view",
        },
        "bounds": {
            "world_bounds": True,
            "entity_clamp": True,
            "world_size": "screen",
            "notes": "Everything on one screen",
        },
        "visual_feedback": {
            "hit_flash_ms": 0,
            "screen_shake": "none",
            "trail": "none",
            "score_popup": True,
            "notes": "Number popups on click; upgrade flash; satisfying increment animations",
        },
        "tuning": {
            "expose_in_debug_hud": True,
            "presets": ["casual", "aggressive", "zen"],
            "default_preset": "casual",
        },
    },

    "tower_defense": {
        "movement_model": {
            "type": "none",
            "notes": "No player character movement — player places towers and pans camera",
        },
        "jump_model": {
            "enabled": False,
            "notes": "No jumping in tower defense",
        },
        "input": {
            "buffer_ms": 50,
            "mobile_scheme": "touch_direct",
            "touch_zone_min_px": 48,
            "key_map": {"place": "Mouse/Touch", "scroll": "WASD/Drag"},
            "notes": "Tap to select tower, tap to place; drag to pan on mobile",
        },
        "camera": {
            "mode": "pan_zones",
            "lerp": 0.12,
            "deadzone": [0, 0],
            "bounds": "world",
            "notes": "Edge-pan or drag-to-scroll; camera bounded to map",
        },
        "bounds": {
            "world_bounds": True,
            "entity_clamp": True,
            "world_size": "extended",
            "notes": "Map larger than screen; enemies follow paths within bounds",
        },
        "visual_feedback": {
            "hit_flash_ms": 50,
            "screen_shake": "none",
            "trail": "subtle",
            "score_popup": True,
            "notes": "Tower range indicators; projectile trails; enemy hit flash; wave complete banner",
        },
        "tuning": {
            "expose_in_debug_hud": True,
            "presets": ["standard", "fast", "strategic"],
            "default_preset": "standard",
        },
    },
}


# ─── User Feel Profile Aggregation ────────────────────────

async def aggregate_user_feel_profile(db: AsyncSession) -> dict[str, Any]:
    """Aggregate a cross-project user feel profile from all memory notes.

    Scans all ExplorationMemoryNote records for:
    - feel_spec values (numerical tendencies)
    - rejected_hypotheses / pitfalls_and_guards (dislikes)
    - validated_hypotheses (likes)
    - user_preferences (style signals)

    Returns a structured profile dict.
    """
    result = await db.execute(
        select(ExplorationMemoryNote)
        .order_by(ExplorationMemoryNote.created_at.desc())
        .limit(50)
    )
    notes = list(result.scalars().all())

    # Also get all user preferences (cross-project)
    result = await db.execute(
        select(UserPreference)
        .order_by(UserPreference.updated_at.desc())
        .limit(10)
    )
    all_prefs = list(result.scalars().all())

    profile: dict[str, Any] = {
        "style_tendency": None,        # tight | floaty | arcade
        "device_preference": None,     # mobile | desktop | both
        "input_preference": None,      # tap | keyboard | swipe
        "session_length": None,        # short | medium | long
        "feedback_level": None,        # strong | moderate | minimal
        "likes": [],
        "dislikes": [],
        "tuning_tendencies": {},       # averaged numerical values from past feel_specs
        "session_count": len(notes),
    }

    # Aggregate from user preferences
    platform_votes: dict[str, int] = {}
    input_votes: dict[str, int] = {}
    pace_votes: dict[str, int] = {}
    session_votes: dict[str, int] = {}
    for pref in all_prefs:
        pj = pref.preference_json
        if isinstance(pj, dict):
            if pj.get("platform"):
                platform_votes[pj["platform"]] = platform_votes.get(pj["platform"], 0) + 1
            if pj.get("input"):
                input_votes[pj["input"]] = input_votes.get(pj["input"], 0) + 1
            if pj.get("pace"):
                pace_votes[pj["pace"]] = pace_votes.get(pj["pace"], 0) + 1
            if pj.get("session_length"):
                session_votes[pj["session_length"]] = session_votes.get(pj["session_length"], 0) + 1

    if platform_votes:
        profile["device_preference"] = max(platform_votes, key=platform_votes.get)
    if input_votes:
        profile["input_preference"] = max(input_votes, key=input_votes.get)
    if session_votes:
        profile["session_length"] = max(session_votes, key=session_votes.get)

    # Aggregate from memory notes
    likes_set: set[str] = set()
    dislikes_set: set[str] = set()
    gravity_values: list[float] = []
    drag_ratios: list[float] = []
    preset_votes: dict[str, int] = {}

    for note in notes:
        cj = note.content_json
        if not isinstance(cj, dict):
            continue

        # Likes from validated hypotheses
        for hyp in cj.get("validated_hypotheses", []):
            if isinstance(hyp, str):
                likes_set.add(hyp)

        # Dislikes from rejected hypotheses + pitfalls
        for hyp in cj.get("rejected_hypotheses", []):
            if isinstance(hyp, str):
                dislikes_set.add(hyp)
        for pit in cj.get("pitfalls_and_guards", []):
            if isinstance(pit, str):
                dislikes_set.add(pit)

        # Extract tuning tendencies from feel_spec
        fs = cj.get("feel_spec")
        if isinstance(fs, dict):
            # Gravity
            jm = fs.get("jump_model")
            if isinstance(jm, dict) and isinstance(jm.get("gravity"), (int, float)):
                gravity_values.append(jm["gravity"])

            # Drag ratio (drag / accel) — higher = tighter feel
            mm = fs.get("movement_model")
            if isinstance(mm, dict):
                accel = mm.get("accel", 0)
                drag = mm.get("drag", 0)
                if isinstance(accel, (int, float)) and isinstance(drag, (int, float)) and accel > 0:
                    drag_ratios.append(drag / accel)

            # Preset preference
            tun = fs.get("tuning")
            if isinstance(tun, dict) and tun.get("default_preset"):
                p = tun["default_preset"]
                preset_votes[p] = preset_votes.get(p, 0) + 1

    profile["likes"] = sorted(likes_set)[:15]
    profile["dislikes"] = sorted(dislikes_set)[:15]

    # Tuning tendencies
    if gravity_values:
        profile["tuning_tendencies"]["avg_gravity"] = round(sum(gravity_values) / len(gravity_values))
    if drag_ratios:
        avg_ratio = sum(drag_ratios) / len(drag_ratios)
        profile["tuning_tendencies"]["avg_drag_ratio"] = round(avg_ratio, 2)
        # Infer style tendency from drag ratio
        if avg_ratio >= 0.85:
            profile["style_tendency"] = "tight"
        elif avg_ratio <= 0.5:
            profile["style_tendency"] = "floaty"
        else:
            profile["style_tendency"] = "arcade"
    if preset_votes:
        profile["tuning_tendencies"]["preferred_preset"] = max(preset_votes, key=preset_votes.get)
        if not profile["style_tendency"]:
            profile["style_tendency"] = max(preset_votes, key=preset_votes.get)

    # Infer feedback level from pace preference
    if pace_votes:
        top_pace = max(pace_votes, key=pace_votes.get)
        profile["feedback_level"] = {
            "fast": "strong", "medium": "moderate", "slow": "minimal", "idle": "minimal"
        }.get(top_pace, "moderate")

    return profile


# ─── Combined Priors ──────────────────────────────────────

def get_game_type_defaults(template_id: str) -> dict[str, Any]:
    """Get the static default feel spec for a given template's game type."""
    game_type = TEMPLATE_TO_GAME_TYPE.get(template_id, "platformer")
    return GAME_TYPE_DEFAULTS.get(game_type, GAME_TYPE_DEFAULTS["platformer"])


async def get_feel_priors(
    db: AsyncSession, template_id: str
) -> dict[str, Any]:
    """Get combined feel priors: game-type defaults + user feel profile.

    Returns a dict with:
    - game_type: the resolved game type
    - game_type_defaults: static baseline feel spec
    - user_profile: cross-project user feel preferences
    """
    game_type = TEMPLATE_TO_GAME_TYPE.get(template_id, "platformer")
    defaults = GAME_TYPE_DEFAULTS.get(game_type, GAME_TYPE_DEFAULTS["platformer"])
    user_profile = await aggregate_user_feel_profile(db)

    return {
        "game_type": game_type,
        "game_type_defaults": defaults,
        "user_profile": user_profile,
    }
