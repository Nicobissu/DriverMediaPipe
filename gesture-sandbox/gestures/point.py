from gestures.base import Gesture, GestureResult
from core.hand_tracker import HandTracker as HT
from utils.math_helpers import distance_2d


class PointGesture(Gesture):
    NAME = "POINT"

    def detect(self, hands, frame_shape):
        if not hands:
            return GestureResult(self.NAME, 0.0, False)

        lm = hands[0]
        wrist = lm[HT.WRIST]

        # Index finger must be extended
        index_extended = distance_2d(lm[HT.INDEX_TIP], wrist) > distance_2d(lm[HT.INDEX_PIP], wrist)

        # Other fingers (middle, ring, pinky) should be curled
        others_curled = all(
            distance_2d(lm[tip], wrist) < distance_2d(lm[pip], wrist)
            for tip, pip in [
                (HT.MIDDLE_TIP, HT.MIDDLE_PIP),
                (HT.RING_TIP, HT.RING_PIP),
                (HT.PINKY_TIP, HT.PINKY_PIP),
            ]
        )

        if index_extended and others_curled:
            # Cursor position: index tip, in pixel coords
            h, w = frame_shape
            cx = lm[HT.INDEX_TIP].x
            cy = lm[HT.INDEX_TIP].y
            return GestureResult(self.NAME, 0.9, True, {"x": cx, "y": cy, "px": int(cx * w), "py": int(cy * h)})

        return GestureResult(self.NAME, 0.0, False)
