from __future__ import annotations

import json
import os
from pathlib import Path


class MemoryStore:
    def __init__(self):
        base = Path(os.environ.get("APPDATA", Path.home())) / "Kittelligence"
        base.mkdir(parents=True, exist_ok=True)
        self.path = base / "memory.json"
        self.data = self.load()

    def load(self):
        defaults = {
            "personality": {"curiosity": 0.82, "playfulness": 0.72,
                            "laziness": 0.48, "affection": 0.78},
            "energy": 0.82, "happiness": 0.78, "boredom": 0.12,
            "hunger": 0.08, "hydration": 0.82, "litter_cleanliness": 0.92,
            "total_pets": 0, "actions": [], "notes": [],
            "last_satisfaction": 50.0, "decision_network": None,
        }
        try:
            if self.path.exists():
                saved = json.loads(self.path.read_text(encoding="utf-8"))
                defaults.update(saved)
                defaults["personality"].update(saved.get("personality", {}))
        except (OSError, ValueError, TypeError):
            pass
        return defaults

    def save(self, data=None):
        if data is not None:
            self.data.update(data)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        temporary.replace(self.path)
