"""Detects the state of each individual finger."""

from gestures.base import Gesture, GestureResult
from core.hand_tracker import HandTracker as HT
from utils.math_helpers import distance_2d


class FingersGesture(Gesture):
    NAME = "FINGERS"

    FINGER_NAMES = ["thumb", "index", "middle", "ring", "pinky"]

    def detect(self, hands, frame_shape):
        if not hands:
            return GestureResult(self.NAME, 0.0, False)

        lm = hands[0]
        wrist = lm[HT.WRIST]

        fingers = {}

        # Thumb: lateral check — tip.x farther from wrist.x than IP joint
        thumb_tip = lm[HT.THUMB_TIP]
        thumb_ip = lm[HT.THUMB_IP]
        thumb_ext = abs(thumb_tip.x - wrist.x) > abs(thumb_ip.x - wrist.x)
        fingers["thumb"] = thumb_ext

        # Index, middle, ring, pinky: tip farther from wrist than MCP
        for name, tip_idx, mcp_idx in [
            ("index", HT.INDEX_TIP, HT.INDEX_MCP),
            ("middle", HT.MIDDLE_TIP, HT.MIDDLE_MCP),
            ("ring", HT.RING_TIP, HT.RING_MCP),
            ("pinky", HT.PINKY_TIP, HT.PINKY_MCP),
        ]:
            tip_dist = distance_2d(lm[tip_idx], wrist)
            mcp_dist = distance_2d(lm[mcp_idx], wrist)
            fingers[name] = tip_dist > mcp_dist * 1.1  # small margin

        # Count
        extended = [name for name, state in fingers.items() if state]
        closed = [name for name, state in fingers.items() if not state]
        count_up = len(extended)

        # Pinch: minimum distance between thumb line (TIP, IP) and index line (MCP, PIP, DIP, TIP)
        thumb_nodes = [HT.THUMB_TIP, HT.THUMB_IP]
        index_nodes = [HT.INDEX_MCP, HT.INDEX_PIP, HT.INDEX_DIP, HT.INDEX_TIP]
        pinch_dist = min(
            distance_2d(lm[t], lm[i])
            for t in thumb_nodes
            for i in index_nodes
        )

        # Position from index tip (for cursor)
        h, w = frame_shape
        cx = lm[HT.INDEX_TIP].x
        cy = lm[HT.INDEX_TIP].y

        return GestureResult(self.NAME, 1.0, True, {
            "fingers": fingers,
            "extended": extended,
            "closed": closed,
            "count_up": count_up,
            "pinch_dist": pinch_dist,
            "x": cx, "y": cy,
            "px": int(cx * w), "py": int(cy * h),
        })
