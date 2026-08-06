"""Main Streamlit interface for Questie."""

import html as html_lib

import streamlit as st

from ai_service import (
    AIServiceError,
    generate_game_turn,
    generate_opening_adventure,
    generate_reaction_turn,
)
from game_state import (
    apply_decision_result,
    apply_reaction_result,
    consume_entity_ui_effects,
    consume_ui_effect,
    get_current_encounter,
    get_game_state,
    initialise_game_state,
    reset_game_state,
    set_loading,
    start_adventure,
)


st.set_page_config(
    page_title="Questie",
    page_icon="⚔️",
    layout="wide",
)


SETTING_PRESETS = {
    "Frozen Mining Village": "A frozen mining village cut off by a supernatural winter",
    "Ruined Arcane City": "A ruined magical city where unstable relics still function",
    "Abandoned Space Station": "An abandoned space station drifting beyond charted space",
    "Post-Apocalyptic Settlement": "A struggling settlement surrounded by a dangerous wasteland",
    "Gothic Coastal Town": "A fog-covered coastal town hiding an old supernatural secret",
}

CLASS_PRESETS = [
    "Apprentice Mage",
    "Ranger",
    "Warrior",
    "Engineer",
    "Detective",
    "Medic",
    "Rogue",
]


def _damage_effect_css(animation_id: int) -> str:
    """Return player-damage CSS with a fresh animation name per hit."""

    suffix = max(0, int(animation_id))
    return f"""
<style>
@keyframes questieDamageShake_{suffix} {{
    0%   {{ transform: translate3d(0, 0, 0); }}
    12%  {{ transform: translate3d(-5px, 1px, 0); }}
    25%  {{ transform: translate3d(5px, -1px, 0); }}
    40%  {{ transform: translate3d(-3px, 1px, 0); }}
    58%  {{ transform: translate3d(3px, 0, 0); }}
    76%  {{ transform: translate3d(-1px, 0, 0); }}
    100% {{ transform: translate3d(0, 0, 0); }}
}}
@keyframes questieDamageFlash_{suffix} {{
    0%   {{ box-shadow: inset 0 0 0 rgba(255, 58, 58, 0); }}
    32%  {{ box-shadow: inset 0 0 95px rgba(255, 58, 58, 0.24); }}
    100% {{ box-shadow: inset 0 0 0 rgba(255, 58, 58, 0); }}
}}
.stApp {{
    will-change: transform, box-shadow;
    animation:
        questieDamageShake_{suffix} 0.46s cubic-bezier(.22,.61,.36,1) 0.18s both,
        questieDamageFlash_{suffix} 0.72s ease-out 0.18s both;
}}
</style>
"""


def _heal_effect_css(animation_id: int) -> str:
    """Return player-heal CSS with a fresh animation name per heal."""

    suffix = max(0, int(animation_id))
    return f"""
<style>
@keyframes questieHealPulse_{suffix} {{
    0%   {{ filter: brightness(1); }}
    45%  {{ filter: brightness(1.10); }}
    100% {{ filter: brightness(1); }}
}}
.stApp {{
    will-change: filter;
    animation: questieHealPulse_{suffix} 0.72s ease-out 0.18s both;
}}
</style>
"""


BASE_UI_CSS = """
<style>
html { scroll-behavior: smooth; }
.stButton > button,
.stFormSubmitButton > button {
    transition: transform 120ms ease, box-shadow 160ms ease, border-color 160ms ease;
}
.stButton > button:active,
.stFormSubmitButton > button:active {
    transform: scale(0.985);
}
</style>
"""


LENGTH_HELP = {
    "Short": "1 monster or puzzle encounter, then the story resolves.",
    "Medium": "2 encounters followed by a mini-boss, then the story resolves.",
    "Long": "3 encounters, a mini-boss, then a boss and final resolution.",
}


