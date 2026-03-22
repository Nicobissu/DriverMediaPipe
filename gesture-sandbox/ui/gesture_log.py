import time
from collections import deque
import pygame
from config import LOG_MAX_ENTRIES, TEXT_COLOR, ACCENT_COLOR, PANEL_BG


# Finger display symbols
FINGER_LABELS = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
FINGER_KEYS = ["thumb", "index", "middle", "ring", "pinky"]


class GestureLog:
    """Center panel: finger state display + gesture log."""

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self._entries = deque(maxlen=LOG_MAX_ENTRIES)
        self._last_gesture = None

    def log(self, gesture_result):
        name = gesture_result.name
        if gesture_result.active and name != self._last_gesture:
            ts = time.strftime("%H:%M:%S")
            d = gesture_result.data
            count = d.get("count_up", "?")
            self._entries.appendleft(f"{ts}  {name:12s} [{count} up]")
            self._last_gesture = name
        elif not gesture_result.active:
            self._last_gesture = None

    def draw(self, surface, current_gesture):
        pygame.draw.rect(surface, PANEL_BG, self.rect)
        pygame.draw.rect(surface, (60, 60, 60), self.rect, 1)

        font = pygame.font.SysFont("consolas", 15)
        font_big = pygame.font.SysFont("consolas", 18, bold=True)
        x0 = self.rect.x + 10
        y = self.rect.y + 8

        # Header
        header = font.render("── Finger State ──", True, ACCENT_COLOR)
        surface.blit(header, (x0, y))
        y += 28

        # Finger indicators
        fingers = current_gesture.data.get("fingers", {})
        for key, label in zip(FINGER_KEYS, FINGER_LABELS):
            state = fingers.get(key, None)
            if state is True:
                icon = "UP"
                color = (0, 230, 120)
            elif state is False:
                icon = "--"
                color = (120, 60, 60)
            else:
                icon = "??"
                color = (80, 80, 80)
            line = font.render(f"  {label:7s}  {icon}", True, color)
            surface.blit(line, (x0, y))
            y += 22

        y += 10

        # Current gesture badge
        badge_color = ACCENT_COLOR if current_gesture.active else (100, 100, 100)
        gesture_label = font_big.render(f"> {current_gesture.name}", True, badge_color)
        surface.blit(gesture_label, (x0, y))
        y += 30

        # Separator
        pygame.draw.line(surface, (60, 60, 60), (x0, y), (self.rect.right - 10, y))
        y += 8

        # Log header
        log_header = font.render("── History ──", True, ACCENT_COLOR)
        surface.blit(log_header, (x0, y))
        y += 22

        # Log entries
        for entry in self._entries:
            if y + 18 > self.rect.y + self.rect.height:
                break
            line = font.render(entry, True, TEXT_COLOR)
            surface.blit(line, (x0, y))
            y += 18
