import math


def distance_2d(p1, p2):
    """Euclidean distance between two (x, y) points or landmark objects."""
    x1, y1 = _unpack(p1)
    x2, y2 = _unpack(p2)
    return math.hypot(x2 - x1, y2 - y1)


def midpoint_2d(p1, p2):
    x1, y1 = _unpack(p1)
    x2, y2 = _unpack(p2)
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def angle_between(p1, p2, p3):
    """Angle at p2 formed by segments p1-p2 and p2-p3, in degrees."""
    x1, y1 = _unpack(p1)
    x2, y2 = _unpack(p2)
    x3, y3 = _unpack(p3)
    v1 = (x1 - x2, y1 - y2)
    v2 = (x3 - x2, y3 - y2)
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.hypot(*v1)
    mag2 = math.hypot(*v2)
    if mag1 * mag2 == 0:
        return 0.0
    cos_a = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cos_a))


def lerp(a, b, t):
    """Linear interpolation between a and b."""
    return a + (b - a) * t


def _unpack(p):
    """Extract (x, y) from a tuple, list, or MediaPipe landmark."""
    if hasattr(p, "x") and hasattr(p, "y"):
        return p.x, p.y
    return p[0], p[1]
