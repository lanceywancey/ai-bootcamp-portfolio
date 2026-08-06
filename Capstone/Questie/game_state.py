"""Manages Questie Streamlit session state."""

from copy import deepcopy
from typing import Any

import streamlit as st


DEFAULT_GAME_STATE: dict[str, Any] = {
    "adventure_started": False,
    "is_loading": False,
    "genre": "",
    "setting": "",
    "character_class": "",
    "class_description": "",
    "tone": "",
    "difficulty": "",
    "adventure_length": "Short",
    "quest_title": "",
    "story_plan": {},
    "story_stage": "Opening",
    "player_health": 100,
    "player_max_health": 100,
    "player_inventory": [],
    "player_location": "",
    "objective": "",
    "objective_complete": False,
    "encounter_plan": [],
    "current_encounter_index": 0,
    "encounters_completed": 0,
    "decisions_in_encounter": 0,
    "resolved_decisions": 0,
    "current_entities": [],
    "history": [],
    "story": "",
    "choices": [],
    "phase": "decision",
    "pending_reaction": None,
    "game_over": False,
    "ending_type": None,
    "ending_summary": "",
    "action_feedback": "",
    "ui_effect": None,
    "ui_effect_value": 0,
    "ui_health_from": 100,
    "ui_health_to": 100,
    "ui_effect_animation_id": 0,
    "ui_animation_sequence": 0,
    "ui_entity_effects": {},
}


def initialise_game_state() -> None:
    """Create or migrate the Questie state for the current session."""

    if "game_state" not in st.session_state:
        st.session_state.game_state = deepcopy(DEFAULT_GAME_STATE)
        return

    state = st.session_state.game_state

    if "resolved_decisions" not in state:
        state["resolved_decisions"] = int(state.get("turn", 0))

    for key, default_value in DEFAULT_GAME_STATE.items():
        if key not in state:
            state[key] = deepcopy(default_value)

    # Older saved adventures did not contain encounter plans. Keep them usable
    # until the player restarts, but new adventures should always use a full plan.
    if state.get("adventure_started") and not state.get("encounter_plan"):
        fallback_objective = state.get("objective") or "Resolve the current quest."
        state["encounter_plan"] = [
            {
                "title": "Final Encounter",
                "encounter_type": "combat",
                "objective": fallback_objective,
                "completion_condition": fallback_objective,
            }
        ]
        state["current_encounter_index"] = 0

    if state["game_over"]:
        state["phase"] = "ended"


def get_game_state() -> dict[str, Any]:
    """Return the current Questie game state."""

    initialise_game_state()
    return st.session_state.game_state


def reset_game_state() -> None:
    """Reset the adventure and remove stale custom-action widgets."""

    st.session_state.game_state = deepcopy(DEFAULT_GAME_STATE)

    for key in list(st.session_state.keys()):
        if key.startswith("custom_action_"):
            del st.session_state[key]


def set_loading(is_loading: bool) -> None:
    """Update whether Questie is waiting for an AI response."""

    get_game_state()["is_loading"] = is_loading


def get_current_encounter() -> dict[str, Any] | None:
    """Return the active planned encounter, if one exists."""

    state = get_game_state()
    plan = state.get("encounter_plan", [])
    index = int(state.get("current_encounter_index", 0))

    if not plan or index < 0 or index >= len(plan):
        return None

    return plan[index]


def consume_ui_effect() -> dict[str, Any] | None:
    """Return and clear one temporary gameplay UI effect."""

    state = get_game_state()
    effect_name = state.get("ui_effect")

    if not effect_name:
        return None

    effect = {
        "name": effect_name,
        "value": int(state.get("ui_effect_value", 0)),
        "health_from": int(
            state.get("ui_health_from", state.get("player_health", 100))
        ),
        "health_to": int(
            state.get("ui_health_to", state.get("player_health", 100))
        ),
        "animation_id": int(state.get("ui_effect_animation_id", 0)),
    }
    state["ui_effect"] = None
    state["ui_effect_value"] = 0
    state["ui_effect_animation_id"] = 0
    state["ui_health_from"] = state["player_health"]
    state["ui_health_to"] = state["player_health"]
    return effect


def consume_entity_ui_effects() -> dict[str, dict[str, Any]]:
    """Return and clear temporary health effects for scene entities."""

    state = get_game_state()
    raw_effects = state.get("ui_entity_effects", {})

    if not isinstance(raw_effects, dict):
        state["ui_entity_effects"] = {}
        return {}

    effects = deepcopy(raw_effects)
    state["ui_entity_effects"] = {}
    return effects


