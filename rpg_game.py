import json
import os
import random
from pathlib import Path


SAVE_DIR = Path(__file__).resolve().parent / "rpg_save"
SAVE_FILE = SAVE_DIR / "save.json"
SAVE_VERSION = 1

ITEMS = {
    "Potion": {"effect": "heal", "amount": 30, "price": 10},
}

ENEMIES = [
    {"name": "Goblin", "hp": 30, "attack": 6, "xp": 10, "gold": 5},
    {"name": "Wolf", "hp": 25, "attack": 8, "xp": 12, "gold": 4},
    {"name": "Orc", "hp": 45, "attack": 10, "xp": 20, "gold": 10},
    {"name": "Skeleton", "hp": 35, "attack": 7, "xp": 15, "gold": 8},
]


def new_player():
    return {
        "version": 1,
        "name": "Hero",
        "hp": 100,
        "max_hp": 100,
        "attack": 12,
        "level": 1,
        "xp": 0,
        "gold": 0,
        "inventory": {"Potion": 2},
    }


def new_state():
    return {
        "schema_version": SAVE_VERSION,
        "player": new_player(),
        "battle": None,
    }


def _as_int(value, field, minimum=0):
    if isinstance(value, bool):
        raise ValueError(f"Save field {field!r} must be an integer.")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Save field {field!r} must be an integer.") from exc
    if number < minimum:
        raise ValueError(f"Save field {field!r} must be at least {minimum}.")
    return number


def upgrade_player(raw_player):
    if not isinstance(raw_player, dict):
        raise ValueError("Saved player data must be an object.")

    player = new_player()
    for field in ("name", "hp", "max_hp", "attack", "level", "xp", "gold"):
        if field in raw_player:
            player[field] = raw_player[field]

    player["version"] = 1
    if not isinstance(player["name"], str) or not player["name"].strip():
        raise ValueError("Save field 'name' must be a non-empty string.")
    player["max_hp"] = _as_int(player["max_hp"], "max_hp", minimum=1)
    player["hp"] = min(_as_int(player["hp"], "hp"), player["max_hp"])
    player["attack"] = _as_int(player["attack"], "attack", minimum=1)
    player["level"] = _as_int(player["level"], "level", minimum=1)
    player["xp"] = _as_int(player["xp"], "xp")
    player["gold"] = _as_int(player["gold"], "gold")

    inventory = raw_player.get("inventory", player["inventory"])
    if not isinstance(inventory, dict):
        raise ValueError("Save field 'inventory' must be an object.")
    player["inventory"] = {
        str(name): _as_int(count, f"inventory.{name}")
        for name, count in inventory.items()
    }
    return player


def _upgrade_enemy(raw_enemy):
    if not isinstance(raw_enemy, dict):
        raise ValueError("Saved enemy data must be an object.")

    required = ("name", "hp", "attack", "xp", "gold")
    if any(field not in raw_enemy for field in required):
        raise ValueError("Saved enemy data is missing required fields.")
    if not isinstance(raw_enemy["name"], str) or not raw_enemy["name"].strip():
        raise ValueError("Saved enemy name must be a non-empty string.")

    enemy = {
        "name": raw_enemy["name"],
        "hp": _as_int(raw_enemy["hp"], "enemy.hp"),
        "max_hp": _as_int(raw_enemy.get("max_hp", raw_enemy["hp"]), "enemy.max_hp", minimum=1),
        "attack": _as_int(raw_enemy["attack"], "enemy.attack", minimum=1),
        "xp": _as_int(raw_enemy["xp"], "enemy.xp"),
        "gold": _as_int(raw_enemy["gold"], "enemy.gold"),
    }
    enemy["hp"] = min(enemy["hp"], enemy["max_hp"])
    return enemy


def normalize_save(raw):
    if not isinstance(raw, dict):
        raise ValueError("Save file must contain a JSON object.")

    if raw.get("schema_version") == SAVE_VERSION and "player" in raw:
        battle = raw.get("battle")
        if battle is not None:
            if not isinstance(battle, dict) or "enemy" not in battle:
                raise ValueError("Saved battle data is invalid.")
            battle = {"enemy": _upgrade_enemy(battle["enemy"])}
        return {
            "schema_version": SAVE_VERSION,
            "player": upgrade_player(raw["player"]),
            "battle": battle,
        }

    if "player" in raw and "enemy" in raw:
        battle = (
            {"enemy": _upgrade_enemy(raw["enemy"])}
            if raw.get("in_battle")
            else None
        )
        return {
            "schema_version": SAVE_VERSION,
            "player": upgrade_player(raw["player"]),
            "battle": battle,
        }

    if any(field in raw for field in ("name", "hp", "level", "inventory")):
        return {
            "schema_version": SAVE_VERSION,
            "player": upgrade_player(raw),
            "battle": None,
        }

    raise ValueError("Save file has an unrecognized format.")


