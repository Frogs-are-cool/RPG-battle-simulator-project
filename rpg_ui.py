import tkinter as tk
from tkinter import messagebox, ttk

import rpg_game as game


BACKGROUND = "#101820"
PANEL = "#1b2833"
PANEL_LIGHT = "#243542"
TEXT = "#f2eadb"
MUTED = "#a9b5bd"
GOLD = "#e5b85c"
GREEN = "#71c99a"
RED = "#e87575"


class RPGWindow:
    def __init__(self, root, state):
        self.root = root
        self.state = state
        self.root.title("Emberfall - RPG Battle Simulator")
        self.root.geometry("900x700")
        self.root.minsize(760, 610)
        self.root.configure(background=BACKGROUND)
        self.root.protocol("WM_DELETE_WINDOW", self.save_and_quit)
        self._configure_styles()
        self._build_layout()
        self._write_log("Your adventure begins. Choose an action below.")
        if self.state["battle"] is not None:
            enemy = self.state["battle"]["enemy"]
            self._write_log(f"You are resuming your battle against {enemy['name']}.")
        self.refresh()

    def _configure_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", font=("Helvetica", 11))
        style.configure("TFrame", background=BACKGROUND)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("PanelLight.TFrame", background=PANEL_LIGHT)
        style.configure("TLabel", background=BACKGROUND, foreground=TEXT)
        style.configure("Panel.TLabel", background=PANEL, foreground=TEXT)
        style.configure("Muted.TLabel", background=PANEL, foreground=MUTED)
        style.configure("Title.TLabel", background=BACKGROUND, foreground=GOLD,
                        font=("Helvetica", 24, "bold"))
        style.configure("Heading.TLabel", background=PANEL, foreground=GOLD,
                        font=("Helvetica", 15, "bold"))
        style.configure("Stat.TLabel", background=PANEL, foreground=TEXT,
                        font=("Helvetica", 12, "bold"))
        style.configure("TButton", padding=(12, 9), background=PANEL_LIGHT,
                        foreground=TEXT, borderwidth=0)
        style.map("TButton", background=[("active", "#344d5c"), ("disabled", PANEL)])
        style.configure("Accent.TButton", background="#80612b", foreground="#ffffff")
        style.map("Accent.TButton", background=[("active", "#9e7937")])
        style.configure("Health.Horizontal.TProgressbar", troughcolor="#394751",
                        background=GREEN, bordercolor="#394751", lightcolor=GREEN,
                        darkcolor=GREEN)
        style.configure("Enemy.Horizontal.TProgressbar", troughcolor="#394751",
                        background=RED, bordercolor="#394751", lightcolor=RED,
                        darkcolor=RED)
        style.configure("XP.Horizontal.TProgressbar", troughcolor="#394751",
                        background=GOLD, bordercolor="#394751", lightcolor=GOLD,
                        darkcolor=GOLD)

    def _build_layout(self):
        shell = ttk.Frame(self.root, padding=24)
        shell.pack(fill="both", expand=True)

        ttk.Label(shell, text="EMBERFALL", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            shell,
            text="A small adventure. A very large number of goblins.",
            foreground=MUTED,
        ).pack(anchor="w", pady=(2, 18))

        panels = ttk.Frame(shell)
        panels.pack(fill="x")
        panels.columnconfigure(0, weight=1)
        panels.columnconfigure(1, weight=1)

        self.player_panel = ttk.Frame(panels, style="Panel.TFrame", padding=18)
        self.player_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.enemy_panel = ttk.Frame(panels, style="Panel.TFrame", padding=18)
        self.enemy_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        ttk.Label(self.player_panel, text="HERO", style="Heading.TLabel").pack(anchor="w")
        self.player_name = ttk.Label(self.player_panel, style="Stat.TLabel")
        self.player_name.pack(anchor="w", pady=(14, 3))
        self.hp_text = ttk.Label(self.player_panel, style="Muted.TLabel")
        self.hp_text.pack(anchor="w")
        self.hp_bar = ttk.Progressbar(
            self.player_panel, style="Health.Horizontal.TProgressbar", maximum=100
        )
        self.hp_bar.pack(fill="x", pady=(5, 12))
        self.xp_text = ttk.Label(self.player_panel, style="Muted.TLabel")
        self.xp_text.pack(anchor="w")
        self.xp_bar = ttk.Progressbar(
            self.player_panel, style="XP.Horizontal.TProgressbar", maximum=100
        )
        self.xp_bar.pack(fill="x", pady=(5, 12))
        self.player_stats = ttk.Label(self.player_panel, style="Panel.TLabel")
        self.player_stats.pack(anchor="w", pady=(4, 0))
        self.inventory_text = ttk.Label(self.player_panel, style="Muted.TLabel")
        self.inventory_text.pack(anchor="w", pady=(8, 0))

        ttk.Label(self.enemy_panel, text="ENCOUNTER", style="Heading.TLabel").pack(anchor="w")
        self.enemy_name = ttk.Label(self.enemy_panel, style="Stat.TLabel")
        self.enemy_name.pack(anchor="w", pady=(14, 3))
        self.enemy_hp_text = ttk.Label(self.enemy_panel, style="Muted.TLabel")
        self.enemy_hp_text.pack(anchor="w")
        self.enemy_hp_bar = ttk.Progressbar(
            self.enemy_panel, style="Enemy.Horizontal.TProgressbar", maximum=100
        )
        self.enemy_hp_bar.pack(fill="x", pady=(5, 12))
        ttk.Label(
            self.enemy_panel,
            text="Find a battle to discover who is lurking nearby.",
            style="Muted.TLabel",
            wraplength=330,
        ).pack(anchor="w", pady=(4, 0))

        ttk.Label(shell, text="ADVENTURE LOG", style="Heading.TLabel").pack(
            anchor="w", pady=(20, 8)
        )
        log_frame = ttk.Frame(shell, style="Panel.TFrame", padding=8)
        log_frame.pack(fill="both", expand=True)
        self.log = tk.Text(
            log_frame,
            height=8,
            wrap="word",
            state="disabled",
            background=PANEL,
            foreground=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=("Menlo", 11),
            padx=8,
            pady=8,
        )
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scrollbar.set)
        self.log.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        actions = ttk.Frame(shell)
        actions.pack(fill="x", pady=(16, 0))
        for column in range(4):
            actions.columnconfigure(column, weight=1)

        self.find_button = ttk.Button(
            actions, text="Find Battle", style="Accent.TButton", command=self.find_battle
        )
        self.find_button.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        self.attack_button = ttk.Button(actions, text="Attack", command=self.attack)
        self.attack_button.grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        self.rest_button = ttk.Button(actions, text="Rest", command=self.rest)
        self.rest_button.grid(row=0, column=2, sticky="ew", padx=4, pady=4)
        self.potion_button = ttk.Button(
            actions, text="Use Potion", command=self.use_potion
        )
        self.potion_button.grid(row=0, column=3, sticky="ew", padx=4, pady=4)

        self.shop_button = ttk.Button(
            actions, text="Buy Potion (10 gold)", command=self.buy_potion
        )
        self.shop_button.grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, pady=4)
        self.new_game_button = ttk.Button(
            actions, text="New Game", command=self.new_game
        )
        self.new_game_button.grid(row=1, column=2, sticky="ew", padx=4, pady=4)
        self.save_button = ttk.Button(
            actions, text="Save & Quit", command=self.save_and_quit
        )
        self.save_button.grid(row=1, column=3, sticky="ew", padx=4, pady=4)

    def _write_log(self, message):
        self.log.configure(state="normal")
        self.log.insert("end", f"{message}\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _perform(self, action):
        try:
            action()
        except (OSError, ValueError) as exc:
            messagebox.showerror("Game action failed", str(exc), parent=self.root)
        self.refresh()

    def find_battle(self):
        def action():
            self._write_log(game.start_battle(self.state))

        self._perform(action)

    def attack(self):
        def action():
            messages, result = game.battle_turn(self.state)
            for message in messages:
                self._write_log(message)
            if result == "won":
                self._write_log("The encounter is over. Your rewards have been saved.")
            elif result == "lost":
                self._write_log("Catch your breath, then decide your next move.")

        self._perform(action)

    def rest(self):
        def action():
            player = self.state["player"]
            recovered = player["max_hp"] - player["hp"]
            player["hp"] = player["max_hp"]
            game.save_game(self.state)
            self._write_log(f"You rest and recover {recovered} HP.")

        self._perform(action)

    def use_potion(self):
        def action():
            self._write_log(game.use_item(self.state, "Potion"))

        self._perform(action)

    def buy_potion(self):
        def action():
            self._write_log(game.buy_item(self.state, "Potion"))

        self._perform(action)

    def new_game(self):
        if not messagebox.askyesno(
            "Start over?", "Replace your saved adventure with a new game?",
            parent=self.root,
        ):
            return

        def action():
            state = game.new_state()
            game.save_game(state)
            self.state = state
            self._write_log("A new adventure begins.")

        self._perform(action)

    def refresh(self):
        player = self.state["player"]
        self.player_name.configure(text=f"{player['name']}  |  Level {player['level']}")
        self.hp_text.configure(text=f"Health  {player['hp']} / {player['max_hp']}")
        self.hp_bar.configure(maximum=player["max_hp"], value=player["hp"])
        xp_needed = player["level"] * 25
        self.xp_text.configure(text=f"Experience  {player['xp']} / {xp_needed}")
        self.xp_bar.configure(maximum=xp_needed, value=player["xp"])
        self.player_stats.configure(
            text=f"Attack  {player['attack']}       Gold  {player['gold']}"
        )
        inventory = player["inventory"]
        inventory_summary = ", ".join(
            f"{name} x{count}" for name, count in inventory.items()
        ) or "Empty"
        self.inventory_text.configure(text=f"Inventory  {inventory_summary}")

        battle = self.state["battle"]
        in_battle = battle is not None
        if in_battle:
            enemy = battle["enemy"]
            self.enemy_name.configure(text=enemy["name"])
            self.enemy_hp_text.configure(text=f"Health  {enemy['hp']} / {enemy['max_hp']}")
            self.enemy_hp_bar.configure(maximum=enemy["max_hp"], value=enemy["hp"])
        else:
            self.enemy_name.configure(text="No active enemy")
            self.enemy_hp_text.configure(text="Health  -")
            self.enemy_hp_bar.configure(maximum=100, value=0)

        self.find_button.configure(state="disabled" if in_battle else "normal")
        self.attack_button.configure(state="normal" if in_battle else "disabled")
        self.rest_button.configure(state="disabled" if in_battle else "normal")
        self.shop_button.configure(state="disabled" if in_battle else "normal")
        self.potion_button.configure(
            state="normal"
            if not in_battle and inventory.get("Potion", 0) > 0
            else "disabled"
        )

    def save_and_quit(self):
        try:
            game.save_game(self.state)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Could not save game", str(exc), parent=self.root)
            return
        self.root.destroy()


def main():
    root = tk.Tk()
    try:
        state = game.load_game()
    except (OSError, ValueError) as exc:
        messagebox.showerror(
            "Could not load save",
            f"{exc}\n\nYour existing save has not been replaced.",
            parent=root,
        )
        root.destroy()
        return

    RPGWindow(root, state)
    root.mainloop()


if __name__ == "__main__":
    main()
