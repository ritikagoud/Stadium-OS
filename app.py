"""Stadium OS - Predictive Personal Experience Engine.

This module provides a simple rule-based assistant for stadium visitors.
It detects intent, predicts near-future crowd behavior, and returns
recommendations with clear reasoning.
"""

import random

from flask import Flask, jsonify, request


# Priority mapping for crowd levels.
# Lower value means lower crowd and therefore better recommendation.
CROWD_PRIORITY = {"low": 1, "medium": 2, "high": 3}


def _increase_level(level):
    """Increase crowd level by one step, capped at 'high'."""
    value = CROWD_PRIORITY.get(level, CROWD_PRIORITY["medium"])
    new_value = min(value + 1, CROWD_PRIORITY["high"])
    reverse_map = {v: k for k, v in CROWD_PRIORITY.items()}
    return reverse_map[new_value]


def _decrease_level(level):
    """Decrease crowd level by one step, capped at 'low'."""
    value = CROWD_PRIORITY.get(level, CROWD_PRIORITY["medium"])
    new_value = max(value - 1, CROWD_PRIORITY["low"])
    reverse_map = {v: k for k, v in CROWD_PRIORITY.items()}
    return reverse_map[new_value]


def _slight_context_variation(context):
    """Apply small, controlled variation so the sample data does not feel static."""
    varied_context = {
        "event_phase": context["event_phase"],
        "gates": [dict(g) for g in context["gates"]],
        "food_stalls": [dict(s) for s in context["food_stalls"]],
        "exits": [dict(e) for e in context["exits"]],
    }

    for gate in varied_context["gates"]:
        if random.random() < 0.5:
            gate["crowd_level"] = random.choice([gate["crowd_level"], _increase_level(gate["crowd_level"]), _decrease_level(gate["crowd_level"])])

    for stall in varied_context["food_stalls"]:
        if random.random() < 0.5:
            stall["wait_time_min"] = max(1, stall["wait_time_min"] + random.choice([-2, -1, 0, 1, 2]))

    for exit_point in varied_context["exits"]:
        if random.random() < 0.35:
            exit_point["congestion"] = random.choice([exit_point["congestion"], _increase_level(exit_point["congestion"]), _decrease_level(exit_point["congestion"])])

    return varied_context


def detect_intent(user_text):
    """Detect user intent from text.

    Returns one of: navigation, food, exit, general.
    """
    intents = detect_intents(user_text)
    return intents[0] if intents else "general"


def detect_intents(user_text):
    """Detect all intents in the order they appear in the query."""
    text = user_text.lower().strip()

    intent_keywords = [
        ("navigation", ["gate", "enter", "entry", "navigation", "seat"]),
        ("food", ["food", "hungry", "eat", "snack", "stall"]),
        ("exit", ["exit", "leave", "go out", "home", "leave early"]),
    ]

    matches = []
    for intent_name, keywords in intent_keywords:
        found_positions = []
        for keyword in keywords:
            position = text.find(keyword)
            if position != -1:
                found_positions.append(position)

        if found_positions:
            matches.append((min(found_positions), intent_name))

    matches.sort(key=lambda item: item[0])

    ordered_intents = []
    for _, intent_name in matches:
        if intent_name not in ordered_intents:
            ordered_intents.append(intent_name)

    return ordered_intents


def get_context():
    """Return sample stadium context dataset."""
    base_context = {
        "event_phase": "halftime",  # entry, live, halftime, ending, exit
        "gates": [
            {"name": "Gate 1", "crowd_level": "high", "distance_m": 140},
            {"name": "Gate 2", "crowd_level": "medium", "distance_m": 220},
            {"name": "Gate 3", "crowd_level": "low", "distance_m": 380},
        ],
        "food_stalls": [
            {"name": "Stall A", "wait_time_min": 12, "distance_m": 90},
            {"name": "Stall B", "wait_time_min": 7, "distance_m": 210},
            {"name": "Stall C", "wait_time_min": 10, "distance_m": 120},
        ],
        "exits": [
            {"name": "Exit North", "distance_m": 350, "congestion": "medium"},
            {"name": "Exit East", "distance_m": 500, "congestion": "low"},
            {"name": "Exit South", "distance_m": 280, "congestion": "high"},
        ],
    }

    return _slight_context_variation(base_context)


