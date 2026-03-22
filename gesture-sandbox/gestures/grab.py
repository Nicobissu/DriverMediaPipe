from gestures.base import Gesture, GestureResult
from core.hand_tracker import HandTracker as HT
from utils.math_helpers import distance_2d


class GrabGesture(Gesture):
    NAME = "GRAB"

    def detect(self, hands, frame_shape):
        if not hands:
            return GestureResult(self.NAME, 0.0, False)

        lm = hands[0]
        wrist = lm[HT.WRIST]

        # Count how many fingers (index, middle, ring, pinky) are curled
        # A finger is curled if its tip is closer to wrist than its MCP joint
        curled_count = 0
        for tip, mcp in [
            (HT.INDEX_TIP, HT.INDEX_MCP),
            (HT.MIDDLE_TIP, HT.MIDDLE_MCP),
            (HT.RING_TIP, HT.RING_MCP),
            (HT.PINKY_TIP, HT.PINKY_MCP),
        ]:
            if distance_2d(lm[tip], wrist) < distance_2d(lm[mcp], wrist) * 1.15:
                curled_count += 1

        # At least 3 of 4 fingers curled = fist (more forgiving)
        is_fist = curled_count >= 3

        if is_fist:
            h, w = frame_shape
            # Use middle of hand (MCP of middle finger) for position
            cx = lm[HT.MIDDLE_MCP].x
            cy = lm[HT.MIDDLE_MCP].y
            confidence = 0.6 + curled_count * 0.1
            return GestureResult(self.NAME, confidence, True, {
                "x": cx, "y": cy,
                "px": int(cx * w), "py": int(cy * h),
            })

        return GestureResult(self.NAME, 0.0, False)
