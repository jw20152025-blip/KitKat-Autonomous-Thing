import random
import threading
import time
import json
from pathlib import Path


class KiteelegenceBrain:
    def __init__(self, pet):
        self.pet = pet

        self.running = False
        self.thread = None

        self.lock = threading.Lock()

        self.state = "idle"
        self.last_action = "startup"

        self.energy = 0.85
        self.happiness = 0.80
        self.boredom = 0.10
        self.curiosity = 0.90
        self.affection = 0.70
        self.hunger = 0.05
        self.excitement = 0.20

        self.personality = {
            "curiosity": 0.90,
            "playfulness": 0.82,
            "laziness": 0.48,
            "chaos": 0.62,
            "affection": 0.76,
            "independence": 0.85,
            "boldness": 0.72
        }

        self.memory = []
        self.action_history = []

        self.cooldowns = {}

        self.statistics = {
            "decisions": 0,
            "walks": 0,
            "chases": 0,
            "sleeps": 0,
            "meows": 0,
            "pets": 0
        }

        self._load_memory()

    # -------------------------
    # Lifecycle
    # -------------------------

    def start(self):
        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self._loop,
            daemon=True
        )

        self.thread.start()

    def stop(self):
        self.running = False

        if self.thread:
            self.thread.join(timeout=1)

        self._save_memory()

    # -------------------------
    # AI loop
    # -------------------------

    def _loop(self):
        while self.running:
            try:
                self._update_internal_state()

                if not self.pet.paused:
                    action = self._choose_action()

                    self.pet.root.after(
                        0,
                        self._execute,
                        action
                    )

            except Exception:
                pass

            time.sleep(
                random.uniform(
                    1.5,
                    4.0
                )
            )

    # -------------------------
    # Internal simulation
    # -------------------------

    def _update_internal_state(self):
        with self.lock:
            self.energy -= 0.002
            self.hunger += 0.002
            self.boredom += 0.006

            if self.state == "sleep":
                self.energy += 0.025

            self.energy = self._clamp(
                self.energy
            )

            self.hunger = self._clamp(
                self.hunger
            )

            self.boredom = self._clamp(
                self.boredom
            )

            self.happiness = self._clamp(
                self.happiness
            )

            self.excitement = self._clamp(
                self.excitement
            )

    # -------------------------
    # Decision engine
    # -------------------------

    def _choose_action(self):
        scores = {
            "idle": 0.10,
            "wander": 0.10,
            "sit": 0.10,
            "sleep": 0.05,
            "chase": 0.05,
            "meow": 0.03
        }

        # Energy
        if self.energy < 0.25:
            scores["sleep"] += 1.5
            scores["chase"] -= 0.8

        # Boredom
        if self.boredom > 0.65:
            scores["wander"] += 0.8
            scores["chase"] += (
                self.personality["playfulness"]
            )
            scores["meow"] += 0.3

        # Curiosity
        scores["wander"] += (
            self.curiosity *
            self.personality["curiosity"]
        )

        # Laziness
        scores["sit"] += (
            self.personality["laziness"] *
            0.8
        )

        # Chaos
        scores["chase"] += (
            self.personality["chaos"] *
            0.35
        )

        # Hunger
        if self.hunger > 0.75:
            scores["meow"] += 0.8
            scores["sit"] += 0.2

        # Randomness prevents robotic repetition
        for action in scores:
            scores[action] += random.uniform(
                0,
                0.25
            )

        # Cooldowns
        now = time.time()

        for action, until in list(
            self.cooldowns.items()
        ):
            if now < until:
                scores[action] *= 0.05

        return max(
            scores,
            key=scores.get
        )

    # -------------------------
    # Execution
    # -------------------------

    def _execute(self, action):
        if not self.running:
            return

        self.last_action = action
        self.state = action

        self.statistics["decisions"] += 1

        if action == "idle":
            self.pet.idle()

        elif action == "wander":
            self.statistics["walks"] += 1
            self.pet.walk()
            self.pet.random_destination()

            self.boredom -= 0.12

        elif action == "sit":
            self.pet.sit()
            self.energy += 0.04

        elif action == "sleep":
            self.statistics["sleeps"] += 1
            self.pet.sleep()
            self.energy += 0.15

        elif action == "chase":
            self.statistics["chases"] += 1
            self.pet.chase_cursor()

            self.excitement += 0.15
            self.boredom -= 0.20
            self.energy -= 0.06

            self.cooldowns[
                "chase"
            ] = time.time() + 8

        elif action == "meow":
            self.statistics["meows"] += 1
            self.pet.meow()

            self.happiness += 0.04
            self.boredom -= 0.06

            self.cooldowns[
                "meow"
            ] = time.time() + 5

        self._clamp_all()

        self.action_history.append(
            {
                "time": time.time(),
                "action": action
            }
        )

        self.action_history = (
            self.action_history[-50:]
        )

    # -------------------------
    # Interaction
    # -------------------------

    def register_pet(self):
        self.statistics["pets"] += 1

        self.affection += 0.08
        self.happiness += 0.12
        self.boredom -= 0.15

        self._clamp_all()

    # -------------------------
    # Persistence
    # -------------------------

    def _memory_file(self):
        path = Path("data")
        path.mkdir(exist_ok=True)
        return path / "kiteelegence.json"

    def _save_memory(self):
        try:
            data = {
                "personality": self.personality,
                "memory": self.memory[-100:],
                "statistics": self.statistics,
                "energy": self.energy,
                "happiness": self.happiness,
                "boredom": self.boredom,
                "curiosity": self.curiosity,
                "affection": self.affection,
                "hunger": self.hunger
            }

            with open(
                self._memory_file(),
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(
                    data,
                    file,
                    indent=2
                )

        except Exception:
            pass

    def _load_memory(self):
        try:
            file = self._memory_file()

            if not file.exists():
                return

            with open(
                file,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(f)

            self.personality.update(
                data.get(
                    "personality",
                    {}
                )
            )

            self.memory = data.get(
                "memory",
                []
            )

            self.statistics.update(
                data.get(
                    "statistics",
                    {}
                )
            )

        except Exception:
            pass

    # -------------------------
    # Helpers
    # -------------------------

    @staticmethod
    def _clamp(value):
        return max(
            0.0,
            min(
                1.0,
                value
            )
        )

    def _clamp_all(self):
        self.energy = self._clamp(
            self.energy
        )

        self.happiness = self._clamp(
            self.happiness
        )

        self.boredom = self._clamp(
            self.boredom
        )

        self.curiosity = self._clamp(
            self.curiosity
        )

        self.affection = self._clamp(
            self.affection
        )

        self.hunger = self._clamp(
            self.hunger
        )

        self.excitement = self._clamp(
            self.excitement
        )