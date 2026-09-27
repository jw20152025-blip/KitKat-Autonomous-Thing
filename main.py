import tkinter as tk

from pet import KitKat
from brain import KiteelegenceBrain
from menu import CatMenu
from console import ControlCenter
from tray import TrayController


class Kittelligence:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()

        # Core systems
        self.pet = KitKat(self.root)
        self.brain = KiteelegenceBrain(self.pet)

        # Control Center
        self.console = ControlCenter(
            self.pet,
            self.brain
        )

        # Right-click menu
        self.menu = CatMenu(
            self.pet,
            self.brain,
            self.console
        )

        # Connect everything
        self.pet.set_menu(self.menu)
        self.pet.set_console(self.console)

        # System tray
        self.tray = TrayController(
            self.pet,
            self.console,
            self.brain,
            self.shutdown
        )

        self.tray.start()
        self.brain.start()

    def run(self):
        self.root.mainloop()

    def shutdown(self):
        try:
            self.brain.stop()
        except Exception:
            pass

        try:
            self.tray.stop()
        except Exception:
            pass

        try:
            self.pet.destroy()
        except Exception:
            pass

        try:
            self.root.quit()
        except Exception:
            pass


if __name__ == "__main__":
    app = Kittelligence()
    app.run()