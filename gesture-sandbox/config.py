# ── Camera ──
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# ── Window layout ──
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
VIDEO_PANEL_WIDTH = 420
LOG_PANEL_WIDTH = 340
TEST_ZONE_WIDTH = 520  # remainder

# ── Colors (RGB) ──
BG_COLOR = (30, 30, 30)
PANEL_BG = (40, 40, 40)
TEXT_COLOR = (220, 220, 220)
ACCENT_COLOR = (0, 200, 150)
LANDMARK_COLOR = (0, 255, 128)
CONNECTION_COLOR = (0, 180, 100)
CURSOR_COLOR = (255, 80, 80)
GRAB_COLOR = (255, 180, 0)
PINCH_COLOR = (80, 200, 255)

# ── MediaPipe ──
MP_MAX_HANDS = 2
MP_DETECTION_CONFIDENCE = 0.7
MP_TRACKING_CONFIDENCE = 0.6

# ── Gesture thresholds ──
PINCH_ACTIVATE_DIST = 0.04      # normalized distance to trigger pinch
PINCH_DEACTIVATE_DIST = 0.06    # hysteresis: release threshold higher
SCROLL_MIN_VELOCITY = 0.005     # minimum y-delta per frame to count as scroll
ZOOM_SENSITIVITY = 2.0          # multiplier for zoom factor
GRAB_CURL_THRESHOLD = 0.15      # how curled fingers must be for grab

# ── Smoothing ──
SMOOTHING_FRAMES = 5            # number of frames to average for stability
GESTURE_HOLD_FRAMES = 3         # frames a gesture must persist to activate

# ── Gesture log ──
LOG_MAX_ENTRIES = 20

# ── FPS ──
FPS_UPDATE_INTERVAL = 0.5       # seconds between FPS display updates