def display_ui_effects(effect: dict | None) -> None:
    """Render the global part of a temporary gameplay effect."""

    if not effect:
        return

    effect_name = effect["name"]
    effect_value = effect["value"]
    animation_id = int(effect.get("animation_id", 0))

    if effect_name == "damage":
        st.markdown(
            _damage_effect_css(animation_id),
            unsafe_allow_html=True,
        )
        st.toast(f"You took {effect_value} damage!", icon="💥")
    elif effect_name == "heal":
        st.markdown(
            _heal_effect_css(animation_id),
            unsafe_allow_html=True,
        )
        st.toast(f"Recovered {effect_value} health.", icon="✨")
    elif effect_name == "item":
        st.toast("Your inventory changed.", icon="🎒")
    elif effect_name == "victory":
        st.balloons()
        st.toast("Quest complete!", icon="🏆")
    elif effect_name == "failure":
        st.markdown(
            _damage_effect_css(animation_id),
            unsafe_allow_html=True,
        )


def _health_animation_html(
    label: str,
    current_health: int,
    max_health: int,
    effect: dict | None,
    compact: bool = False,
    animation_id: int = 0,
) -> str:
    """Build a browser-side HP animation that never blocks Streamlit."""

    safe_max = max(1, int(max_health))
    safe_current = max(0, min(safe_max, int(current_health)))

    start_health = safe_current
    end_health = safe_current
    effect_name = "none"

    if isinstance(effect, dict):
        candidate_effect = str(effect.get("effect", effect.get("name", "none")))
        candidate_from = effect.get("health_from")
        candidate_to = effect.get("health_to")

        if (
            candidate_effect in {"damage", "heal"}
            and isinstance(candidate_from, int)
            and isinstance(candidate_to, int)
            and candidate_from != candidate_to
        ):
            effect_name = candidate_effect
            start_health = max(0, min(safe_max, candidate_from))
            end_health = max(0, min(safe_max, candidate_to))

    difference = abs(end_health - start_health)
    escaped_label = html_lib.escape(label)
    safe_animation_id = max(0, int(animation_id))
    active_colour = "#e34b4b" if effect_name == "damage" else "#35a866"
    impact_icon = "💥" if effect_name == "damage" else "✨"
    impact_word = "damage" if effect_name == "damage" else "HP"

    # Scale animation duration gently with the size of the hit, but keep it quick.
    duration_ms = max(700, min(1250, 650 + difference * 10))
    height = "0.52rem" if compact else "0.62rem"
    label_size = "0.80rem" if compact else "0.88rem"

    return f"""
    <!doctype html>
    <!-- Questie HP animation event: {safe_animation_id} -->
    <html data-questie-animation-id="{safe_animation_id}">
    <head>
    <meta charset="utf-8">
    <style>
        :root {{ color-scheme: light dark; }}
        html, body {{
            margin: 0;
            padding: 0;
            overflow: hidden;
            background: transparent;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }}
        .questie-hp {{
            position: relative;
            padding: 0.05rem 0 0.15rem 0;
            color: light-dark(#31333f, #fafafa);
        }}
        .questie-hp.hit {{
            animation: localHit 0.42s cubic-bezier(.22,.61,.36,1);
            will-change: transform;
        }}
        .questie-hp.heal {{
            animation: localHeal 0.55s ease-out;
        }}
        .hp-header {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: 0.75rem;
            margin-bottom: 0.28rem;
            font-size: {label_size};
        }}
        .hp-label {{ font-weight: 600; opacity: 0.92; }}
        .hp-value {{ font-weight: 700; font-variant-numeric: tabular-nums; }}
        .hp-track {{
            width: 100%;
            height: {height};
            background: light-dark(#e6e8ed, #31343d);
            border-radius: 999px;
            overflow: hidden;
            box-shadow: inset 0 0 0 1px rgba(127,127,127,0.10);
        }}
        .hp-fill {{
            height: 100%;
            width: 0%;
            border-radius: 999px;
            background: #2f80ed;
            transform-origin: left center;
            will-change: width, background-color;
        }}
        .impact {{
            position: absolute;
            right: 0;
            top: -0.03rem;
            font-size: 0.77rem;
            font-weight: 750;
            opacity: 0;
            transform: translateY(4px);
            pointer-events: none;
        }}
        .impact.show {{
            animation: impactFloat 0.95s ease-out forwards;
        }}
        @keyframes localHit {{
            0% {{ transform: translate3d(0,0,0); }}
            24% {{ transform: translate3d(-4px,0,0); }}
            48% {{ transform: translate3d(4px,0,0); }}
            72% {{ transform: translate3d(-2px,0,0); }}
            100% {{ transform: translate3d(0,0,0); }}
        }}
        @keyframes localHeal {{
            0% {{ transform: scale(1); filter: brightness(1); }}
            50% {{ transform: scale(1.008); filter: brightness(1.08); }}
            100% {{ transform: scale(1); filter: brightness(1); }}
        }}
        @keyframes impactFloat {{
            0% {{ opacity: 0; transform: translateY(5px); }}
            18% {{ opacity: 1; transform: translateY(0); }}
            72% {{ opacity: 1; transform: translateY(-2px); }}
            100% {{ opacity: 0; transform: translateY(-8px); }}
        }}
    </style>
    </head>
    <body>
        <div id="wrap" class="questie-hp">
            <div class="hp-header">
                <span class="hp-label">{escaped_label}</span>
                <span id="hpValue" class="hp-value">{start_health} / {safe_max}</span>
            </div>
            <div class="hp-track">
                <div id="hpFill" class="hp-fill"></div>
            </div>
            <div id="impact" class="impact"></div>
        </div>

        <script>
        (() => {{
            const wrap = document.getElementById('wrap');
            const fill = document.getElementById('hpFill');
            const value = document.getElementById('hpValue');
            const impact = document.getElementById('impact');

            const maxHp = {safe_max};
            const startHp = {start_health};
            const endHp = {end_health};
            const effect = {effect_name!r};
            const duration = {duration_ms};
            const delay = 220;
            const animationId = {safe_animation_id};
            document.body.dataset.questieAnimationId = String(animationId);
            const normalColour = '#2f80ed';
            const activeColour = {active_colour!r};

            const pct = (hp) => Math.max(0, Math.min(100, (hp / maxHp) * 100));
            fill.style.width = pct(startHp) + '%';
            fill.style.backgroundColor = normalColour;

            if (effect === 'none' || startHp === endHp) {{
                value.textContent = `${{endHp}} / ${{maxHp}}`;
                fill.style.width = pct(endHp) + '%';
                return;
            }}

            const delta = Math.abs(endHp - startHp);
            impact.textContent = {impact_icon!r} + ' ' + (effect === 'damage' ? '-' : '+') + delta + ' {impact_word}';

            window.setTimeout(() => {{
                wrap.classList.add(effect === 'damage' ? 'hit' : 'heal');
                impact.style.color = activeColour;
                impact.classList.add('show');
                fill.style.backgroundColor = activeColour;

                let animationStart = null;
                const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);

                const animate = (timestamp) => {{
                    if (animationStart === null) animationStart = timestamp;
                    const elapsed = timestamp - animationStart;
                    const rawProgress = Math.min(1, elapsed / duration);
                    const eased = easeOutCubic(rawProgress);
                    const hp = Math.round(startHp + (endHp - startHp) * eased);

                    value.textContent = `${{hp}} / ${{maxHp}}`;
                    fill.style.width = pct(hp) + '%';

                    if (rawProgress < 1) {{
                        window.requestAnimationFrame(animate);
                    }} else {{
                        value.textContent = `${{endHp}} / ${{maxHp}}`;
                        fill.style.width = pct(endHp) + '%';
                        window.setTimeout(() => {{
                            fill.style.transition = 'background-color 260ms ease';
                            fill.style.backgroundColor = normalColour;
                        }}, 90);
                    }}
                }};

                window.requestAnimationFrame(animate);
            }}, delay);
        }})();
        </script>
    </body>
    </html>
    """