def predict_crowd(context):
    """Predict near-future context using simple rule-based logic.

    Rules:
    - entry phase: gate crowd generally increases
    - halftime: food wait times increase
    - ending/exit phase: exit congestion increases
    """
    predicted = {
        "event_phase": context["event_phase"],
        "gates": [dict(g) for g in context["gates"]],
        "food_stalls": [dict(s) for s in context["food_stalls"]],
        "exits": [dict(e) for e in context["exits"]],
    }

    phase = context["event_phase"]

    if phase == "entry":
        for gate in predicted["gates"]:
            gate["crowd_level"] = _increase_level(gate["crowd_level"])

    if phase == "halftime":
        for stall in predicted["food_stalls"]:
            stall["wait_time_min"] += 5

    if phase in ("ending", "exit"):
        for exit_point in predicted["exits"]:
            exit_point["congestion"] = _increase_level(exit_point["congestion"])

    return predicted


def _proactive_suggestions(context):
    """Generate proactive alerts from the current event phase."""
    phase = context["event_phase"]
    suggestions = []

    if phase == "halftime":
        suggestions.append("Food stalls are expected to get busier during halftime.")
    if phase in ("ending", "exit"):
        suggestions.append("Exit rush is expected soon. Consider leaving a few minutes early.")
    if phase == "entry":
        suggestions.append("Entry queues may rise quickly. Prefer gates with low current crowd.")

    return suggestions


def _get_prediction_window(context):
    """Return a simple human-readable near-future window for the current phase."""
    phase = context["event_phase"]
    if phase == "halftime":
        return "5-10 minutes"
    if phase in ("ending", "exit"):
        return "soon"
    if phase == "entry":
        return "a few minutes"
    return "a short time"


def _get_priority_weights(priority):
    """Return simple weights for crowd, time, and distance."""
    if priority == "least_crowd":
        return {"crowd": 3, "time": 1, "distance": 1}
    if priority == "shortest_distance":
        return {"crowd": 1, "time": 1, "distance": 3}
    return {"crowd": 1, "time": 3, "distance": 1}


def _score_gate(gate, weights):
    crowd_score = CROWD_PRIORITY[gate["crowd_level"]] * weights["crowd"]
    distance_score = gate["distance_m"] * weights["distance"]
    total_score = crowd_score + distance_score
    return total_score, {"crowd": crowd_score, "time": 0, "distance": distance_score}


def _score_food_stall(stall, weights):
    time_score = stall["wait_time_min"] * weights["time"]
    distance_score = stall["distance_m"] * weights["distance"]
    total_score = time_score + distance_score
    return total_score, {"crowd": 0, "time": time_score, "distance": distance_score}


def _score_exit(exit_point, weights):
    crowd_score = CROWD_PRIORITY[exit_point["congestion"]] * weights["crowd"]
    distance_score = exit_point["distance_m"] * weights["distance"]
    total_score = crowd_score + distance_score
    return total_score, {"crowd": crowd_score, "time": 0, "distance": distance_score}


def _rank_options(options, scorer):
    scored_options = []
    for option in options:
        total_score, parts = scorer(option)
        scored_options.append((total_score, parts, option))
    scored_options.sort(key=lambda item: item[0])
    return scored_options


def _summarize_tradeoff(best, alt, category):
    """Create a short, user-friendly explanation for the chosen option."""
    if category == "navigation":
        if alt:
            if best["crowd_level"] == "high":
                return (
                    f"Although {best['name']} has higher crowd, it is still the faster entry choice because it is closer. "
                    f"{alt['name']} is less crowded, but the extra distance makes it slower overall."
                )
            if best["crowd_level"] == "low":
                return (
                    f"{best['name']} is the better entry choice because it stays calmer while still giving you a reasonable walk. "
                    f"{alt['name']} is a backup if you want a different balance."
                )
            return (
                f"{best['name']} is the best balance right now: it keeps the walk practical while avoiding the busiest option. "
                f"{alt['name']} is the backup if you want to trade distance for a different crowd level."
            )
        if best["crowd_level"] == "high":
            return f"Although {best['name']} has higher crowd, it is still the fastest entry option because it is the closest route."
        return f"{best['name']} is the smoothest entry option right now and should keep your walk simple."

    if category == "food":
        if alt:
            if best["wait_time_min"] > alt["wait_time_min"] and best["distance_m"] < alt["distance_m"]:
                return (
                    f"{best['name']} is the better food choice because the shorter walk makes it faster overall, "
                    f"even if the queue is not the lowest. {alt['name']} may look easier on paper, but it takes longer to reach."
                )
            return (
                f"{best['name']} gives you the fastest food stop right now. "
                f"{alt['name']} is the backup if you want a different balance, but it is slower overall."
            )
        return f"{best['name']} is the quickest food option right now and keeps the delay low."

    if category == "exit":
        if alt:
            if best["congestion"] == "high":
                return (
                    f"Although {best['name']} has higher crowd, it is still the faster exit because the route is shorter. "
                    f"{alt['name']} is less crowded, but it takes longer to reach overall."
                )
            if best["congestion"] == "low":
                return (
                    f"{best['name']} is the better exit choice because it stays calmer while still being practical to reach. "
                    f"{alt['name']} is the backup if you want a different trade-off."
                )
            return (
                f"{best['name']} is the best exit choice right now: it avoids the busiest route without adding too much extra walking. "
                f"{alt['name']} is the backup if you want to trade comfort for distance."
            )
        if best["congestion"] == "high":
            return f"Although {best['name']} has higher crowd, it is still the fastest exit because the route is shorter."
        return f"{best['name']} is the easiest exit right now and should help you leave with less friction."

    return "This is the most balanced option based on the current stadium conditions."


