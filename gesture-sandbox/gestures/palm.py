from gestures.base import Gesture, GestureResult
from core.hand_tracker import HandTracker as HT
from utils.math_helpers import distance_2d


class PalmGesture(Gesture):
    NAME = "PALM"

    def detect(self, hands, frame_shape):
        if not hands:
            return GestureResult(self.NAME, 0.0, False)

        lm = hands[0]
        wrist = lm[HT.WRIST]

        # All 5 fingers extended
        all_extended = all(
            distance_2d(lm[tip], wrist) > distance_2d(lm[pip], wrist)
            for tip, pip in zip(HT.FINGER_TIPS[1:], HT.FINGER_PIPS[1:])
        )

        # Thumb: tip.x farther from wrist.x than MCP.x
        thumb_ext = abs(lm[HT.THUMB_TIP].x - wrist.x) > abs(lm[HT.THUMB_MCP].x - wrist.x)

        if all_extended and thumb_ext:
            return GestureResult(self.NAME, 0.9, True)

        return GestureResult(self.NAME, 0.0, False)
