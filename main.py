import tkinter as tk

from pet import KitKat
from brain import KiteelegenceBrain
from menu import CatMenu
from console import ControlCenter
from tray import TrayController
from updater import check_for_update

class Kittelligence:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()

        self.shutting_down = False

        self.pet = KitKat(self.root)
        self.brain = KiteelegenceBrain(self.pet)

        self.console = ControlCenter(
            self.pet,
            self.brain
        )

        self.menu = CatMenu(
            self.pet,
            self.brain,
            self.console
        )

        self.pet.set_menu(self.menu)
        self.pet.set_console(self.console)

        self.tray = TrayController(
            self.pet,
            self.console,
            self.brain,
            self.shutdown
        )

        self.tray.start()
        self.brain.start()

        # If someone tries to close the Tk root.
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)

    def run(self):
        self.root.mainloop()

    def shutdown(self):
        if self.shutting_down:
            return

        self.shutting_down = True

        print("[Kittelligence] Shutting down...")

        # Stop the AI first.
        try:
            self.brain.stop()
        except Exception as e:
            print(f"[Kittelligence] Brain shutdown error: {e}")

        # Stop the tray icon.
        try:
            self.tray.stop()
        except Exception as e:
            print(f"[Kittelligence] Tray shutdown error: {e}")

        # Destroy KitKat.
        try:
            self.pet.destroy()
        except Exception as e:
            print(f"[Kittelligence] Pet shutdown error: {e}")

        # Close Tkinter.
        try:
            self.root.quit()
        except Exception:
            pass

        try:
            self.root.destroy()
        except Exception:
            pass


if __name__ == "__main__":

    check_for_update()

    app = Kittelligence()
    app.run()