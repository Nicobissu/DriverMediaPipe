"""Right panel: shows current gesture status for both hands."""

import pygame
from config import ACCENT_COLOR, TEXT_COLOR, PANEL_BG


class StatusPanel:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self._font = None
        self._font_big = None

    def _ensure_fonts(self):
        if self._font is None:
            self._font = pygame.font.SysFont("consolas", 16)
            self._font_big = pygame.font.SysFont("consolas", 22, bold=True)

    def draw(self, surface, right_gesture, left_gesture):
        self._ensure_fonts()

        # Background
        pygame.draw.rect(surface, PANEL_BG, self.rect)
        pygame.draw.rect(surface, (60, 60, 60), self.rect, 1)

        y = self.rect.y + 10
        x = self.rect.x + 15

        # Title
        title = self._font.render("── Status ──", True, ACCENT_COLOR)
        surface.blit(title, (x, y))
        y += 30

        # Right hand
        rn = right_gesture.name if right_gesture.active else "---"
        color_r = (0, 255, 128)
        lbl = self._font.render("Right hand:", True, TEXT_COLOR)
        surface.blit(lbl, (x, y))
        y += 22
        val = self._font_big.render(f"  {rn}", True, color_r)
        surface.blit(val, (x, y))
        y += 35

        # Right hand fingers
        if right_gesture.active and "fingers" in right_gesture.data:
            for fname in ["thumb", "index", "middle", "ring", "pinky"]:
                state = right_gesture.data["fingers"].get(fname, False)
                icon = "UP" if state else "DN"
                c = (0, 200, 100) if state else (120, 120, 120)
                txt = self._font.render(f"  {fname:<8} {icon}", True, c)
                surface.blit(txt, (x, y))
                y += 20
        y += 15

        # Left hand
        ln = left_gesture.name if left_gesture.active else "---"
        color_l = (255, 150, 50)
        lbl2 = self._font.render("Left hand:", True, TEXT_COLOR)
        surface.blit(lbl2, (x, y))
        y += 22
        val2 = self._font_big.render(f"  {ln}", True, color_l)
        surface.blit(val2, (x, y))
        y += 35

        if left_gesture.active and "fingers" in left_gesture.data:
            for fname in ["thumb", "index", "middle", "ring", "pinky"]:
                state = left_gesture.data["fingers"].get(fname, False)
                icon = "UP" if state else "DN"
                c = (200, 150, 50) if state else (120, 120, 120)
                txt = self._font.render(f"  {fname:<8} {icon}", True, c)
                surface.blit(txt, (x, y))
                y += 20
        y += 20

        # Controls legend
        pygame.draw.line(surface, (60, 60, 60), (x, y), (x + self.rect.width - 30, y))
        y += 10
        legend_title = self._font.render("── Controls ──", True, ACCENT_COLOR)
        surface.blit(legend_title, (x, y))
        y += 25

        controls_r = [
            ("Idx+Mid", "Move cursor"),
            ("Idx+Mid+Ring", "Scroll"),
            ("Index only", "Standby"),
            ("Fist", "Click"),
            ("Thumb~Index", "Double click"),
        ]
        controls_l = [
            ("Thumb+Index", "Minimize"),
            ("Idx+Pinky", "Close"),
            ("Fist", "Select app"),
        ]

        lbl_r = self._font.render("RIGHT:", True, (0, 200, 100))
        surface.blit(lbl_r, (x, y))
        y += 20
        for gesture, action in controls_r:
            txt = self._font.render(f"  {gesture:<14} {action}", True, (180, 180, 180))
            surface.blit(txt, (x, y))
            y += 18

        y += 8
        lbl_l = self._font.render("LEFT:", True, (200, 150, 50))
        surface.blit(lbl_l, (x, y))
        y += 20
        for gesture, action in controls_l:
            txt = self._font.render(f"  {gesture:<14} {action}", True, (180, 180, 180))
            surface.blit(txt, (x, y))
            y += 18
