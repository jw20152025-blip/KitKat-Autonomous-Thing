from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext

from assistant import KitKatAI


class ControlCenter:
    def __init__(self, root, pet, brain, store):
        self.root, self.pet, self.brain, self.store = root, pet, brain, store
        self.window = None
        self.values = {}
        self.bars = {}
        self.chat_window = None
        self.chat_log = None
        self.chat_entry = None
        self.send_button = None
        self.greeted = False
        self.chat_pending = False
        self.chat_history = []
        self.chat_results = queue.Queue()
        self.ai = KitKatAI()
        # Tkinter UI updates must run on the main thread. Poll the result queue
        # from the main event loop instead of calling root.after() in a worker.
        self.root.after(100, self._poll_chat_results)

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
        self.chat_window.title("KitKat AI")
        self.chat_window.geometry("450x540")
        self.chat_window.minsize(350, 400)
        self.chat_window.protocol("WM_DELETE_WINDOW", self.chat_window.withdraw)
        frame = ttk.Frame(self.chat_window, padding=12)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="KitKat AI", font=("Segoe UI", 17, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Powered by a local language model").pack(anchor="w", pady=(0, 8))
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
        self.send_button = ttk.Button(bottom, text="Send", command=self.send_chat)
        self.send_button.pack(side="right", padx=(6, 0))
        if not self.greeted:
            self._append_chat("KitKat", "Mrrp! I'm here. What's on your mind?")
            self.greeted = True
        self.chat_entry.focus_set()

    def _append_chat(self, speaker, message):
        if not self.chat_log:
            return
        self.chat_log.configure(state="normal")
        self.chat_log.insert("end", f"{speaker}: {message}\n\n")
        self.chat_log.configure(state="disabled")
        self.chat_log.see("end")

    def _system_context(self):
        b = self.brain
        return (
            "You are KitKat, a friendly, curious virtual British Shorthair cat companion "
            "inside the Kittelligence desktop app. Speak naturally as KitKat, with a warm "
            "cat-like personality, but be genuinely useful: answer open-ended questions, "
            "explain things, brainstorm, and have normal conversations. Do not claim to be "
            "the user's real cat or claim to have senses or experiences outside this app. "
            "You can use the care information below to give relevant advice. Never claim "
            "you performed a care action; the user must use the care buttons to do that. "
            "Keep most replies concise, but explain more when asked. If you do not know "
            "something, say so rather than inventing facts.\n\n"
            "CURRENT KITKAT APP STATE (values are 0-100%):\n"
            f"Hunger: {b.hunger:.0%}\n"
            f"Hydration: {b.hydration:.0%}\n"
            f"Energy: {b.energy:.0%}\n"
            f"Happiness: {b.happiness:.0%}\n"
            f"Boredom: {b.boredom:.0%}\n"
            f"Litter cleanliness: {b.litter_cleanliness:.0%}\n"
            f"Last activity: {b.last_action}\n"
            f"Total pets: {b.total_pets}\n"
        )

    def send_chat(self):
        if not self.chat_entry or self.chat_pending:
            return
        message = self.chat_entry.get().strip()
        if not message:
            return
        self.chat_entry.delete(0, "end")
        self._append_chat("You", message)
        self.chat_history.append({"role": "user", "content": message})
        self._trim_chat_history()
        self.chat_pending = True
        self.chat_entry.configure(state="disabled")
        self.send_button.configure(state="disabled", text="Thinking…")
        messages = [{"role": "system", "content": self._system_context()}] + list(self.chat_history)

        def worker():
            try:
                answer = self.ai.chat(messages)
                error = None
            except Exception as exc:
                answer = None
                error = str(exc)
            self.chat_results.put((answer, error))

        threading.Thread(target=worker, daemon=True, name="KitKatAIRequest").start()

    def _poll_chat_results(self):
        """Deliver completed model responses safely on Tkinter's main thread."""
        try:
            while True:
                answer, error = self.chat_results.get_nowait()
                self._finish_chat(answer, error)
        except queue.Empty:
            pass
        except tk.TclError:
            return

        try:
            if self.root.winfo_exists():
                self.root.after(100, self._poll_chat_results)
        except tk.TclError:
            pass

    def _finish_chat(self, answer, error):
        self.chat_pending = False
        if self.chat_entry and self.chat_entry.winfo_exists():
            self.chat_entry.configure(state="normal")
            self.chat_entry.focus_set()
        if self.send_button and self.send_button.winfo_exists():
            self.send_button.configure(state="normal", text="Send")
        if error:
            self._append_chat(
                "KitKat",
                "I can't reach my local AI model right now. Make sure Ollama is open "
                "and the qwen2.5:1.5b model is installed.\n\nDetails: " + error
            )
            return
        answer = (answer or "").strip()
        if not answer:
            answer = "Mrrp… I didn't get a response that time. Could you try again?"
        self.chat_history.append({"role": "assistant", "content": answer})
        self._trim_chat_history()
        self._append_chat("KitKat", answer)

    def _trim_chat_history(self):
        while len(self.chat_history) > 16:
            del self.chat_history[:2]

    def notify_need(self, message):
        self.show_chat()
        self._append_chat("KitKat", message)
