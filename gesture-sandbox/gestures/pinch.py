from gestures.base import Gesture, GestureResult
from core.hand_tracker import HandTracker as HT
from utils.math_helpers import distance_2d, midpoint_2d
from config import PINCH_ACTIVATE_DIST, PINCH_DEACTIVATE_DIST


class PinchGesture(Gesture):
    NAME = "PINCH"

    def __init__(self):
        self._active = False

    def detect(self, hands, frame_shape):
        if not hands:
            self._active = False
            return GestureResult(self.NAME, 0.0, False)

        lm = hands[0]
        thumb_tip = lm[HT.THUMB_TIP]
        index_tip = lm[HT.INDEX_TIP]
        dist = distance_2d(thumb_tip, index_tip)

        # Hysteresis
        if self._active:
            self._active = dist < PINCH_DEACTIVATE_DIST
        else:
            self._active = dist < PINCH_ACTIVATE_DIST

        if self._active:
            mx, my = midpoint_2d(thumb_tip, index_tip)
            h, w = frame_shape
            confidence = max(0.0, 1.0 - dist / PINCH_DEACTIVATE_DIST)
            return GestureResult(self.NAME, confidence, True, {
                "x": mx, "y": my,
                "px": int(mx * w), "py": int(my * h),
                "distance": dist,
            })

        return GestureResult(self.NAME, 0.0, False)
