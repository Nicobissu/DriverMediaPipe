"""Emotion Detector — facial expression analysis with MediaPipe."""

import sys
import os
import time
import cv2
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.camera import Camera
from core.full_tracker import FullTracker


# ─── Emotion definitions ───
# Each emotion has:
#   primary:   blendshapes that MUST be active (all must pass threshold)
#   secondary: blendshapes that boost the score
#   inhibit:   blendshapes that suppress this emotion
#   threshold: minimum primary signal to even consider this emotion
#   color, emoji: display

EMOTIONS = {
    "FELIZ": {
        "primary": {
            "mouthSmileLeft": 0.25,
            "mouthSmileRight": 0.25,
        },
        "secondary": {
            "cheekSquintLeft": 0.15,
            "cheekSquintRight": 0.15,
            "mouthDimpleLeft": 0.1,
            "mouthDimpleRight": 0.1,
        },
        "inhibit": {
            "mouthFrownLeft": 0.3,
            "mouthFrownRight": 0.3,
            "browDownLeft": 0.4,
            "browDownRight": 0.4,
        },
        "threshold": 0.15,
        "color": (0, 230, 150),
        "emoji": ":)",
    },
    "MUY FELIZ": {
        "primary": {
            "mouthSmileLeft": 0.5,
            "mouthSmileRight": 0.5,
            "cheekSquintLeft": 0.2,
            "cheekSquintRight": 0.2,
        },
        "secondary": {
            "jawOpen": 0.15,     # laughing
            "mouthDimpleLeft": 0.1,
            "mouthDimpleRight": 0.1,
        },
        "inhibit": {
            "mouthFrownLeft": 0.2,
            "browDownLeft": 0.3,
        },
        "threshold": 0.3,
        "color": (0, 255, 100),
        "emoji": "XD",
    },
    "TRISTE": {
        "primary": {
            "mouthFrownLeft": 0.15,
            "mouthFrownRight": 0.15,
        },
        "secondary": {
            "browInnerUp": 0.15,
            "mouthLowerDownLeft": 0.1,
            "mouthLowerDownRight": 0.1,
            "mouthPucker": 0.1,
            "mouthShrugLower": 0.1,
        },
        "inhibit": {
            "mouthSmileLeft": 0.3,
            "mouthSmileRight": 0.3,
        },
        "threshold": 0.1,
        "color": (230, 160, 50),
        "emoji": ":(",
    },
    "ENOJADO": {
        "primary": {
            "browDownLeft": 0.2,
            "browDownRight": 0.2,
        },
        "secondary": {
            "noseSneerLeft": 0.15,
            "noseSneerRight": 0.15,
            "jawForward": 0.1,
            "mouthShrugLower": 0.1,
            "eyeSquintLeft": 0.1,
            "eyeSquintRight": 0.1,
            "mouthPressLeft": 0.1,
            "mouthPressRight": 0.1,
        },
        "inhibit": {
            "mouthSmileLeft": 0.3,
            "mouthSmileRight": 0.3,
            "browInnerUp": 0.4,
        },
        "threshold": 0.15,
        "color": (30, 40, 255),
        "emoji": ">:(",
    },
    "SORPRENDIDO": {
        "primary": {
            "eyeWideLeft": 0.15,
            "eyeWideRight": 0.15,
            "jawOpen": 0.2,
        },
        "secondary": {
            "browInnerUp": 0.2,
            "browOuterUpLeft": 0.15,
            "browOuterUpRight": 0.15,
            "mouthFunnel": 0.1,
        },
        "inhibit": {
            "browDownLeft": 0.3,
            "browDownRight": 0.3,
            "eyeSquintLeft": 0.3,
        },
        "threshold": 0.12,
        "color": (0, 200, 255),
        "emoji": ":O",
    },
    "DISGUSTO": {
        "primary": {
            "noseSneerLeft": 0.2,
            "noseSneerRight": 0.2,
        },
        "secondary": {
            "mouthUpperUpLeft": 0.15,
            "mouthUpperUpRight": 0.15,
            "mouthShrugUpper": 0.15,
            "browDownLeft": 0.1,
        },
        "inhibit": {
            "mouthSmileLeft": 0.3,
            "mouthSmileRight": 0.3,
        },
        "threshold": 0.15,
        "color": (50, 200, 50),
        "emoji": "X(",
    },
    "CONCENTRADO": {
        "primary": {
            "eyeSquintLeft": 0.15,
            "eyeSquintRight": 0.15,
        },
        "secondary": {
            "browDownLeft": 0.1,
            "browDownRight": 0.1,
            "mouthPressLeft": 0.1,
            "mouthPressRight": 0.1,
        },
        "inhibit": {
            "mouthSmileLeft": 0.3,
            "jawOpen": 0.3,
            "eyeWideLeft": 0.2,
        },
        "threshold": 0.1,
        "color": (200, 180, 100),
        "emoji": "-_-",
    },
    "SKEPTICO": {
        "primary": {
            "browOuterUpLeft": 0.2,   # one brow up
        },
        "secondary": {
            "mouthLeft": 0.1,
            "mouthPressLeft": 0.1,
            "eyeSquintRight": 0.1,
        },
        "inhibit": {
            "browOuterUpRight": 0.25,  # both brows up = surprised, not skeptic
            "jawOpen": 0.3,
        },
        "threshold": 0.15,
        "color": (180, 140, 220),
        "emoji": "o_O",
    },
    "GUINO ;)": {
        "primary": {
            "eyeBlinkLeft": 0.4,
        },
        "secondary": {
            "mouthSmileLeft": 0.15,
            "mouthSmileRight": 0.15,
            "cheekSquintLeft": 0.15,
        },
        "inhibit": {
            "eyeBlinkRight": 0.35,  # both eyes closed = blink, not wink
        },
        "threshold": 0.3,
        "color": (255, 180, 50),
        "emoji": ";)",
    },
}


