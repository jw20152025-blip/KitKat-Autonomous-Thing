import tkinter as tk


class CatMenu:
    def __init__(self, pet, brain, console):
        self.pet = pet
        self.brain = brain
        self.console = console

        self.menu = tk.Menu(
            self.pet.window,
            tearoff=False
        )

        self._build_menu()

    def _build_menu(self):
        self.menu.add_command(
            label="🐱 Meow",
            command=self.pet.meow
        )

        self.menu.add_command(
            label="🎯 Chase Cursor",
            command=self.pet.chase_cursor
        )

        self.menu.add_separator()

        self.menu.add_command(
            label="🚶 Random Walk",
            command=self.pet.random_walk
        )

        self.menu.add_command(
            label="🪑 Sit",
            command=self.pet.sit
        )

        self.menu.add_command(
            label="😴 Sleep",
            command=self.pet.sleep
        )

        self.menu.add_separator()

        self.menu.add_command(
            label="👻 Hide KitKat",
            command=self.pet.hide
        )

        self.menu.add_command(
            label="👁 Show KitKat",
            command=self.pet.show
        )

        self.menu.add_command(
            label="🔒 Lock KitKat",
            command=self.pet.lock
        )

        self.menu.add_command(
            label="🔓 Unlock KitKat",
            command=self.pet.unlock
        )

        self.menu.add_separator()

        self.menu.add_command(
            label="📦 Confine",
            command=self.confine
        )

        self.menu.add_command(
            label="🌎 Release",
            command=self.pet.release
        )

        self.menu.add_separator()

        self.menu.add_command(
            label="⏸ Pause AI",
            command=self.pet.pause
        )

        self.menu.add_command(
            label="▶ Resume AI",
            command=self.pet.resume
        )

        self.menu.add_separator()

        self.menu.add_command(
            label="⚙ Control Center",
            command=self.open_console
        )

        self.menu.add_command(
            label="❌ Close Menu",
            command=self.hide
        )

    def show(self, x, y):
        try:
            self.menu.tk_popup(x, y)
        finally:
            self.menu.grab_release()

    def hide(self):
        try:
            self.menu.unpost()
        except Exception:
            pass

    def confine(self):
        width = 500
        height = 400

        x = int(self.pet.x - width / 2)
        y = int(self.pet.y - height / 2)

        self.pet.confine(
            x=x,
            y=y,
            width=width,
            height=height
        )

    def open_console(self):
        if self.console:
            self.console.show()