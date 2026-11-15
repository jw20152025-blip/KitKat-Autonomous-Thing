from __future__ import annotations

import random
import sys
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk
from monitor_manager import MonitorManager

APP_DIR = Path(__file__).resolve().parent
BUNDLE_DIR = Path(getattr(sys, "_MEIPASS")) if hasattr(sys, "_MEIPASS") else APP_DIR.parent
ASSET_DIR = BUNDLE_DIR / "assets"
SOUND_DIR = BUNDLE_DIR / "sounds"
TRANSPARENT_COLOR = "#ff00ff"


def remove_magenta_fringe(image):
    """Remove magenta matte pixels and unblend antialiased edges from pet artwork."""
    image = image.convert("RGBA")
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, alpha = pixels[x, y]
            if alpha == 0:
                continue
            if r > 115 and b > 115 and g < 155 and r > g * 1.30 and b > g * 1.30:
                chroma = min(255, max(r - g, b - g))
                opacity = max(0.0, 1.0 - chroma / 255.0)
                new_alpha = int(alpha * opacity)
                if new_alpha < 10:
                    pixels[x, y] = (0, 0, 0, 0)
                    continue
                if opacity > 0.04:
                    nr = int(max(0, min(255, (r - 255 * (1 - opacity)) / opacity)))
                    ng = int(max(0, min(255, g / opacity)))
                    nb = int(max(0, min(255, (b - 255 * (1 - opacity)) / opacity)))
                    pixels[x, y] = (nr, ng, nb, new_alpha)
    return image


class KitKatPet:
    SIZE = 180

    def __init__(self, root):
        self.root = root
        self.monitors = MonitorManager()
        self.current_monitor = 0
        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.geometry(f"{self.SIZE}x{self.SIZE}+420+420")
        self.window.configure(bg=TRANSPARENT_COLOR)
        self.window.attributes("-transparentcolor", TRANSPARENT_COLOR)
        self.canvas = tk.Canvas(
            self.window, width=self.SIZE, height=self.SIZE,
            bg=TRANSPARENT_COLOR, highlightthickness=0, bd=0
        )
        self.canvas.pack()
        self.frames = self._load_frames()
        self.animation = "idle"
        self.frame = 0
        self.x, self.y = 420.0, 420.0
        self.target = None
        self.paused = False
        self.visible = True
        self.destroyed = False
        self.on_interaction = None
        self.on_menu = None
        self._meow_serial = 0
        self._dragging = False
        self.window.bind("<ButtonPress-1>", self._drag_start)
        self.window.bind("<B1-Motion>", self._drag)
        self.window.bind("<ButtonRelease-1>", self._click)
        self.window.bind("<Button-3>", self._right_click)
        self._animate()
        self._move()

    def _load_frames(self):
        result = {}
        for name in ("idle", "walk", "chase", "sit", "sleep", "meow"):
            folder = ASSET_DIR / name
            frames = []
            if folder.exists():
                for path in sorted(folder.iterdir()):
                    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                        try:
                            im = Image.open(path).convert("RGBA")
                            im.thumbnail((self.SIZE - 12, self.SIZE - 12), Image.Resampling.LANCZOS)
                            frames.append(remove_magenta_fringe(im))
                        except OSError:
                            continue
            result[name] = frames
        fallback = ASSET_DIR / "idle" / "kitkat.png"
        if not result["idle"] and fallback.exists():
            try:
                im = Image.open(fallback).convert("RGBA")
                im.thumbnail((self.SIZE - 12, self.SIZE - 12), Image.Resampling.LANCZOS)
                result["idle"] = [remove_magenta_fringe(im)]
            except OSError:
                pass
        return result

    def _set_animation(self, name):
        if name not in self.frames:
            name = "idle"
        if self.animation != name:
            self.animation, self.frame = name, 0

    def _animate(self):
        if self.destroyed:
            return
        frames = self.frames.get(self.animation) or self.frames.get("idle") or []
        self.canvas.delete("all")
        if frames:
            self.frame %= len(frames)
            image = frames[self.frame]
            if self.animation in ("walk", "chase") and self.target and self.target[0] > self.x:
                image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            photo = ImageTk.PhotoImage(image)
            self.canvas.create_image(self.SIZE // 2, self.SIZE // 2, image=photo)
            self.canvas.image = photo
            self.frame += 1
        self.root.after(130, self._animate)

    def _play_sound(self, name):
        sound_path = SOUND_DIR / name / f"{name}.wav"
        if not sound_path.is_file():
            return
        try:
            import winsound
            winsound.PlaySound(str(sound_path),
                               winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        except (ImportError, RuntimeError, OSError):
            pass

    def _drag_start(self, event):
        self._dragging = False
        self.drag_dx, self.drag_dy = event.x, event.y
        self.target = None
        self._set_animation("idle")

    def _drag(self, event):
        if abs(event.x - self.drag_dx) > 3 or abs(event.y - self.drag_dy) > 3:
            self._dragging = True
        self.x = self.window.winfo_x() + event.x - self.drag_dx
        self.y = self.window.winfo_y() + event.y - self.drag_dy
        self._place()

    def _click(self, _event):
        was_dragging = self._dragging
        self._dragging = False
        if self.on_interaction and not was_dragging:
            self.on_interaction()

    def _right_click(self, event):
        if self.on_menu:
            self.on_menu(event.x_root, event.y_root)

    def _place(self):
        nearest = self.monitors.clamp_to_nearest_monitor(self.x, self.y, self.SIZE, self.SIZE, 0)
        if nearest:
            self.current_monitor, self.x, self.y = nearest
        self.window.geometry(f"{self.SIZE}x{self.SIZE}{int(self.x):+d}{int(self.y):+d}")

    def _move(self):
        if self.destroyed:
            return
        if not self.paused and self.target:
            tx, ty = self.target
            dx, dy = tx - self.x, ty - self.y
            distance = (dx * dx + dy * dy) ** 0.5
            if distance < 5:
                self.x, self.y = tx, ty
                self.target = None
                self._set_animation("idle")
            else:
                step = min(3.0, distance) / distance
                self.x += dx * step * 3.0
                self.y += dy * step * 3.0
                self._place()
                self._set_animation("walk")
        self.root.after(30, self._move)

    def wander(self):
        if self.paused:
            return
        self.monitors.refresh()
        preferred = None
        # Most trips stay local; occasional trips deliberately explore another display.
        if len(self.monitors.monitors) > 1 and random.random() < 0.38:
            choices = [i for i in range(len(self.monitors.monitors)) if i != self.current_monitor]
            preferred = random.choice(choices) if choices else None
        _monitor, position = self.monitors.choose_position(self.SIZE, self.SIZE, preferred=preferred)
        self.target = position
        self._set_animation("walk")

    def sleep(self):
        self.target = None
        self._set_animation("sleep")

    def sit(self):
        self.target = None
        self._set_animation("sit")

    def meow(self):
        self._play_sound("meow")
        self._meow_serial += 1
        serial = self._meow_serial
        self._set_animation("meow")
        self.root.after(1000, lambda: self._set_animation("idle") if serial == self._meow_serial else None)

    def purr(self):
        self._play_sound("purr")

    def show(self):
        self.visible = True
        self.window.deiconify()
        self.window.attributes("-topmost", True)

    def hide(self):
        self.visible = False
        self.window.withdraw()

    def destroy(self):
        self.destroyed = True
        try:
            self.window.destroy()
        except tk.TclError:
            pass
