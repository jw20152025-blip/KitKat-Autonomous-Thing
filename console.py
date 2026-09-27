import tkinter as tk
from tkinter import ttk


class ControlCenter:
    def __init__(self, pet, brain):
        self.pet = pet
        self.brain = brain

        self.window = None
        self.stats_labels = {}

    def show(self):
        if self.window is not None:
            try:
                if self.window.winfo_exists():
                    self.window.deiconify()
                    self.window.lift()
                    self.window.focus_force()
                    return
            except tk.TclError:
                pass

        self._create_window()

    def _create_window(self):
        self.window = tk.Toplevel(self.pet.root)

        self.window.title("Kiteelegence Control Center")
        self.window.geometry("520x680")
        self.window.minsize(480, 600)

        self.window.protocol(
            "WM_DELETE_WINDOW",
            self.hide
        )

        self._build_ui()
        self._update_stats()

    # =========================================================
    # UI
    # =========================================================

    def _build_ui(self):
        main = ttk.Frame(
            self.window,
            padding=15
        )

        main.pack(
            fill="both",
            expand=True
        )

        title = ttk.Label(
            main,
            text="🐈 Kiteelegence Control Center",
            font=("Segoe UI", 18, "bold")
        )

        title.pack(
            pady=(0, 15)
        )

        # -----------------------------------------------------
        # KitKat controls
        # -----------------------------------------------------

        controls = ttk.LabelFrame(
            main,
            text="KitKat"
        )

        controls.pack(
            fill="x",
            pady=5
        )

        self._button(
            controls,
            "👁 Show",
            self.pet.show
        )

        self._button(
            controls,
            "👻 Hide",
            self.pet.hide
        )

        self._button(
            controls,
            "🔒 Lock",
            self.pet.lock
        )

        self._button(
            controls,
            "🔓 Unlock",
            self.pet.unlock
        )

        self._button(
            controls,
            "📦 Confine",
            self.confine
        )

        self._button(
            controls,
            "🌎 Release",
            self.pet.release
        )

        # -----------------------------------------------------
        # Behavior
        # -----------------------------------------------------

        behavior = ttk.LabelFrame(
            main,
            text="Behavior"
        )

        behavior.pack(
            fill="x",
            pady=5
        )

        self._button(
            behavior,
            "🚶 Random Walk",
            self.pet.random_walk
        )

        self._button(
            behavior,
            "🎯 Chase Cursor",
            self.pet.chase_cursor
        )

        self._button(
            behavior,
            "🪑 Sit",
            self.pet.sit
        )

        self._button(
            behavior,
            "😴 Sleep",
            self.pet.sleep
        )

        self._button(
            behavior,
            "🐱 Meow",
            self.pet.meow
        )

        self._button(
            behavior,
            "🔊 Purr",
            self.pet.purr
        )

        # -----------------------------------------------------
        # AI
        # -----------------------------------------------------

        ai = ttk.LabelFrame(
            main,
            text="AI"
        )

        ai.pack(
            fill="x",
            pady=5
        )

        self._button(
            ai,
            "⏸ Pause AI",
            self.pause_ai
        )

        self._button(
            ai,
            "▶ Resume AI",
            self.resume_ai
        )

        # -----------------------------------------------------
        # Statistics
        # -----------------------------------------------------

        stats = ttk.LabelFrame(
            main,
            text="Live State"
        )

        stats.pack(
            fill="both",
            expand=True,
            pady=5
        )

        fields = [
            "state",
            "animation",
            "x",
            "y",
            "energy",
            "happiness",
            "boredom",
            "curiosity",
            "affection",
            "hunger",
            "excitement",
            "last_action",
            "actions",
        ]

        for field in fields:

            row = ttk.Frame(stats)

            row.pack(
                fill="x",
                padx=8,
                pady=2
            )

            name = ttk.Label(
                row,
                text=field.replace(
                    "_",
                    " "
                ).title() + ":",
                width=16
            )

            name.pack(
                side="left"
            )

            value = ttk.Label(
                row,
                text="..."
            )

            value.pack(
                side="left"
            )

            self.stats_labels[field] = value

    def _button(self, parent, text, command):
        button = ttk.Button(
            parent,
            text=text,
            command=command
        )

        button.pack(
            fill="x",
            padx=8,
            pady=3
        )

    # =========================================================
    # ACTIONS
    # =========================================================

    def confine(self):
        width = 500
        height = 400

        x = int(
            self.pet.x - width / 2
        )

        y = int(
            self.pet.y - height / 2
        )

        self.pet.confine(
            x=x,
            y=y,
            width=width,
            height=height
        )

    def pause_ai(self):
        try:
            self.brain.pause()
        except AttributeError:
            self.pet.pause()

    def resume_ai(self):
        try:
            self.brain.resume()
        except AttributeError:
            self.pet.resume()

    def register_interaction(self, interaction):
        try:
            self.brain.register_pet(
                interaction
            )
        except Exception:
            pass

    # =========================================================
    # STATS
    # =========================================================

    def _update_stats(self):
        if self.window is None:
            return

        try:
            if not self.window.winfo_exists():
                return
        except tk.TclError:
            return

        pet_state = self.pet.get_state()

        values = {
            "state": (
                "Visible"
                if pet_state["visible"]
                else "Hidden"
            ),

            "animation": pet_state[
                "animation"
            ],

            "x": pet_state["x"],
            "y": pet_state["y"],
        }

        # Get AI state if available.
        try:
            brain_state = self.brain.get_state()

            values.update({
                "energy": brain_state.get(
                    "energy",
                    "?"
                ),

                "happiness": brain_state.get(
                    "happiness",
                    "?"
                ),

                "boredom": brain_state.get(
                    "boredom",
                    "?"
                ),

                "curiosity": brain_state.get(
                    "curiosity",
                    "?"
                ),

                "affection": brain_state.get(
                    "affection",
                    "?"
                ),

                "hunger": brain_state.get(
                    "hunger",
                    "?"
                ),

                "excitement": brain_state.get(
                    "excitement",
                    "?"
                ),

                "last_action": brain_state.get(
                    "last_action",
                    "?"
                ),

                "actions": brain_state.get(
                    "actions",
                    "?"
                ),
            })

        except Exception:
            pass

        for key, label in self.stats_labels.items():

            value = values.get(
                key,
                "?"
            )

            try:
                label.config(
                    text=str(value)
                )
            except tk.TclError:
                return

        self.window.after(
            500,
            self._update_stats
        )

    # =========================================================
    # HIDE / CLOSE
    # =========================================================

    def hide(self):
        if self.window is None:
            return

        try:
            self.window.withdraw()
        except tk.TclError:
            pass

    def destroy(self):
        if self.window is None:
            return

        try:
            self.window.destroy()
        except tk.TclError:
            pass

        self.window = None