def start_adventure(
    opening_data: dict[str, Any],
    adventure_config: dict[str, str],
) -> None:
    """Populate state using setup choices and a generated opening."""

    required_config_fields = (
        "genre",
        "setting",
        "character_class",
        "tone",
        "difficulty",
        "adventure_length",
    )

    cleaned_config: dict[str, str] = {}

    for field_name in required_config_fields:
        value = adventure_config.get(field_name)

        if not isinstance(value, str) or not value.strip():
            readable_name = field_name.replace("_", " ")
            raise ValueError(
                f"Adventure configuration is missing {readable_name}."
            )

        cleaned_config[field_name] = value.strip()

    class_description = adventure_config.get("class_description", "")
    if not isinstance(class_description, str):
        class_description = ""

    encounter_plan = deepcopy(opening_data["story_plan"]["encounters"])

    if not encounter_plan:
        raise ValueError("The generated adventure did not contain encounters.")

    state = deepcopy(DEFAULT_GAME_STATE)
    state.update(
        {
            "adventure_started": True,
            **cleaned_config,
            "class_description": class_description.strip(),
            "quest_title": opening_data["quest_title"],
            "story_plan": deepcopy(opening_data["story_plan"]),
            "story_stage": "Opening",
            "player_health": opening_data["player_health"],
            "player_max_health": opening_data["player_max_health"],
            "player_inventory": list(opening_data["player_inventory"]),
            "player_location": opening_data["player_location"],
            "objective": opening_data["objective"],
            "objective_complete": False,
            "encounter_plan": encounter_plan,
            "current_encounter_index": 0,
            "encounters_completed": 0,
            "decisions_in_encounter": 0,
            "resolved_decisions": 0,
            "current_entities": deepcopy(opening_data["current_entities"]),
            "history": [],
            "story": opening_data["story"],
            "choices": list(opening_data["choices"]),
            "phase": "decision",
            "pending_reaction": None,
            "game_over": False,
            "ending_type": None,
            "ending_summary": "",
            "action_feedback": "",
            "ui_effect": None,
            "ui_effect_value": 0,
            "ui_health_from": opening_data["player_health"],
            "ui_health_to": opening_data["player_health"],
            "ui_effect_animation_id": 0,
            "ui_animation_sequence": 0,
            "ui_entity_effects": {},
        }
    )

    st.session_state.game_state = state


def _next_ui_animation_id(state: dict[str, Any]) -> int:
    """Return a fresh ID so every HP animation is treated as a new event."""

    next_id = int(state.get("ui_animation_sequence", 0)) + 1
    state["ui_animation_sequence"] = next_id
    return next_id


def _apply_player_changes(
    state: dict[str, Any],
    result_data: dict[str, Any],
) -> None:
    """Apply validated health and inventory changes to the player."""

    health_change = int(result_data["player_health_change"])
    previous_health = int(state["player_health"])
    updated_health = previous_health + health_change
    state["player_health"] = max(
        0,
        min(state["player_max_health"], updated_health),
    )

    if health_change < 0:
        state["ui_effect"] = "damage"
        state["ui_effect_value"] = abs(health_change)
        state["ui_health_from"] = previous_health
        state["ui_health_to"] = state["player_health"]
        state["ui_effect_animation_id"] = _next_ui_animation_id(state)
    elif health_change > 0:
        state["ui_effect"] = "heal"
        state["ui_effect_value"] = health_change
        state["ui_health_from"] = previous_health
        state["ui_health_to"] = state["player_health"]
        state["ui_effect_animation_id"] = _next_ui_animation_id(state)

    item_added = False
    for item in result_data["player_items_added"]:
        if item not in state["player_inventory"]:
            state["player_inventory"].append(item)
            item_added = True

    for item in result_data["player_items_removed"]:
        if item in state["player_inventory"]:
            state["player_inventory"].remove(item)

    if item_added and state["ui_effect"] is None:
        state["ui_effect"] = "item"
        state["ui_effect_value"] = 0
        state["ui_health_from"] = state["player_health"]
        state["ui_health_to"] = state["player_health"]


def _record_entity_health_effects(
    state: dict[str, Any],
    new_entities: list[dict[str, Any]],
) -> None:
    """Record enemy, creature, and companion HP changes for UI animation."""

    old_entities = {
        str(entity.get("name", "")).strip().casefold(): entity
        for entity in state.get("current_entities", [])
        if isinstance(entity, dict) and entity.get("name")
    }

    effects: dict[str, dict[str, Any]] = {}

    for new_entity in new_entities:
        if not isinstance(new_entity, dict):
            continue

        name = str(new_entity.get("name", "")).strip()
        entity_type = str(new_entity.get("entity_type", "")).strip().casefold()

        if not name or entity_type not in {"enemy", "creature", "companion"}:
            continue

        old_entity = old_entities.get(name.casefold())
        if not isinstance(old_entity, dict):
            continue

        old_health = old_entity.get("current_health")
        new_health = new_entity.get("current_health")
        max_health = new_entity.get("max_health")

        if (
            not isinstance(old_health, int)
            or isinstance(old_health, bool)
            or not isinstance(new_health, int)
            or isinstance(new_health, bool)
            or not isinstance(max_health, int)
            or isinstance(max_health, bool)
            or max_health <= 0
            or old_health == new_health
        ):
            continue

        effects[name] = {
            "effect": "damage" if new_health < old_health else "heal",
            "health_from": old_health,
            "health_to": new_health,
            "max_health": max_health,
            "value": abs(new_health - old_health),
            "entity_type": entity_type,
            "animation_id": _next_ui_animation_id(state),
        }

    state["ui_entity_effects"] = effects


