from collections import deque
from gestures.fingers import FingersGesture
from gestures.base import GestureResult
from config import SMOOTHING_FRAMES, GESTURE_HOLD_FRAMES, PINCH_ACTIVATE_DIST, PINCH_DEACTIVATE_DIST


class GestureEngine:
    """Detects individual fingers, then maps combinations to actions."""

    def __init__(self):
        self._fingers_detector = FingersGesture()
        self.current_gesture = GestureResult("IDLE", 0.0, False)
        self.finger_state = {}  # live state of each finger
        self._history = deque(maxlen=GESTURE_HOLD_FRAMES)
        self._position_buffer = deque(maxlen=SMOOTHING_FRAMES)
        self._pinch_active = False

    def update(self, hands, frame_shape):
        """Run finger detection, classify gesture, return result."""
        finger_result = self._fingers_detector.detect(hands, frame_shape)

        if not finger_result.active:
            self.finger_state = {}
            self.current_gesture = GestureResult("IDLE", 0.0, False)
            self._history.clear()
            self._position_buffer.clear()
            return self.current_gesture

        d = finger_result.data
        self.finger_state = d["fingers"]
        count = d["count_up"]
        extended = set(d["extended"])

        # ── Pinch detection with hysteresis ──
        pinch_dist = d.get("pinch_dist", 1.0)
        if self._pinch_active:
            self._pinch_active = pinch_dist < PINCH_DEACTIVATE_DIST
        else:
            self._pinch_active = pinch_dist < PINCH_ACTIVATE_DIST

        # ── Classify gesture from finger state ──
        if self._pinch_active:
            gesture_name = "PINCH"          # thumb + index touching → double click
        elif count == 0:
            gesture_name = "FIST"           # all closed → click
        elif "index" in extended and "middle" in extended and "ring" in extended:
            gesture_name = "THREE"          # index+middle+ring → scroll
        elif "index" in extended and "middle" in extended:
            gesture_name = "CURSOR"         # index+middle → move cursor
        elif extended == {"index"}:
            gesture_name = "STANDBY"        # only index → standby (no action)
        elif count == 5:
            gesture_name = "PALM"           # all open
        else:
            gesture_name = f"FINGERS_{count}"

        best = GestureResult(gesture_name, 0.9, True, {
            "fingers": d["fingers"],
            "extended": d["extended"],
            "closed": d["closed"],
            "count_up": count,
            "x": d["x"], "y": d["y"],
            "px": d["px"], "py": d["py"],
        })

        # Stabilize: require consistent detection for GESTURE_HOLD_FRAMES
        self._history.append(gesture_name)
        if len(self._history) == GESTURE_HOLD_FRAMES:
            if all(g == gesture_name for g in self._history):
                self.current_gesture = best
        else:
            self.current_gesture = best

        # Smooth position
        self._position_buffer.append((d["x"], d["y"]))
        if self._position_buffer:
            avg_x = sum(p[0] for p in self._position_buffer) / len(self._position_buffer)
            avg_y = sum(p[1] for p in self._position_buffer) / len(self._position_buffer)
            h, w = frame_shape
            self.current_gesture.data["smooth_x"] = avg_x
            self.current_gesture.data["smooth_y"] = avg_y
            self.current_gesture.data["smooth_px"] = int(avg_x * w)
            self.current_gesture.data["smooth_py"] = int(avg_y * h)

        return self.current_gesture
