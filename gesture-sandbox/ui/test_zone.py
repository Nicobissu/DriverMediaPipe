import pygame
from config import (
    PANEL_BG, CURSOR_COLOR, GRAB_COLOR, PINCH_COLOR,
    ACCENT_COLOR, TEXT_COLOR,
)


class TestZone:
    """Right panel: interactive area to test gestures with a virtual cursor."""

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)

        # Draggable box
        self.box = pygame.Rect(x + 60, y + 80, 80, 80)
        self._dragging = False
        self._drag_offset = (0, 0)

        # Zoomable image (just a colored rect for now)
        self._zoom_level = 1.0
        self._zoom_center = (x + width // 2, y + 300)

        # Scrollable text
        self._scroll_offset = 0
        self._scroll_lines = [f"Line {i}: Sample scrollable text content" for i in range(1, 41)]

        # Cursor state
        self.cursor_pos = (0, 0)
        self.cursor_style = "default"

    def update(self, gesture):
        """React to the current gesture."""
        d = gesture.data

        # Map cursor position into panel-local coords
        if "smooth_px" in d:
            # Remap from camera space (0..1 normalized) to panel space
            cx = self.rect.x + int(d.get("smooth_x", 0) * self.rect.width)
            cy = self.rect.y + int(d.get("smooth_y", 0) * self.rect.height)
            self.cursor_pos = (cx, cy)
        elif "px" in d:
            cx = self.rect.x + int(d.get("x", 0) * self.rect.width)
            cy = self.rect.y + int(d.get("y", 0) * self.rect.height)
            self.cursor_pos = (cx, cy)

        name = gesture.name

        if name == "GRAB":
            self.cursor_style = "grab"
            if self.box.collidepoint(self.cursor_pos):
                if not self._dragging:
                    self._dragging = True
                    self._drag_offset = (
                        self.cursor_pos[0] - self.box.x,
                        self.cursor_pos[1] - self.box.y,
                    )
            if self._dragging:
                self.box.x = self.cursor_pos[0] - self._drag_offset[0]
                self.box.y = self.cursor_pos[1] - self._drag_offset[1]
                # Clamp inside panel
                self.box.clamp_ip(self.rect)
        else:
            self._dragging = False

        if name == "PINCH":
            self.cursor_style = "pinch"
        elif name == "POINT":
            self.cursor_style = "point"
        elif name == "ZOOM" and "factor" in d:
            self.cursor_style = "zoom"
            self._zoom_level = max(0.3, min(3.0, 1.0 + d["factor"]))
        elif name == "SCROLL" and "velocity" in d:
            self.cursor_style = "scroll"
            self._scroll_offset += int(d["velocity"] * 800)
            max_scroll = max(0, len(self._scroll_lines) * 18 - 150)
            self._scroll_offset = max(0, min(max_scroll, self._scroll_offset))
        elif name == "PALM":
            self.cursor_style = "palm"
        elif name == "IDLE":
            self.cursor_style = "default"

    def draw(self, surface):
        pygame.draw.rect(surface, PANEL_BG, self.rect)
        pygame.draw.rect(surface, (60, 60, 60), self.rect, 1)

        font = pygame.font.SysFont("consolas", 14)

        # Header
        header = font.render("─── Test Zone ───", True, ACCENT_COLOR)
        surface.blit(header, (self.rect.x + 10, self.rect.y + 8))

        # ── Draggable box ──
        box_color = GRAB_COLOR if self._dragging else (80, 80, 180)
        pygame.draw.rect(surface, box_color, self.box)
        label = font.render("DRAG ME", True, (255, 255, 255))
        surface.blit(label, (self.box.x + 6, self.box.y + 32))

        # ── Zoomable area ──
        zoom_rect = pygame.Rect(
            self.rect.x + 180, self.rect.y + 60,
            int(100 * self._zoom_level), int(100 * self._zoom_level),
        )
        zoom_rect.clamp_ip(self.rect)
        pygame.draw.rect(surface, (60, 120, 180), zoom_rect)
        zt = font.render(f"ZOOM {self._zoom_level:.1f}x", True, (255, 255, 255))
        surface.blit(zt, (zoom_rect.x + 4, zoom_rect.y + 4))

        # ── Scrollable text area ──
        scroll_area = pygame.Rect(self.rect.x + 10, self.rect.y + 200, self.rect.width - 20, 160)
        pygame.draw.rect(surface, (35, 35, 35), scroll_area)
        # Clip
        clip_prev = surface.get_clip()
        surface.set_clip(scroll_area)
        y = scroll_area.y - self._scroll_offset
        for line_text in self._scroll_lines:
            if y + 18 > scroll_area.y - 18 and y < scroll_area.bottom:
                lt = font.render(line_text, True, TEXT_COLOR)
                surface.blit(lt, (scroll_area.x + 4, y))
            y += 18
        surface.set_clip(clip_prev)
        # Scroll indicator
        if len(self._scroll_lines) * 18 > scroll_area.height:
            bar_h = max(20, scroll_area.height * scroll_area.height // (len(self._scroll_lines) * 18))
            max_scroll = len(self._scroll_lines) * 18 - scroll_area.height
            bar_y = scroll_area.y + int((scroll_area.height - bar_h) * self._scroll_offset / max(1, max_scroll))
            pygame.draw.rect(surface, (80, 80, 80), (scroll_area.right - 6, bar_y, 4, bar_h))

        # ── Cursor ──
        cx, cy = self.cursor_pos
        if self.rect.collidepoint(cx, cy):
            if self.cursor_style == "point":
                pygame.draw.circle(surface, CURSOR_COLOR, (cx, cy), 8)
                pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 3)
            elif self.cursor_style == "pinch":
                pygame.draw.circle(surface, PINCH_COLOR, (cx, cy), 12, 3)
                pygame.draw.line(surface, PINCH_COLOR, (cx - 6, cy), (cx + 6, cy), 2)
                pygame.draw.line(surface, PINCH_COLOR, (cx, cy - 6), (cx, cy + 6), 2)
            elif self.cursor_style == "grab":
                pygame.draw.rect(surface, GRAB_COLOR, (cx - 8, cy - 8, 16, 16), 3)
            elif self.cursor_style == "zoom":
                pygame.draw.circle(surface, ACCENT_COLOR, (cx, cy), 14, 2)
                pygame.draw.circle(surface, ACCENT_COLOR, (cx, cy), 6, 2)
            elif self.cursor_style == "scroll":
                pygame.draw.polygon(surface, TEXT_COLOR, [(cx, cy - 10), (cx - 6, cy), (cx + 6, cy)])
                pygame.draw.polygon(surface, TEXT_COLOR, [(cx, cy + 10), (cx - 6, cy), (cx + 6, cy)])
            elif self.cursor_style == "palm":
                pygame.draw.circle(surface, (100, 100, 100), (cx, cy), 16, 2)
            else:
                pygame.draw.circle(surface, (150, 150, 150), (cx, cy), 5)
