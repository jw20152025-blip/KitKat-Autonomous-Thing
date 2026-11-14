from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from pathlib import Path

from brain import AutonomousBrain
from control_center import ControlCenter
from kitkat import KitKatPet
from storage import MemoryStore
from updater import UpdateManager

APP_VERSION = "2.0.0"


class KittelligenceApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("Kittelligence")
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)

        self.store = MemoryStore()
        self.pet = KitKatPet(self.root)
        self.brain = AutonomousBrain(self.pet, self.store)
        self.console = ControlCenter(self.root, self.pet, self.brain, self.store)
        self.updater = UpdateManager(self.root, APP_VERSION)

        self.pet.on_interaction = self.brain.on_petted
        self.pet.on_menu = self.show_menu
        self.brain.start()
        self._build_menu()

        self.root.after(1800, self.check_updates_silently)

    def _build_menu(self):
        self.menu = tk.Menu(self.root, tearoff=False)
        self.menu.add_command(label="Open Kittelligence Control Center", command=self.console.show)
        self.menu.add_command(label="Pause / Resume autonomy", command=self.brain.toggle_pause)
        self.menu.add_separator()
        self.menu.add_command(label="Check for updates…", command=lambda: self.updater.check(manual=True))
        self.menu.add_command(label="Quit", command=self.shutdown)

    def show_menu(self, x, y):
        try:
            self.menu.tk_popup(x, y)
        finally:
            self.menu.grab_release()

    def check_updates_silently(self):
        self.updater.check(manual=False)

    def run(self):
        self.root.mainloop()

    def shutdown(self):
        self.brain.stop()
        self.store.save(self.brain.export_state())
        self.pet.destroy()
        self.root.destroy()


if __name__ == "__main__":
    KittelligenceApp().run()
