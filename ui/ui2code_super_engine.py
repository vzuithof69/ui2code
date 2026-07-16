"""UI2Code Super Engine.

Main UI interface for the UI2Code conversion system.
"""

import sys
import os
from typing import Optional, Dict, Any, List

# Import logging first
from tools.ui2code_logging import initialize_logging, get_logger

# Initialize logging at module load
_logger = None

# Import engine classes first (no Qt dependency)
from engine.ui2code_core import UI2CodeCore
from engine.ui2code_detect import UI2CodeDetect
from engine.ui2code_detect_v2 import UI2CodeDetect as UI2CodeDetectV2
from engine.ui2code_layout import UI2CodeLayout
from engine.ui2code_export import UI2CodeExport
from engine.models import UIElement

# Try to import Qt - will fail in environments without Qt libraries
try:
    from PySide6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
        QPushButton, QLabel, QFileDialog, QScrollArea,
        QGroupBox, QFormLayout, QLineEdit, QSlider, QTabWidget,
        QListWidget, QTableWidget, QTableWidgetItem, QAbstractItemView,
        QSizePolicy, QMessageBox, QApplication, QHeaderView
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QPixmap, QColor, QBrush, QPainter
    _QT_AVAILABLE = True
except ImportError:
    _QT_AVAILABLE = False
    # Define stubs for when Qt is not available
    QMainWindow = object  # type: ignore
    QWidget = object  # type: ignore
    QGroupBox = object  # type: ignore
    QScrollArea = object  # type: ignore

# Import overlay renderer (requires Qt)
if _QT_AVAILABLE:
    from ui.preview_overlay import OverlayRenderer