def _queue_health_animation(
    animation_queue: list[dict],
    *,
    label: str,
    current_health: int,
    max_health: int,
    effect: dict | None,
    compact: bool,
    height: int,
) -> None:
    """Reserve the HP position and defer its animation until page render ends."""

    placeholder = st.empty()
    animation_queue.append(
        {
            "placeholder": placeholder,
            "label": label,
            "current_health": current_health,
            "max_health": max_health,
            "effect": effect,
            "compact": compact,
            "height": height,
            "animation_id": (
                int(effect.get("animation_id", 0))
                if isinstance(effect, dict)
                else 0
            ),
        }
    )


def _flush_health_animations(animation_queue: list[dict]) -> None:
    """Start every queued HP animation after the rest of the page is stable."""

    for animation in animation_queue:
        placeholder = animation["placeholder"]
        with placeholder:
            st.iframe(
                _health_animation_html(
                    label=animation["label"],
                    current_health=animation["current_health"],
                    max_health=animation["max_health"],
                    effect=animation["effect"],
                    compact=animation["compact"],
                    animation_id=animation["animation_id"],
                ),
                width="stretch",
                height=animation["height"],
            )


def _display_animated_player_health(
    effect: dict | None,
    current_health: int,
    max_health: int,
    animation_queue: list[dict],
) -> None:
    """Reserve the player HP bar so all HP changes can animate together."""

    _queue_health_animation(
        animation_queue,
        label="Health",
        current_health=current_health,
        max_health=max_health,
        effect=effect,
        compact=False,
        height=72,
    )

