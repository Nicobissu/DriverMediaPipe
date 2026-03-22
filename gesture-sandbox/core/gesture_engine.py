from collections import deque
from gestures.fingers import FingersGesture
from gestures.base import GestureResult
from config import SMOOTHING_FRAMES, GESTURE_HOLD_FRAMES, PINCH_ACTIVATE_DIST, PINCH_DEACTIVATE_DIST
from utils.math_helpers import distance_2d


class _HandState:
    """Per-hand tracking state."""

    def __init__(self):
        self.gesture = GestureResult("IDLE", 0.0, False)
        self.finger_state = {}
        self._history = deque(maxlen=GESTURE_HOLD_FRAMES)
        self._position_buffer = deque(maxlen=SMOOTHING_FRAMES)
        self._pinch_active = False

    def reset(self):
        self.gesture = GestureResult("IDLE", 0.0, False)
        self.finger_state = {}
        self._history.clear()
        self._position_buffer.clear()
        self._pinch_active = False


def _classify_right(extended, count, pinch_active):
    """Right hand: cursor control, click, scroll."""
    if pinch_active:
        return "R_DOUBLE_CLICK"
    if count == 0:
        return "R_CLICK"
    if "index" in extended and "middle" in extended and "ring" in extended:
        return "R_SCROLL"
    if "index" in extended and "middle" in extended:
        return "R_CURSOR"
    if extended == {"index"}:
        return "R_STANDBY"
    if count == 5:
        return "R_PALM"
    return f"R_FINGERS_{count}"


def _classify_left(extended, count, pinch_active, pinky_index_close):
    """Left hand: window management commands."""
    if pinch_active:
        return "L_MINIMIZE"         # thumb + index = minimize
    if pinky_index_close:
        return "L_CLOSE"            # index + pinky together = close
    if count == 0:
        return "L_SELECT"           # fist = select/focus app
    if count == 5:
        return "L_IDLE"             # palm open = idle
    return f"L_FINGERS_{count}"


class GestureEngine:
    """Detects individual fingers per hand, classifies gestures."""

    def __init__(self):
        self._fingers_detector = FingersGesture()
        self.right = _HandState()
        self.left = _HandState()

    def update(self, hands_dict, frame_shape):
        """Process both hands. Returns (right_gesture, left_gesture)."""
        right_gesture = self._process_hand(
            hands_dict.get("right"), frame_shape, self.right, is_right=True
        )
        left_gesture = self._process_hand(
            hands_dict.get("left"), frame_shape, self.left, is_right=False
        )
        return right_gesture, left_gesture

    def _process_hand(self, hand_landmarks, frame_shape, state, is_right):
        """Process a single hand."""
        if hand_landmarks is None:
            state.reset()
            return state.gesture

        # Wrap in list (fingers detector expects list of hands)
        finger_result = self._fingers_detector.detect([hand_landmarks], frame_shape)

        if not finger_result.active:
            state.reset()
            return state.gesture

        d = finger_result.data
        state.finger_state = d["fingers"]
        count = d["count_up"]
        extended = set(d["extended"])

        # Pinch detection with hysteresis
        pinch_dist = d.get("pinch_dist", 1.0)
        if state._pinch_active:
            state._pinch_active = pinch_dist < PINCH_DEACTIVATE_DIST
        else:
            state._pinch_active = pinch_dist < PINCH_ACTIVATE_DIST

        # Classify based on which hand
        if is_right:
            gesture_name = _classify_right(extended, count, state._pinch_active)
        else:
            # Check if index and pinky tips are close (for close window gesture)
            from core.hand_tracker import HandTracker as HT
            idx_tip = hand_landmarks[HT.INDEX_TIP]
            pinky_tip = hand_landmarks[HT.PINKY_TIP]
            pinky_index_dist = distance_2d(idx_tip, pinky_tip)
            pinky_index_close = pinky_index_dist < 0.06

            gesture_name = _classify_left(extended, count, state._pinch_active, pinky_index_close)

        best = GestureResult(gesture_name, 0.9, True, {
            "fingers": d["fingers"],
            "extended": d["extended"],
            "closed": d["closed"],
            "count_up": count,
            "x": d["x"], "y": d["y"],
            "px": d["px"], "py": d["py"],
        })

        # Stabilize
        state._history.append(gesture_name)
        if len(state._history) == GESTURE_HOLD_FRAMES:
            if all(g == gesture_name for g in state._history):
                state.gesture = best
        else:
            state.gesture = best

        # Smooth position
        state._position_buffer.append((d["x"], d["y"]))
        if state._position_buffer:
            avg_x = sum(p[0] for p in state._position_buffer) / len(state._position_buffer)
            avg_y = sum(p[1] for p in state._position_buffer) / len(state._position_buffer)
            h, w = frame_shape
            state.gesture.data["smooth_x"] = avg_x
            state.gesture.data["smooth_y"] = avg_y
            state.gesture.data["smooth_px"] = int(avg_x * w)
            state.gesture.data["smooth_py"] = int(avg_y * h)

        return state.gesture
