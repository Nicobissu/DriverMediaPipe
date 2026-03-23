# Gesture Driver — Documentación Técnica

## Qué es

Un driver virtual que usa la webcam para detectar manos y convertir gestos en acciones del mouse y ventanas de Windows. No necesita hardware especial — solo una webcam.

## Stack tecnológico

| Tecnología | Para qué se usa | Versión |
|---|---|---|
| **Python 3.10+** | Lenguaje base | 3.10.8 |
| **MediaPipe** (Tasks API) | Detección de manos — 21 landmarks por mano | >=0.10.0 |
| **OpenCV** (cv2) | Captura de video, conversión de color, UI con `imshow` | >=4.8.0 |
| **ctypes / user32.dll** | Inyección de input en Windows (mouse, teclado, ventanas) | Built-in |
| **NumPy** | Cálculos matemáticos con landmarks | >=1.24.0 |
| **Pygame** | UI alternativa con paneles (sandbox mode) | >=2.5.0 |
| **mss** | Captura de pantalla para desktop mirror | >=10.0.0 |

## Arquitectura — Flujo de datos

```
┌─────────────────────────────────────────────┐
│  WEBCAM (640x480 @30fps, espejado)          │
│  core/camera.py — OpenCV + CAP_DSHOW        │
└──────────────────┬──────────────────────────┘
                   │ frame BGR
                   ▼
┌─────────────────────────────────────────────┐
│  HAND TRACKER                               │
│  core/hand_tracker.py — MediaPipe Tasks API │
│  • Detecta hasta 2 manos                    │
│  • 21 landmarks normalizados (0-1) por mano │
│  • Identifica mano derecha vs izquierda     │
│  • Corrige el espejado de MediaPipe         │
└──────────────────┬──────────────────────────┘
                   │ {right: landmarks, left: landmarks}
                   ▼
┌─────────────────────────────────────────────┐
│  GESTURE ENGINE                             │
│  core/gesture_engine.py                     │
│  • Analiza qué dedos están extendidos       │
│  • Clasifica gestos por combinación         │
│  • Suaviza posición (promedio 3 frames)     │
│  • Estabiliza gesto (hold 2 frames)         │
│  • Histéresis en pinch (evita flickering)   │
└──────┬───────────────────┬──────────────────┘
       │                   │
       ▼                   ▼
┌──────────────┐   ┌──────────────────┐
│ INPUT DRIVER │   │ UI (cv2.imshow)  │
│ ctypes       │   │ HUD con info de  │
│ • Mouse      │   │ gestos, dedos,   │
│ • Click      │   │ FPS, leyenda     │
│ • Scroll     │   └──────────────────┘
│ • Ventanas   │
│ • Task View  │
└──────────────┘
```

## Cómo se conectan los módulos

### 1. Camera → HandTracker

```python
# camera.py captura y espeja el frame
ok, frame = camera.read()  # frame BGR, flippeado horizontal

# hand_tracker.py lo convierte a RGB y lo pasa a MediaPipe
rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
result = self._landmarker.detect_for_video(mp_image, timestamp)
```

MediaPipe devuelve landmarks normalizados (0.0 a 1.0) relativos al frame. El tracker corrige la etiqueta de mano (MediaPipe etiqueta "Left" lo que para el usuario es la mano derecha, porque el frame está espejado).

### 2. HandTracker → GestureEngine

```python
hands, all_landmarks = tracker.process(frame)
# hands = {"right": [21 landmarks], "left": [21 landmarks]}

right_gesture, left_gesture = engine.update(hands, frame_shape)
```

El engine procesa cada mano independientemente con `_HandState`:
- **FingersGesture** determina qué dedos están extendidos/cerrados
- **Clasificación** mapea combinaciones de dedos a nombres de gestos
- **Smoothing** promedia las últimas 3 posiciones
- **Hold** requiere que el gesto se mantenga 2 frames consecutivos

### 3. GestureEngine → InputDriver

```python
# Mano derecha → control del cursor
if name == "R_CURSOR":
    sx, sy = self._map_to_screen(gesture)  # normalizado → píxeles
    self.input.move_mouse(sx, sy)           # ctypes → SetCursorPos

# Mano izquierda → comandos de ventana
if name == "L_MINIMIZE":
    self.input.minimize_window()  # ctypes → ShowWindow(hwnd, SW_MINIMIZE)
```

El mapeo de coordenadas:
1. Coordenada normalizada de MediaPipe (0-1)
2. Se recorta a la zona útil de la cámara (CAM_X_MIN..CAM_X_MAX)
3. Se remapea a resolución de pantalla (SCREEN_W × SCREEN_H)
4. Se aplica suavizado (lerp con factor `smooth`)

## Detección de dedos

```
Landmark indices por dedo:
   4 ← THUMB_TIP
   │
   3 ← THUMB_IP
   │
   2 ← THUMB_MCP        8 ← INDEX_TIP    12 ← MIDDLE_TIP
   │                     │                  │
   1 ← THUMB_CMC        7 ← INDEX_DIP     11 ← MIDDLE_DIP
                         │                  │
                         6 ← INDEX_PIP     10 ← MIDDLE_PIP
                         │                  │
                         5 ← INDEX_MCP      9 ← MIDDLE_MCP
                         │                  │
                         └───── 0 (WRIST) ──┘
```

