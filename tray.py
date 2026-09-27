import threading

import pystray
from PIL import Image


class TrayController:
    def __init__(self, pet, console, brain, shutdown):
        self.pet = pet
        self.console = console
        self.brain = brain
        self.shutdown_callback = shutdown

        self.icon = None
        self.thread = None

    def _create_image(self):
        try:
            return Image.open(
                "assets/idle/kitkat.png"
            ).convert("RGBA")
        except Exception:
            return Image.new(
                "RGBA",
                (64, 64),
                (0, 0, 0, 0)
            )

    def _show_kitkat(self, icon=None, item=None):
        self.pet.show()

    def _hide_kitkat(self, icon=None, item=None):
        self.pet.hide()

    def _open_console(self, icon=None, item=None):
        self.console.show()

    def _exit(self, icon=None, item=None):
        self.shutdown_callback()

    def start(self):
        menu = pystray.Menu(
            pystray.MenuItem(
                "🐱 Show KitKat",
                self._show_kitkat
            ),
            pystray.MenuItem(
                "👻 Hide KitKat",
                self._hide_kitkat
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "⚙ Control Center",
                self._open_console
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "❌ Exit Kittelligence",
                self._exit
            )
        )

        self.icon = pystray.Icon(
            "Kittelligence",
            self._create_image(),
            "Kittelligence",
            menu
        )

        self.thread = threading.Thread(
            target=self.icon.run,
            daemon=True
        )

        self.thread.start()

    def stop(self):
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass

            self.icon = None