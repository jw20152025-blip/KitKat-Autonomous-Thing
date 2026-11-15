from __future__ import annotations

import math
import random
from typing import Iterable


class DeepDecisionNetwork:
    """Small CPU-friendly deep MLP that predicts action satisfaction.

    Six hidden layers are intentionally used. This is a local behavioural policy,
    not a language model; it learns from scored experiences rather than generating text.
    """

    AUTONOMOUS_ACTIONS = ("wander", "sit", "sleep", "meow", "idle")
    ACTIONS = AUTONOMOUS_ACTIONS + ("feed", "water", "play", "rest", "litter", "brush", "pet", "purr")
    INPUTS = 10
    WIDTHS = (128, 128, 96, 96, 64, 48)
    LEARNING_RATE = 0.0025

    def __init__(self, saved=None):
        self.rng = random.Random()
        self.weights = []
        self.biases = []
        sizes = (self.INPUTS,) + self.WIDTHS + (len(self.ACTIONS),)
        for fan_in, fan_out in zip(sizes[:-1], sizes[1:]):
            scale = math.sqrt(2.0 / fan_in)
            self.weights.append([
                [self.rng.gauss(0.0, scale) for _ in range(fan_in)]
                for _ in range(fan_out)
            ])
            self.biases.append([0.0] * fan_out)
        self.experiences = []
        self.training_steps = 0
        if isinstance(saved, dict):
            self._load(saved)

    @staticmethod
    def _sigmoid(value):
        value = max(-30.0, min(30.0, value))
        return 1.0 / (1.0 + math.exp(-value))

    def _forward(self, inputs):
        activations = [list(inputs)]
        current = list(inputs)
        for layer_index, (matrix, bias) in enumerate(zip(self.weights, self.biases)):
            values = [
                sum(weight * item for weight, item in zip(row, current)) + offset
                for row, offset in zip(matrix, bias)
            ]
            if layer_index == len(self.weights) - 1:
                current = [self._sigmoid(value) for value in values]
            else:
                current = [math.tanh(value) for value in values]
            activations.append(current)
        return activations

    def predict(self, inputs):
        return self._forward(self._normalise(inputs))[-1]

    def _normalise(self, inputs):
        values = list(inputs)[:self.INPUTS]
        values += [0.0] * (self.INPUTS - len(values))
        return [max(-1.0, min(1.0, float(value))) for value in values]

    def train(self, inputs, action_index, satisfaction):
        """Fit the chosen action's predicted satisfaction to its observed reward."""
        x = self._normalise(inputs)
        target = max(0.0, min(1.0, float(satisfaction) / 100.0))
        activations = self._forward(x)
        output = activations[-1]
        deltas = [[0.0] * len(layer) for layer in activations[1:]]
        last = len(self.weights) - 1
        for i, prediction in enumerate(output):
            if i == action_index:
                deltas[last][i] = (prediction - target) * prediction * (1.0 - prediction)
            else:
                deltas[last][i] = 0.0

        for layer in range(last - 1, -1, -1):
            next_delta = deltas[layer + 1]
            next_weights = self.weights[layer + 1]
            for i, activation in enumerate(activations[layer + 1]):
                propagated = sum(next_delta[j] * next_weights[j][i]
                                 for j in range(len(next_delta)))
                deltas[layer][i] = propagated * (1.0 - activation * activation)

        for layer_index, delta in enumerate(deltas):
            previous = activations[layer_index]
            for neuron_index, error in enumerate(delta):
                row = self.weights[layer_index][neuron_index]
                for weight_index in range(len(row)):
                    row[weight_index] -= self.LEARNING_RATE * error * previous[weight_index]
                self.biases[layer_index][neuron_index] -= self.LEARNING_RATE * error

        self.training_steps += 1
        self.experiences.append({
            "input": x,
            "action": int(action_index),
            "satisfaction": round(float(satisfaction), 2),
        })
        self.experiences = self.experiences[-500:]

    def export(self):
        return {
            "weights": self.weights,
            "biases": self.biases,
            "experiences": self.experiences[-500:],
            "training_steps": self.training_steps,
            "architecture": [self.INPUTS, *self.WIDTHS, len(self.ACTIONS)],
        }

    def _load(self, saved):
        try:
            weights = saved.get("weights")
            biases = saved.get("biases")
            if len(weights) != len(self.weights) or len(biases) != len(self.biases):
                return
            for index in range(len(self.weights)):
                if len(weights[index]) != len(self.weights[index]):
                    return
                if any(len(row) != len(self.weights[index][i])
                       for i, row in enumerate(weights[index])):
                    return
            self.weights = [[[float(v) for v in row] for row in layer] for layer in weights]
            self.biases = [[float(v) for v in layer] for layer in biases]
            self.experiences = list(saved.get("experiences", []))[-500:]
            self.training_steps = int(saved.get("training_steps", 0))
        except (TypeError, ValueError, KeyError, IndexError):
            # A corrupt or incompatible model is ignored; the pet can still start.
            pass
