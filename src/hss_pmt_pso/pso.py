from __future__ import annotations

from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from collections.abc import Callable
from typing import TypedDict
import random


class Particle(TypedDict):
    position: dict[str, float]
    velocity: dict[str, float]
    best_position: dict[str, float]
    best_score: float


@dataclass(frozen=True)
class PSOResult:
    best_position: dict[str, float]
    best_score: float
    history: tuple[float, ...]


def optimize(
    *,
    objective: Callable[[dict[str, float]], float],
    bounds: dict[str, tuple[float, float]],
    particles: int,
    iterations: int,
    w: float,
    c1: float,
    c2: float,
    seed: int,
    workers: int = 1,
) -> PSOResult:
    if not bounds:
        raise ValueError("bounds cannot be empty")
    if particles < 2:
        raise ValueError("particles must be >= 2")
    if iterations < 1:
        raise ValueError("iterations must be >= 1")
    if workers < 1:
        raise ValueError("workers must be >= 1")
    for name, (lo, hi) in bounds.items():
        if lo >= hi:
            raise ValueError(f"invalid bound for {name!r}: min must be < max")

    rnd = random.Random(seed)
    names = tuple(bounds.keys())

    swarm: list[Particle] = []
    for _ in range(particles):
        position = {name: rnd.uniform(bounds[name][0], bounds[name][1]) for name in names}
        velocity = {name: 0.0 for name in names}
        swarm.append(
            {
                "position": position,
                "velocity": velocity,
                "best_position": dict(position),
                "best_score": float("inf"),
            }
        )

    global_best = dict(swarm[0]["position"])
    global_best_score = float("inf")
    history: list[float] = []

    def score_particle(particle: Particle) -> float:
        return objective(particle["position"])

    for _ in range(iterations):
        if workers > 1:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                scores = list(pool.map(score_particle, swarm))
        else:
            scores = [score_particle(p) for p in swarm]

        for particle, score in zip(swarm, scores):
            if score < particle["best_score"]:
                particle["best_score"] = score
                particle["best_position"] = dict(particle["position"])
            if score < global_best_score:
                global_best_score = score
                global_best = dict(particle["position"])

        history.append(global_best_score)

        for particle in swarm:
            for name in names:
                r1 = rnd.random()
                r2 = rnd.random()
                pbest = particle["best_position"][name]
                gbest = global_best[name]
                pos = particle["position"][name]
                vel = particle["velocity"][name]

                vel = w * vel + c1 * r1 * (pbest - pos) + c2 * r2 * (gbest - pos)
                next_pos = pos + vel
                lo, hi = bounds[name]

                if next_pos < lo:
                    next_pos = lo
                    vel *= -0.3
                elif next_pos > hi:
                    next_pos = hi
                    vel *= -0.3

                particle["position"][name] = next_pos
                particle["velocity"][name] = vel

    return PSOResult(
        best_position=global_best,
        best_score=global_best_score,
        history=tuple(history),
    )