def save_game(state):
    normalized = normalize_save(state)
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    temp_file = SAVE_FILE.with_name(SAVE_FILE.name + ".tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as save_file:
            json.dump(normalized, save_file, indent=2)
            save_file.flush()
            os.fsync(save_file.fileno())
        os.replace(temp_file, SAVE_FILE)
    finally:
        if temp_file.exists():
            temp_file.unlink()


def load_game():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as save_file:
            raw = json.load(save_file)
    except FileNotFoundError:
        return new_state()
    except json.JSONDecodeError as exc:
        raise ValueError(f"Save file contains invalid JSON: {SAVE_FILE}") from exc

    state = normalize_save(raw)
    if raw.get("schema_version") != SAVE_VERSION:
        save_game(state)
    return state


def check_level_up(player):
    while player["xp"] >= player["level"] * 25:
        player["xp"] -= player["level"] * 25
        player["level"] += 1
        player["max_hp"] += 15
        player["hp"] = player["max_hp"]
        player["attack"] += 3
        print(f"Level up! You are now level {player['level']}.")


def start_battle(state):
    enemy = dict(random.choice(ENEMIES))
    enemy["max_hp"] = enemy["hp"]
    state["battle"] = {"enemy": enemy}
    print(f"\nA wild {enemy['name']} appears!")
    save_game(state)


def use_item(state, item_name):
    player = state["player"]
    item_name = item_name.strip()
    if item_name not in ITEMS:
        print(f"{item_name!r} is not a usable item.")
        return False
    if player["inventory"].get(item_name, 0) <= 0:
        print(f"You don't have any {item_name}.")
        return False

    item = ITEMS[item_name]
    if item["effect"] == "heal":
        old_hp = player["hp"]
        player["hp"] = min(player["max_hp"], player["hp"] + item["amount"])
        print(f"Used a {item_name}; recovered {player['hp'] - old_hp} HP.")

    player["inventory"][item_name] -= 1
    if player["inventory"][item_name] == 0:
        del player["inventory"][item_name]
    save_game(state)
    return True


def buy_item(state, item_name):
    player = state["player"]
    if item_name not in ITEMS:
        print(f"{item_name!r} is not sold here.")
        return False

    item = ITEMS[item_name]
    if player["gold"] < item["price"]:
        print(f"Not enough gold for {item_name}.")
        return False

    player["gold"] -= item["price"]
    player["inventory"][item_name] = player["inventory"].get(item_name, 0) + 1
    print(f"Bought a {item_name}.")
    save_game(state)
    return True


def shop(state):
    print(f"Gold: {state['player']['gold']}")
    for name, item in ITEMS.items():
        print(f"  {name} - {item['price']} gold")
    choice = input("Buy which item? (or 'exit')\n> ").strip()
    if choice == "exit":
        return
    buy_item(state, choice)


def battle(state):
    if state["battle"] is None:
        start_battle(state)

    player = state["player"]
    enemy = state["battle"]["enemy"]

    while enemy["hp"] > 0 and player["hp"] > 0:
        choice = input("1) Attack  2) Save & Quit Battle\n> ").strip()
        if choice == "2":
            save_game(state)
            print("Battle saved. See you next time!")
            return "saved"
        if choice != "1":
            print("Invalid choice.")
            continue

        damage = random.randint(max(1, player["attack"] - 3), player["attack"] + 3)
        enemy["hp"] = max(0, enemy["hp"] - damage)
        print(f"You hit the {enemy['name']} for {damage}. (Enemy HP: {enemy['hp']})")
        if enemy["hp"] > 0:
            damage = random.randint(max(1, enemy["attack"] - 2), enemy["attack"] + 2)
            player["hp"] = max(0, player["hp"] - damage)
            print(f"The {enemy['name']} hits you for {damage}. (Your HP: {player['hp']})")

        if player["hp"] > 0 and enemy["hp"] > 0:
            save_game(state)

    if player["hp"] == 0:
        print("You were defeated. Your progress is safe; you recover with 1 HP.")
        player["hp"] = 1
        state["battle"] = None
        save_game(state)
        return "lost"

    print(f"Victory! +{enemy['xp']} XP, +{enemy['gold']} gold")
    player["xp"] += enemy["xp"]
    player["gold"] += enemy["gold"]
    check_level_up(player)
    state["battle"] = None
    save_game(state)
    return "won"


def new_game_option():
    confirm = input("Erase the existing save and start over? (yes/no)\n> ").strip().lower()
    if confirm != "yes":
        print("Cancelled.")
        return None

    state = new_state()
    save_game(state)
    print("Starting a new game.")
    return state


def show_stats(player):
    xp_needed = player["level"] * 25
    print(f"\n{player['name']} — Level {player['level']}")
    print(f"HP: {player['hp']}/{player['max_hp']}")
    print(f"Attack: {player['attack']}")
    print(f"XP: {player['xp']}/{xp_needed}")
    print(f"Gold: {player['gold']}")
    print(f"Inventory: {player['inventory']}")


def main():
    try:
        state = load_game()
    except ValueError as exc:
        print(f"Could not load your save: {exc}")
        print("The save was left unchanged. Move or repair it before starting a new game.")
        return

    if state["battle"] is not None:
        enemy_name = state["battle"]["enemy"]["name"]
        print(f"Welcome back! Resuming your battle against {enemy_name}.")
        if battle(state) == "saved":
            return
    else:
        print(f"Welcome back, {state['player']['name']}! (Level {state['player']['level']})")

    while True:
        choice = input(
            "\n1) Fight  2) Rest  3) Stats  4) Save & Quit"
            "  5) New Game  6) Shop  7) Use Item\n> "
        ).strip()

        if choice == "1":
            battle(state)
        elif choice == "2":
            state["player"]["hp"] = state["player"]["max_hp"]
            save_game(state)
            print("You rest and recover all HP.")
        elif choice == "3":
            show_stats(state["player"])
        elif choice == "4":
            save_game(state)
            print("Game saved. See you next time!")
            break
        elif choice == "5":
            replacement_state = new_game_option()
            if replacement_state is not None:
                state = replacement_state
        elif choice == "6":
            shop(state)
        elif choice == "7":
            print("Inventory:", state["player"]["inventory"])
            use_item(state, input("Use which item?\n> "))
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
