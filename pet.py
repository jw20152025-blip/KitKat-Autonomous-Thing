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

        self.window = tk.Toplevel(root)

        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.config(bg="#ff00ff")
        self.window.attributes(
            "-transparentcolor",
            "#ff00ff"
        )

        self.canvas = tk.Canvas(
            self.window,
            width=self.WINDOW_SIZE,
            height=self.WINDOW_SIZE,
            bg="#ff00ff",
            highlightthickness=0
        )

        self.canvas.pack()

        self.window.geometry(
            f"{self.WINDOW_SIZE}x"
            f"{self.WINDOW_SIZE}+500+500"
        )

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

        self.confine_x1 = 0
        self.confine_y1 = 0
        self.confine_x2 = 800
        self.confine_y2 = 600

        self.menu = None
        self.console = None

        self.animations = {}
        self.animation_frames = {}

        self._load_animations()

        self._bind_mouse()

        self._move_window()

        self._animation_loop()
        self._movement_loop()

    # ---------------------------------------------------------
    # SETUP
    # ---------------------------------------------------------

    def set_menu(self, menu):
        self.menu = menu

    def set_console(self, console):
        self.console = console

    # ---------------------------------------------------------
    # ANIMATIONS
    # ---------------------------------------------------------

    def _load_animations(self):

        for animation, folder in ANIMATION_FOLDERS.items():

            frames = []

            if folder.exists():

                files = sorted(
                    [
                        file
                        for file in folder.iterdir()
                        if file.suffix.lower()
                        in {
                            ".png",
                            ".jpg",
                            ".jpeg",
                            ".webp"
                        }
                    ]
                )

                for file in files:

                    try:

                        image = Image.open(
                            file
                        ).convert("RGBA")

                        image.thumbnail(
                            (
                                self.WINDOW_SIZE - 10,
                                self.WINDOW_SIZE - 10
                            ),
                            Image.Resampling.LANCZOS
                        )

                        pixels = image.load()

                        for py in range(image.height):

                            for px in range(image.width):

                                r, g, b, a = (
                                    pixels[px, py]
                                )

                                if (
                                    r > 245
                                    and g < 15
                                    and b > 245
                                ):
                                    pixels[px, py] = (
                                        255,
                                        0,
                                        255,
                                        0
                                    )

                        frames.append(image)

                    except Exception:
                        pass

            self.animations[animation] = frames

            self.animation_frames[animation] = frames

        if not self.animations.get("idle"):

            self.animations["idle"] = []

    def _set_animation(self, animation):

        if animation not in self.animations:
            return

        if not self.animations[animation]:
            return

        if self.current_animation != animation:

            self.current_animation = animation
            self.animation_index = 0

    def _animation_loop(self):

        if self.destroyed:
            return

        frames = self.animations.get(
            self.current_animation,
            []
        )

        if frames:

            if self.animation_index >= len(frames):
                self.animation_index = 0

            image = frames[self.animation_index]

            if (
                self.facing_right
                and self.current_animation
                in {"walk", "chase"}
            ):

                image = image.transpose(
                    Image.Transpose.FLIP_LEFT_RIGHT
                )

            photo = ImageTk.PhotoImage(image)

            self.canvas.delete("all")

            self.canvas.create_image(
                self.WINDOW_SIZE // 2,
                self.WINDOW_SIZE // 2,
                image=photo
            )

            self.canvas.image = photo

            self.animation_index += 1

        self.root.after(
            self.animation_speed,
            self._animation_loop
        )

    # ---------------------------------------------------------
    # MOUSE
    # ---------------------------------------------------------

    def _bind_mouse(self):

        self.window.bind(
            "<ButtonPress-1>",
            self._mouse_down
        )

        self.window.bind(
            "<B1-Motion>",
            self._mouse_drag
        )

        self.window.bind(
            "<ButtonRelease-1>",
            self._mouse_up
        )

        self.root.bind_all(
            "<Button-3>",
            self._global_right_click
        )

    def _global_right_click(self, event):

        if self.destroyed:
            return

        # Get the actual screen position of KitKat.
        left = self.window.winfo_rootx()
        top = self.window.winfo_rooty()

        right = (
            left
            + self.WINDOW_SIZE
        )

        bottom = (
            top
            + self.WINDOW_SIZE
        )

        # Only react when the right-click happened
        # inside KitKat's window.
        if not (
            left <= event.x_root <= right
            and
            top <= event.y_root <= bottom
        ):
            return

        print(
            "[KitKat] RIGHT CLICK DETECTED"
        )

        if self.menu is None:

            print(
                "[KitKat] ERROR: menu is not connected."
            )

            return "break"

        try:

            self.menu.show(
                event.x_root,
                event.y_root
            )

        except Exception as error:

            print(
                f"[KitKat] Menu error: {error}"
            )

        return "break"

    def _mouse_down(self, event):

        if self.locked:
            return

        self.drag_offset_x = event.x
        self.drag_offset_y = event.y

        self.chasing_cursor = False
        self.target_x = None
        self.target_y = None

        self._set_animation("idle")

    def _mouse_drag(self, event):

        if self.locked:
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

        self.x = float(new_x)
        self.y = float(new_y)

        self._apply_boundaries()
        self._move_window()

    def _mouse_up(self, event):

        self.interaction_count += 1

    # ---------------------------------------------------------
    # MOVEMENT
    # ---------------------------------------------------------

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

        monitors = self.get_monitors()

        if not monitors:
            return

        monitor = random.choice(monitors)

        margin = 50

        min_x = (
            monitor["left"]
            + margin
        )

        min_y = (
            monitor["top"]
            + margin
        )

        max_x = (
            monitor["right"]
            - self.WINDOW_SIZE
            - margin
        )

        max_y = (
            monitor["bottom"]
            - self.WINDOW_SIZE
            - margin
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

        self._set_animation("walk")

    # ---------------------------------------------------------
    # WINDOWS MONITOR DETECTION
    # ---------------------------------------------------------

    def get_monitors(self):

        monitors = []

        user32 = ctypes.windll.user32

        MONITORINFOF_PRIMARY = 1

        class RECT(ctypes.Structure):

            _fields_ = [
                ("left", wintypes.LONG),
                ("top", wintypes.LONG),
                ("right", wintypes.LONG),
                ("bottom", wintypes.LONG)
            ]

        class MONITORINFO(ctypes.Structure):

            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("rcMonitor", RECT),
                ("rcWork", RECT),
                ("dwFlags", wintypes.DWORD)
            ]

        MonitorEnumProc = ctypes.WINFUNCTYPE(
            wintypes.BOOL,
            wintypes.HMONITOR,
            wintypes.HDC,
            ctypes.POINTER(RECT),
            wintypes.LPARAM
        )

        def callback(
            monitor,
            hdc,
            rect,
            data
        ):

            info = MONITORINFO()

            info.cbSize = ctypes.sizeof(
                MONITORINFO
            )

            if user32.GetMonitorInfoW(
                monitor,
                ctypes.byref(info)
            ):

                monitors.append(
                    {
                        "left":
                            info.rcMonitor.left,

                        "top":
                            info.rcMonitor.top,

                        "right":
                            info.rcMonitor.right,

                        "bottom":
                            info.rcMonitor.bottom,

                        "primary":
                            bool(
                                info.dwFlags
                                & MONITORINFOF_PRIMARY
                            )
                    }
                )

            return True

        callback_ref = MonitorEnumProc(
            callback
        )

        user32.EnumDisplayMonitors(
            None,
            None,
            callback_ref,
            0
        )

        return monitors

    def get_current_monitor(self):

        monitors = self.get_monitors()

        center_x = (
            self.x
            + self.WINDOW_SIZE / 2
        )

        center_y = (
            self.y
            + self.WINDOW_SIZE / 2
        )

        for monitor in monitors:

            if (
                monitor["left"]
                <= center_x
                <= monitor["right"]
                and
                monitor["top"]
                <= center_y
                <= monitor["bottom"]
            ):

                return monitor

        return None

    # ---------------------------------------------------------
    # MOVEMENT LOOP
    # ---------------------------------------------------------

    def _movement_loop(self):

        if self.destroyed:
            return

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

            self._set_animation("chase")

        else:

            speed = self.walk_speed

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

                    self._set_animation(
                        "chase"
                    )

                else:

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

    # ---------------------------------------------------------
    # CURSOR
    # ---------------------------------------------------------

    def get_cursor_position(self):

        point = wintypes.POINT()

        ctypes.windll.user32.GetCursorPos(
            ctypes.byref(point)
        )

        return (
            point.x,
            point.y
        )

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

    # ---------------------------------------------------------
    # DIRECTION
    # ---------------------------------------------------------

    def _update_direction(self):

        if self.target_x is None:
            return

        dx = (
            self.target_x
            - self.x
        )

        if abs(dx) < 1:
            return

        self.facing_right = (
            dx > 0
        )

    # ---------------------------------------------------------
    # BOUNDARIES
    # ---------------------------------------------------------

    def _apply_boundaries(self):

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

            monitors = self.get_monitors()

            if not monitors:
                return

            min_x = min(
                monitor["left"]
                for monitor in monitors
            )

            min_y = min(
                monitor["top"]
                for monitor in monitors
            )

            max_x = max(
                monitor["right"]
                for monitor in monitors
            ) - self.WINDOW_SIZE

            max_y = max(
                monitor["bottom"]
                for monitor in monitors
            ) - self.WINDOW_SIZE

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

    # ---------------------------------------------------------
    # WINDOW POSITION
    # ---------------------------------------------------------

    def _move_window(self):

        self.window.geometry(
            f"{self.WINDOW_SIZE}x"
            f"{self.WINDOW_SIZE}+"
            f"{int(self.x)}+"
            f"{int(self.y)}"
        )

    # ---------------------------------------------------------
    # HIDE / SHOW
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # LOCK
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # PAUSE
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # CONFINE
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # STATIONARY ACTIONS
    # ---------------------------------------------------------

    def sit(self):

        if self.locked:
            return

        self.chasing_cursor = False

        self.target_x = None
        self.target_y = None

        self.stationary_action = "sit"

        self._set_animation(
            "sit"
        )

    def sleep(self):

        if self.locked:
            return

        self.chasing_cursor = False

        self.target_x = None
        self.target_y = None

        self.stationary_action = "sleep"

        self._set_animation(
            "sleep"
        )

    def wake(self):

        self.stationary_action = None

        self._set_animation(
            "idle"
        )

    # ---------------------------------------------------------
    # SOUND
    # ---------------------------------------------------------

    def meow(self):

        sounds = []

        folder = SOUND_FOLDERS["meow"]

        if folder.exists():

            sounds = [
                file
                for file in folder.iterdir()
                if file.suffix.lower()
                == ".wav"
            ]

        if sounds:

            try:

                winsound.PlaySound(
                    str(random.choice(sounds)),
                    winsound.SND_FILENAME
                    | winsound.SND_ASYNC
                )

            except Exception:
                pass

        elif FALLBACK_MEOW.exists():

            try:

                winsound.PlaySound(
                    str(FALLBACK_MEOW),
                    winsound.SND_FILENAME
                    | winsound.SND_ASYNC
                )

            except Exception:
                pass

        self._set_animation(
            "meow"
        )

    # ---------------------------------------------------------
    # DESTROY
    # ---------------------------------------------------------

    def destroy(self):

        if self.destroyed:
            return

        self.destroyed = True

        try:
            self.root.unbind_all(
                "<Button-3>"
            )
        except Exception:
            pass

        try:
            self.window.destroy()
        except Exception:
            pass