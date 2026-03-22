"""Scene manager — holds all objects, handles picking and manipulation."""

from OpenGL.GL import *
from OpenGL.GLU import *
from scene.objects import Cube, Sphere, Plane
from scene.grid import draw_grid


class Scene:
    def __init__(self):
        self.objects = []
        self.selected = None
        self._next_color_idx = 0
        self._palette = [
            [0.3, 0.6, 0.9, 0.9],   # blue
            [0.9, 0.4, 0.3, 0.9],   # red
            [0.3, 0.8, 0.5, 0.9],   # green
            [0.9, 0.7, 0.2, 0.9],   # yellow
            [0.7, 0.3, 0.8, 0.9],   # purple
            [0.2, 0.8, 0.8, 0.9],   # cyan
        ]

        # Start with a few demo objects
        self._add_demo_objects()

    def _next_color(self):
        c = self._palette[self._next_color_idx % len(self._palette)]
        self._next_color_idx += 1
        return list(c)

    def _add_demo_objects(self):
        c1 = Cube(pos=(-2, 0.5, 0))
        c1.color = self._next_color()
        self.objects.append(c1)

        s1 = Sphere(pos=(2, 0.5, 0))
        s1.color = self._next_color()
        self.objects.append(s1)

        p1 = Plane(pos=(0, 1.5, -2))
        p1.color = [0.95, 0.92, 0.8, 0.95]
        self.objects.append(p1)

    def add_cube(self, pos=(0, 0.5, 0)):
        c = Cube(pos=pos)
        c.color = self._next_color()
        self.objects.append(c)
        return c

    def add_sphere(self, pos=(0, 0.5, 0)):
        s = Sphere(pos=pos)
        s.color = self._next_color()
        self.objects.append(s)
        return s

    def add_plane(self, pos=(0, 1.5, 0)):
        p = Plane(pos=pos)
        self.objects.append(p)
        return p

    def delete_selected(self):
        if self.selected:
            self.objects.remove(self.selected)
            self.selected = None

    def select(self, obj):
        if self.selected:
            self.selected.selected = False
        self.selected = obj
        if obj:
            obj.selected = True

    def deselect(self):
        if self.selected:
            self.selected.selected = False
            self.selected = None

    def pick(self, mouse_x, mouse_y, viewport_w, viewport_h, camera):
        """Ray-cast pick: find object under mouse cursor."""
        # Get OpenGL matrices
        camera.apply()
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        viewport = glGetIntegerv(GL_VIEWPORT)

        # Flip Y for OpenGL coords
        wy = viewport[3] - mouse_y

        # Unproject near and far points
        near = gluUnProject(mouse_x, wy, 0.0, modelview, projection, viewport)
        far = gluUnProject(mouse_x, wy, 1.0, modelview, projection, viewport)

        # Ray direction
        dx = far[0] - near[0]
        dy = far[1] - near[1]
        dz = far[2] - near[2]
        length = (dx*dx + dy*dy + dz*dz) ** 0.5
        if length < 1e-8:
            return None
        dx /= length; dy /= length; dz /= length

        # Test each object (simple sphere bounding test)
        best_obj = None
        best_t = float('inf')

        for obj in self.objects:
            # Bounding sphere radius
            r = max(obj.scale) * 0.8
            # Vector from ray origin to object center
            ox = obj.pos[0] - near[0]
            oy = obj.pos[1] - near[1]
            oz = obj.pos[2] - near[2]
            # Project onto ray
            t = ox*dx + oy*dy + oz*dz
            if t < 0:
                continue
            # Distance from object center to ray
            cx = near[0] + t*dx - obj.pos[0]
            cy = near[1] + t*dy - obj.pos[1]
            cz = near[2] + t*dz - obj.pos[2]
            dist2 = cx*cx + cy*cy + cz*cz
            if dist2 < r*r and t < best_t:
                best_t = t
                best_obj = obj

        return best_obj

    def get_world_pos_on_grid(self, mouse_x, mouse_y, camera):
        """Get world position where mouse ray hits the y=0 grid plane."""
        camera.apply()
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        viewport = glGetIntegerv(GL_VIEWPORT)
        wy = viewport[3] - mouse_y
        near = gluUnProject(mouse_x, wy, 0.0, modelview, projection, viewport)
        far = gluUnProject(mouse_x, wy, 1.0, modelview, projection, viewport)

        # Intersect with y=0 plane
        dy = far[1] - near[1]
        if abs(dy) < 1e-8:
            return None
        t = -near[1] / dy
        if t < 0:
            return None
        x = near[0] + t * (far[0] - near[0])
        z = near[2] + t * (far[2] - near[2])
        return (x, 0.5, z)

    def draw(self):
        draw_grid()
        for obj in self.objects:
            obj.draw()