if _QT_AVAILABLE:
    from PySide6.QtCore import Signal
    
    class ElementEditor(QGroupBox):
        """Element editor panel for editing UI element properties."""
        
        # Signal emitted when element data changes: (element, field_name, old_value, new_value)
        element_changed = Signal(object, str, object, object)

        def __init__(self, parent: Optional[QWidget] = None) -> None:
            """Initialize the element editor.

            Args:
                parent: Parent widget.
            """
            super().__init__("Element Editor", parent)
            self._current_element: Optional[UIElement] = None
            self._setup_ui()
            self._setup_connections()

        def _setup_ui(self) -> None:
            """Set up the element editor UI."""
            layout = QFormLayout()
            layout.setSpacing(4)
            layout.setContentsMargins(8, 8, 8, 8)

            # Create input fields
            self.id_edit = QLineEdit()
            self.id_edit.setReadOnly(True)  # ID is not editable

            self.name_edit = QLineEdit()
            self.type_edit = QLineEdit()
            self.category_edit = QLineEdit()
            self.color_rgb_edit = QLineEdit()
            self.color_hex_edit = QLineEdit()
            self.x_edit = QLineEdit()
            self.y_edit = QLineEdit()
            self.w_edit = QLineEdit()
            self.h_edit = QLineEdit()
            self.confidence_edit = QLineEdit()
            self.confidence_edit.setReadOnly(True)  # Confidence is not editable

            # Add fields to layout
            layout.addRow("ID:", self.id_edit)
            layout.addRow("Naam:", self.name_edit)
            layout.addRow("Type:", self.type_edit)
            layout.addRow("Categorie:", self.category_edit)
            layout.addRow("Kleur (RGB):", self.color_rgb_edit)
            layout.addRow("Kleur (HEX):", self.color_hex_edit)
            layout.addRow("X:", self.x_edit)
            layout.addRow("Y:", self.y_edit)
            layout.addRow("W:", self.w_edit)
            layout.addRow("H:", self.h_edit)
            layout.addRow("Confidence:", self.confidence_edit)

            self.setLayout(layout)

        def _setup_connections(self) -> None:
            """Set up signal/slot connections for editor fields."""
            self.name_edit.editingFinished.connect(self._on_field_changed)
            self.type_edit.editingFinished.connect(self._on_field_changed)
            self.category_edit.editingFinished.connect(self._on_field_changed)
            self.x_edit.editingFinished.connect(self._on_field_changed)
            self.y_edit.editingFinished.connect(self._on_field_changed)
            self.w_edit.editingFinished.connect(self._on_field_changed)
            self.h_edit.editingFinished.connect(self._on_field_changed)
            self.color_hex_edit.editingFinished.connect(self._on_color_changed)
            self.color_rgb_edit.editingFinished.connect(self._on_rgb_color_changed)

        def _get_old_values(self) -> Dict[str, Any]:
            """Get current values before change for logging.
            
            Returns:
                Dictionary with current field values.
            """
            if self._current_element is None:
                return {}
            return {
                'name': self._current_element.name,
                'element_type': self._current_element.element_type,
                'category': self._current_element.category,
                'x': self._current_element.x,
                'y': self._current_element.y,
                'width': self._current_element.width,
                'height': self._current_element.height,
                'color_rgb': self._current_element.color_rgb,
                'color_hex': self._current_element.color_hex,
            }

        def _on_field_changed(self) -> None:
            """Handle field change and update current element."""
            if self._current_element is None:
                return

            old_values = self._get_old_values()
            
            try:
                # Store old values for logging
                old_name = self._current_element.name
                old_type = self._current_element.element_type
                old_category = self._current_element.category
                old_x = self._current_element.x
                old_y = self._current_element.y
                old_width = self._current_element.width
                old_height = self._current_element.height
                
                # Update element
                self._current_element.name = self.name_edit.text()
                self._current_element.element_type = self.type_edit.text()
                self._current_element.category = self.category_edit.text()
                
                # Validate and update numeric fields
                try:
                    new_x = int(self.x_edit.text() or 0)
                    self._current_element.x = new_x
                except ValueError:
                    # Restore old value on invalid input
                    self.x_edit.setText(str(old_x))
                    return
                
                try:
                    new_y = int(self.y_edit.text() or 0)
                    self._current_element.y = new_y
                except ValueError:
                    self.y_edit.setText(str(old_y))
                    return
                
                try:
                    new_width = int(self.w_edit.text() or 0)
                    self._current_element.width = new_width
                except ValueError:
                    self.w_edit.setText(str(old_width))
                    return
                
                try:
                    new_height = int(self.h_edit.text() or 0)
                    self._current_element.height = new_height
                except ValueError:
                    self.h_edit.setText(str(old_height))
                    return
                
                # Emit signal for each changed field
                if self._current_element.name != old_name:
                    self.element_changed.emit(
                        self._current_element, 'name', old_name, self._current_element.name
                    )
                if self._current_element.element_type != old_type:
                    self.element_changed.emit(
                        self._current_element, 'element_type', old_type, self._current_element.element_type
                    )
                if self._current_element.category != old_category:
                    self.element_changed.emit(
                        self._current_element, 'category', old_category, self._current_element.category
                    )
                if self._current_element.x != old_x:
                    self.element_changed.emit(
                        self._current_element, 'x', old_x, self._current_element.x
                    )
                if self._current_element.y != old_y:
                    self.element_changed.emit(
                        self._current_element, 'y', old_y, self._current_element.y
                    )
                if self._current_element.width != old_width:
                    self.element_changed.emit(
                        self._current_element, 'width', old_width, self._current_element.width
                    )
                if self._current_element.height != old_height:
                    self.element_changed.emit(
                        self._current_element, 'height', old_height, self._current_element.height
                    )
                    
            except (ValueError, AttributeError) as e:
                # Log warning but don't crash
                if _logger is not None:
                    _logger.warning(f"Invalid input in element editor: {e}")
                pass

        def _on_color_changed(self) -> None:
            """Handle color hex change and update RGB."""
            if self._current_element is None:
                return

            old_hex = self._current_element.color_hex
            old_rgb = self._current_element.color_rgb
            
            hex_color = self.color_hex_edit.text()
            try:
                rgb = UIElement._hex_to_rgb(hex_color)
                self._current_element.color_hex = hex_color
                self._current_element.color_rgb = rgb
                
                # Update RGB field without triggering another change
                self.color_rgb_edit.blockSignals(True)
                self.color_rgb_edit.setText(f"{rgb[0]},{rgb[1]},{rgb[2]}")
                self.color_rgb_edit.blockSignals(False)
                
                # Emit signals for color changes
                self.element_changed.emit(
                    self._current_element, 'color_hex', old_hex, hex_color
                )
                self.element_changed.emit(
                    self._current_element, 'color_rgb', old_rgb, rgb
                )
            except ValueError as e:
                # Invalid hex color - restore old value
                self.color_hex_edit.setText(old_hex)
                if _logger is not None:
                    _logger.warning(f"Invalid hex color: {hex_color} - {e}")

        def _on_rgb_color_changed(self) -> None:
            """Handle color RGB change and update HEX."""
            if self._current_element is None:
                return

            old_hex = self._current_element.color_hex
            old_rgb = self._current_element.color_rgb
            
            rgb_text = self.color_rgb_edit.text()
            try:
                # Parse "R,G,B" format
                parts = rgb_text.split(',')
                if len(parts) != 3:
                    raise ValueError("RGB must be in format R,G,B")
                r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
                
                # Validate range
                if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
                    raise ValueError("RGB values must be 0-255")
                
                hex_color = UIElement._rgb_to_hex((r, g, b))
                self._current_element.color_rgb = (r, g, b)
                self._current_element.color_hex = hex_color
                
                # Update HEX field without triggering another change
                self.color_hex_edit.blockSignals(True)
                self.color_hex_edit.setText(hex_color)
                self.color_hex_edit.blockSignals(False)
                
                # Emit signals for color changes
                self.element_changed.emit(
                    self._current_element, 'color_rgb', old_rgb, (r, g, b)
                )
                self.element_changed.emit(
                    self._current_element, 'color_hex', old_hex, hex_color
                )
            except ValueError as e:
                # Invalid RGB - restore old value
                self.color_rgb_edit.setText(f"{old_rgb[0]},{old_rgb[1]},{old_rgb[2]}")
                if _logger is not None:
                    _logger.warning(f"Invalid RGB color: {rgb_text} - {e}")

        def get_element_data(self) -> Dict[str, Any]:
            """Get current element data from editor fields.

            Returns:
                Dictionary containing element properties.
            """
            return {
                "id": self.id_edit.text(),
                "name": self.name_edit.text(),
                "type": self.type_edit.text(),
                "category": self.category_edit.text(),
                "color_rgb": self.color_rgb_edit.text(),
                "color_hex": self.color_hex_edit.text(),
                "x": self.x_edit.text(),
                "y": self.y_edit.text(),
                "w": self.w_edit.text(),
                "h": self.h_edit.text()
            }

        def set_element_data(self, data: Dict[str, Any]) -> None:
            """Set element data in editor fields.

            Args:
                data: Dictionary containing element properties.
            """
            self.id_edit.setText(str(data.get("id", "")))
            self.name_edit.setText(str(data.get("name", "")))
            self.type_edit.setText(str(data.get("type", "")))
            self.category_edit.setText(str(data.get("category", "")))
            self.color_rgb_edit.setText(str(data.get("color_rgb", "")))
            self.color_hex_edit.setText(str(data.get("color_hex", "")))
            self.x_edit.setText(str(data.get("x", "")))
            self.y_edit.setText(str(data.get("y", "")))
            self.w_edit.setText(str(data.get("w", "")))
            self.h_edit.setText(str(data.get("h", "")))

        def set_element(self, element: Optional[UIElement]) -> None:
            """Set the current element being edited.

            Args:
                element: UIElement to edit, or None to clear.
            """
            self._current_element = element

            if element is None:
                self.clear()
                return

            # Block signals during update
            self.blockSignals(True)

            self.id_edit.setText(element.id)
            self.name_edit.setText(element.name)
            self.type_edit.setText(element.element_type)
            self.category_edit.setText(element.category)
            self.color_rgb_edit.setText(f"{element.color_rgb[0]},{element.color_rgb[1]},{element.color_rgb[2]}")
            self.color_hex_edit.setText(element.color_hex)
            self.x_edit.setText(str(element.x))
            self.y_edit.setText(str(element.y))
            self.w_edit.setText(str(element.width))
            self.h_edit.setText(str(element.height))
            self.confidence_edit.setText(f"{element.confidence:.2f}")

            self.blockSignals(False)

        def clear(self) -> None:
            """Clear all editor fields."""
            self.blockSignals(True)
            self.id_edit.clear()
            self.name_edit.clear()
            self.type_edit.clear()
            self.category_edit.clear()
            self.color_rgb_edit.clear()
            self.color_hex_edit.clear()
            self.x_edit.clear()
            self.y_edit.clear()
            self.w_edit.clear()
            self.h_edit.clear()
            self.confidence_edit.clear()
            self._current_element = None
            self.blockSignals(False)

        def get_current_element(self) -> Optional[UIElement]:
            """Get the current element being edited.

            Returns:
                Current UIElement or None.
            """
            return self._current_element


    class PreviewArea(QScrollArea):
        """Preview area for displaying UI images with zoom and overlay support."""

        def __init__(self, parent: Optional[QWidget] = None) -> None:
            """Initialize the preview area.

            Args:
                parent: Parent widget.
            """
            super().__init__(parent)
            self._zoom_factor: float = 1.0
            self._pixmap: Optional[QPixmap] = None
            self._overlay_elements: List[UIElement] = []
            self._selected_element_id: Optional[str] = None
            self._setup_ui()
            self._setup_overlay()

        def _setup_ui(self) -> None:
            """Set up the preview area UI."""
            self.setWidgetResizable(True)
            self.setAlignment(Qt.AlignCenter)
            self.setMinimumSize(400, 300)

            # Create placeholder label
            self.placeholder_label = QLabel("Geen afbeelding geladen")
            self.placeholder_label.setAlignment(Qt.AlignCenter)
            self.placeholder_label.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-size: 18px;
                    background-color: #f5f5f5;
                    border: 2px dashed #cccccc;
                    border-radius: 8px;
                    padding: 20px;
                }
            """)
            self.setWidget(self.placeholder_label)

        def _setup_overlay(self) -> None:
            """Set up overlay renderer."""
            self._renderer = OverlayRenderer()

        def set_image(self, filepath: str) -> bool:
            """Load and display an image from file.

            Args:
                filepath: Path to the image file.

            Returns:
                True if image loaded successfully, False otherwise.
            """
            if not os.path.exists(filepath):
                return False

            self._pixmap = QPixmap(filepath)
            if self._pixmap.isNull():
                return False

            self._update_display()
            return True

        def set_overlay_elements(
            self,
            elements: List[UIElement],
            selected_id: Optional[str] = None
        ) -> None:
            """Set elements to display as overlay.

            Args:
                elements: List of UI elements to draw.
                selected_id: ID of selected element to highlight.
            """
            self._overlay_elements = elements
            self._selected_element_id = selected_id
            self._update_display()

        def highlight_element(self, element_id: Optional[str]) -> None:
            """Highlight a specific element in the overlay.

            Args:
                element_id: ID of element to highlight, or None to clear.
            """
            self._selected_element_id = element_id
            self._update_display()

        def set_zoom(self, zoom_factor: float) -> None:
            """Set zoom factor for the displayed image.

            Args:
                zoom_factor: Zoom factor (0.1 to 10.0).
            """
            self._zoom_factor = max(0.1, min(10.0, zoom_factor))
            self._update_display()

        def get_zoom(self) -> float:
            """Get current zoom factor.

            Returns:
                Current zoom factor.
            """
            return self._zoom_factor

        def zoom_in(self) -> None:
            """Zoom in by 25%."""
            self.set_zoom(self._zoom_factor * 1.25)

        def zoom_out(self) -> None:
            """Zoom out by 25%."""
            self.set_zoom(self._zoom_factor / 1.25)

        def _update_display(self) -> None:
            """Update the displayed image with overlay."""
            if self._pixmap is None:
                return

            # Render with overlay
            result_pixmap = self._renderer.render_overlay(
                self._pixmap,
                self._overlay_elements,
                self._selected_element_id,
                self._zoom_factor
            )

            image_label = QLabel()
            image_label.setPixmap(result_pixmap)
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.setWidget(image_label)

        def clear(self) -> None:
            """Clear the preview area and show placeholder."""
            self._pixmap = None
            self._zoom_factor = 1.0
            self._overlay_elements = []
            self._selected_element_id = None
            self.setWidget(self.placeholder_label)


    class UI2CodeSuperEngineWindow(QMainWindow):
        """Main window for the UI2Code Super Engine application."""

        def __init__(self) -> None:
            """Initialize the main window."""
            super().__init__()
            self._current_image_path: Optional[str] = None
            self._elements: List[UIElement] = []
            self._manual_corrections: Dict[str, Dict[str, Any]] = {}  # Store manual corrections by element ID
            
            # Initialize logging
            global _logger
            _logger = initialize_logging()
            
            # Initialize detection engine (use V2 for multi-pass detection)
            self.detector = UI2CodeDetectV2()
            
            self._setup_ui()
            self._setup_connections()

        def _setup_ui(self) -> None:
            """Set up the main window UI."""
            self.setWindowTitle("RackPlanner UI2Code Super-Engine")
            self.setMinimumSize(1200, 800)

            # Create central widget and main layout
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(8, 8, 8, 8)
            main_layout.setSpacing(8)

            # Create horizontal splitter
            splitter = QSplitter(Qt.Horizontal)
            main_layout.addWidget(splitter)

            # Create left panel
            left_panel = self._create_left_panel()
            splitter.addWidget(left_panel)

            # Create right panel
            right_panel = self._create_right_panel()
            splitter.addWidget(right_panel)

            # Set splitter sizes (left: 350px, right: rest)
            splitter.setSizes([350, 850])

        def _create_left_panel(self) -> QWidget:
            """Create the left panel with buttons and element editor.

            Returns:
                Left panel widget.
            """
            left_widget = QWidget()
            left_layout = QVBoxLayout(left_widget)
            left_layout.setContentsMargins(0, 0, 0, 0)
            left_layout.setSpacing(8)

            # Action buttons group
            action_group = QGroupBox("Acties")
            action_layout = QVBoxLayout(action_group)
            action_layout.setSpacing(4)

            self.btn_choose_image = QPushButton("Kies afbeelding")
            self.btn_detect_ui = QPushButton("Detecteer UI")
            self.btn_ocr_labels = QPushButton("OCR Labels")
            self.btn_auto_name = QPushButton("Auto-naam uit OCR")
            self.btn_export = QPushButton("Export TXT/JSON")
            self.btn_save_snapshot = QPushButton("Save snapshot")
            self.btn_load_state = QPushButton("Load state")

            for btn in [self.btn_choose_image, self.btn_detect_ui, self.btn_ocr_labels,
                        self.btn_auto_name, self.btn_export, self.btn_save_snapshot,
                        self.btn_load_state]:
                btn.setMinimumHeight(32)
                action_layout.addWidget(btn)

            left_layout.addWidget(action_group)

            # Element editor
            self.element_editor = ElementEditor()
            left_layout.addWidget(self.element_editor)

            left_layout.addStretch()

            return left_widget

        def _create_right_panel(self) -> QWidget:
            """Create the right panel with preview and tabs.

            Returns:
                Right panel widget.
            """
            right_widget = QWidget()
            right_layout = QVBoxLayout(right_widget)
            right_layout.setContentsMargins(0, 0, 0, 0)
            right_layout.setSpacing(8)

            # Preview area with zoom controls
            preview_group = QGroupBox("Preview")
            preview_layout = QVBoxLayout(preview_group)
            preview_layout.setSpacing(4)

            # Zoom controls
            zoom_layout = QHBoxLayout()
            zoom_layout.setSpacing(4)

            self.btn_zoom_out = QPushButton("-")
            self.btn_zoom_out.setFixedSize(32, 32)
            self.btn_zoom_out.setToolTip("Zoom uit")

            self.zoom_slider = QSlider(Qt.Horizontal)
            self.zoom_slider.setMinimum(10)
            self.zoom_slider.setMaximum(500)
            self.zoom_slider.setValue(100)
            self.zoom_slider.setMinimumWidth(150)

            self.btn_zoom_in = QPushButton("+")
            self.btn_zoom_in.setFixedSize(32, 32)
            self.btn_zoom_in.setToolTip("Zoom in")

            self.zoom_label = QLabel("100%")
            self.zoom_label.setMinimumWidth(50)
            self.zoom_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            zoom_layout.addWidget(self.btn_zoom_out)
            zoom_layout.addWidget(self.zoom_slider)
            zoom_layout.addWidget(self.btn_zoom_in)
            zoom_layout.addWidget(self.zoom_label)
            zoom_layout.addStretch()

            preview_layout.addLayout(zoom_layout)

            # Preview area
            self.preview_area = PreviewArea()
            self.preview_area.setMinimumHeight(400)
            preview_layout.addWidget(self.preview_area)

            right_layout.addWidget(preview_group)

            # Tabs
            self.tabs = QTabWidget()
            self.tab_elements = self._create_elements_table()
            self.tab_groups = QListWidget()
            self.tab_labels = QListWidget()
            self.tab_ocr_zones = QListWidget()

            self.tabs.addTab(self.tab_elements, "Elementen")
            self.tabs.addTab(self.tab_groups, "Groepen")
            self.tabs.addTab(self.tab_labels, "Labels (OCR)")
            self.tabs.addTab(self.tab_ocr_zones, "OCR Zones")

            right_layout.addWidget(self.tabs)

            return right_widget

        def _create_elements_table(self) -> QTableWidget:
            """Create the elements table widget.

            Returns:
                Configured QTableWidget for displaying elements.
            """
            table = QTableWidget()
            table.setColumnCount(11)
            table.setHorizontalHeaderLabels([
                "ID", "Naam", "Type", "Categorie",
                "X", "Y", "W", "H",
                "Kleur HEX", "Confidence", "Source"
            ])

            # Set column widths
            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
            header.setSectionResizeMode(1, QHeaderView.Stretch)  # Naam
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Type
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Categorie
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # X
            header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Y
            header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # W
            header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # H
            header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # Kleur
            header.setSectionResizeMode(9, QHeaderView.ResizeToContents)  # Confidence
            header.setSectionResizeMode(10, QHeaderView.ResizeToContents)  # Source

            # Enable single row selection
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
            table.setSelectionMode(QAbstractItemView.SingleSelection)
            table.setAlternatingRowColors(True)

            # Make table read-only (no editing)
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)

            return table

        def _setup_connections(self) -> None:
            """Set up signal/slot connections."""
            self.btn_choose_image.clicked.connect(self._on_choose_image)
            self.btn_detect_ui.clicked.connect(self._on_detect_ui)
            self.btn_ocr_labels.clicked.connect(self._on_placeholder_action)
            self.btn_auto_name.clicked.connect(self._on_placeholder_action)
            self.btn_export.clicked.connect(self._on_placeholder_action)
            self.btn_save_snapshot.clicked.connect(self._on_placeholder_action)
            self.btn_load_state.clicked.connect(self._on_placeholder_action)

            self.btn_zoom_in.clicked.connect(self._on_zoom_in)
            self.btn_zoom_out.clicked.connect(self._on_zoom_out)
            self.zoom_slider.valueChanged.connect(self._on_zoom_slider_changed)

            # Connect table selection to editor
            self.tab_elements.itemSelectionChanged.connect(self._on_element_selected)
            
            # Connect editor changes to table update and logging
            self.element_editor.element_changed.connect(self._on_element_changed)

        def _on_choose_image(self) -> None:
            """Handle choose image button click."""
            global _logger
            if _logger is None:
                _logger = get_logger()
            
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Kies afbeelding",
                "",
                "Afbeeldingen (*.png *.jpg *.jpeg *.bmp);;Alle bestanden (*)"
            )

            if file_path:
                _logger.info(f"Afbeelding gekozen: {file_path}")
                self._current_image_path = file_path
                if self.preview_area.set_image(file_path):
                    _logger.info("Afbeelding succesvol geladen in preview")
                    self._update_zoom_display()
                else:
                    _logger.error(f"Kan afbeelding niet laden: {file_path}")
                    QMessageBox.warning(
                        self,
                        "Fout",
                        f"Kan afbeelding niet laden:\n{file_path}"
                    )

        def _on_placeholder_action(self) -> None:
            """Show placeholder status message for unimplemented actions."""
            sender = self.sender()
            if sender:
                QMessageBox.information(
                    self,
                    "Nog niet geïmplementeerd",
                    f"Functionaliteit '{sender.text()}' is nog niet geïmplementeerd in fase 2."
                )

        def _on_zoom_in(self) -> None:
            """Handle zoom in button click."""
            self.preview_area.zoom_in()
            self._update_zoom_display()

        def _on_zoom_out(self) -> None:
            """Handle zoom out button click."""
            self.preview_area.zoom_out()
            self._update_zoom_display()

        def _on_zoom_slider_changed(self, value: int) -> None:
            """Handle zoom slider value change.

            Args:
                value: Slider value (10-500).
            """
            zoom_factor = value / 100.0
            self.preview_area.set_zoom(zoom_factor)
            self._update_zoom_display()

        def _update_zoom_display(self) -> None:
            """Update zoom slider and label to match current zoom."""
            zoom_percent = int(self.preview_area.get_zoom() * 100)
            self.zoom_slider.blockSignals(True)
            self.zoom_slider.setValue(zoom_percent)
            self.zoom_slider.blockSignals(False)
            self.zoom_label.setText(f"{zoom_percent}%")

        def _on_detect_ui(self) -> None:
            """Handle detect UI button click."""
            global _logger
            if _logger is None:
                _logger = get_logger()
            
            if not self._current_image_path:
                _logger.warning("Detectie geprobeerd zonder geladen afbeelding")
                QMessageBox.warning(
                    self,
                    "Geen afbeelding",
                    "Kies eerst een afbeelding voordat je UI-elementen detecteert."
                )
                return

            try:
                # Store manual corrections before re-detection
                old_corrections = self._store_manual_corrections()
                _logger.info(f"Handmatige correcties opgeslagen: {len(old_corrections)} element(en)")
                
                # Log detectie start
                _logger.info(f"Start multi-pass detectie - afbeeldingspad: {self._current_image_path}")
                
                # Verify file exists
                if not os.path.exists(self._current_image_path):
                    _logger.error(f"Afbeeldingsbestand bestaat niet: {self._current_image_path}")
                    raise FileNotFoundError(f"Image file not found: {self._current_image_path}")
                
                # Log image info
                try:
                    from PySide6.QtGui import QImage
                    test_img = QImage(self._current_image_path)
                    _logger.info(
                        f"Afbeelding geladen: {test_img.width()}x{test_img.height()} pixels"
                    )
                except Exception as img_err:
                    _logger.warning(f"Kon afbeeldingsinformatie niet lezen: {img_err}")
                
                # Run multi-pass detection
                _logger.info("Roep detect_elements() aan met Fase 3B multi-pass detectie")
                elements = self.detector.detect_elements(image_data=self._current_image_path)
                
                # Preserve manual corrections
                preserved_count = self._preserve_manual_corrections(elements, old_corrections)
                _logger.info(f"Handmatige correcties behouden: {preserved_count} element(en)")
                
                # Log resultaat
                _logger.info(f"Detectie voltooid - {len(elements)} element(en) gedetecteerd")
                
                # Log classification distribution
                by_type: Dict[str, int] = {}
                for elem in elements:
                    by_type[elem.element_type] = by_type.get(elem.element_type, 0) + 1
                _logger.info(f"Classificatieverdeling: {by_type}")
                
                # Log confidence statistics
                if elements:
                    confidences = [e.confidence for e in elements]
                    _logger.info(
                        f"Confidence statistieken: min={min(confidences):.3f}, "
                        f"max={max(confidences):.3f}, avg={sum(confidences)/len(confidences):.3f}"
                    )
                
                # Store elements
                self._elements = elements

                # Update table
                self._update_elements_table(elements)

                # Update overlay
                self.preview_area.set_overlay_elements(elements)

                # Clear editor
                self.element_editor.clear()

                # Show status
                count = len(elements)
                if count > 0:
                    QMessageBox.information(
                        self,
                        "Detectie voltooid",
                        f"{count} UI-element(eren) gedetecteerd."
                    )
                else:
                    QMessageBox.information(
                        self,
                        "Geen elementen",
                        "Geen UI-elementen gedetecteerd in deze afbeelding."
                    )

            except FileNotFoundError as e:
                _logger.exception("Bestand niet gevonden tijdens detectie")
                QMessageBox.critical(
                    self,
                    "Bestand niet gevonden",
                    f"Afbeelding niet gevonden:\n{e}"
                )
            except ImportError as e:
                _logger.exception("Import error tijdens detectie")
                QMessageBox.critical(
                    self,
                    "Import error",
                    f"Qt libraries niet beschikbaar:\n{e}"
                )
            except Exception as e:
                _logger.exception("Onverwachte fout tijdens detectie")
                QMessageBox.critical(
                    self,
                    "Detectiefout",
                    f"Er is een fout opgetreden bij het detecteren:\n{str(e)}"
                )

        def _store_manual_corrections(self) -> Dict[str, Dict[str, Any]]:
            """Store current manual corrections.
            
            Returns:
                Dictionary mapping element ID to corrected fields.
            """
            corrections = {}
            for elem in self._elements:
                if elem.manually_corrected:
                    corrections[elem.id] = {
                        'name': elem.name if 'name' in elem.manually_corrected else None,
                        'element_type': elem.element_type if 'element_type' in elem.manually_corrected else None,
                        'category': elem.category if 'category' in elem.manually_corrected else None,
                        'fields': set(elem.manually_corrected)
                    }
            return corrections

        def _preserve_manual_corrections(
            self,
            new_elements: List[UIElement],
            old_corrections: Dict[str, Dict[str, Any]]
        ) -> int:
            """Preserve manual corrections after re-detection.
            
            Matches new elements to old corrections based on geometric overlap.
            
            Args:
                new_elements: Newly detected elements.
                old_corrections: Previously stored corrections.
            
            Returns:
                Number of corrections preserved.
            """
            if not old_corrections:
                return 0
            
            preserved = 0
            
            for new_elem in new_elements:
                # Find best matching old element by IoU
                best_match = None
                best_iou = 0.3  # Minimum 30% overlap
                
                for old_id, correction in old_corrections.items():
                    # Find old element in current elements by ID pattern or position
                    # For simplicity, match by position overlap
                    old_elem = next((e for e in self._elements if e.id == old_id), None)
                    if old_elem is None:
                        continue
                    
                    # Calculate overlap
                    iou = self._calculate_overlap(new_elem, old_elem)
                    if iou > best_iou:
                        best_iou = iou
                        best_match = (old_id, correction)
                
                if best_match:
                    old_id, correction = best_match
                    # Apply corrections
                    if correction['name'] is not None:
                        new_elem.name = correction['name']
                    if correction['element_type'] is not None:
                        new_elem.element_type = correction['element_type']
                    if correction['category'] is not None:
                        new_elem.category = correction['category']
                    new_elem.manually_corrected = correction['fields'].copy()
                    preserved += 1
            
            return preserved

        def _calculate_overlap(self, elem1: UIElement, elem2: UIElement) -> float:
            """Calculate overlap ratio between two elements.
            
            Args:
                elem1: First element.
                elem2: Second element.
            
            Returns:
                Overlap ratio (0.0 to 1.0).
            """
            # Calculate intersection
            x1 = max(elem1.x, elem2.x)
            y1 = max(elem1.y, elem2.y)
            x2 = min(elem1.x + elem1.width, elem2.x + elem2.width)
            y2 = min(elem1.y + elem1.height, elem2.y + elem2.height)
            
            if x1 >= x2 or y1 >= y2:
                return 0.0
            
            intersection = (x2 - x1) * (y2 - y1)
            area1 = elem1.width * elem1.height
            area2 = elem2.width * elem2.height
            
            if area1 == 0 or area2 == 0:
                return 0.0
            
            # Use smaller area as reference
            return intersection / min(area1, area2)

        def _update_elements_table(self, elements: List[UIElement]) -> None:
            """Update the elements table with detected elements.

            Args:
                elements: List of detected UI elements.
            """
            table = self.tab_elements
            table.setRowCount(0)  # Clear existing rows

            for elem in elements:
                row = table.rowCount()
                table.insertRow(row)

                # ID
                item = QTableWidgetItem(elem.id)
                item.setData(Qt.UserRole, elem)  # Store element reference
                table.setItem(row, 0, item)

                # Name
                table.setItem(row, 1, QTableWidgetItem(elem.name))

                # Type
                table.setItem(row, 2, QTableWidgetItem(elem.element_type))

                # Category
                table.setItem(row, 3, QTableWidgetItem(elem.category))

                # X
                table.setItem(row, 4, QTableWidgetItem(str(elem.x)))

                # Y
                table.setItem(row, 5, QTableWidgetItem(str(elem.y)))

                # Width
                table.setItem(row, 6, QTableWidgetItem(str(elem.width)))

                # Height
                table.setItem(row, 7, QTableWidgetItem(str(elem.height)))

                # Color HEX
                color_item = QTableWidgetItem(elem.color_hex)
                # Set background color to show the actual color
                try:
                    qcolor = QColor(elem.color_hex)
                    color_item.setBackground(QBrush(qcolor))
                    # Set white or black text based on brightness
                    brightness = (elem.color_rgb[0] * 299 +
                                  elem.color_rgb[1] * 587 +
                                  elem.color_rgb[2] * 114) / 1000
                    if brightness > 128:
                        color_item.setForeground(QBrush(QColor("black")))
                    else:
                        color_item.setForeground(QBrush(QColor("white")))
                except:
                    pass
                table.setItem(row, 8, color_item)

                # Confidence
                table.setItem(row, 9, QTableWidgetItem(f"{elem.confidence:.2f}"))

                # Source
                table.setItem(row, 10, QTableWidgetItem(elem.source))

            # Resize columns to fit content
            table.resizeColumnsToContents()

        def _on_element_selected(self) -> None:
            """Handle element selection in the table."""
            table = self.tab_elements
            selected_items = table.selectedItems()

            if not selected_items:
                self.element_editor.clear()
                self.preview_area.highlight_element(None)
                return

            # Get the first selected row
            row = selected_items[0].row()

            # Get the element from the first column (ID)
            id_item = table.item(row, 0)
            if id_item is None:
                self.element_editor.clear()
                self.preview_area.highlight_element(None)
                return

            element = id_item.data(Qt.UserRole)
            if isinstance(element, UIElement):
                self.element_editor.set_element(element)
                # Highlight element in overlay
                self.preview_area.highlight_element(element.id)
            else:
                self.element_editor.clear()
                self.preview_area.highlight_element(None)

        def _on_element_changed(
            self,
            element: UIElement,
            field_name: str,
            old_value: Any,
            new_value: Any
        ) -> None:
            """Handle element change and update table.
            
            Args:
                element: The UIElement that changed.
                field_name: Name of the field that changed.
                old_value: Previous value.
                new_value: New value.
            """
            global _logger
            if _logger is None:
                _logger = get_logger()
            
            # Log the change
            _logger.info(
                f"Element {element.id} field {field_name} changed "
                f"from {repr(old_value)} to {repr(new_value)}"
            )
            
            # Find the row for this element and update the table cell
            table = self.tab_elements
            for row in range(table.rowCount()):
                id_item = table.item(row, 0)
                if id_item is not None:
                    row_element = id_item.data(Qt.UserRole)
                    if row_element is element:
                        # Update the appropriate cell based on field name
                        self._update_table_cell(row, field_name, new_value)
                        break

        def _update_table_cell(self, row: int, field_name: str, value: Any) -> None:
            """Update a single table cell.
            
            Args:
                row: Row index to update.
                field_name: Name of the field to update.
                value: New value for the cell.
            """
            table = self.tab_elements
            
            # Map field names to column indices
            field_to_column = {
                'name': 1,
                'element_type': 2,
                'category': 3,
                'x': 4,
                'y': 5,
                'width': 6,
                'height': 7,
                'color_hex': 8,
                'color_rgb': 8,  # Color column shows HEX
            }
            
            column = field_to_column.get(field_name)
            if column is None:
                return
            
            # Get existing item or create new one
            item = table.item(row, column)
            
            if field_name in ('color_hex', 'color_rgb'):
                # Special handling for color - update background and text
                if isinstance(value, tuple):
                    # RGB tuple - convert to hex for display
                    hex_value = UIElement._rgb_to_hex(value)
                else:
                    hex_value = str(value)
                
                if item is None:
                    item = QTableWidgetItem(hex_value)
                    table.setItem(row, column, item)
                else:
                    item.setText(hex_value)
                
                # Update background color
                try:
                    qcolor = QColor(hex_value)
                    item.setBackground(QBrush(qcolor))
                    # Get current element for brightness calculation
                    id_item = table.item(row, 0)
                    if id_item is not None:
                        elem = id_item.data(Qt.UserRole)
                        if elem is not None:
                            brightness = (elem.color_rgb[0] * 299 +
                                        elem.color_rgb[1] * 587 +
                                        elem.color_rgb[2] * 114) / 1000
                            if brightness > 128:
                                item.setForeground(QBrush(QColor("black")))
                            else:
                                item.setForeground(QBrush(QColor("white")))
                except:
                    pass
            else:
                # Regular text field
                text_value = str(value)
                if item is None:
                    item = QTableWidgetItem(text_value)
                    table.setItem(row, column, item)
                else:
                    item.setText(text_value)


class UI2CodeSuperEngine:
    """Super Engine orchestrating all UI2Code components."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize the Super Engine.

        Args:
            config_path: Optional path to configuration file.
        """
        self.config_path = config_path
        self.core = UI2CodeCore()
        self.detector = UI2CodeDetect()
        self.layout = UI2CodeLayout()
        self.export = UI2CodeExport()
        self.window: Optional["UI2CodeSuperEngineWindow"] = None

    def run(self, ui_input: Any) -> Any:
        """Run the complete UI to code conversion pipeline.

        Args:
            ui_input: Input UI data.

        Returns:
            Generated code output.
        """
        # Detect elements
        elements = self.detector.detect_elements(ui_input)

        # Analyze layout
        layout_structure = self.layout.analyze_layout(elements)

        # Process through core
        result = self.core.process(layout_structure)

        return result

    def export_result(self, code: str, filename: str) -> str:
        """Export the generated code.

        Args:
            code: Generated code.
            filename: Output filename.

        Returns:
            Path to exported file.
        """
        return self.export.export_code(code, filename)

    def launch_gui(self) -> int:
        """Launch the GUI application.

        Returns:
            Application exit code.

        Raises:
            ImportError: If Qt libraries are not available.
        """
        if not _QT_AVAILABLE:
            raise ImportError(
                "Qt libraries not available. Install PySide6 and required system dependencies."
            )
        app = QApplication(sys.argv)
        self.window = UI2CodeSuperEngineWindow()  # type: ignore
        self.window.show()
        return app.exec()


if __name__ == "__main__":
    # Launch GUI when run as main module
    engine = UI2CodeSuperEngine()
    try:
        exit_code = engine.launch_gui()
        sys.exit(exit_code)
    except ImportError as e:
        print(f"Error: {e}")
        print("GUI cannot be launched without Qt libraries.")
        sys.exit(1)
