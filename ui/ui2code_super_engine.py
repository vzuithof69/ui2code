"""UI2Code Super Engine.

Main UI interface for the UI2Code conversion system.
"""

import sys
import os
from typing import Optional, Dict, Any

# Import engine classes first (no Qt dependency)
from engine.ui2code_core import UI2CodeCore
from engine.ui2code_detect import UI2CodeDetect
from engine.ui2code_layout import UI2CodeLayout
from engine.ui2code_export import UI2CodeExport

# Try to import Qt - will fail in environments without Qt libraries
try:
    from PySide6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
        QPushButton, QLabel, QFileDialog, QScrollArea,
        QGroupBox, QFormLayout, QLineEdit, QSlider, QTabWidget,
        QListWidget, QSizePolicy, QMessageBox, QApplication
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QPixmap
    _QT_AVAILABLE = True
except ImportError:
    _QT_AVAILABLE = False
    # Define stubs for when Qt is not available
    QMainWindow = object  # type: ignore
    QWidget = object  # type: ignore
    QGroupBox = object  # type: ignore
    QScrollArea = object  # type: ignore


if _QT_AVAILABLE:
    class ElementEditor(QGroupBox):
        """Element editor panel for editing UI element properties."""

        def __init__(self, parent: Optional[QWidget] = None) -> None:
            """Initialize the element editor.

            Args:
                parent: Parent widget.
            """
            super().__init__("Element Editor", parent)
            self._setup_ui()

        def _setup_ui(self) -> None:
            """Set up the element editor UI."""
            layout = QFormLayout()
            layout.setSpacing(4)
            layout.setContentsMargins(8, 8, 8, 8)

            # Create input fields
            self.id_edit = QLineEdit()
            self.name_edit = QLineEdit()
            self.type_edit = QLineEdit()
            self.category_edit = QLineEdit()
            self.color_rgb_edit = QLineEdit()
            self.color_hfx_edit = QLineEdit()
            self.x_edit = QLineEdit()
            self.y_edit = QLineEdit()
            self.w_edit = QLineEdit()
            self.h_edit = QLineEdit()

            # Add fields to layout
            layout.addRow("ID:", self.id_edit)
            layout.addRow("Naam:", self.name_edit)
            layout.addRow("Type:", self.type_edit)
            layout.addRow("Categorie:", self.category_edit)
            layout.addRow("Kleur (RGB):", self.color_rgb_edit)
            layout.addRow("Kleur (HFX):", self.color_hfx_edit)
            layout.addRow("X:", self.x_edit)
            layout.addRow("Y:", self.y_edit)
            layout.addRow("W:", self.w_edit)
            layout.addRow("H:", self.h_edit)

            self.setLayout(layout)

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
                "color_hfx": self.color_hfx_edit.text(),
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
            self.color_hfx_edit.setText(str(data.get("color_hfx", "")))
            self.x_edit.setText(str(data.get("x", "")))
            self.y_edit.setText(str(data.get("y", "")))
            self.w_edit.setText(str(data.get("w", "")))
            self.h_edit.setText(str(data.get("h", "")))


    class PreviewArea(QScrollArea):
        """Preview area for displaying UI images with zoom support."""

        def __init__(self, parent: Optional[QWidget] = None) -> None:
            """Initialize the preview area.

            Args:
                parent: Parent widget.
            """
            super().__init__(parent)
            self._zoom_factor: float = 1.0
            self._pixmap: Optional[QPixmap] = None
            self._setup_ui()

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
            """Update the displayed image based on current zoom."""
            if self._pixmap is None:
                return

            scaled_pixmap = self._pixmap.scaled(
                int(self._pixmap.width() * self._zoom_factor),
                int(self._pixmap.height() * self._zoom_factor),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            image_label = QLabel()
            image_label.setPixmap(scaled_pixmap)
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.setWidget(image_label)

        def clear(self) -> None:
            """Clear the preview area and show placeholder."""
            self._pixmap = None
            self._zoom_factor = 1.0
            self.setWidget(self.placeholder_label)


    class UI2CodeSuperEngineWindow(QMainWindow):
        """Main window for the UI2Code Super Engine application."""

        def __init__(self) -> None:
            """Initialize the main window."""
            super().__init__()
            self._current_image_path: Optional[str] = None
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
            self.tab_elements = QListWidget()
            self.tab_groups = QListWidget()
            self.tab_labels = QListWidget()
            self.tab_ocr_zones = QListWidget()

            self.tabs.addTab(self.tab_elements, "Elementen")
            self.tabs.addTab(self.tab_groups, "Groepen")
            self.tabs.addTab(self.tab_labels, "Labels (OCR)")
            self.tabs.addTab(self.tab_ocr_zones, "OCR Zones")

            right_layout.addWidget(self.tabs)

            return right_widget

        def _setup_connections(self) -> None:
            """Set up signal/slot connections."""
            self.btn_choose_image.clicked.connect(self._on_choose_image)
            self.btn_detect_ui.clicked.connect(self._on_placeholder_action)
            self.btn_ocr_labels.clicked.connect(self._on_placeholder_action)
            self.btn_auto_name.clicked.connect(self._on_placeholder_action)
            self.btn_export.clicked.connect(self._on_placeholder_action)
            self.btn_save_snapshot.clicked.connect(self._on_placeholder_action)
            self.btn_load_state.clicked.connect(self._on_placeholder_action)

            self.btn_zoom_in.clicked.connect(self._on_zoom_in)
            self.btn_zoom_out.clicked.connect(self._on_zoom_out)
            self.zoom_slider.valueChanged.connect(self._on_zoom_slider_changed)

        def _on_choose_image(self) -> None:
            """Handle choose image button click."""
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Kies afbeelding",
                "",
                "Afbeeldingen (*.png *.jpg *.jpeg *.bmp);;Alle bestanden (*)"
            )

            if file_path:
                self._current_image_path = file_path
                if self.preview_area.set_image(file_path):
                    self._update_zoom_display()
                else:
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
