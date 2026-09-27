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

        # This color becomes transparent on Windows.
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
        self.stationary_action = None
        self.confined = False

        self.current_animation = "idle"
        self.animation_index = 0

        self.animation_speed = 120

        self.x = 500.0
        self.y = 500.0

        self.target_x = None
        self.target_y = None

        self.walk_speed = 2.5
        self.chase_speed = 5.5

        self.facing_right = True

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

        # Stores PIL images.
        self.animation_images = {}

        # Stores PhotoImage objects.
        self.animation_photos = {}

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
        # START
        # =====================================================

        self._set_animation("idle")

        self._animation_loop()
        self._movement_loop()

        print(
            "[KitKat] Animations:",
            {
                name: len(frames)
                for name, frames in self.animation_images.items()
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
    # IMAGE CLEANING
    # =========================================================

    def _remove_magenta_background(self, image):
        """
        Remove the common bright-magenta background color.

        This prevents the #ff00ff box/halo from appearing
        around KitKat if an asset was exported with a magenta
        background.
        """

        image = image.convert("RGBA")

        pixels = image.load()

        width, height = image.size

        for py in range(height):

            for px in range(width):

                r, g, b, a = pixels[px, py]

                # Strong magenta / purple background.
                if (
                    r >= 220
                    and b >= 220
                    and g <= 80
                ):
                    pixels[px, py] = (
                        r,
                        g,
                        b,
                        0
                    )

        return image

    # =========================================================
    # ANIMATION LOADING
    # =========================================================

    def _load_animations(self):

        for name, folder in ANIMATION_FOLDERS.items():

            images = []
            photos = []

            if not folder.exists():

                self.animation_images[name] = []
                self.animation_photos[name] = []

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

                    # Remove accidental magenta background.
                    image = self._remove_magenta_background(
                        image
                    )

                    # Resize while preserving aspect ratio.
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

                    images.append(image)

                    photos.append(
                        ImageTk.PhotoImage(image)
                    )

                except Exception as error:

                    print(
                        f"[KitKat] Could not load "
                        f"{file}: {error}"
                    )

            self.animation_images[name] = images
            self.animation_photos[name] = photos

    # =========================================================
    # ANIMATION SELECTION
    # =========================================================

    def _set_animation(self, name):

        frames = self.animation_images.get(
            name,
            []
        )

        if not frames:

            # Missing animation → idle.
            if name != "idle":

                idle = self.animation_images.get(
                    "idle",
                    []
                )

                if idle:

                    if self.current_animation != "idle":

                        self.current_animation = "idle"
                        self.animation_index = 0

            return

        if self.current_animation != name:

            self.current_animation = name
            self.animation_index = 0

    # =========================================================
    # GET CURRENT FRAME
    # =========================================================

    def _get_current_frame(self):

        frames = self.animation_images.get(
            self.current_animation,
            []
        )

        if not frames:

            frames = self.animation_images.get(
                "idle",
                []
            )

        if not frames:
            return None

        if self.animation_index >= len(frames):

            self.animation_index = 0

        image = frames[
            self.animation_index
        ]

        # Only flip movement animations.
        if (
            self.facing_right
            and self.current_animation in {"walk", "chase"}
        ):
            image = image.transpose(
                Image.Transpose.FLIP_LEFT_RIGHT
            )

        return image

    # =========================================================
    # ANIMATION LOOP
    # =========================================================

    def _animation_loop(self):

        if self.destroyed:
            return

        if self.visible:

            frame = self._get_current_frame()

            if frame is not None:

                photo = ImageTk.PhotoImage(
                    frame
                )

                # Keep a reference alive.
                self.current_photo = photo

                self.canvas.delete(
                    "kitkat"
                )

                self.canvas.create_image(
                    self.WINDOW_SIZE // 2,
                    self.WINDOW_SIZE // 2,
                    image=photo,
                    anchor="center",
                    tags="kitkat"
                )

                frames = self.animation_images.get(
                    self.current_animation,
                    []
                )

                if frames:

                    self.animation_index += 1

                    if (
                        self.animation_index
                        >= len(frames)
                    ):

                        self.animation_index = 0

        self.root.after(
            self.animation_speed,
            self._animation_loop
        )

    # =========================================================
    # WALK
    # =========================================================

    def walk(self):

        if self.locked or self.paused:
            return

        self.chasing_cursor = False

        self.random_destination()

    def random_walk(self):

        self.walk()

    def random_destination(self):

        if self.locked or self.paused:
            return

        screen_width = (
            self.root.winfo_screenwidth()
        )

        screen_height = (
            self.root.winfo_screenheight()
        )

        margin = 50

        min_x = margin
        min_y = margin

        max_x = (
            screen_width
            - self.WINDOW_SIZE
            - margin
        )

        max_y = (
            screen_height
            - self.WINDOW_SIZE
            - margin
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

        max_x = max(
            min_x,
            max_x
        )

        max_y = max(
            min_y,
            max_y
        )

        self.target_x = random.randint(
            int(min_x),
            int(max_x)
        )

        self.target_y = random.randint(
            int(min_y),
            int(max_y)
        )

        self._update_direction()

        self._set_animation(
            "walk"
        )

    # =========================================================
    # MOVEMENT
    # =========================================================

    def _movement_loop(self):

        if self.destroyed:
            return

        # =====================================================
        # PAUSED / LOCKED / HIDDEN
        # =====================================================

        if (
            not self.visible
            or self.locked
            or self.paused
        ):

            self.root.after(
                30,
                self._movement_loop
            )

            return

        # =====================================================
        # CURSOR CHASE
        # =====================================================

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

            speed = self.chase_speed

            self._set_animation(
                "chase"
            )

        else:

            speed = self.walk_speed

        # =====================================================
        # MOVE
        # =====================================================

        if (
            self.target_x is not None
            and self.target_y is not None
        ):

            dx = (
                self.target_x
                - self.x
            )

            dy = (
                self.target_y
                - self.y
            )

            distance = math.sqrt(
                dx * dx
                + dy * dy
            )

            if distance > 4:

                self._update_direction()

                self.x += (
                    dx / distance
                ) * speed

                self.y += (
                    dy / distance
                ) * speed

                self._apply_boundaries()

                self._move_window()

                if self.chasing_cursor:

                    self._set_animation(
                        "chase"
                    )

                else:

                    self._set_animation(
                        "walk"
                    )

            else:

                if self.chasing_cursor:

                    # Stay in chase mode so cursor tracking
                    # continues even when KitKat catches it.

                    self._set_animation(
                        "chase"
                    )

                else:

                    # Random destination reached.
                    self.target_x = None
                    self.target_y = None

                    self._set_animation(
                        "idle"
                    )

        else:

            if not self.chasing_cursor:

                if self.stationary_action:
                    self._set_animation(
                        self.stationary_action
                    )
                else:
                    self._set_animation(
                        "idle"
                    )

        self.root.after(
            30,
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

        self.target_x = None
        self.target_y = None

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

    def _update_direction(self):

        if self.target_x is None:
            return

        dx = self.target_x - self.x

        # Ignore tiny movements.
        if abs(dx) < 1:
            return

        # KitKat's default sprite faces RIGHT.
        self.facing_right = dx > 0

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

        self.target_x = None
        self.target_y = None

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

        self.target_x = None
        self.target_y = None

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

        self.target_x = None
        self.target_y = None

        self._move_window()

    def release(self):

        self.confined = False

    # =========================================================
    # SIT / SLEEP
    # =========================================================

    def sit(self):

        if self.locked:
            return

        self.chasing_cursor = False
        self.target_x = None
        self.target_y = None

        self.stationary_action = "sit"

        self._set_animation("sit")

    def sleep(self):

        if self.locked:
            return

        self.chasing_cursor = False
        self.target_x = None
        self.target_y = None

        self.stationary_action = "sleep"

        self._set_animation("sleep")

    def wake(self):

        self.stationary_action = None

        self._set_animation("idle")

    # =========================================================
    # MEOW
    # =========================================================

    def meow(self):

        self.interaction_count += 1

        self.chasing_cursor = False

        self.target_x = None
        self.target_y = None

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

    def _find_sound(
        self,
        sound_type
    ):

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

        self.target_x = None
        self.target_y = None

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

        self.target_x = None
        self.target_y = None

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

        if self.target_x is None:
            return None

        if self.target_y is None:
            return None

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
            "target_x": (
                None
                if self.target_x is None
                else int(self.target_x)
            ),
            "target_y": (
                None
                if self.target_y is None
                else int(self.target_y)
            ),
            "interactions": self.interaction_count,
            "facing_right": self.facing_right,
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

        self.target_x = None
        self.target_y = None

        self.chasing_cursor = False

        self._set_animation(
            "idle"
        )

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