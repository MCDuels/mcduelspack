"""Easing for the frames that have to be baked; the backend eases everything that only slides."""
import math

DROP_TICKS = 4
DROP_FROM_SCALE = 3
SPRING_TICKS = 13
IMPACT_TICKS = 10


def ease_out_expo(x):
    return 1 if x >= 1 else 1 - 2 ** (-10 * x)


def drop_scales():
    """The VS shrinks from 3x with an ease-in, so it lands hard on the impact tick."""
    return [DROP_FROM_SCALE + (1 - DROP_FROM_SCALE) * (tick / DROP_TICKS) ** 3 for tick in range(DROP_TICKS)]


def spring_depths():
    """How far the echoes trail the letters on each tick after impact, as a damped spring."""
    depths = []
    for tick in range(SPRING_TICKS):
        seconds = tick / 20
        depths.append(0.35 + math.exp(-seconds * 6) * math.cos(seconds * 18) * 0.9)
    return depths
