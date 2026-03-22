"""Windows input injection via ctypes — moves mouse, clicks, scrolls."""

import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

# --- Constants ---
INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_ABSOLUTE = 0x8000

SCREEN_W = user32.GetSystemMetrics(0)
SCREEN_H = user32.GetSystemMetrics(1)


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("_input", _INPUT),
    ]


def _send_input(inp):
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


class InputDriver:
    """Translates gestures into real Windows input events."""

    def __init__(self):
        self._left_down = False

    def move_mouse(self, x, y):
        """Move cursor to absolute screen position (x, y) in pixels."""
        x = max(0, min(SCREEN_W - 1, int(x)))
        y = max(0, min(SCREEN_H - 1, int(y)))
        # SetCursorPos is simpler and more reliable for absolute positioning
        user32.SetCursorPos(x, y)

    def click(self, x=None, y=None):
        """Left click at current position (or move first if x,y given)."""
        if x is not None and y is not None:
            self.move_mouse(x, y)
        # mouse_event is more compatible than SendInput across apps
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def double_click(self, x=None, y=None):
        """Double left click."""
        if x is not None and y is not None:
            self.move_mouse(x, y)
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def mouse_down(self):
        """Press left button down (for drag)."""
        if not self._left_down:
            inp = INPUT(type=INPUT_MOUSE)
            inp.mi.dwFlags = MOUSEEVENTF_LEFTDOWN
            _send_input(inp)
            self._left_down = True

    def mouse_up(self):
        """Release left button (end drag)."""
        if self._left_down:
            inp = INPUT(type=INPUT_MOUSE)
            inp.mi.dwFlags = MOUSEEVENTF_LEFTUP
            _send_input(inp)
            self._left_down = False

    def scroll(self, amount):
        """Scroll wheel. Positive = up, negative = down."""
        inp = INPUT(type=INPUT_MOUSE)
        inp.mi.dwFlags = MOUSEEVENTF_WHEEL
        inp.mi.mouseData = int(amount)
        _send_input(inp)

    # ── Window management ──

    SW_MINIMIZE = 6
    SW_RESTORE = 9

    def minimize_window(self):
        """Minimize the foreground window."""
        hwnd = user32.GetForegroundWindow()
        if hwnd:
            user32.ShowWindow(hwnd, self.SW_MINIMIZE)

    def close_window(self):
        """Close the foreground window (send WM_CLOSE)."""
        WM_CLOSE = 0x0010
        hwnd = user32.GetForegroundWindow()
        if hwnd:
            user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)

    def focus_window_at_cursor(self):
        """Click at the current cursor position to focus/select the window there."""
        self.click()

    def task_view(self):
        """Open Windows Task View (Win+Tab)."""
        import ctypes
        VK_LWIN = 0x5B
        VK_TAB = 0x09
        KEYEVENTF_KEYUP = 0x0002
        user32.keybd_event(VK_LWIN, 0, 0, 0)
        user32.keybd_event(VK_TAB, 0, 0, 0)
        user32.keybd_event(VK_TAB, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)
