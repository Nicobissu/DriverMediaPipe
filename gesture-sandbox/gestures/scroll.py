from gestures.base import Gesture, GestureResult
from core.hand_tracker import HandTracker as HT
from utils.math_helpers import distance_2d
from config import SCROLL_MIN_VELOCITY


class ScrollGesture(Gesture):
    NAME = "SCROLL"

    def __init__(self):
        self._prev_y = None

    def detect(self, hands, frame_shape):
        if not hands:
            self._prev_y = None
            return GestureResult(self.NAME, 0.0, False)

        lm = hands[0]
        wrist = lm[HT.WRIST]

        # Index and middle extended, others curled
        index_ext = distance_2d(lm[HT.INDEX_TIP], wrist) > distance_2d(lm[HT.INDEX_PIP], wrist)
        middle_ext = distance_2d(lm[HT.MIDDLE_TIP], wrist) > distance_2d(lm[HT.MIDDLE_PIP], wrist)
        ring_curled = distance_2d(lm[HT.RING_TIP], wrist) < distance_2d(lm[HT.RING_PIP], wrist)
        pinky_curled = distance_2d(lm[HT.PINKY_TIP], wrist) < distance_2d(lm[HT.PINKY_PIP], wrist)

        if not (index_ext and middle_ext and ring_curled and pinky_curled):
            self._prev_y = None
            return GestureResult(self.NAME, 0.0, False)

        avg_y = (lm[HT.INDEX_TIP].y + lm[HT.MIDDLE_TIP].y) / 2

        if self._prev_y is None:
            self._prev_y = avg_y
            return GestureResult(self.NAME, 0.3, False)

        dy = avg_y - self._prev_y
        self._prev_y = avg_y

        if abs(dy) < SCROLL_MIN_VELOCITY:
            return GestureResult(self.NAME, 0.3, False)

        direction = "down" if dy > 0 else "up"
        return GestureResult(self.NAME, 0.8, True, {
            "direction": direction,
            "velocity": dy,
        })
