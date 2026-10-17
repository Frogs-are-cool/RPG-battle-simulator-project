import os
import secrets
from datetime import timedelta
from pathlib import Path
import hmac

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

import rpg_game as game


def _load_secret_key(instance_path):
    configured_key = os.environ.get("FLASK_SECRET_KEY")
    if configured_key:
        return configured_key

    key_file = Path(instance_path) / "flask_secret_key"
    key_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        file_descriptor = os.open(
            key_file,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
    except FileExistsError:
        return key_file.read_text(encoding="utf-8").strip()

    secret_key = secrets.token_hex(32)
    with os.fdopen(file_descriptor, "w", encoding="utf-8") as secret_file:
        secret_file.write(secret_key)
    return secret_key


app = Flask(__name__)
app.secret_key = _load_secret_key(app.instance_path)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_COOKIE_SECURE") == "1",
    PERMANENT_SESSION_LIFETIME=timedelta(days=30),
    MAX_CONTENT_LENGTH=16 * 1024,
)


def _get_game_state():
    raw_state = session.get("game_state")
    state = game.new_state() if raw_state is None else game.normalize_save(raw_state)
    session.permanent = True
    session["game_state"] = state
    return state


def _get_csrf_token():
    token = session.get("csrf_token")
    if not isinstance(token, str):
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


@app.errorhandler(ValueError)
def invalid_session(error):
    return f"Could not load this browser's game session: {error}", 400


@app.get("/")
def index():
    state = _get_game_state()
    return render_template("index.html", state=state, csrf_token=_get_csrf_token())


@app.post("/action")
def perform_action():
    expected_token = session.get("csrf_token")
    submitted_token = request.form.get("csrf_token", "")
    if not isinstance(expected_token, str) or not hmac.compare_digest(
        expected_token, submitted_token
    ):
        abort(400, description="The form expired. Reload the page and try again.")

    state = _get_game_state()
    action = request.form.get("action", "")
    player = state["player"]

    if action == "find_battle":
        if state["battle"] is not None:
            flash("You are already in a battle.", "warning")
        else:
            flash(game.start_battle(state, persist=False), "battle")
    elif action == "attack":
        if state["battle"] is None:
            flash("Find a battle before attacking.", "warning")
        else:
            messages, result = game.battle_turn(state, persist=False)
            for message in messages:
                flash(message, "battle")
            if result == "won":
                flash("Your rewards and progress are saved in this browser.", "success")
    elif action == "rest":
        if state["battle"] is not None:
            flash("You cannot rest while an enemy is attacking.", "warning")
        else:
            recovered = player["max_hp"] - player["hp"]
            player["hp"] = player["max_hp"]
            flash(f"You rest and recover {recovered} HP.", "success")
    elif action == "use_potion":
        if state["battle"] is not None:
            flash("You cannot use a Potion during battle.", "warning")
        else:
            flash(game.use_item(state, "Potion", persist=False), "info")
    elif action == "buy_potion":
        if state["battle"] is not None:
            flash("You cannot shop during battle.", "warning")
        else:
            flash(game.buy_item(state, "Potion", persist=False), "info")
    elif action == "new_game":
        state = game.new_state()
        flash("A new adventure begins.", "success")
    elif action == "save":
        flash("Progress saved in this browser for up to 30 days.", "success")
    else:
        flash("That action is not available.", "warning")

    session["game_state"] = state
    session.modified = True
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
