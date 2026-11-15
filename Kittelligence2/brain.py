from __future__ import annotations

import random
import time


class AutonomousBrain:
    """Local, explainable needs and behaviour system for the desktop pet."""

    def __init__(self, pet, store):
        self.pet = pet
        self.store = store
        data = store.data
        self.personality = data["personality"]
        self.energy = float(data["energy"])
        self.happiness = float(data["happiness"])
        self.boredom = float(data["boredom"])
        self.hunger = float(data["hunger"])
        self.hydration = float(data.get("hydration", 0.82))
        self.litter_cleanliness = float(data.get("litter_cleanliness", 0.92))
        self.total_pets = int(data["total_pets"])
        self.history = list(data.get("actions", []))
        self.last_action = "Just woke up"
        self.paused = False
        self.after_id = None
        self.started_at = time.time()
        self.on_need = None
        self.alerted_needs = set()

    def start(self):
        self._schedule(2500)

    def stop(self):
        if self.after_id:
            try:
                self.pet.root.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None

    def _schedule(self, delay):
        self.after_id = self.pet.root.after(delay, self._think)

    @staticmethod
    def _clamp(value):
        return max(0.0, min(1.0, value))

    def _check_important_needs(self):
        needs = []
        if self.hunger >= 0.88:
            needs.append(("food", "I'm getting hungry. Could you give me a meal?"))
        if self.hydration <= 0.16:
            needs.append(("water", "I'm thirsty. Could you refill my water bowl?"))
        if self.energy <= 0.12:
            needs.append(("sleep", "I'm really tired. I could use a nap."))
        if self.litter_cleanliness <= 0.18:
            needs.append(("litter", "My litter area needs cleaning."))
        active = {key for key, _ in needs}
        self.alerted_needs.intersection_update(active)
        for key, message in needs:
            if key not in self.alerted_needs:
                self.alerted_needs.add(key)
                if self.on_need:
                    self.on_need(message)

    def _think(self):
        self.after_id = None
        if not self.paused and not self.pet.paused:
            self.energy = self._clamp(self.energy - 0.003)
            self.boredom = self._clamp(self.boredom + 0.012)
            self.hunger = self._clamp(self.hunger + 0.004)
            self.hydration = self._clamp(self.hydration - 0.0025)
            self.litter_cleanliness = self._clamp(self.litter_cleanliness - 0.0008)
            if self.pet.animation == "sleep":
                self.energy = self._clamp(self.energy + 0.055)
            self._check_important_needs()
            self._act(self._choose_action())
            self.store.save(self.export_state())
        self._schedule(random.randint(3500, 6500))

    def _choose_action(self):
        p = self.personality
        if self.energy < 0.22:
            return "sleep"
        if self.hunger > 0.88 and random.random() < 0.55:
            return "meow"
        weights = {
            "wander": 1.0 + self.boredom * 2.0 + p["curiosity"],
            "sit": 0.5 + p["laziness"],
            "sleep": 0.25 + (1 - self.energy) * 1.8,
            "meow": 0.15 + p["affection"] * 0.25,
            "idle": 0.25,
        }
        return random.choices(list(weights), weights=list(weights.values()), k=1)[0]

    def _record(self, action, description):
        self.last_action = description
        self.history.append({"time": time.time(), "action": action})
        self.history = self.history[-100:]
        self.store.save(self.export_state())

    def _act(self, action):
        self.last_action = action.title()
        if action == "wander":
            self.pet.wander()
            self.boredom = self._clamp(self.boredom - 0.24)
        elif action == "sleep":
            self.pet.sleep()
            self.energy = self._clamp(self.energy + 0.12)
        elif action == "sit":
            self.pet.sit()
            self.energy = self._clamp(self.energy + 0.035)
        elif action == "meow":
            self.pet.meow()
            self.happiness = self._clamp(self.happiness + 0.025)
        else:
            self.pet._set_animation("idle")
        self.history.append({"time": time.time(), "action": action})
        self.history = self.history[-100:]

    def feed(self):
        self.hunger = self._clamp(self.hunger - 0.65)
        self.happiness = self._clamp(self.happiness + 0.05)
        self._record("feed", "Had a meal")

    def give_water(self):
        self.hydration = self._clamp(self.hydration + 0.65)
        self._record("water", "Had some water")

    def play(self):
        self.boredom = self._clamp(self.boredom - 0.55)
        self.energy = self._clamp(self.energy - 0.08)
        self.happiness = self._clamp(self.happiness + 0.10)
        self.pet.wander()
        self._record("play", "Played with you")

    def rest(self):
        self.pet.sleep()
        self.energy = self._clamp(self.energy + 0.12)
        self._record("rest", "Settled down for a nap")

    def clean_litter(self):
        self.litter_cleanliness = 1.0
        self.happiness = self._clamp(self.happiness + 0.03)
        self._record("litter", "Litter area cleaned")

    def brush(self):
        self.happiness = self._clamp(self.happiness + 0.08)
        self.boredom = self._clamp(self.boredom - 0.05)
        self._record("brush", "Enjoyed a brush")

    def on_petted(self):
        self.total_pets += 1
        self.happiness = self._clamp(self.happiness + 0.10)
        self.boredom = self._clamp(self.boredom - 0.18)
        self._record("pet", "Enjoyed a pet")

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.pet.target = None
            self.pet._set_animation("idle")
        return self.paused

    def export_state(self):
        return {
            "personality": self.personality,
            "energy": self.energy,
            "happiness": self.happiness,
            "boredom": self.boredom,
            "hunger": self.hunger,
            "hydration": self.hydration,
            "litter_cleanliness": self.litter_cleanliness,
            "total_pets": self.total_pets,
            "actions": self.history,
        }