def _smart_tip(intents, predicted_context):
    """Return one short tip that gives the user a useful next-step insight."""
    phase = predicted_context["event_phase"]
    primary_intent = intents[0] if intents else "general"

    if primary_intent == "food" and phase == "halftime":
        return "Tip: If you wait a few minutes, food queues may grow quickly during halftime."
    if primary_intent == "exit" and phase in ("ending", "exit"):
        return "Tip: Leaving now may help you avoid the exit rush."
    if primary_intent == "navigation" and phase == "entry":
        return "Tip: Gates are likely to get busier soon, so moving now may save time."

    return "Tip: Conditions look steady, so you have a little flexibility if you want to wait."


def _prediction_insight(current_best, future_best, prediction_window, category):
    """Explain whether conditions are stable or changing in a useful way."""
    if current_best["name"] == future_best["name"]:
        if category == "food":
            return (
                f"Best now and in {prediction_window}: {future_best['name']}. Conditions are stable, so there is no urgency."
            )
        if category == "exit":
            return (
                f"Best now and in {prediction_window}: {future_best['name']}. Conditions are stable, so you can leave at a steady pace."
            )
        return (
            f"Best now and in {prediction_window}: {future_best['name']}. Conditions are stable, so no urgency."
        )

    if category == "food":
        return (
            f"Best now is {current_best['name']}, but in {prediction_window} the better option is {future_best['name']}. "
            f"Recommended to act now before wait times rise."
        )
    if category == "exit":
        return (
            f"Best now is {current_best['name']}, but in {prediction_window} the better option is {future_best['name']}. "
            f"Recommended to move now before congestion increases."
        )
    return (
        f"Best now is {current_best['name']}, but in {prediction_window} the better option is {future_best['name']}. "
        f"Recommended to move now before conditions change."
    )


def get_route_hint(location):
    """Simulate a Google Maps route hint for a location.

    This is designed so real Google Maps API integration can be added in production.
    """
    return f"Route optimized using Google Maps API (simulated) for {location}"