def _advance_encounter_if_complete(
    state: dict[str, Any],
    result_data: dict[str, Any],
) -> None:
    """Advance the hidden encounter plan after a completed encounter."""

    if not result_data.get("encounter_complete"):
        state["decisions_in_encounter"] += 1
        return

    state["encounters_completed"] += 1
    state["decisions_in_encounter"] = 0

    if state["game_over"]:
        return

    last_index = max(0, len(state["encounter_plan"]) - 1)
    if state["current_encounter_index"] < last_index:
        state["current_encounter_index"] += 1


def _complete_resolved_decision(
    state: dict[str, Any],
    history_entry: dict[str, Any],
    result_data: dict[str, Any],
) -> None:
    """Finish one meaningful decision and update encounter/story state."""

    _apply_player_changes(state, result_data)
    _record_entity_health_effects(
        state,
        result_data["current_entities"],
    )

    state["resolved_decisions"] += 1
    history_entry["decision"] = state["resolved_decisions"]
    state["history"].append(history_entry)

    state["story"] = result_data["story"]
    state["story_stage"] = result_data["story_stage"]
    state["player_location"] = result_data["player_location"]
    state["current_entities"] = deepcopy(result_data["current_entities"])
    state["action_feedback"] = result_data["action_feedback"]
    state["objective_complete"] = bool(result_data["objective_complete"])
    state["game_over"] = bool(result_data["game_over"])
    state["ending_type"] = result_data["ending_type"]
    state["ending_summary"] = result_data["ending_summary"]
    state["pending_reaction"] = None

    _advance_encounter_if_complete(state, result_data)

    if state["player_health"] <= 0 and not state["game_over"]:
        state["player_health"] = 0
        state["game_over"] = True
        state["ending_type"] = "failure"
        state["story_stage"] = "Resolution"
        state["objective_complete"] = False
        state["ending_summary"] = (
            "Your injuries leave you unable to continue the adventure. "
            "The quest objective remains unresolved, and the consequences of "
            "your final decision bring this journey to a close."
        )

    if state["game_over"]:
        state["phase"] = "ended"
        state["choices"] = []
        if state["ending_type"] == "success":
            state["ui_effect"] = "victory"
            state["ui_effect_value"] = 0
        elif state["ui_effect"] is None:
            state["ui_effect"] = "failure"
            state["ui_effect_value"] = 0
    else:
        state["phase"] = "decision"
        state["choices"] = list(result_data["choices"])


def apply_decision_result(
    player_action: str,
    result_data: dict[str, Any],
) -> None:
    """Apply a decision result or open a reaction in the same decision."""

    state = get_game_state()

    state["story"] = result_data["story"]
    state["story_stage"] = result_data["story_stage"]
    state["player_location"] = result_data["player_location"]
    state["action_feedback"] = result_data["action_feedback"]

    if result_data["reaction_required"]:
        # No resolved HP change exists yet during a reaction request. Update
        # scene entities here, but preserve old HP for normal resolved turns.
        state["current_entities"] = deepcopy(result_data["current_entities"])
        state["phase"] = "reaction"
        state["choices"] = []
        state["game_over"] = False
        state["ending_type"] = None
        state["ending_summary"] = ""
        state["pending_reaction"] = {
            "original_action": player_action,
            "trigger_story": result_data["story"],
            "reaction_prompt": result_data["reaction_prompt"],
            "reaction_choices": list(result_data["reaction_choices"]),
        }
        return

    _complete_resolved_decision(
        state=state,
        history_entry={
            "action": player_action,
            "reaction": "",
            "trigger_story": "",
            "result": result_data["story"],
        },
        result_data=result_data,
    )


def apply_reaction_result(
    reaction_action: str,
    result_data: dict[str, Any],
) -> None:
    """Resolve a pending reaction and finish the current decision."""

    state = get_game_state()
    pending_reaction = state.get("pending_reaction")

    if not isinstance(pending_reaction, dict):
        raise ValueError("No reaction is currently waiting to be resolved.")

    _complete_resolved_decision(
        state=state,
        history_entry={
            "action": pending_reaction["original_action"],
            "reaction": reaction_action,
            "trigger_story": pending_reaction["trigger_story"],
            "result": result_data["story"],
        },
        result_data=result_data,
    )