def process_player_action(player_action: str) -> bool:
    """Process a fixed or custom decision or reaction."""

    cleaned_action = player_action.strip()
    if not cleaned_action:
        st.warning("Please select or enter an action.")
        return False

    state = get_game_state()
    if state["game_over"]:
        st.warning("This adventure has already ended.")
        return False

    set_loading(True)

    try:
        with st.spinner("The Game Master is resolving your action..."):
            if state["phase"] == "reaction":
                result_data = generate_reaction_turn(
                    game_state=state,
                    reaction_action=cleaned_action,
                )
                apply_reaction_result(
                    reaction_action=cleaned_action,
                    result_data=result_data,
                )
            else:
                result_data = generate_game_turn(
                    game_state=state,
                    player_action=cleaned_action,
                )
                apply_decision_result(
                    player_action=cleaned_action,
                    result_data=result_data,
                )

    except AIServiceError as error:
        st.error(str(error))
        return False
    except Exception as error:
        st.error(f"Questie encountered an unexpected gameplay error: {error}")
        return False
    finally:
        set_loading(False)

    return True


def display_setup_form() -> None:
    """Display the controls used to configure a new adventure."""

    st.title("⚔️ Questie")
    st.subheader("Create and play your own AI-generated adventure")
    st.write(
        "Choose a ready-made world or write your own. Questie uses an "
        "encounter plan so the story has a real objective and a definite ending."
    )

    left_column, right_column = st.columns(2)

    with left_column:
        genre = st.selectbox(
            "Genre",
            [
                "Fantasy",
                "Science Fiction",
                "Mystery",
                "Horror",
                "Steampunk",
                "Post-Apocalyptic",
            ],
        )

        setting_choice = st.selectbox(
            "Setting",
            [*SETTING_PRESETS.keys(), "Custom Setting"],
        )

        if setting_choice == "Custom Setting":
            setting = st.text_area(
                "Describe your custom setting",
                placeholder=(
                    "Example: A floating city powered by captured storms, where "
                    "old machines are beginning to fail."
                ),
                height=110,
            )
        else:
            setting = SETTING_PRESETS[setting_choice]
            st.caption(setting)

        class_choice = st.selectbox(
            "Character Class",
            [*CLASS_PRESETS, "Custom Class"],
        )

        class_description = ""
        if class_choice == "Custom Class":
            character_class = st.text_input(
                "Custom Class Name",
                placeholder="Example: Storm Alchemist",
            )
            class_description = st.text_area(
                "What can this class do?",
                placeholder=(
                    "Example: Uses bottled weather effects and mechanical tools. "
                    "Powerful effects require preparation."
                ),
                height=100,
                help=(
                    "Questie may reinterpret an incompatible or overpowered "
                    "concept so it remains playable in the selected world."
                ),
            )
        else:
            character_class = class_choice

    with right_column:
        tone = st.selectbox(
            "Tone",
            [
                "Mysterious",
                "Adventurous",
                "Dark Comedy",
                "Heroic",
                "Suspenseful",
                "Light-hearted",
            ],
        )
        difficulty = st.selectbox(
            "Difficulty",
            ["Easy", "Normal", "Hard"],
            index=1,
        )
        adventure_length = st.selectbox(
            "Adventure Length",
            ["Short", "Medium", "Long"],
            help=(
                "Length controls the number of encounters, not a visible turn "
                "counter. Each encounter ends when its objective is resolved."
            ),
        )
        st.info(LENGTH_HELP[adventure_length])

    submitted = st.button(
        "Generate Adventure",
        type="primary",
        use_container_width=True,
    )

    if not submitted:
        return

    if not setting.strip():
        st.warning("Please provide an adventure setting.")
        return
    if not character_class.strip():
        st.warning("Please provide a character class.")
        return
    if class_choice == "Custom Class" and not class_description.strip():
        st.warning("Please briefly describe what your custom class can do.")
        return

    adventure_config = {
        "genre": genre,
        "setting": setting.strip(),
        "character_class": character_class.strip(),
        "class_description": class_description.strip(),
        "tone": tone,
        "difficulty": difficulty,
        "adventure_length": adventure_length,
    }

    try:
        with st.spinner("Questie is creating your adventure..."):
            opening_data = generate_opening_adventure(
                genre=genre,
                setting=setting.strip(),
                character_class=character_class.strip(),
                class_description=class_description.strip(),
                tone=tone,
                difficulty=difficulty,
                adventure_length=adventure_length,
            )
            start_adventure(
                opening_data=opening_data,
                adventure_config=adventure_config,
            )
    except AIServiceError as error:
        st.error(str(error))
        return
    except Exception as error:
        st.error(f"Questie encountered an unexpected setup error: {error}")
        return

    st.rerun()


