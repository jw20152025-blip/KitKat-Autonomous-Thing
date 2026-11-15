from __future__ import annotations

import random
import time

from decision_network import DeepDecisionNetwork


class AutonomousBrain:
    """Needs, experience scoring and a persistent deep neural behaviour policy."""

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
        self.history = list(data.get("actions", []))[-500:]
        self.last_action = "Just woke up"
        self.last_satisfaction = float(data.get("last_satisfaction", 50.0))
        self.paused = False
        self.after_id = None
        self.started_at = time.time()
        self.on_need = None
        self.alerted_needs = set()
        self.network = DeepDecisionNetwork(data.get("decision_network"))
        self._pending_action = None
        self._tick_count = 0

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

    def _features(self):
        p = self.personality
        hour = time.localtime().tm_hour
        day_phase = (hour / 24.0) * 2.0 - 1.0
        return [
            self.energy * 2 - 1, self.happiness * 2 - 1,
            self.boredom * 2 - 1, self.hunger * 2 - 1,
            self.hydration * 2 - 1, self.litter_cleanliness * 2 - 1,
            float(p.get("curiosity", .5)) * 2 - 1,
            float(p.get("playfulness", .5)) * 2 - 1,
            float(p.get("laziness", .5)) * 2 - 1,
            day_phase,
        ]

    def _base_action_scores(self):
        p = self.personality
        return {
            "wander": 0.20 + self.boredom * 0.42 + p.get("curiosity", .5) * .16
                      + p.get("playfulness", .5) * .12 - (1 - self.energy) * .22,
            "sit": 0.15 + p.get("laziness", .5) * .25 + (1 - self.energy) * .15,
            "sleep": 0.08 + (1 - self.energy) * .80,
            "meow": 0.08 + p.get("affection", .5) * .15 + self.hunger * .18,
            "idle": 0.12,
        }

    def _choose_action(self):
        actions = self.network.ACTIONS
        learned = self.network.predict(self._features())
        base = self._base_action_scores()
        scores = {
            action: base[action] + (learned[index] - 0.5) * 0.28
            for index, action in enumerate(actions)
        }
        # Needs remain hard constraints; learning cannot make him ignore exhaustion.
        if self.energy < 0.16:
            return "sleep"
        if self.hunger > 0.91 and random.random() < 0.45:
            return "meow"
        # Small exploration rate lets him discover actions whose outcomes may surprise him.
        if random.random() < 0.08:
            return random.choice(actions)
        return max(scores, key=scores.get)

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

    def _wellbeing(self):
        return (
            self.energy * .24 + self.happiness * .22
            + (1 - self.boredom) * .18 + (1 - self.hunger) * .16
            + self.hydration * .12 + self.litter_cleanliness * .08
        )

    def _score_experience(self, before, action, user_action=False):
        after = self._wellbeing()
        delta = after - before
        preference = {
            "wander": self.personality.get("curiosity", .5) * 5,
            "sit": self.personality.get("laziness", .5) * 4,
            "sleep": (1 - self.energy) * 7,
            "meow": self.personality.get("affection", .5) * 4,
            "idle": 0,
            "feed": self.hunger * 8,
            "water": (1 - self.hydration) * 8,
            "play": self.boredom * 8,
            "rest": (1 - self.energy) * 8,
            "litter": (1 - self.litter_cleanliness) * 8,
            "brush": self.personality.get("affection", .5) * 6,
            "pet": self.personality.get("affection", .5) * 7,
        }.get(action, 0)
        # Satisfaction is a scored experience, not a claim that the cat has real feelings.
        satisfaction = max(0.0, min(100.0, 52.0 + delta * 260.0 + preference))
        if user_action:
            satisfaction = min(100.0, satisfaction + 3.0)
        self.last_satisfaction = round(satisfaction, 1)
        if action in self.network.ACTIONS:
            self.network.train(self._features(), self.network.ACTIONS.index(action), satisfaction)
        self.history.append({
            "time": time.time(), "action": action,
            "satisfaction": self.last_satisfaction,
            "wellbeing_delta": round(delta, 5),
        })
        self.history = self.history[-500:]
        return self.last_satisfaction

    def _record(self, action, description, before, user_action=False):
        self.last_action = description
        self._score_experience(before, action, user_action=user_action)
        self.store.save(self.export_state())

    def _think(self):
        self.after_id = None
        if not self.paused and not self.pet.paused:
            before = self._wellbeing()
            self.energy = self._clamp(self.energy - 0.0025)
            self.boredom = self._clamp(self.boredom + 0.008)
            self.hunger = self._clamp(self.hunger + 0.0025)
            self.hydration = self._clamp(self.hydration - 0.0015)
            self.litter_cleanliness = self._clamp(self.litter_cleanliness - 0.0005)
            if self.pet.animation == "sleep":
                self.energy = self._clamp(self.energy + 0.035)
            self._check_important_needs()
            action = self._choose_action()
            self._act(action, before)
            self._tick_count += 1
            if self._tick_count % 8 == 0:
                self.store.save(self.export_state())
        self._schedule(random.randint(3500, 6500))

    def _act(self, action, before=None):
        if before is None:
            before = self._wellbeing()
        self.last_action = action.title()
        if action == "wander":
            self.pet.wander()
            self.boredom = self._clamp(self.boredom - 0.16)
        elif action == "sleep":
            self.pet.sleep()
            self.energy = self._clamp(self.energy + 0.09)
        elif action == "sit":
            self.pet.sit()
            self.energy = self._clamp(self.energy + 0.025)
        elif action == "meow":
            self.pet.meow()
            self.happiness = self._clamp(self.happiness + 0.02)
        else:
            self.pet._set_animation("idle")
        self._score_experience(before, action)

    def _care(self, action, description, change):
        before = self._wellbeing()
        change()
        self._record(action, description, before, user_action=True)

    def feed(self):
        self._care("feed", "Had a meal", lambda: (
            setattr(self, "hunger", self._clamp(self.hunger - .65)),
            setattr(self, "happiness", self._clamp(self.happiness + .05))
        ))

    def give_water(self):
        self._care("water", "Had some water",
                   lambda: setattr(self, "hydration", self._clamp(self.hydration + .65)))

    def play(self):
        def change():
            self.boredom = self._clamp(self.boredom - .55)
            self.energy = self._clamp(self.energy - .08)
            self.happiness = self._clamp(self.happiness + .10)
            self.pet.wander()
        self._care("play", "Played with you", change)

    def rest(self):
        def change():
            self.pet.sleep()
            self.energy = self._clamp(self.energy + .12)
        self._care("rest", "Settled down for a nap", change)

    def clean_litter(self):
        def change():
            self.litter_cleanliness = 1.0
            self.happiness = self._clamp(self.happiness + .03)
        self._care("litter", "Litter area cleaned", change)

    def brush(self):
        def change():
            self.happiness = self._clamp(self.happiness + .08)
            self.boredom = self._clamp(self.boredom - .05)
        self._care("brush", "Enjoyed a brush", change)

    def on_petted(self):
        def change():
            self.total_pets += 1
            self.happiness = self._clamp(self.happiness + .10)
            self.boredom = self._clamp(self.boredom - .18)
        self._care("pet", "Enjoyed a pet", change)

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.pet.target = None
            self.pet._set_animation("idle")
        return self.paused

    def export_state(self):
        return {
            "personality": self.personality,
            "energy": self.energy, "happiness": self.happiness,
            "boredom": self.boredom, "hunger": self.hunger,
            "hydration": self.hydration,
            "litter_cleanliness": self.litter_cleanliness,
            "total_pets": self.total_pets, "actions": self.history,
            "last_satisfaction": self.last_satisfaction,
            "decision_network": self.network.export(),
        }
