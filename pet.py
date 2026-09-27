import ctypes
import math
import random
import tkinter as tk
import winsound
from ctypes import wintypes
from pathlib import Path

from PIL import Image, ImageTk


ROOT = Path(__file__).resolve().parent

ANIMATION_FOLDERS = {
    "idle": ROOT / "assets" / "idle",
    "walk": ROOT / "assets" / "walk",
    "chase": ROOT / "assets" / "chase",
    "sit": ROOT / "assets" / "sit",
    "sleep": ROOT / "assets" / "sleep",
    "meow": ROOT / "assets" / "meow",
}

SOUND_FOLDERS = {
    "meow": ROOT / "sounds" / "meow",
    "purr": ROOT / "sounds" / "purr",
}

FALLBACK_MEOW = ROOT / "sounds" / "meow.wav"


class KitKat:

    WINDOW_SIZE = 180

    def __init__(self, root):

        self.root = root

        # =====================================================
        # WINDOW
        # =====================================================

        self.window = tk.Toplevel(root)

        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)

        # Use a color that is unlikely to appear in KitKat.
        self.transparent_color = "#ff00ff"

        self.window.configure(
            bg=self.transparent_color
        )

        try:
            self.window.attributes(
                "-transparentcolor",
                self.transparent_color
            )
        except tk.TclError:
            pass

        self.canvas = tk.Canvas(
            self.window,
            width=self.WINDOW_SIZE,
            height=self.WINDOW_SIZE,
            bg=self.transparent_color,
            highlightthickness=0,
            bd=0
        )

        self.canvas.pack()

        # =====================================================
        # CONNECTIONS
        # =====================================================

        self.menu = None
        self.console = None

        # =====================================================
        # STATE
        # =====================================================

        self.destroyed = False

        self.visible = True
        self.locked = False
        self.paused = False
        self.confined = False

        self.current_animation = "idle"
        self.animation_index = 0

        self.animation_speed = 120

        self.x = 500.0
        self.y = 500.0

        self.target_x = self.x
        self.target_y = self.y

        self.walk_speed = 2.5
        self.chase_speed = 5.5

        self.direction = 1

        self.chasing_cursor = False

        self.interaction_count = 0

        # =====================================================
        # CONFINE BOX
        # =====================================================

        self.confine_x1 = 0
        self.confine_y1 = 0
        self.confine_x2 = 800
        self.confine_y2 = 600

        # =====================================================
        # DRAGGING
        # =====================================================

        self.dragging = False

        self.drag_offset_x = 0
        self.drag_offset_y = 0

        # =====================================================
        # ANIMATIONS
        # =====================================================

        self.animations = {}

        self._load_animations()

        # =====================================================
        # MOUSE
        # =====================================================

        self.canvas.bind(
            "<Button-1>",
            self._mouse_down
        )

        self.canvas.bind(
            "<B1-Motion>",
            self._mouse_drag
        )

        self.canvas.bind(
            "<ButtonRelease-1>",
            self._mouse_up
        )

        self.canvas.bind(
            "<Button-3>",
            self._right_click
        )

        self.canvas.bind(
            "<Double-Button-1>",
            self._double_click
        )

        # =====================================================
        # POSITION
        # =====================================================

        self._apply_boundaries()

        self._move_window()

        # =====================================================
        # START LOOPS
        # =====================================================

        self._set_animation("idle")

        self._animation_loop()
        self._movement_loop()

        print(
            "[KitKat] Animations:",
            {
                name: len(frames)
                for name, frames in self.animations.items()
            }
        )

    # =========================================================
    # CONNECTIONS
    # =========================================================

    def set_menu(self, menu):
        self.menu = menu

    def set_console(self, console):
        self.console = console

    # =========================================================
    # ANIMATION LOADING
    # =========================================================

    def _load_animations(self):

        for name, folder in ANIMATION_FOLDERS.items():

            frames = []

            if not folder.exists():
                self.animations[name] = []
                continue

            files = sorted(
                [
                    file
                    for file in folder.iterdir()
                    if file.suffix.lower()
                    in {
                        ".png",
                        ".jpg",
                        ".jpeg",
                        ".gif",
                        ".webp"
                    }
                ]
            )

            for file in files:

                try:

                    image = Image.open(
                        file
                    ).convert("RGBA")

                    max_size = 170

                    width, height = image.size

                    scale = min(
                        max_size / max(width, 1),
                        max_size / max(height, 1),
                        1
                    )

                    if scale != 1:

                        image = image.resize(
                            (
                                int(width * scale),
                                int(height * scale)
                            ),
                            Image.Resampling.LANCZOS
                        )

                    frame = ImageTk.PhotoImage(
                        image
                    )

                    frames.append(frame)

                except Exception as error:

                    print(
                        f"[KitKat] Could not load "
                        f"{file}: {error}"
                    )

            self.animations[name] = frames

    def _set_animation(self, name):

        frames = self.animations.get(
            name,
            []
        )

        if not frames:

            # If the requested animation doesn't
            # exist, safely fall back to idle.
            if name != "idle":
                idle = self.animations.get(
                    "idle",
                    []
                )

                if idle:
                    self.current_animation = "idle"
                    self.animation_index = 0

            return

        if self.current_animation != name:

            self.current_animation = name
            self.animation_index = 0

    def _animation_loop(self):

        if self.destroyed:
            return

        if self.visible:

            frames = self.animations.get(
                self.current_animation,
                []
            )

            if not frames:

                frames = self.animations.get(
                    "idle",
                    []
                )

            if frames:

                if self.animation_index >= len(frames):
                    self.animation_index = 0

                frame = frames[
                    self.animation_index
                ]

                self.canvas.delete(
                    "kitkat"
                )

                self.canvas.create_image(
                    self.WINDOW_SIZE // 2,
                    self.WINDOW_SIZE // 2,
                    image=frame,
                    anchor="center",
                    tags="kitkat"
                )

                self.animation_index += 1

        self.root.after(
            self.animation_speed,
            self._animation_loop
        )

    # =========================================================
    # WALK
    # =========================================================

    def walk(self):
        """Start autonomous walking toward a random destination."""

        if self.locked or self.paused:
            return

        self.chasing_cursor = False

        self.random_destination()

    def random_destination(self):
        """Choose a new random destination for the AI brain."""

        if self.locked or self.paused:
            return

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        margin = 50

        min_x = margin
        min_y = margin

        max_x = max(
            min_x,
            screen_width - self.WINDOW_SIZE - margin
        )

        max_y = max(
            min_y,
            screen_height - self.WINDOW_SIZE - margin
        )

        # Respect confinement.
        if self.confined:
            min_x = self.confine_x1
            min_y = self.confine_y1

            max_x = max(
                min_x,
                self.confine_x2 - self.WINDOW_SIZE
            )

            max_y = max(
                min_y,
                self.confine_y2 - self.WINDOW_SIZE
            )

        self.target_x = random.randint(
            int(min_x),
            int(max_x)
        )

        self.target_y = random.randint(
            int(min_y),
            int(max_y)
        )

        self._set_animation("walk")

    def random_walk(self):
        """Compatibility alias for the UI/menu."""

        self.random_destination()

    # =========================================================
    # MOVEMENT
    # =========================================================

    def _movement_loop(self):

        if self.destroyed:
            return

        if (
            self.visible
            and not self.paused
            and not self.locked
        ):

            # -------------------------------------------------
            # CONTINUOUS CURSOR CHASING
            # -------------------------------------------------

            if self.chasing_cursor:

                cursor_x, cursor_y = (
                    self.get_cursor_position()
                )

                self.target_x = (
                    cursor_x
                    - self.WINDOW_SIZE / 2
                )

                self.target_y = (
                    cursor_y
                    - self.WINDOW_SIZE / 2
                )

                self._set_animation(
                    "chase"
                )

            # -------------------------------------------------
            # MOVE TOWARD TARGET
            # -------------------------------------------------

            dx = self.target_x - self.x
            dy = self.target_y - self.y

            distance = math.hypot(
                dx,
                dy
            )

            if distance > 1:

                if self.chasing_cursor:
                    speed = self.chase_speed
                else:
                    speed = self.walk_speed

                step = min(
                    speed,
                    distance
                )

                self.x += (
                    dx / distance
                ) * step

                self.y += (
                    dy / distance
                ) * step

                self._update_direction(
                    dx
                )

                self._apply_boundaries()

                self._move_window()

            else:

                if (
                    self.current_animation
                    in {"walk", "chase"}
                    and not self.chasing_cursor
                ):

                    self._set_animation(
                        "idle"
                    )

        self.root.after(
            25,
            self._movement_loop
        )

    # =========================================================
    # CURSOR CHASE
    # =========================================================

    def chase_cursor(self):

        if self.locked:
            return

        if self.paused:
            return

        self.chasing_cursor = True

        self._set_animation(
            "chase"
        )

    def stop_chasing(self):

        self.chasing_cursor = False

        if self.current_animation == "chase":

            self._set_animation(
                "idle"
            )

    def get_cursor_position(self):

        point = wintypes.POINT()

        ctypes.windll.user32.GetCursorPos(
            ctypes.byref(point)
        )

        return (
            point.x,
            point.y
        )

    # =========================================================
    # DIRECTION
    # =========================================================

    def _update_direction(self, dx):

        if dx > 0:
            self.direction = 1

        elif dx < 0:
            self.direction = -1

    # =========================================================
    # BOUNDARIES
    # =========================================================

    def _apply_boundaries(self):

        screen_width = (
            self.root.winfo_screenwidth()
        )

        screen_height = (
            self.root.winfo_screenheight()
        )

        if self.confined:

            min_x = self.confine_x1
            min_y = self.confine_y1

            max_x = (
                self.confine_x2
                - self.WINDOW_SIZE
            )

            max_y = (
                self.confine_y2
                - self.WINDOW_SIZE
            )

        else:

            min_x = 0
            min_y = 0

            max_x = (
                screen_width
                - self.WINDOW_SIZE
            )

            max_y = (
                screen_height
                - self.WINDOW_SIZE
            )

        max_x = max(
            min_x,
            max_x
        )

        max_y = max(
            min_y,
            max_y
        )

        self.x = max(
            min_x,
            min(
                self.x,
                max_x
            )
        )

        self.y = max(
            min_y,
            min(
                self.y,
                max_y
            )
        )

    def _move_window(self):

        self.window.geometry(
            f"{self.WINDOW_SIZE}x"
            f"{self.WINDOW_SIZE}+"
            f"{int(self.x)}+"
            f"{int(self.y)}"
        )

    # =========================================================
    # HIDE / SHOW
    # =========================================================

    def hide(self):

        if self.destroyed:
            return

        self.visible = False

        self.window.withdraw()

    def show(self):

        if self.destroyed:
            return

        self.visible = True

        self.window.deiconify()

        self.window.attributes(
            "-topmost",
            True
        )

        self._move_window()

    def toggle_visibility(self):

        if self.visible:
            self.hide()
        else:
            self.show()

    # =========================================================
    # LOCK
    # =========================================================

    def lock(self):

        self.locked = True

        self.chasing_cursor = False

        self.target_x = self.x
        self.target_y = self.y

        self._set_animation(
            "idle"
        )

    def unlock(self):

        self.locked = False

    def toggle_lock(self):

        if self.locked:
            self.unlock()
        else:
            self.lock()

    # =========================================================
    # PAUSE
    # =========================================================

    def pause(self):

        self.paused = True

        self.chasing_cursor = False

        self._set_animation(
            "idle"
        )

    def resume(self):

        self.paused = False

    def toggle_pause(self):

        if self.paused:
            self.resume()
        else:
            self.pause()

    # =========================================================
    # CONFINE
    # =========================================================

    def confine(
        self,
        x=None,
        y=None,
        width=500,
        height=400
    ):

        if x is None:
            x = int(
                self.x
                - width / 2
            )

        if y is None:
            y = int(
                self.y
                - height / 2
            )

        self.confine_x1 = int(x)
        self.confine_y1 = int(y)

        self.confine_x2 = (
            int(x)
            + int(width)
        )

        self.confine_y2 = (
            int(y)
            + int(height)
        )

        self.confined = True

        self._apply_boundaries()

        self.target_x = self.x
        self.target_y = self.y

        self._move_window()

    def release(self):

        self.confined = False

    # =========================================================
    # SIT / SLEEP
    # =========================================================

    def sit(self):

        self.chasing_cursor = False

        self.target_x = self.x
        self.target_y = self.y

        self._set_animation(
            "sit"
        )

    def sleep(self):

        self.chasing_cursor = False

        self.target_x = self.x
        self.target_y = self.y

        self._set_animation(
            "sleep"
        )

    def wake(self):

        self._set_animation(
            "idle"
        )

    # =========================================================
    # MEOW
    # =========================================================

    def meow(self):

        self.interaction_count += 1

        self.chasing_cursor = False

        self._set_animation(
            "meow"
        )

        sound = self._find_sound(
            "meow"
        )

        if sound:
            self._play_sound(
                sound
            )

        elif FALLBACK_MEOW.exists():

            self._play_sound(
                FALLBACK_MEOW
            )

        self._register_interaction(
            "meow"
        )

    def purr(self):

        sound = self._find_sound(
            "purr"
        )

        if sound:
            self._play_sound(
                sound
            )

    def _find_sound(self, sound_type):

        folder = SOUND_FOLDERS.get(
            sound_type
        )

        if not folder:
            return None

        if not folder.exists():
            return None

        files = [
            file
            for file in folder.iterdir()
            if file.suffix.lower()
            == ".wav"
        ]

        if not files:
            return None

        return random.choice(
            files
        )

    def _play_sound(self, path):

        try:

            if path.suffix.lower() == ".wav":

                winsound.PlaySound(
                    str(path),
                    winsound.SND_FILENAME
                    | winsound.SND_ASYNC
                )

        except Exception as error:

            print(
                f"[KitKat] Sound error: {error}"
            )

    # =========================================================
    # MOUSE
    # =========================================================

    def _mouse_down(self, event):

        if self.locked:
            return

        self.dragging = True

        self.drag_offset_x = event.x
        self.drag_offset_y = event.y

        self.chasing_cursor = False

        self._set_animation(
            "idle"
        )

    def _mouse_drag(self, event):

        if self.locked:
            return

        if not self.dragging:
            return

        new_x = (
            self.window.winfo_x()
            + event.x
            - self.drag_offset_x
        )

        new_y = (
            self.window.winfo_y()
            + event.y
            - self.drag_offset_y
        )

        self.x = new_x
        self.y = new_y

        self.target_x = new_x
        self.target_y = new_y

        self._apply_boundaries()

        self._move_window()

    def _mouse_up(self, event):

        if not self.dragging:
            return

        self.dragging = False

        self.interaction_count += 1

        self._register_interaction(
            "drag"
        )

    def _double_click(self, event):

        self.interaction_count += 1

        self.meow()

    def _right_click(self, event):

        if self.menu:

            try:

                self.menu.show(
                    event.x_root,
                    event.y_root
                )

            except Exception as error:

                print(
                    f"[KitKat] Menu error: {error}"
                )

    # =========================================================
    # BRAIN COMMUNICATION
    # =========================================================

    def _register_interaction(
        self,
        interaction
    ):

        if not self.console:
            return

        try:

            self.console.register_interaction(
                interaction
            )

        except Exception:
            pass

    # =========================================================
    # STATE
    # =========================================================

    def get_position(self):

        return (
            int(self.x),
            int(self.y)
        )

    def get_target(self):

        return (
            int(self.target_x),
            int(self.target_y)
        )

    def get_state(self):

        return {
            "visible": self.visible,
            "locked": self.locked,
            "paused": self.paused,
            "confined": self.confined,
            "chasing": self.chasing_cursor,
            "animation": self.current_animation,
            "x": int(self.x),
            "y": int(self.y),
            "target_x": int(self.target_x),
            "target_y": int(self.target_y),
            "interactions": self.interaction_count,
        }

    # =========================================================
    # RESET
    # =========================================================

    def reset_position(self):

        screen_width = (
            self.root.winfo_screenwidth()
        )

        screen_height = (
            self.root.winfo_screenheight()
        )

        self.x = (
            screen_width
            - self.WINDOW_SIZE
        ) / 2

        self.y = (
            screen_height
            - self.WINDOW_SIZE
        ) / 2

        self.target_x = self.x
        self.target_y = self.y

        self._move_window()

    # =========================================================
    # DESTROY
    # =========================================================

    def destroy(self):

        if self.destroyed:
            return

        self.destroyed = True

        try:
            self.window.destroy()
        except Exception:
            pass