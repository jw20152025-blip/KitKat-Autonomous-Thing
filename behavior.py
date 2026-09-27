class Behavior:

    IDLE = "idle"
    SIT = "sit"
    WALK = "walk"
    SLEEP = "sleep"
    MEOW = "meow"
    CHASE = "chase"
    PLAY = "play"
    GROOM = "groom"
    EAT = "eat"
    LOOK = "look"
    NONE = "none"


class KitKatState:

    def __init__(self):
        self.behavior = Behavior.IDLE
        self.energy = 100
        self.boredom = 0
        self.sleeping = False
        self.chasing_mouse = False
        self.mood = "curious"

    def set_behavior(self, behavior):
        self.behavior = behavior

    def sit(self):
        self.behavior = Behavior.SIT
        self.sleeping = False
        self.chasing_mouse = False
        self.mood = "calm"

    def sleep(self):
        self.behavior = Behavior.SLEEP
        self.sleeping = True
        self.chasing_mouse = False
        self.mood = "sleepy"

    def wake(self):
        self.behavior = Behavior.IDLE
        self.sleeping = False
        self.mood = "curious"

    def get_state(self):
        return {
            "behavior": self.behavior,
            "energy": self.energy,
            "boredom": self.boredom,
            "sleeping": self.sleeping,
            "chasing_mouse": self.chasing_mouse,
            "mood": self.mood
        }