from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ControlCenter:
    def __init__(self, root, pet, brain, store):
        self.root, self.pet, self.brain, self.store = root, pet, brain, store
        self.window = None
        self.values = {}

    def show(self):
        if self.window and self.window.winfo_exists():
            self.window.deiconify()
            self.window.lift()
            return
        self.window = tk.Toplevel(self.root)
        self.window.title("Kittelligence Control Center")
        self.window.geometry("460x540")
        self.window.minsize(420, 480)
        self.window.protocol("WM_DELETE_WINDOW", self.window.withdraw)
        outer = ttk.Frame(self.window, padding=18)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Kittelligence", font=("Segoe UI", 21, "bold")).pack(anchor="w")
        ttk.Label(outer, text="KitKat's little corner of your desktop").pack(anchor="w", pady=(0, 14))

        actions = ttk.LabelFrame(outer, text="Quick actions", padding=10)
        actions.pack(fill="x", pady=6)
        for label, command in [
            ("Wander", self.pet.wander), ("Sit", self.pet.sit),
            ("Sleep", self.pet.sleep), ("Meow", self.pet.meow),
            ("Show", self.pet.show), ("Hide", self.pet.hide),
            ("Pause / resume autonomy", self.brain.toggle_pause),
        ]:
            ttk.Button(actions, text=label, command=command).pack(fill="x", pady=2)

        stats = ttk.LabelFrame(outer, text="Live status", padding=10)
        stats.pack(fill="both", expand=True, pady=6)
        for key in ("last_action", "energy", "happiness", "boredom", "hunger", "total_pets", "memory_file"):
            row = ttk.Frame(stats)
            row.pack(fill="x", pady=3)
            ttk.Label(row, text=key.replace("_", " ").title(), width=18).pack(side="left")
            value = ttk.Label(row, text="—")
            value.pack(side="left")
            self.values[key] = value
        self._refresh()

    def _refresh(self):
        if not self.window or not self.window.winfo_exists():
            return
        state = self.brain.export_state()
        values = {
            "last_action": self.brain.last_action,
            "energy": f"{state['energy']:.0%}",
            "happiness": f"{state['happiness']:.0%}",
            "boredom": f"{state['boredom']:.0%}",
            "hunger": f"{state['hunger']:.0%}",
            "total_pets": state["total_pets"],
            "memory_file": str(self.store.path),
        }
        for key, label in self.values.items():
            label.config(text=str(values[key]))
        self.window.after(700, self._refresh)