def _display_entity_health(
    entity: dict,
    animation_queue: list[dict],
    effect: dict | None = None,
) -> None:
    """Reserve entity HP so simultaneous damage animations start together."""

    current_health = entity.get("current_health")
    max_health = entity.get("max_health")

    if not isinstance(current_health, int) or not isinstance(max_health, int):
        return
    if max_health <= 0:
        return

    _queue_health_animation(
        animation_queue,
        label=f"HP · {entity['name']}",
        current_health=current_health,
        max_health=max_health,
        effect=effect,
        compact=True,
        height=64,
    )

def display_current_entities(
    entity_effects: dict[str, dict] | None = None,
    animation_queue: list[dict] | None = None,
) -> None:
    """Display scene entities and animate health changes where applicable."""

    state = get_game_state()
    effects = entity_effects or {}
    queue = animation_queue if animation_queue is not None else []
    st.subheader("Scene Elements")

    if not state["current_entities"]:
        st.write("Nothing else is currently interacting with you.")
        return

    for entity in state["current_entities"]:
        with st.container(border=True):
            name_column, type_column = st.columns([3, 1])
            name_column.markdown(f"**{entity['name']}**")
            type_column.caption(entity["entity_type"])
            scene_effect = (
                None
                if entity.get("entity_type") == "companion"
                else effects.get(entity["name"])
            )
            _display_entity_health(entity, queue, scene_effect)
            st.write(entity["status"])