def detect_emotion(bs_map):
    """Score emotions from blendshape dict. Returns sorted list of (name, score)."""
    if not bs_map:
        return [("NEUTRAL", 1.0)]

    scores = {}

    for emotion, rule in EMOTIONS.items():
        # Check inhibitors first
        inhibited = False
        for bs_name, thresh in rule.get("inhibit", {}).items():
            if bs_map.get(bs_name, 0) > thresh:
                inhibited = True
                break
        if inhibited:
            scores[emotion] = 0.0
            continue

        # Primary signals — all must exceed their threshold
        primary_score = 0.0
        primary_count = 0
        all_primary_met = True
        for bs_name, min_val in rule["primary"].items():
            val = bs_map.get(bs_name, 0)
            if val < min_val * 0.5:  # at least half the threshold
                all_primary_met = False
                break
            # Score: how far above threshold (0 at threshold, 1 at 2x threshold)
            normalized = min(1.0, val / min_val) if min_val > 0 else 0
            primary_score += normalized
            primary_count += 1

        if not all_primary_met or primary_count == 0:
            scores[emotion] = 0.0
            continue

        primary_avg = primary_score / primary_count

        # Secondary signals — optional boosters
        secondary_score = 0.0
        secondary_count = 0
        for bs_name, min_val in rule.get("secondary", {}).items():
            val = bs_map.get(bs_name, 0)
            if val > min_val * 0.3:
                normalized = min(1.0, val / min_val)
                secondary_score += normalized
                secondary_count += 1

        secondary_avg = secondary_score / max(1, secondary_count)

        # Combined: primary is 70%, secondary is 30%
        raw = primary_avg * 0.7 + secondary_avg * 0.3

        # Apply threshold — below threshold fades to zero
        thresh = rule["threshold"]
        if primary_avg < thresh:
            raw *= 0.1

        # Non-linear: make strong signals stand out more
        final = min(1.0, raw * raw * 1.5)

        scores[emotion] = final

    # Neutral = inverse of strongest emotion
    max_score = max(scores.values()) if scores else 0
    scores["NEUTRAL"] = max(0.0, 1.0 - max_score * 2.0)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def draw_emotion_bars(frame, ranked, x, y_start, bar_w=200):
    """Draw emotion score bars."""
    for i, (emotion, score) in enumerate(ranked):
        if score < 0.005:
            continue
        rule = EMOTIONS.get(emotion, {"color": (180, 180, 180), "emoji": ":|"})
        color = rule["color"]
        emoji = rule.get("emoji", "")
        y = y_start + i * 30

        # Background bar
        cv2.rectangle(frame, (x, y), (x + bar_w, y + 22), (30, 30, 30), -1)
        # Score bar
        bw = int(score * bar_w)
        if bw > 0:
            cv2.rectangle(frame, (x, y), (x + bw, y + 22), color, -1)
        # Border
        cv2.rectangle(frame, (x, y), (x + bar_w, y + 22), (60, 60, 60), 1)
        # Label
        label = f"{emoji} {emotion} {score:.0%}"
        cv2.putText(frame, label, (x + 5, y + 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1)


def draw_face_oval(frame, face_landmarks, w, h, color, thickness=2):
    """Draw oval around face."""
    if not face_landmarks:
        return
    import numpy as np
    oval_idx = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
                397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
                172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
    pts = []
    for idx in oval_idx:
        if idx < len(face_landmarks):
            p = face_landmarks[idx]
            pts.append([int(p.x * w), int(p.y * h)])
    if len(pts) > 3:
        cv2.polylines(frame, [np.array(pts, np.int32)], True, color, thickness)


def main():
    cam = Camera()
    tracker = FullTracker()

    fps = 0
    fps_t = time.time()
    fps_c = 0

    # Smoothing
    smooth_scores = {}
    alpha = 0.3  # EMA factor: lower = smoother, higher = more responsive

    print("Emotion Detector — ESC to quit")
    cv2.namedWindow("Emotion Detector", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Emotion Detector", 960, 720)

    while True:
        ok, frame = cam.read()
        if not ok:
            continue

        result = tracker.process(frame)
        h, w = frame.shape[:2]

        # FPS
        fps_c += 1
        now = time.time()
        if now - fps_t >= 0.5:
            fps = fps_c / (now - fps_t)
            fps_c = 0
            fps_t = now

        # Build blendshape map
        bs_map = {}
        if result.face_blendshapes:
            bs_map = {bs.category_name: bs.score for bs in result.face_blendshapes}

        # Detect
        ranked = detect_emotion(bs_map)

        # EMA smoothing
        for emotion, score in ranked:
            prev = smooth_scores.get(emotion, 0.0)
            smooth_scores[emotion] = prev + alpha * (score - prev)

        smoothed = sorted(smooth_scores.items(), key=lambda x: x[1], reverse=True)

        # Top emotion
        top_emotion = "NEUTRAL"
        top_score = 0.0
        for emo, sc in smoothed:
            if emo != "NEUTRAL" and sc > top_score:
                top_emotion = emo
                top_score = sc
        # If no strong emotion, show neutral
        if top_score < 0.08:
            top_emotion = "NEUTRAL"
            top_score = smooth_scores.get("NEUTRAL", 1.0)

        top_rule = EMOTIONS.get(top_emotion, {"color": (180, 180, 180), "emoji": ":|"})

        # ── Draw ──

        # Face mesh (subtle dots)
        if result.face_landmarks:
            for p in result.face_landmarks:
                cx, cy = int(p.x * w), int(p.y * h)
                cv2.circle(frame, (cx, cy), 1, (80, 60, 100), -1)

        # Face oval colored by emotion
        thickness = 2 + int(top_score * 3)
        draw_face_oval(frame, result.face_landmarks, w, h, top_rule["color"], thickness)

        # Top emotion label (centered, top)
        emoji = top_rule.get("emoji", "")
        label = f"{emoji}  {top_emotion}"
        text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 1.3, 3)[0]
        tx = (w - text_size[0]) // 2
        # Shadow
        cv2.rectangle(frame, (tx - 15, 8), (tx + text_size[0] + 15, 58), (0, 0, 0), -1)
        cv2.rectangle(frame, (tx - 15, 8), (tx + text_size[0] + 15, 58), top_rule["color"], 2)
        cv2.putText(frame, label, (tx, 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.3, top_rule["color"], 3)

        # Confidence bar
        bar_total = 250
        bar_x = (w - bar_total) // 2
        bw = int(min(1.0, top_score) * bar_total)
        cv2.rectangle(frame, (bar_x, 62), (bar_x + bw, 72), top_rule["color"], -1)
        cv2.rectangle(frame, (bar_x, 62), (bar_x + bar_total, 72), (60, 60, 60), 1)

        # All emotion bars (right side)
        draw_emotion_bars(frame, smoothed, w - 240, 90)

        # FPS (top left)
        cv2.putText(frame, f"FPS: {fps:.0f}", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 120), 2)

        # Active blendshapes (bottom left)
        if bs_map:
            active = [(k, v) for k, v in bs_map.items() if v > 0.1 and k != "_neutral"]
            active.sort(key=lambda x: x[1], reverse=True)
            y_pos = h - 18 * min(len(active), 12) - 25
            cv2.putText(frame, "Blendshapes:", (10, y_pos - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (140, 140, 140), 1)
            for name, score in active[:12]:
                y_pos += 16
                bw2 = int(score * 100)
                cv2.rectangle(frame, (10, y_pos - 9), (10 + bw2, y_pos + 1), (60, 120, 170), -1)
                cv2.putText(frame, f"{name}: {score:.2f}", (12, y_pos),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.3, (210, 210, 210), 1)

        # No face warning
        if not result.face_landmarks:
            cv2.putText(frame, "No face detected", (w // 2 - 100, h // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        cv2.imshow("Emotion Detector", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cam.release()
    tracker.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nERROR: {e}")
        input("Press Enter to exit...")
