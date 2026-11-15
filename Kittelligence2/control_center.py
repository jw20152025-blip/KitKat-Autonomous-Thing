from __future__ import annotations

import tkinter as tk
from tkinter import ttk, scrolledtext


class ControlCenter:
    def __init__(self, root, pet, brain, store):
        self.root, self.pet, self.brain, self.store = root, pet, brain, store
        self.window = None
        self.values = {}
        self.bars = {}
        self.chat_window = None
        self.chat_log = None
        self.chat_entry = None
        self.greeted = False

    def show(self):
        if self.window and self.window.winfo_exists():
            self.window.deiconify()
            self.window.lift()
            return
        self.window = tk.Toplevel(self.root)
        self.window.title("Kittelligence | KitKat Care")
        self.window.geometry("510x690")
        self.window.minsize(420, 500)
        self.window.protocol("WM_DELETE_WINDOW", self.window.withdraw)

        shell = ttk.Frame(self.window)
        shell.pack(fill="both", expand=True)
        canvas = tk.Canvas(shell, highlightthickness=0)
        scrollbar = ttk.Scrollbar(shell, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        content = ttk.Frame(canvas, padding=18)
        content_id = canvas.create_window((0, 0), window=content, anchor="nw")

        content.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(content_id, width=e.width))
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))

        ttk.Label(content, text="Kittelligence", font=("Segoe UI", 22, "bold")).pack(anchor="w")
        ttk.Label(content, text="KitKat's care centre", font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 14))

        needs = ttk.LabelFrame(content, text="KitKat's needs", padding=12)
        needs.pack(fill="x", pady=(0, 10))
        for key, label in (
            ("hunger", "Hunger"),
            ("hydration", "Hydration"),
            ("energy", "Energy"),
            ("happiness", "Happiness"),
            ("boredom", "Boredom"),
            ("litter_cleanliness", "Litter cleanliness"),
        ):
            row = ttk.Frame(needs)
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=label, width=19).pack(side="left")
            bar = ttk.Progressbar(row, maximum=100, mode="determinate")
            bar.pack(side="left", fill="x", expand=True, padx=(4, 8))
            value = ttk.Label(row, text="—", width=5)
            value.pack(side="right")
            self.bars[key] = bar
            self.values[key] = value

        actions = ttk.LabelFrame(content, text="Take care of KitKat", padding=10)
        actions.pack(fill="x", pady=6)
        buttons = [
            ("Feed", self.brain.feed),
            ("Give water", self.brain.give_water),
            ("Play", self.brain.play),
            ("Nap", self.brain.rest),
            ("Clean litter", self.brain.clean_litter),
            ("Brush", self.brain.brush),
            ("Pet", self.brain.on_petted),
            ("Meow", self.pet.meow),
            ("Purr", self.pet.purr),
            ("Chat with KitKat", self.show_chat),
        ]
        for index, (label, command) in enumerate(buttons):
            ttk.Button(actions, text=label, command=command).grid(
                row=index // 2, column=index % 2, sticky="ew", padx=4, pady=4
            )
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)

        status = ttk.LabelFrame(content, text="Activity", padding=10)
        status.pack(fill="x", pady=6)
        self.last_action = ttk.Label(status, text="Just woke up")
        self.last_action.pack(anchor="w")
        self.pet_count = ttk.Label(status, text="Pets: 0")
        self.pet_count.pack(anchor="w", pady=(4, 0))
        self.pause_button = ttk.Button(status, text="Pause autonomy", command=self._toggle_pause)
        self.pause_button.pack(fill="x", pady=(8, 0))

        memory = ttk.LabelFrame(content, text="Saved memory", padding=10)
        memory.pack(fill="x", pady=6)
        ttk.Label(memory, text=str(self.store.path), wraplength=440).pack(anchor="w")
        self._refresh()

    def _toggle_pause(self):
        paused = self.brain.toggle_pause()
        self.pause_button.configure(text="Resume autonomy" if paused else "Pause autonomy")

    def _refresh(self):
        if not self.window or not self.window.winfo_exists():
            return
        state = self.brain.export_state()
        values = {
            "hunger": state["hunger"],
            "hydration": state["hydration"],
            "energy": state["energy"],
            "happiness": state["happiness"],
            "boredom": state["boredom"],
            "litter_cleanliness": state["litter_cleanliness"],
        }
        for key, number in values.items():
            percent = int(max(0, min(1, number)) * 100)
            self.bars[key]["value"] = percent
            self.values[key].configure(text=f"{percent}%")
        self.last_action.configure(text=f"Last activity: {self.brain.last_action}")
        self.pet_count.configure(text=f"Pets: {self.brain.total_pets}")
        self.window.after(700, self._refresh)

    def show_chat(self):
        if self.chat_window and self.chat_window.winfo_exists():
            self.chat_window.deiconify()
            self.chat_window.lift()
            return
        self.chat_window = tk.Toplevel(self.root)
        self.chat_window.title("KitKat Assistant")
        self.chat_window.geometry("430x520")
        self.chat_window.minsize(340, 380)
        self.chat_window.protocol("WM_DELETE_WINDOW", self.chat_window.withdraw)
        frame = ttk.Frame(self.chat_window, padding=12)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="KitKat Assistant", font=("Segoe UI", 17, "bold")).pack(anchor="w")
        ttk.Label(frame, text="A little local assistant for KitKat's care").pack(anchor="w", pady=(0, 8))
        self.chat_log = scrolledtext.ScrolledText(
            frame, wrap="word", height=16, state="disabled",
            font=("Segoe UI", 10), padx=8, pady=8
        )
        self.chat_log.pack(fill="both", expand=True)
        bottom = ttk.Frame(frame)
        bottom.pack(fill="x", pady=(8, 0))
        self.chat_entry = ttk.Entry(bottom)
        self.chat_entry.pack(side="left", fill="x", expand=True)
        self.chat_entry.bind("<Return>", lambda _e: self.send_chat())
        ttk.Button(bottom, text="Send", command=self.send_chat).pack(side="right", padx=(6, 0))
        if not self.greeted:
            self._append_chat("KitKat", "Mrrp! I'm your KitKat care assistant. Ask how I'm doing, or tell me to feed, water, play with, brush, or help me nap.")
            self.greeted = True
        self.chat_entry.focus_set()

    def _append_chat(self, speaker, message):
        if not self.chat_log:
            return
        self.chat_log.configure(state="normal")
        self.chat_log.insert("end", f"{speaker}: {message}\n\n")
        self.chat_log.configure(state="disabled")
        self.chat_log.see("end")

    def send_chat(self):
        if not self.chat_entry:
            return
        message = self.chat_entry.get().strip()
        if not message:
            return
        self.chat_entry.delete(0, "end")
        self._append_chat("You", message)
        self._append_chat("KitKat", self._respond(message))

    def _status_summary(self):
        b = self.brain
        return (
            f"I'm at {b.happiness:.0%} happiness, {b.energy:.0%} energy, "
            f"{b.hunger:.0%} hunger, {b.hydration:.0%} hydration, "
            f"{b.boredom:.0%} boredom, and {b.litter_cleanliness:.0%} litter cleanliness. "
            f"My last activity was: {b.last_action.lower()}."
        )

    def _respond(self, message):
        text = message.lower()
        b = self.brain
        if any(word in text for word in ("feed", "food", "hungry", "meal")):
            b.feed()
            return "Yum! Thanks for feeding me. My hunger has gone down."
        if any(word in text for word in ("water", "thirst", "drink", "bowl")):
            b.give_water()
            return "Glug glug. My water bowl is topped up!"
        if any(word in text for word in ("play", "toy", "bored")):
            b.play()
            return "Let's play! That helped with my boredom. I might need a nap after all that excitement."
        if any(word in text for word in ("sleep", "nap", "tired", "rest")):
            b.rest()
            return "Nap time. I'll rest and build my energy back up."
        if any(word in text for word in ("litter", "clean up", "clean my")):
            b.clean_litter()
            return "Thank you! My litter area is clean again."
        if any(word in text for word in ("brush", "groom")):
            b.brush()
            return "That was lovely. My coat appreciates it!"
        if any(word in text for word in ("pet me", "pet you", "pat you", "stroke")):
            b.on_petted()
            return "Prrrr. I like spending time with you."
        if "meow" in text:
            self.pet.meow()
            return "Meeeow!"
        if "purr" in text:
            self.pet.purr()
            return "Prrrrrrrr."
        if any(word in text for word in ("status", "stats", "how are you", "how am i", "doing")):
            return self._status_summary()
        if any(word in text for word in ("what should", "what do i", "need", "help", "care")):
            options = [
                (b.hunger, "food", "I'm getting hungry. The Feed button will help."),
                (1 - b.hydration, "water", "I'm getting thirsty. Please give me water."),
                (1 - b.energy, "rest", "I'm low on energy. A nap would be great."),
                (b.boredom, "play", "I'm getting bored. Let's play!"),
                (1 - b.litter_cleanliness, "litter", "My litter area could use a clean."),
            ]
            score, _key, advice = max(options, key=lambda item: item[0])
            if score < 0.25:
                return "I'm doing pretty well right now! You can pet me or play with me if you'd like."
            return advice
        if any(word in text for word in ("hello", "hi", "hey")):
            return "Mrrp! Hello! What's happening?"
        if any(word in text for word in ("thank", "thanks")):
            return "You're welcome! Being looked after is pretty great."
        return "Mrrp! I can help with feeding, water, playtime, naps, brushing, litter care, meows, and my current stats. What should we do?"

    def notify_need(self, message):
        self.show_chat()
        self._append_chat("KitKat", message)