def decision_engine(intent, context, predicted_context, user_profile=None):
    """Generate recommendation and reasoning based on intent + prediction."""
    user_profile = user_profile or {}
    priority = user_profile.get("priority", "fastest")
    valid_priorities = {"fastest", "least_crowd", "shortest_distance"}
    if priority not in valid_priorities:
        priority = "fastest"

    result = {
        "recommendation": "",
        "reasoning": "",
        "alternative": "",
        "proactive": _proactive_suggestions(predicted_context),
        "prediction_note": "",
    }

    prediction_window = _get_prediction_window(context)
    weights = _get_priority_weights(priority)

    if intent == "navigation":
        scored_gates = _rank_options(
            predicted_context["gates"],
            lambda gate: _score_gate(gate, weights),
        )
        current_best = _rank_options(
            context["gates"],
            lambda gate: _score_gate(gate, weights),
        )[0][2]

        best_score, best_parts, best = scored_gates[0]
        alt_score, _, alt = scored_gates[1] if len(scored_gates) > 1 else (None, None, None)

        result["recommendation"] = f"Use {best['name']}."
        result["prediction_note"] = _prediction_insight(current_best, best, prediction_window, "navigation")
        result["route_hint"] = get_route_hint(best["name"])
        if alt:
            result["reasoning"] = _summarize_tradeoff(best, alt, "navigation")
            result["alternative"] = f"{alt['name']} if you want a different trade-off."
        else:
            result["reasoning"] = _summarize_tradeoff(best, None, "navigation")

    elif intent == "food":
        scored_stalls = _rank_options(
            predicted_context["food_stalls"],
            lambda stall: _score_food_stall(stall, weights),
        )
        current_best = _rank_options(
            context["food_stalls"],
            lambda stall: _score_food_stall(stall, weights),
        )[0][2]

        best_score, best_parts, best = scored_stalls[0]
        alt_score, _, alt = scored_stalls[1] if len(scored_stalls) > 1 else (None, None, None)

        result["recommendation"] = f"Go to {best['name']}."
        result["prediction_note"] = _prediction_insight(current_best, best, prediction_window, "food")
        if alt:
            result["reasoning"] = _summarize_tradeoff(best, alt, "food")
            result["alternative"] = f"{alt['name']} if you prefer a shorter walk."
        else:
            result["reasoning"] = _summarize_tradeoff(best, None, "food")

    elif intent == "exit":
        scored_exits = _rank_options(
            predicted_context["exits"],
            lambda exit_point: _score_exit(exit_point, weights),
        )
        current_best = _rank_options(
            context["exits"],
            lambda exit_point: _score_exit(exit_point, weights),
        )[0][2]

        best_score, best_parts, best = scored_exits[0]
        alt_score, _, alt = scored_exits[1] if len(scored_exits) > 1 else (None, None, None)

        result["recommendation"] = f"Take {best['name']}."
        result["prediction_note"] = _prediction_insight(current_best, best, prediction_window, "exit")
        result["route_hint"] = get_route_hint(best["name"])
        if alt:
            result["reasoning"] = _summarize_tradeoff(best, alt, "exit")
            result["alternative"] = f"{alt['name']} if you want a different route balance."
        else:
            result["reasoning"] = _summarize_tradeoff(best, None, "exit")

    else:
        result["recommendation"] = "I can help with entry gates, food stalls, or exits."
        result["reasoning"] = (
            "Ask where to enter, where to eat, or the fastest way to exit for a personalized recommendation."
        )

    if not result["reasoning"]:
        result["reasoning"] = "Recommendation selected from predicted stadium conditions."

    if intent in {"food", "exit", "navigation"}:
        result["prediction_note"] = result["prediction_note"] or (
            f"Best now and in {prediction_window}: conditions are stable, so there is no urgency."
        )

    return result


def build_step_by_step_plan(intents, context, predicted_context, user_profile=None):
    """Build a sequential plan for one or more intents."""
    plan_lines = []

    if not intents:
        intents = ["general"]

    for index, intent in enumerate(intents, start=1):
        decision = decision_engine(intent, context, predicted_context, user_profile)
        plan_lines.append(f"Step {index}: {decision['recommendation']}")

        if decision.get("prediction_note"):
            plan_lines.append(f"Now vs soon: {decision['prediction_note']}")

        if decision.get("route_hint"):
            plan_lines.append(f"Route note: {decision['route_hint']}")

        plan_lines.append(f"Why this works: {decision['reasoning']}")

        if decision["alternative"]:
            alt_label = "Backup option" if index == 1 else "Another option"
            plan_lines.append(f"{alt_label}: {decision['alternative']}")

    proactive = _proactive_suggestions(predicted_context)
    if proactive:
        plan_lines.append("Proactive suggestion: " + " ".join(proactive))

    plan_lines.append(_smart_tip(intents, predicted_context))

    return "\n".join(plan_lines)


def generate_response(user_text, context=None):
    """End-to-end helper that returns a readable response string."""
    if context is None:
        context = get_context()

    user_profile = context.get("user_profile", {})

    intents = detect_intents(user_text)
    predicted_context = predict_crowd(context)

    selected_priority = user_profile.get("priority", "fastest")

    lines = [
        f"I found these intents: {', '.join(intents) if intents else 'general'}",
        f"Your priority is set to: {selected_priority}",
    ]

    lines.append(build_step_by_step_plan(intents, context, predicted_context, user_profile))

    return "\n".join(lines)


app = Flask(__name__)


@app.get("/")
def home():
    """Simple health endpoint for Cloud Run checks."""
    return jsonify({"status": "Stadium OS API is running"})


@app.post("/query")
def query_api():
    """Accept user query JSON and return assistant response."""
    payload = request.get_json(silent=True) or {}
    user_query = payload.get("query")

    if not isinstance(user_query, str) or not user_query.strip():
        return jsonify({"error": "Please provide JSON with a non-empty 'query' string."}), 400

    response_text = generate_response(user_query)
    return jsonify({"response": response_text})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)


