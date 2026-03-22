"""Right panel: live desktop mirror showing where the virtual cursor maps."""

import numpy as np
import pygame
import mss
from config import ACCENT_COLOR, CURSOR_COLOR, PINCH_COLOR, GRAB_COLOR, TEXT_COLOR
from core.input_driver import SCREEN_W, SCREEN_H


class DesktopPanel:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self._sct = mss.mss()
        self._monitor = self._sct.monitors[1]  # primary monitor
        # Capture every N frames to save CPU
        self._frame_skip = 6
        self._frame_count = 0
        self._cached_surface = None
        self._cursor_pos = (0, 0)
        self._cursor_style = "default"

    def update(self, gesture, screen_x, screen_y):
        """Update cursor position and style based on active gesture."""
        self._cursor_pos = (screen_x, screen_y)
        name = gesture.name
        if name == "R_CURSOR":
            self._cursor_style = "point"
        elif name == "R_DOUBLE_CLICK":
            self._cursor_style = "pinch"
        elif name == "R_CLICK":
            self._cursor_style = "grab"
        elif name == "R_SCROLL":
            self._cursor_style = "scroll"
        else:
            self._cursor_style = "default"

    def draw(self, surface):
        self._frame_count += 1

        # Capture desktop periodically
        if self._cached_surface is None or self._frame_count % self._frame_skip == 0:
            shot = self._sct.grab(self._monitor)
            img = np.array(shot)[:, :, :3]  # BGRA → BGR, drop alpha
            # Resize to fit panel
            scale = min(self.rect.width / SCREEN_W, self.rect.height / SCREEN_H)
            new_w = int(SCREEN_W * scale)
            new_h = int(SCREEN_H * scale)
            # Use numpy slicing for fast resize (nearest neighbor)
            import cv2
            small = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            # BGR → RGB
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            self._cached_surface = pygame.surfarray.make_surface(np.transpose(rgb, (1, 0, 2)))
            self._scale = scale
            self._offset = (
                self.rect.x + (self.rect.width - new_w) // 2,
                self.rect.y + (self.rect.height - new_h) // 2,
            )

        # Draw desktop thumbnail
        if self._cached_surface:
            surface.blit(self._cached_surface, self._offset)

        # Draw cursor indicator on the desktop thumbnail
        sx = self._offset[0] + int(self._cursor_pos[0] * self._scale)
        sy = self._offset[1] + int(self._cursor_pos[1] * self._scale)

        if self._cursor_style == "point":
            pygame.draw.circle(surface, CURSOR_COLOR, (sx, sy), 6)
            pygame.draw.circle(surface, (255, 255, 255), (sx, sy), 2)
        elif self._cursor_style == "pinch":
            pygame.draw.circle(surface, PINCH_COLOR, (sx, sy), 10, 3)
        elif self._cursor_style == "grab":
            pygame.draw.rect(surface, GRAB_COLOR, (sx - 6, sy - 6, 12, 12), 3)
        elif self._cursor_style == "scroll":
            pygame.draw.polygon(surface, TEXT_COLOR, [(sx, sy - 8), (sx - 5, sy), (sx + 5, sy)])
            pygame.draw.polygon(surface, TEXT_COLOR, [(sx, sy + 8), (sx - 5, sy), (sx + 5, sy)])
        else:
            pygame.draw.circle(surface, (150, 150, 150), (sx, sy), 4)

        # Border
        pygame.draw.rect(surface, (60, 60, 60), self.rect, 1)

        # Label
        font = pygame.font.SysFont("consolas", 14)
        label = font.render("─── Desktop Mirror ───", True, ACCENT_COLOR)
        surface.blit(label, (self.rect.x + 8, self.rect.y + 4))
