from gestures.base import Gesture, GestureResult
from core.hand_tracker import HandTracker as HT
from utils.math_helpers import distance_2d, midpoint_2d
from config import ZOOM_SENSITIVITY


class ZoomGesture(Gesture):
    NAME = "ZOOM"

    def __init__(self):
        self._initial_dist = None

    def detect(self, hands, frame_shape):
        if len(hands) < 2:
            self._initial_dist = None
            return GestureResult(self.NAME, 0.0, False)

        # Pinch point of each hand: midpoint of thumb tip + index tip
        p1 = midpoint_2d(hands[0][HT.THUMB_TIP], hands[0][HT.INDEX_TIP])
        p2 = midpoint_2d(hands[1][HT.THUMB_TIP], hands[1][HT.INDEX_TIP])
        dist = distance_2d(p1, p2)

        if self._initial_dist is None:
            self._initial_dist = dist

        if self._initial_dist > 0:
            factor = (dist / self._initial_dist - 1.0) * ZOOM_SENSITIVITY
        else:
            factor = 0.0

        center = midpoint_2d(p1, p2)
        h, w = frame_shape
        return GestureResult(self.NAME, 0.85, True, {
            "factor": factor,
            "distance": dist,
            "center_x": center[0],
            "center_y": center[1],
            "px": int(center[0] * w),
            "py": int(center[1] * h),
        })
