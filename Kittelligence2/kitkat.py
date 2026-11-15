from __future__ import annotations

import random
import sys
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk


APP_DIR = Path(__file__).resolve().parent
ASSET_DIR = (Path(getattr(sys, "_MEIPASS")) / "assets") if hasattr(sys, "_MEIPASS") else (APP_DIR.parent / "assets")


class KitKatPet:
    SIZE = 180

    def __init__(self, root):
        self.root = root
        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.geometry(f"{self.SIZE}x{self.SIZE}+420+420")
        self.window.configure(bg="#ff00ff")
        try:
            self.window.attributes("-transparentcolor", "#ff00ff")
        except tk.TclError:
            pass
        self.canvas = tk.Canvas(self.window, width=self.SIZE, height=self.SIZE, bg="#ff00ff", highlightthickness=0)
        self.canvas.pack()
        self.frames = self._load_frames()
        self.images = []
        self.animation = "idle"
        self.frame = 0
        self.x, self.y = 420.0, 420.0
        self.target = None
        self.paused = False
        self.visible = True
        self.destroyed = False
        self.on_interaction = None
        self.on_menu = None
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
                            frames.append(im)
                        except OSError:
                            continue
            result[name] = frames
        fallback = ASSET_DIR / "idle" / "kitkat.png"
        if not result["idle"] and fallback.exists():
            try:
                im = Image.open(fallback).convert("RGBA")
                im.thumbnail((self.SIZE - 12, self.SIZE - 12), Image.Resampling.LANCZOS)
                result["idle"] = [im]
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
        if frames:
            self.frame %= len(frames)
            image = frames[self.frame]
            if self.animation in ("walk", "chase") and self.target and self.target[0] > self.x:
                image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            photo = ImageTk.PhotoImage(image)
            self.canvas.delete("all")
            self.canvas.create_image(self.SIZE // 2, self.SIZE // 2, image=photo)
            self.canvas.image = photo

            # If no dedicated meow animation frames were supplied, still give
            # immediate visible feedback instead of silently showing the idle pose.
            if self.animation == "meow" and not self.frames.get("meow"):
                self.canvas.create_oval(105, 8, 174, 43, fill="white", outline="#444444", width=1)
                self.canvas.create_text(139, 25, text="Meow!", fill="#222222",
                                        font=("Segoe UI", 11, "bold"))

            self.frame += 1
        self.root.after(130, self._animate)

    def _drag_start(self, event):
        self.drag_dx, self.drag_dy = event.x, event.y
        self.target = None
        self._set_animation("idle")

    def _drag(self, event):
        self.x = self.window.winfo_x() + event.x - self.drag_dx
        self.y = self.window.winfo_y() + event.y - self.drag_dy
        self._place()

    def _click(self, _event):
        if self.on_interaction:
            self.on_interaction()

    def _right_click(self, event):
        if self.on_menu:
            self.on_menu(event.x_root, event.y_root)

    def _place(self):
        self.x = max(0, min(self.root.winfo_screenwidth() - self.SIZE, self.x))
        self.y = max(0, min(self.root.winfo_screenheight() - self.SIZE, self.y))
        self.window.geometry(f"+{int(self.x)}+{int(self.y)}")

    def _move(self):
        if self.destroyed:
            return
        if not self.paused and self.target:
            tx, ty = self.target
            dx, dy = tx - self.x, ty - self.y
            distance = (dx * dx + dy * dy) ** 0.5
            if distance < 5:
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
        width, height = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.target = (random.randint(30, max(31, width - self.SIZE - 30)),
                       random.randint(30, max(31, height - self.SIZE - 30)))
        self._set_animation("walk")

    def sleep(self):
        self.target = None
        self._set_animation("sleep")

    def sit(self):
        self.target = None
        self._set_animation("sit")

    def meow(self):
        self._set_animation("meow")
        self.root.after(1000, lambda: self._set_animation("idle"))

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