def get_active_action_details() -> tuple[str, list[str], str, str]:
    """Return labels and choices for the current interaction phase."""

    state = get_game_state()

    if state["phase"] == "reaction":
        pending_reaction = state["pending_reaction"] or {}
        return (
            "Critical Moment — React Now",
            list(pending_reaction.get("reaction_choices", [])),
            "Or type your own reaction",
            "Example: Use an item or class ability to change the outcome",
        )

    return (
        "What Will You Do?",
        list(state["choices"]),
        "Or type your own action",
        "Example: Use an item, question someone, attack, investigate, or improvise",
    )


def display_action_controls() -> None:
    """Display fixed choices and custom input for the active phase."""

    state = get_game_state()

    if state["game_over"]:
        if state["ending_type"] == "success":
            st.success("Quest completed successfully.")
        else:
            st.error("The quest ended in failure.")

        with st.container(border=True):
            st.markdown("### Ending")
            st.write(state["ending_summary"])
        return

    if state["phase"] == "reaction":
        pending_reaction = state["pending_reaction"]
        if isinstance(pending_reaction, dict):
            st.warning(
                f"**Reaction required:** {pending_reaction['reaction_prompt']}"
            )

    title, choices, input_label, placeholder = get_active_action_details()
    st.subheader(title)

    if len(choices) == 3:
        for index, choice in enumerate(choices):
            clicked = st.button(
                choice,
                key=(
                    f"{state['phase']}_choice_"
                    f"{state['resolved_decisions']}_{index}"
                ),
                use_container_width=True,
                disabled=state["is_loading"],
            )
            if clicked and process_player_action(choice):
                st.rerun()
    else:
        st.warning("The current phase does not contain exactly three choices.")

    st.divider()

    form_key = (
        f"custom_action_form_{state['phase']}_"
        f"{state['resolved_decisions']}"
    )
    input_key = (
        f"custom_action_{state['phase']}_"
        f"{state['resolved_decisions']}"
    )

    with st.form(form_key, clear_on_submit=True):
        custom_action = st.text_input(
            input_label,
            key=input_key,
            placeholder=placeholder,
            disabled=state["is_loading"],
        )
        submitted = st.form_submit_button(
            (
                "Perform Reaction"
                if state["phase"] == "reaction"
                else "Perform Custom Action"
            ),
            use_container_width=True,
            disabled=state["is_loading"],
        )

    if submitted and process_player_action(custom_action):
        st.rerun()


def display_history() -> None:
    """Display previous decisions, reactions, and results."""

    state = get_game_state()

    with st.expander("Adventure History"):
        if not state["history"]:
            st.write("No resolved decisions yet.")
            return

        for entry in state["history"]:
            st.markdown(f"**Decision {entry['decision']}**")
            st.write(entry["action"])

            if entry.get("reaction"):
                st.markdown("**Critical moment**")
                st.write(entry["trigger_story"])
                st.markdown("**Player reaction**")
                st.write(entry["reaction"])

            st.markdown("**Result**")
            st.write(entry["result"])
            st.divider()


def display_party_panel(
    entity_effects: dict[str, dict] | None = None,
    animation_queue: list[dict] | None = None,
) -> None:
    """Display companions and their health in the side panel."""

    state = get_game_state()
    effects = entity_effects or {}
    queue = animation_queue if animation_queue is not None else []
    companions = [
        entity
        for entity in state["current_entities"]
        if entity.get("entity_type") == "companion"
    ]

    if not companions:
        return

    with st.container(border=True):
        st.markdown("### Party")
        for companion in companions:
            st.markdown(f"**{companion['name']}**")
            _display_entity_health(
                companion,
                queue,
                effects.get(companion["name"]),
            )
            st.caption(companion["status"])


