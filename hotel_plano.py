"""
Hotel Interactivo — Plano de Planta
Aplicación PySide6 con plano interactivo del hotel.
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
    QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem,
    QGraphicsEllipseItem, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect,
    QGraphicsProxyWidget
)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (
    QColor, QBrush, QPen, QFont, QPainter, QCursor
)


# ── Color palette ──────────────────────────────────────────────
class Palette:
    BG_DARK       = QColor("#1a1f2e")
    BG_SCENE      = QColor("#1e2538")

    # Building
    BUILDING_FILL   = QColor("#252d42")
    BUILDING_BORDER = QColor("#ffffff")

    # Guest rooms
    GUEST_ROOM    = QColor("#1c2940")
    GUEST_BORDER  = QColor("#2d4a6a")
    GUEST_HOVER   = QColor("#253755")

    # Utility rooms
    UTILITY_ROOM  = QColor("#2a2235")
    UTILITY_BORDER= QColor("#4a3a5c")
    UTILITY_HOVER = QColor("#352a45")

    # Corridor
    CORRIDOR      = QColor("#212940")
    CORRIDOR_BORDER = QColor("#2e3650")

    # Walls
    WALL          = QColor("#4a5568")

    # Interaction
    HIGHLIGHT     = QColor("#5b9bd5")
    HIGHLIGHT_GLOW= QColor(91, 155, 213, 80)

    # Text
    TEXT_PRIMARY   = QColor("#e2e8f0")
    TEXT_SECONDARY = QColor("#8899aa")
    TEXT_DIM       = QColor("#5a6a7a")

    # Panel
    PANEL_BG      = QColor("#1a1f2e")
    PANEL_BORDER  = QColor("#2d3548")

    # Status
    STATUS_GREEN  = QColor("#48bb78")
    STATUS_ORANGE = QColor("#ed8936")

    # Accents
    ACCENT_CYAN   = QColor("#63b3ed")
    ACCENT_GREEN  = QColor("#48bb78")
    ACCENT_PURPLE = QColor("#9f7aea")
    ACCENT_ORANGE = QColor("#ed8936")

    # Card label
    CARD_TEXT      = QColor("#2d3748")
    CARD_SUBTEXT   = QColor("#718096")

    # Furniture
    BED_COLOR     = QColor("#3a4a5e")
    BED_BORDER    = QColor("#4a5a6e")


# ── Dimensions ─────────────────────────────────────────────────
SCALE = 55

# Room dimensions
ROOM_W = 3.5
ROOM_H = 3.8
ROOM_GAP = 0.3

# Layout: 5 rooms top, 5 rooms bottom, corridor in the middle
NUM_ROOMS_PER_ROW = 5
TOTAL_ROOMS_W = NUM_ROOMS_PER_ROW * ROOM_W + (NUM_ROOMS_PER_ROW - 1) * ROOM_GAP
MARGIN_X = 0.6  # margin inside building walls
CORRIDOR_H = 2.0

# Building dimensions derived from rooms
BUILDING_W = TOTAL_ROOMS_W + 2 * MARGIN_X
BUILDING_H = ROOM_H + CORRIDOR_H + ROOM_H + 2 * 0.4  # top rooms + corridor + bottom rooms + margins

TOP_ROOM_Y = 0.4
CORRIDOR_Y = TOP_ROOM_Y + ROOM_H
BOT_ROOM_Y = CORRIDOR_Y + CORRIDOR_H
ROW_X_START = MARGIN_X


# ── Room data ─────────────────────────────────────────────────
def build_rooms():
    rooms = []

    # Top row: Hab 01..05
    for i in range(5):
        x = ROW_X_START + i * (ROOM_W + ROOM_GAP)
        room_num = i + 1
        if room_num == 2:
            rtype = "Almacén"
            color = Palette.UTILITY_ROOM
            border = Palette.UTILITY_BORDER
            hover = Palette.UTILITY_HOVER
            status = "internal"
        elif room_num == 4:
            rtype = "Termotanque"
            color = Palette.UTILITY_ROOM
            border = Palette.UTILITY_BORDER
            hover = Palette.UTILITY_HOVER
            status = "internal"
        else:
            rtype = "Huéspedes"
            color = Palette.GUEST_ROOM
            border = Palette.GUEST_BORDER
            hover = Palette.GUEST_HOVER
            status = "available"
        rooms.append({
            "name": f"Habitación {room_num:02d}",
            "short": f"Hab {room_num:02d}",
            "type": rtype,
            "status": status,
            "rect": QRectF(x * SCALE, TOP_ROOM_Y * SCALE, ROOM_W * SCALE, ROOM_H * SCALE),
            "color": color,
            "border": border,
            "hover": hover,
            "row": "top",
        })

    # Bottom row: Hab 06..10
    for i in range(5):
        x = ROW_X_START + i * (ROOM_W + ROOM_GAP)
        room_num = i + 6
        rooms.append({
            "name": f"Habitación {room_num:02d}",
            "short": f"Hab {room_num:02d}",
            "type": "Huéspedes",
            "status": "available",
            "rect": QRectF(x * SCALE, BOT_ROOM_Y * SCALE, ROOM_W * SCALE, ROOM_H * SCALE),
            "color": Palette.GUEST_ROOM,
            "border": Palette.GUEST_BORDER,
            "hover": Palette.GUEST_HOVER,
            "row": "bottom",
        })

    return rooms


# ── Floating card label ────────────────────────────────────────
class RoomCardLabel(QGraphicsProxyWidget):
    """White rounded card that floats over each room."""

    def __init__(self, room_data, parent_item):
        super().__init__(parent_item)
        self.setAcceptedMouseButtons(Qt.NoButton)
        self.setAcceptHoverEvents(False)

        card = QFrame()
        card.setFixedSize(150, 64)

        status = room_data.get("status", "available")
        if status == "available":
            dot_color = Palette.STATUS_GREEN.name()
            border_left = Palette.STATUS_GREEN.name()
        else:
            dot_color = Palette.STATUS_ORANGE.name()
            border_left = Palette.STATUS_ORANGE.name()

        card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 235);
                border-radius: 10px;
                border-left: 4px solid {border_left};
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 6, 8, 6)
        layout.setSpacing(2)

        # Title row with dot
        title_row = QHBoxLayout()
        title_row.setSpacing(6)

        name_lbl = QLabel(room_data["name"])
        name_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        name_lbl.setStyleSheet(f"color: {Palette.CARD_TEXT.name()}; background: transparent; border: none;")
        title_row.addWidget(name_lbl)
        title_row.addStretch()

        dot = QLabel("●")
        dot.setFont(QFont("Segoe UI", 10))
        dot.setStyleSheet(f"color: {dot_color}; background: transparent; border: none;")
        dot.setFixedSize(16, 16)
        title_row.addWidget(dot)

        layout.addLayout(title_row)

        # Type
        type_lbl = QLabel(room_data["type"])
        type_lbl.setFont(QFont("Segoe UI", 8))
        type_lbl.setStyleSheet(f"color: {Palette.CARD_SUBTEXT.name()}; background: transparent; border: none;")
        layout.addWidget(type_lbl)

        self.setWidget(card)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(2, 3)
        card.setGraphicsEffect(shadow)


# ── Interactive room item ──────────────────────────────────────
class RoomItem(QGraphicsRectItem):
    def __init__(self, room_data, info_panel, scene):
        r = room_data["rect"]
        super().__init__(0, 0, r.width(), r.height())
        self.setPos(r.x(), r.y())
        self.data = room_data
        self.info_panel = info_panel
        self._scene = scene

        self.base_color = room_data["color"]
        self.border_color = room_data["border"]
        self.hover_color = room_data["hover"]
        self._selected = False

        self.setBrush(QBrush(self.base_color))
        self.setPen(QPen(self.border_color, 1.5))
        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setZValue(1)

        # Furniture
        if room_data["type"] == "Huéspedes":
            self._draw_beds(r.width(), r.height())
        elif room_data["type"] == "Almacén":
            self._draw_storage(r.width(), r.height())
        elif room_data["type"] == "Termotanque":
            self._draw_heater(r.width(), r.height())

        # Floating card
        card = RoomCardLabel(room_data, self)
        card_w = 150
        card_h = 64
        cx = (r.width() - card_w) / 2
        cy = (r.height() - card_h) / 2
        card.setPos(cx, cy)
        card.setZValue(20)

    def _draw_beds(self, w, h):
        bed_w = w * 0.28
        bed_h = h * 0.22
        y_off = h * 0.70

        bed1 = QGraphicsRectItem(w * 0.12, y_off, bed_w, bed_h, self)
        bed1.setBrush(QBrush(Palette.BED_COLOR))
        bed1.setPen(QPen(Palette.BED_BORDER, 1))
        bed1.setOpacity(0.6)

        bed2 = QGraphicsRectItem(w * 0.60, y_off, bed_w, bed_h, self)
        bed2.setBrush(QBrush(Palette.BED_COLOR))
        bed2.setPen(QPen(Palette.BED_BORDER, 1))
        bed2.setOpacity(0.6)

    def _draw_storage(self, w, h):
        shelf_c = QColor("#3a3050")
        shelf_b = QColor("#4a4060")
        for i in range(3):
            sy = h * (0.60 + i * 0.10)
            shelf = QGraphicsRectItem(w * 0.1, sy, w * 0.8, h * 0.06, self)
            shelf.setBrush(QBrush(shelf_c))
            shelf.setPen(QPen(shelf_b, 1))
            shelf.setOpacity(0.5)

    def _draw_heater(self, w, h):
        tank = QGraphicsEllipseItem(w * 0.25, h * 0.60, w * 0.5, w * 0.45, self)
        tank.setBrush(QBrush(QColor("#3a3050")))
        tank.setPen(QPen(QColor("#5a4a70"), 1.5))
        tank.setOpacity(0.6)

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(self.hover_color))
        self.setPen(QPen(Palette.HIGHLIGHT, 2.5))
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(30)
        glow.setColor(Palette.HIGHLIGHT_GLOW)
        glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)
        self.setZValue(10)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if not self._selected:
            self.setBrush(QBrush(self.base_color))
            self.setPen(QPen(self.border_color, 1.5))
        else:
            self.setPen(QPen(Palette.HIGHLIGHT, 2.5))
            self.setBrush(QBrush(self.hover_color))
        self.setGraphicsEffect(None)
        self.setZValue(1)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        for item in self._scene.items():
            if isinstance(item, RoomItem) and item is not self:
                item._selected = False
                item.setBrush(QBrush(item.base_color))
                item.setPen(QPen(item.border_color, 1.5))
        self._selected = True
        self.setBrush(QBrush(self.hover_color))
        self.setPen(QPen(Palette.HIGHLIGHT, 2.5))
        self.info_panel.show_room(self.data)
        super().mousePressEvent(event)


# ── Info Panel (no legend) ─────────────────────────────────────
class InfoPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(280)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Palette.PANEL_BG.name()};
                border-left: 2px solid {Palette.PANEL_BORDER.name()};
            }}
            QLabel {{
                color: {Palette.TEXT_PRIMARY.name()};
                padding: 2px 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(8)

        # Header
        self.header = QLabel("🏨 Hotel Interactivo")
        self.header.setFont(QFont("Segoe UI", 15, QFont.Bold))
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setStyleSheet(f"color: {Palette.ACCENT_CYAN.name()};")
        layout.addWidget(self.header)

        # Status pills
        status_row = QHBoxLayout()
        status_row.setSpacing(6)
        status_row.addStretch()
        for text, color in [("Disponibles", Palette.STATUS_GREEN),
                            ("Ocupadas", Palette.STATUS_ORANGE),
                            ("Interno", Palette.ACCENT_PURPLE)]:
            pill = QLabel(text)
            pill.setFont(QFont("Segoe UI", 7, QFont.Bold))
            pill.setAlignment(Qt.AlignCenter)
            pill.setFixedHeight(20)
            pill.setStyleSheet(f"""
                background-color: {color.name()};
                color: white;
                border-radius: 8px;
                padding: 2px 8px;
                border: none;
            """)
            status_row.addWidget(pill)
        status_row.addStretch()
        status_container = QWidget()
        status_container.setLayout(status_row)
        layout.addWidget(status_container)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background-color: {Palette.PANEL_BORDER.name()}; max-height: 1px; margin: 4px 16px;")
        layout.addWidget(sep)

        # Instruction
        self.instruction = QLabel("Haz clic en una habitación\npara ver sus detalles")
        self.instruction.setFont(QFont("Segoe UI", 10))
        self.instruction.setAlignment(Qt.AlignCenter)
        self.instruction.setStyleSheet(f"color: {Palette.TEXT_SECONDARY.name()};")
        layout.addWidget(self.instruction)

        # Room icon
        self.room_icon = QLabel("")
        self.room_icon.setFont(QFont("Segoe UI", 42))
        self.room_icon.setAlignment(Qt.AlignCenter)
        self.room_icon.hide()
        layout.addWidget(self.room_icon)

        # Room name
        self.room_name = QLabel("")
        self.room_name.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.room_name.setAlignment(Qt.AlignCenter)
        self.room_name.hide()
        layout.addWidget(self.room_name)

        # Room type
        self.room_type = QLabel("")
        self.room_type.setFont(QFont("Segoe UI", 12))
        self.room_type.setAlignment(Qt.AlignCenter)
        self.room_type.hide()
        layout.addWidget(self.room_type)

        # Separator 2
        self.sep2 = QFrame()
        self.sep2.setFrameShape(QFrame.HLine)
        self.sep2.setStyleSheet(f"background-color: {Palette.PANEL_BORDER.name()}; max-height: 1px; margin: 8px 16px;")
        self.sep2.hide()
        layout.addWidget(self.sep2)

        # Status
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Segoe UI", 11))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.hide()
        layout.addWidget(self.status_label)

        # Spacer (no legend below)
        layout.addStretch()

    def show_room(self, data):
        self.instruction.hide()
        self.room_icon.show()
        self.room_name.show()
        self.room_type.show()
        self.sep2.show()
        self.status_label.show()

        rtype = data["type"]
        if rtype == "Huéspedes":
            icon = "🛏️"
            color = Palette.ACCENT_GREEN.name()
            status = "🟢  Disponible"
        elif rtype == "Almacén":
            icon = "📦"
            color = Palette.ACCENT_PURPLE.name()
            status = "📦  Uso interno"
        else:
            icon = "🔥"
            color = Palette.ACCENT_ORANGE.name()
            status = "🔧  Uso interno"

        self.room_icon.setText(icon)
        self.room_name.setText(data["name"])
        self.room_type.setText(rtype)
        self.room_type.setStyleSheet(f"color: {color}; padding: 2px 12px;")
        self.status_label.setText(status)
        self.status_label.setStyleSheet(f"color: {Palette.TEXT_SECONDARY.name()}; padding: 2px 12px;")


# ── Graphics View ──────────────────────────────────────────────
class FloorPlanView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setStyleSheet(f"background-color: {Palette.BG_SCENE.name()}; border: none;")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._zoom = 0

    def wheelEvent(self, event):
        factor = 1.15
        if event.angleDelta().y() > 0:
            if self._zoom < 10:
                self.scale(factor, factor)
                self._zoom += 1
        else:
            if self._zoom > -5:
                self.scale(1 / factor, 1 / factor)
                self._zoom -= 1

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._zoom == 0:
            self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)


# ── Main Window ────────────────────────────────────────────────
class HotelFloorPlan(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🏨 Hotel Interactivo — Plano de Planta")
        self.setMinimumSize(1200, 700)
        self.setStyleSheet(f"background-color: {Palette.BG_DARK.name()};")

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QBrush(Palette.BG_SCENE))

        self.info_panel = InfoPanel()
        self._build_floor_plan()

        self.view = FloorPlanView(self.scene)
        main_layout.addWidget(self.view, 1)
        main_layout.addWidget(self.info_panel)

        margin = 60
        sr = self.scene.itemsBoundingRect().adjusted(-margin, -margin, margin, margin)
        self.scene.setSceneRect(sr)

    def _build_floor_plan(self):
        S = SCALE

        # ── Building outline — thick white border ──
        building_rect = QGraphicsRectItem(0, 0, BUILDING_W * S, BUILDING_H * S)
        building_rect.setPen(QPen(Palette.BUILDING_BORDER, 5))
        building_rect.setBrush(QBrush(Palette.BUILDING_FILL))
        self.scene.addItem(building_rect)

        # Outer glow
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(50)
        glow.setColor(QColor(255, 255, 255, 30))
        glow.setOffset(0, 0)
        building_rect.setGraphicsEffect(glow)

        # ── Corridor ──
        corridor = QGraphicsRectItem(0, CORRIDOR_Y * S,
                                     BUILDING_W * S, CORRIDOR_H * S)
        corridor.setBrush(QBrush(Palette.CORRIDOR))
        corridor.setPen(QPen(Palette.CORRIDOR_BORDER, 1))
        self.scene.addItem(corridor)

        corr_label = QGraphicsTextItem("Corredor / Pasillo")
        corr_label.setDefaultTextColor(Palette.TEXT_DIM)
        corr_label.setFont(QFont("Segoe UI", 8))
        clbr = corr_label.boundingRect()
        corr_label.setPos((BUILDING_W * S - clbr.width()) / 2,
                          CORRIDOR_Y * S + (CORRIDOR_H * S - clbr.height()) / 2)
        self.scene.addItem(corr_label)

        # ── Rooms ──
        rooms = build_rooms()
        for room in rooms:
            item = RoomItem(room, self.info_panel, self.scene)
            self.scene.addItem(item)

        # ── Corridor wall lines ──
        wall_pen = QPen(Palette.WALL, 1)
        self.scene.addLine(0, CORRIDOR_Y * S,
                           BUILDING_W * S, CORRIDOR_Y * S, wall_pen)
        self.scene.addLine(0, (CORRIDOR_Y + CORRIDOR_H) * S,
                           BUILDING_W * S, (CORRIDOR_Y + CORRIDOR_H) * S, wall_pen)

        # Vertical separators between rooms
        for i in range(1, NUM_ROOMS_PER_ROW):
            x = (ROW_X_START + i * (ROOM_W + ROOM_GAP) - ROOM_GAP / 2) * S
            # Top row
            self.scene.addLine(x, TOP_ROOM_Y * S, x, (TOP_ROOM_Y + ROOM_H) * S,
                               QPen(Palette.WALL, 0.5))
            # Bottom row
            self.scene.addLine(x, BOT_ROOM_Y * S, x, (BOT_ROOM_Y + ROOM_H) * S,
                               QPen(Palette.WALL, 0.5))


# ── Entry point ────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = HotelFloorPlan()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