**Criterio de extensión:**
- Dedos (index, middle, ring, pinky): `distancia(tip, wrist) > distancia(mcp, wrist) × 1.1`
- Pulgar: `|tip.x - wrist.x| > |ip.x - wrist.x|` (movimiento lateral)

**Detección de pinch:**
- Distancia mínima entre nodos del pulgar (TIP, IP) y nodos del índice (MCP, PIP, DIP, TIP)
- Histéresis: activa a 0.07, desactiva a 0.10 (evita flickering)

## Gestos y acciones

### Mano derecha (verde) — Control

| Gesto | Dedos | Acción |
|---|---|---|
| **R_CURSOR** | Índice + Medio extendidos | Mover cursor |
| **R_SCROLL** | Índice + Medio + Anular | Scroll (mover mano arriba/abajo) |
| **R_STANDBY** | Solo Índice | Pausa — cursor quieto |
| **R_CLICK** | Puño (todo cerrado) | Click izquierdo |
| **R_DOUBLE_CLICK** | Pulgar toca índice (pinch) | Doble click |
| **R_PALM** | Todos extendidos | Sin acción |

### Mano izquierda (naranja) — Ventanas

| Gesto | Dedos | Acción |
|---|---|---|
| **L_MINIMIZE** | Pulgar + Índice (pinch) | Minimizar ventana activa |
| **L_CLOSE** | Índice + Meñique juntos | Cerrar ventana (WM_CLOSE) |
| **L_SELECT** | Puño | Task View (Win+Tab) |
| **L_IDLE** | Palma abierta | Sin acción |

## Inyección de input en Windows

```python
# Mouse — SetCursorPos para posición absoluta
user32.SetCursorPos(x, y)

# Click — mouse_event para compatibilidad
user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

# Scroll — SendInput con MOUSEEVENTF_WHEEL
inp.mi.dwFlags = MOUSEEVENTF_WHEEL
inp.mi.mouseData = amount  # positivo=arriba, negativo=abajo

# Task View — keybd_event simula Win+Tab
user32.keybd_event(VK_LWIN, 0, 0, 0)
user32.keybd_event(VK_TAB, 0, 0, 0)
user32.keybd_event(VK_TAB, 0, KEYEVENTF_KEYUP, 0)
user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)

# Ventanas — ShowWindow, PostMessage
user32.ShowWindow(hwnd, SW_MINIMIZE)
user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
```

## Configuración clave (config.py)

```python
# Zona útil de la cámara (la mano no llega a 0.0 ni 1.0)
CAM_X_MIN = 0.15    # margen izquierdo
CAM_X_MAX = 0.85    # margen derecho
CAM_Y_MIN = 0.10    # margen superior
CAM_Y_MAX = 0.80    # margen inferior

# Suavizado
SMOOTHING_FRAMES = 3     # frames para promediar posición
GESTURE_HOLD_FRAMES = 2  # frames para confirmar gesto

# Pinch
PINCH_ACTIVATE_DIST = 0.07   # distancia para activar
PINCH_DEACTIVATE_DIST = 0.10 # distancia para desactivar (histéresis)
```

## Estructura de archivos

```
gesture-sandbox/
├── main.py                  # Entry point — loop principal con cv2
├── config.py                # Constantes configurables
├── requirements.txt         # Dependencias Python
├── hand_landmarker.task     # Modelo MediaPipe (manos)
├── pose_landmarker.task     # Modelo MediaPipe (pose corporal)
├── face_landmarker.task     # Modelo MediaPipe (cara)
├── core/
│   ├── camera.py            # Captura webcam (OpenCV + CAP_DSHOW)
│   ├── hand_tracker.py      # MediaPipe HandLandmarker wrapper
│   ├── gesture_engine.py    # Clasifica gestos por combinación de dedos
│   ├── input_driver.py      # Inyección de input Windows (ctypes)
│   └── full_tracker.py      # Tracker completo (pose+manos+cara)
├── gestures/
│   ├── base.py              # GestureResult dataclass + Gesture ABC
│   ├── fingers.py           # Detección individual de cada dedo
│   ├── pinch.py             # Pulgar + índice
│   ├── grab.py              # Puño cerrado
│   ├── palm.py              # Palma abierta
│   ├── point.py             # Solo índice extendido
│   ├── scroll.py            # Dos dedos vertical
│   └── zoom.py              # Dos manos, pinch-to-zoom
├── ui/
│   ├── sandbox_window.py    # Ventana Pygame (modo sandbox)
│   ├── video_panel.py       # Panel con feed de cámara
│   ├── gesture_log.py       # Log de gestos en tiempo real
│   ├── desktop_panel.py     # Mirror del escritorio
│   ├── status_panel.py      # Estado de manos y controles
│   └── test_zone.py         # Zona interactiva de prueba
├── utils/
│   ├── math_helpers.py      # distance_2d, midpoint, angle, lerp
│   └── fps_counter.py       # Contador de FPS
└── scene/
    └── ar_object.py         # Objetos 3D para modo AR (experimental)
```

## Cómo correr

```bash
cd gesture-sandbox
python main.py
```

Presionar **ESC** para salir.

## Requisitos

- Windows 10/11
- Python 3.10+
- Webcam
- `pip install -r requirements.txt`
