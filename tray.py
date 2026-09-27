import threading

import pystray
from PIL import Image


class TrayController:
    def __init__(
        self,
        pet,
        console,
        brain,
        shutdown
    ):
        self.pet = pet
        self.console = console
        self.brain = brain
        self.shutdown_callback = shutdown

        image = Image.new(
            "RGBA",
            (64, 64),
            (0, 0, 0, 0)
        )

        self.icon = pystray.Icon(
            "Kiteelegence",
            image,
            "Kiteelegence",
            menu=pystray.Menu(
                pystray.MenuItem(
                    "Show KitKat",
                    self.show
                ),
                pystray.MenuItem(
                    "Hide KitKat",
                    self.hide
                ),
                pystray.MenuItem(
                    "Control Center",
                    self.open_console
                ),
                pystray.MenuItem(
                    "Pause AI",
                    self.pause
                ),
                pystray.MenuItem(
                    "Resume AI",
                    self.resume
                ),
                pystray.MenuItem(
                    "Exit Kiteelegence",
                    self.exit
                )
            )
        )

    def start(self):
        threading.Thread(
            target=self.icon.run,
            daemon=True
        ).start()

    def show(self):
        self.pet.root.after(
            0,
            self.pet.show
        )

    def hide(self):
        self.pet.root.after(
            0,
            self.pet.hide
        )

    def open_console(self):
        self.pet.root.after(
            0,
            self.console.show
        )

    def pause(self):
        self.pet.root.after(
            0,
            self.pet.pause
        )

    def resume(self):
        self.pet.root.after(
            0,
            self.pet.resume
        )

    def exit(self):
        self.pet.root.after(
            0,
            self.shutdown_callback
        )

    def stop(self):
        try:
            self.icon.stop()
        except Exception:
            pass