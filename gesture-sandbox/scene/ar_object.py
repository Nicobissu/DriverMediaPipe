"""AR objects that live in camera/screen space."""

from OpenGL.GL import *
from OpenGL.GLU import *
import math


class ARObject:
    """A 3D object positioned in screen-normalized coordinates (0-1)."""

    _id_counter = 0

    def __init__(self, shape="cube", x=0.5, y=0.5, size=0.06):
        ARObject._id_counter += 1
        self.id = ARObject._id_counter
        self.shape = shape          # "cube", "sphere", "pyramid"
        self.x = x                  # 0..1 in camera space
        self.y = y
        self.size = size            # relative to screen
        self.rot_y = 0.0            # rotation
        self.selected = False
        self.color = [0.3, 0.6, 0.9, 0.85]

    def draw(self, screen_w, screen_h):
        """Draw the object at its screen position using OpenGL."""
        # Convert normalized coords to pixel coords
        px = self.x * screen_w
        py = self.y * screen_h
        sz = self.size * min(screen_w, screen_h)

        glPushMatrix()
        glTranslatef(px, py, 0)
        glScalef(sz, sz, sz)
        self.rot_y += 0.5  # slow auto-rotate for 3D feel

        # Color
        if self.selected:
            glColor4f(min(1, self.color[0] + 0.3),
                      min(1, self.color[1] + 0.3),
                      min(1, self.color[2] + 0.3), 1.0)
        else:
            glColor4f(*self.color)

        if self.shape == "cube":
            self._draw_cube()
        elif self.shape == "sphere":
            self._draw_sphere()
        elif self.shape == "pyramid":
            self._draw_pyramid()

        # Selection ring
        if self.selected:
            glColor4f(1.0, 1.0, 0.3, 0.8)
            glLineWidth(2.0)
            glBegin(GL_LINE_LOOP)
            for i in range(32):
                a = i * 2 * math.pi / 32
                glVertex3f(math.cos(a) * 1.3, math.sin(a) * 1.3, 0)
            glEnd()
            glLineWidth(1.0)

        glPopMatrix()

    def contains(self, nx, ny, screen_w, screen_h):
        """Check if normalized point (nx, ny) is inside this object."""
        sz = self.size * min(screen_w, screen_h)
        px = self.x * screen_w
        py = self.y * screen_h
        tx = nx * screen_w
        ty = ny * screen_h
        return abs(tx - px) < sz and abs(ty - py) < sz

    def _draw_cube(self):
        glPushMatrix()
        glRotatef(self.rot_y, 0.3, 1, 0.1)

        glBegin(GL_QUADS)
        # Front
        glNormal3f(0, 0, 1)
        glVertex3f(-1, -1, 1); glVertex3f(1, -1, 1)
        glVertex3f(1, 1, 1); glVertex3f(-1, 1, 1)
        # Back
        glNormal3f(0, 0, -1)
        glVertex3f(-1, -1, -1); glVertex3f(-1, 1, -1)
        glVertex3f(1, 1, -1); glVertex3f(1, -1, -1)
        # Top
        glNormal3f(0, 1, 0)
        glVertex3f(-1, 1, -1); glVertex3f(-1, 1, 1)
        glVertex3f(1, 1, 1); glVertex3f(1, 1, -1)
        # Bottom
        glNormal3f(0, -1, 0)
        glVertex3f(-1, -1, -1); glVertex3f(1, -1, -1)
        glVertex3f(1, -1, 1); glVertex3f(-1, -1, 1)
        # Left
        glNormal3f(-1, 0, 0)
        glVertex3f(-1, -1, -1); glVertex3f(-1, -1, 1)
        glVertex3f(-1, 1, 1); glVertex3f(-1, 1, -1)
        # Right
        glNormal3f(1, 0, 0)
        glVertex3f(1, -1, -1); glVertex3f(1, 1, -1)
        glVertex3f(1, 1, 1); glVertex3f(1, -1, 1)
        glEnd()
        glPopMatrix()

    def _draw_sphere(self):
        glPushMatrix()
        glRotatef(self.rot_y, 0, 1, 0)
        quad = gluNewQuadric()
        gluQuadricNormals(quad, GLU_SMOOTH)
        gluSphere(quad, 1.0, 20, 14)
        gluDeleteQuadric(quad)
        glPopMatrix()

    def _draw_pyramid(self):
        glPushMatrix()
        glRotatef(self.rot_y, 0, 1, 0)
        glBegin(GL_TRIANGLES)
        # Front
        glNormal3f(0, 0.5, 1)
        glVertex3f(0, 1.2, 0); glVertex3f(-1, -0.8, 1); glVertex3f(1, -0.8, 1)
        # Right
        glNormal3f(1, 0.5, 0)
        glVertex3f(0, 1.2, 0); glVertex3f(1, -0.8, 1); glVertex3f(1, -0.8, -1)
        # Back
        glNormal3f(0, 0.5, -1)
        glVertex3f(0, 1.2, 0); glVertex3f(1, -0.8, -1); glVertex3f(-1, -0.8, -1)
        # Left
        glNormal3f(-1, 0.5, 0)
        glVertex3f(0, 1.2, 0); glVertex3f(-1, -0.8, -1); glVertex3f(-1, -0.8, 1)
        glEnd()
        # Base
        glBegin(GL_QUADS)
        glNormal3f(0, -1, 0)
        glVertex3f(-1, -0.8, 1); glVertex3f(-1, -0.8, -1)
        glVertex3f(1, -0.8, -1); glVertex3f(1, -0.8, 1)
        glEnd()
        glPopMatrix()
