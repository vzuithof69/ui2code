"""UI2Code Preview Overlay Module.

Overlay rendering for detected UI elements.
"""

import os
from typing import List, Optional, Any

try:
    from PySide6.QtWidgets import QLabel, QSizePolicy
    from PySide6.QtGui import QPixmap, QColor, QPen, QBrush, QPainter, QFont
    from PySide6.QtCore import Qt
    _QT_AVAILABLE = True
except ImportError:
    _QT_AVAILABLE = False
    QLabel = object  # type: ignore

from engine.models import UIElement


class OverlayRenderer:
    """Renders UI element overlays on images."""

    def __init__(self) -> None:
        """Initialize the overlay renderer."""
        self._type_colors = {
            'window': QColor(100, 100, 255),      # Blue
            'panel': QColor(100, 200, 100),       # Green
            'group': QColor(150, 200, 150),       # Light green
            'button': QColor(255, 100, 100),      # Red
            'label': QColor(255, 200, 100),       # Orange
            'input': QColor(200, 100, 255),       # Purple
            'checkbox': QColor(255, 100, 200),    # Pink
            'tab': QColor(100, 200, 255),         # Cyan
            'table_or_list': QColor(200, 200, 100),  # Yellow-green
            'image': QColor(200, 150, 100),       # Brown
            'separator': QColor(150, 150, 150),   # Gray
            'unknown': QColor(180, 180, 180),     # Light gray
        }

    def render_overlay(
        self,
        pixmap: QPixmap,
        elements: List[UIElement],
        selected_id: Optional[str] = None,
        zoom_factor: float = 1.0
    ) -> QPixmap:
        """Render overlay on pixmap.

        Args:
            pixmap: Base pixmap to draw on.
            elements: List of UI elements to draw.
            selected_id: ID of selected element to highlight.
            zoom_factor: Current zoom factor.

        Returns:
            Pixmap with overlay rendered.
        """
        if not _QT_AVAILABLE:
            return pixmap

        # Scale pixmap
        scaled_width = int(pixmap.width() * zoom_factor)
        scaled_height = int(pixmap.height() * zoom_factor)
        scaled_pixmap = pixmap.scaled(
            scaled_width, scaled_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        # Create overlay
        overlay = QPixmap(scaled_pixmap.size())
        overlay.fill(Qt.transparent)

        # Draw elements
        painter = QPainter(overlay)
        painter.setRenderHint(QPainter.Antialiasing)

        for elem in elements:
            self._draw_element(painter, elem, selected_id, zoom_factor)

        painter.end()

        # Composite
        result = QPixmap(scaled_pixmap)
        painter = QPainter(result)
        painter.drawPixmap(0, 0, overlay)
        painter.end()

        return result

    def _draw_element(
        self,
        painter: QPainter,
        elem: UIElement,
        selected_id: Optional[str],
        zoom_factor: float
    ) -> None:
        """Draw a single element.

        Args:
            painter: QPainter instance.
            elem: UI element to draw.
            selected_id: ID of selected element.
            zoom_factor: Current zoom factor.
        """
        # Calculate scaled coordinates
        x = int(elem.x * zoom_factor)
        y = int(elem.y * zoom_factor)
        w = int(elem.width * zoom_factor)
        h = int(elem.height * zoom_factor)

        # Determine color
        color = self._type_colors.get(elem.element_type, self._type_colors['unknown'])

        # Highlight selected
        if elem.id == selected_id:
            pen_width = 4
            pen_color = QColor(255, 255, 0)  # Yellow
        else:
            pen_width = 2
            pen_color = color

        # Draw rectangle
        pen = QPen(pen_color, pen_width)
        painter.setPen(pen)

        # Semi-transparent fill
        brush_color = QColor(color)
        brush_color.setAlpha(60)
        painter.setBrush(QBrush(brush_color))

        painter.drawRect(x, y, w, h)

        # Draw ID label for larger elements
        if w > 40 and h > 15:
            font = painter.font()
            font.setPointSize(8)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))
            label_bg = QColor(0, 0, 0, 180)
            painter.fillRect(x, y, min(80, w), 14, label_bg)
            painter.drawText(x + 2, y + 11, f"{elem.id[-4:]}")

    def get_type_color(self, element_type: str) -> QColor:
        """Get color for element type.

        Args:
            element_type: Type of element.

        Returns:
            QColor for the element type.
        """
        return self._type_colors.get(element_type, self._type_colors['unknown'])