def display_player_panel(
    effect: dict | None = None,
    entity_effects: dict[str, dict] | None = None,
    animation_queue: list[dict] | None = None,
) -> None:
    """Display player, encounter, inventory, and quest information."""

    state = get_game_state()
    encounter = get_current_encounter()
    queue = animation_queue if animation_queue is not None else []

    if st.button(
        "Restart Adventure",
        key="restart_adventure",
        use_container_width=True,
    ):
        reset_game_state()
        st.rerun()

    with st.container(border=True):
        st.markdown("### Player Stats")
        stage_column, encounter_column = st.columns(2)
        stage_column.metric("Story Stage", state["story_stage"])
        encounter_column.metric(
            "Encounters",
            f"{state['encounters_completed']} / {len(state['encounter_plan'])}",
        )

        _display_animated_player_health(
            effect=effect,
            current_health=state["player_health"],
            max_health=state["player_max_health"],
            animation_queue=queue,
        )
        st.write(f"**Location:** {state['player_location']}")

        phase_label = {
            "decision": "Choosing an action",
            "reaction": "Reaction required",
            "ended": "Adventure ended",
        }.get(state["phase"], state["phase"])
        st.write(f"**Current phase:** {phase_label}")

    if encounter and not state["game_over"]:
        with st.container(border=True):
            st.markdown("### Current Encounter")
            encounter_type = encounter["encounter_type"].replace("_", " ").title()
            st.write(f"**{encounter['title']}**")
            st.caption(encounter_type)
            st.write(encounter["objective"])

    with st.container(border=True):
        st.markdown("### Inventory")
        if state["player_inventory"]:
            for item in state["player_inventory"]:
                st.write(f"- {item}")
        else:
            st.write("Inventory is empty.")

    display_party_panel(entity_effects, queue)

    with st.container(border=True):
        st.markdown("### Current Quest")
        st.write(state["objective"])

        if state["game_over"]:
            quest_status = (
                "Completed" if state["objective_complete"] else "Failed"
            )
        else:
            quest_status = "In Progress"
        st.write(f"**Status:** {quest_status}")

    with st.expander("Adventure Setup"):
        st.write(f"**Genre:** {state['genre']}")
        st.write(f"**Class:** {state['character_class']}")
        if state.get("class_description"):
            st.write(f"**Class concept:** {state['class_description']}")
        st.write(f"**Tone:** {state['tone']}")
        st.write(f"**Difficulty:** {state['difficulty']}")
        st.write(f"**Length:** {state['adventure_length']}")


def display_adventure() -> None:
    """Display the active adventure and launch all HP animations together."""

    effect = consume_ui_effect()
    entity_effects = consume_entity_ui_effects()
    state = get_game_state()
    animation_queue: list[dict] = []
    left_column, right_column = st.columns([2, 1], gap="large")

    with left_column:
        st.title(f"⚔️ {state['quest_title']}")
        st.caption(
            f"{state['genre']} · {state['character_class']} · "
            f"{state['tone']} · {state['difficulty']} · "
            f"{state['adventure_length']}"
        )
        st.subheader("Current Scene")

        with st.container(border=True):
            st.write(state["story"])

        if state["action_feedback"]:
            st.info(state["action_feedback"])

        display_current_entities(
            entity_effects,
            animation_queue,
        )
        st.divider()
        display_action_controls()
        display_history()

    with right_column:
        display_player_panel(
            effect,
            entity_effects,
            animation_queue,
        )

    # IMPORTANT: nothing that can restructure the page is rendered after this.
    # First emit the global hit/heal feedback, then fill every reserved HP slot.
    # Because the enemy/player/companion iframes are launched in one final pass,
    # simultaneous HP changes overlap instead of interrupting each other.
    display_ui_effects(effect)
    _flush_health_animations(animation_queue)


def main() -> None:
    """Run the Questie application."""

    st.markdown(BASE_UI_CSS, unsafe_allow_html=True)
    initialise_game_state()
    state = get_game_state()

    if state["adventure_started"]:
        display_adventure()
    else:
        display_setup_form()


if __name__ == "__main__":
    main()
