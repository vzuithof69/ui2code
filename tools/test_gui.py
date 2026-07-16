"""UI2Code GUI Smoketest.

Headless test script to verify the PySide6 GUI can be created and basic operations work.
Uses QT_QPA_PLATFORM=offscreen for headless testing.

This test:
- Creates a QApplication instance
- Creates the UI2CodeSuperEngineWindow
- Verifies all widgets are present
- Tests zoom functionality
- Mocks file dialogs to prevent blocking
- Properly closes the window
- Cleans up resources
"""

import sys
import os
import signal
from unittest.mock import patch

# Set headless platform before importing PySide6
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestTimeoutError(Exception):
    """Raised when a test exceeds the maximum allowed duration."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for test timeout."""
    raise TestTimeoutError("Test exceeded maximum duration (30 seconds)")


def test_gui_creation() -> bool:
    """Test GUI window creation and basic functionality.

    Returns:
        True if all tests passed, False otherwise.
    """
    print("Testing UI2Code GUI creation (headless mode)...")
    print("-" * 40)

    # Set timeout for entire test (30 seconds max)
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)

    try:
        # First check if Qt is available
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import QTimer
        except ImportError as qt_err:
            print(f"  ⚠ Qt libraries not available: {qt_err}")
            print("  Skipping GUI tests (system libraries missing)")
            print("-" * 40)
            print("GUI tests skipped - Qt system libraries not installed")
            return False

        from ui.ui2code_super_engine import UI2CodeSuperEngineWindow, ElementEditor, PreviewArea

        # Create QApplication
        print("Creating QApplication...")
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        print("  ✓ QApplication created")
        print(f"  ✓ Application name: {app.applicationName()}")

        # Test ElementEditor
        print("\nTesting ElementEditor...")
        editor = ElementEditor()
        print("  ✓ ElementEditor instantiated")

        # Test setting and getting element data
        test_data = {
            "id": "test-001",
            "name": "Test Element",
            "type": "button",
            "category": "controls",
            "color_rgb": "255,128,64",
            "color_hex": "#FF8040",
            "x": "100",
            "y": "200",
            "w": "150",
            "h": "50"
        }
        editor.set_element_data(test_data)
        retrieved_data = editor.get_element_data()
        assert retrieved_data["id"] == test_data["id"], "ID mismatch"
        assert retrieved_data["name"] == test_data["name"], "Name mismatch"
        assert retrieved_data["color_hex"] == test_data["color_hex"], "HEX color mismatch"
        print("  ✓ ElementEditor data operations work")

        # Test PreviewArea
        print("\nTesting PreviewArea...")
        preview = PreviewArea()
        print("  ✓ PreviewArea instantiated")

        # Test zoom operations
        preview.zoom_in()
        assert preview.get_zoom() > 1.0, "Zoom in failed"
        print(f"  ✓ Zoom in works (current: {preview.get_zoom():.2f}x)")

        preview.zoom_out()
        assert preview.get_zoom() < 1.25, "Zoom out failed"
        print(f"  ✓ Zoom out works (current: {preview.get_zoom():.2f}x)")

        preview.set_zoom(1.5)
        assert abs(preview.get_zoom() - 1.5) < 0.01, "Set zoom failed"
        print(f"  ✓ Set zoom works (current: {preview.get_zoom():.2f}x)")

        # Test with non-existent image (should return False)
        result = preview.set_image("/nonexistent/path/image.png")
        assert result is False, "Should fail for non-existent file"
        print("  ✓ Image loading handles missing files correctly")

        # Test main window
        print("\nTesting UI2CodeSuperEngineWindow...")
        window = UI2CodeSuperEngineWindow()
        print("  ✓ UI2CodeSuperEngineWindow instantiated")

        # Verify window properties
        assert window.windowTitle() == "RackPlanner UI2Code Super-Engine", "Window title incorrect"
        print(f"  ✓ Window title: {window.windowTitle()}")

        # Verify minimum size
        min_size = window.minimumSize()
        assert min_size.width() == 1200, f"Minimum width incorrect: {min_size.width()}"
        assert min_size.height() == 800, f"Minimum height incorrect: {min_size.height()}"
        print(f"  ✓ Minimum size: {min_size.width()}x{min_size.height()}")

        # Verify left panel components exist
        assert hasattr(window, "btn_choose_image"), "btn_choose_image missing"
        assert hasattr(window, "btn_detect_ui"), "btn_detect_ui missing"
        assert hasattr(window, "btn_ocr_labels"), "btn_ocr_labels missing"
        assert hasattr(window, "btn_auto_name"), "btn_auto_name missing"
        assert hasattr(window, "btn_export"), "btn_export missing"
        assert hasattr(window, "btn_save_snapshot"), "btn_save_snapshot missing"
        assert hasattr(window, "btn_load_state"), "btn_load_state missing"
        print("  ✓ All left panel buttons present")

        # Verify element editor exists
        assert hasattr(window, "element_editor"), "element_editor missing"
        print("  ✓ Element editor present")

        # Verify right panel components exist
        assert hasattr(window, "preview_area"), "preview_area missing"
        assert hasattr(window, "btn_zoom_in"), "btn_zoom_in missing"
        assert hasattr(window, "btn_zoom_out"), "btn_zoom_out missing"
        assert hasattr(window, "zoom_slider"), "zoom_slider missing"
        assert hasattr(window, "zoom_label"), "zoom_label missing"
        assert hasattr(window, "tabs"), "tabs missing"
        print("  ✓ All right panel components present")

        # Verify tabs
        tab_count = window.tabs.count()
        assert tab_count == 4, f"Expected 4 tabs, got {tab_count}"
        tab_names = [window.tabs.tabText(i) for i in range(tab_count)]
        expected_tabs = ["Elementen", "Groepen", "Labels (OCR)", "OCR Zones"]
        assert tab_names == expected_tabs, f"Tab names incorrect: {tab_names}"
        print(f"  ✓ All tabs present: {', '.join(tab_names)}")

        # Show window (in offscreen mode)
        print("\nShowing window...")
        window.show()
        print("  ✓ Window shown successfully")

        # Verify window is visible
        assert window.isVisible(), "Window should be visible"
        print("  ✓ Window is visible")

        # Test button clicks with mocked dialogs
        print("\nTesting button clicks (with mocked dialogs)...")
        
        # Mock QFileDialog and QMessageBox to prevent blocking
        with patch("ui.ui2code_super_engine.QFileDialog.getOpenFileName", return_value=("", "")):
            with patch("ui.ui2code_super_engine.QMessageBox.information"):
                with patch("ui.ui2code_super_engine.QMessageBox.warning"):
                    print("  Testing btn_choose_image...")
                    window.btn_choose_image.click()
                    app.processEvents()
                    print("  ✓ btn_choose_image works (mocked)")

                    print("  Testing btn_detect_ui...")
                    window.btn_detect_ui.click()
                    app.processEvents()
                    print("  ✓ btn_detect_ui works (mocked)")

                    print("  Testing btn_ocr_labels...")
                    window.btn_ocr_labels.click()
                    app.processEvents()
                    print("  ✓ btn_ocr_labels works (mocked)")

                    print("  Testing btn_auto_name...")
                    window.btn_auto_name.click()
                    app.processEvents()
                    print("  ✓ btn_auto_name works (mocked)")

                    print("  Testing btn_export...")
                    window.btn_export.click()
                    app.processEvents()
                    print("  ✓ btn_export works (mocked)")

                    print("  Testing btn_save_snapshot...")
                    window.btn_save_snapshot.click()
                    app.processEvents()
                    print("  ✓ btn_save_snapshot works (mocked)")

                    print("  Testing btn_load_state...")
                    window.btn_load_state.click()
                    app.processEvents()
                    print("  ✓ btn_load_state works (mocked)")

        print("  ✓ All button clicks work (dialogs mocked)")

        # Process events to ensure everything is rendered
        app.processEvents()
        print("  ✓ Events processed")

        # Close window
        print("\nClosing window...")
        window.close()
        print("  ✓ Window closed")

        # Verify window is closed
        assert not window.isVisible(), "Window should be closed"
        print("  ✓ Window is no longer visible")

        # Cleanup
        print("\nCleaning up...")
        app.quit()
        print("  ✓ QApplication quit")

        # Cancel timeout
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)

        print("-" * 40)
        print("All GUI tests passed!")
        return True

    except TestTimeoutError as e:
        print(f"  ✗ Timeout error: {e}")
        print("  Test took longer than 30 seconds - possible deadlock")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        # Cancel timeout
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
        return False


if __name__ == "__main__":
    success = test_gui_creation()
    sys.exit(0 if success else 1)
