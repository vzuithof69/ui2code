#!/usr/bin/env python3
"""UI2Code Detection Tests.

Tests for the UI2CodeDetect engine including:
- Contour detection
- Filtering
- Duplicate removal
- Color extraction
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set headless mode before Qt imports
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from engine.ui2code_detect import UI2CodeDetect
from engine.models import UIElement


def test_detector_creation() -> bool:
    """Test detector instantiation."""
    print("Testing detector creation...")

    detector = UI2CodeDetect()

    assert detector is not None, "Detector should be created"
    assert hasattr(detector, 'detect_elements'), "Should have detect_elements method"
    assert hasattr(detector, 'MIN_WIDTH'), "Should have MIN_WIDTH constant"
    assert hasattr(detector, 'MIN_HEIGHT'), "Should have MIN_HEIGHT constant"
    assert hasattr(detector, 'MIN_AREA'), "Should have MIN_AREA constant"

    print("  ✓ Detector creation works")
    return True


def test_detect_with_qimage() -> bool:
    """Test detection with QImage input."""
    print("Testing detection with QImage...")

    try:
        from PySide6.QtGui import QImage
    except ImportError:
        print("  ⚠ Qt not available, skipping")
        return True

    detector = UI2CodeDetect()

    # Create a simple test image (100x100 with a rectangle)
    image = QImage(100, 100, QImage.Format_RGB32)
    image.fill(0xFFFFFFFF)  # White background

    # Draw a black rectangle (simulating a button)
    for y in range(20, 40):
        for x in range(30, 70):
            image.setPixel(x, y, 0xFF000000)  # Black

    elements = detector.detect_elements(image_data=image)

    assert isinstance(elements, list), "Should return a list"
    # Should detect at least the rectangle edges
    print(f"  ✓ Detected {len(elements)} elements")
    return True


def test_detect_with_path() -> bool:
    """Test detection with file path."""
    print("Testing detection with file path...")

    try:
        from PySide6.QtGui import QImage
    except ImportError:
        print("  ⚠ Qt not available, skipping")
        return True

    detector = UI2CodeDetect()

    # Create a test image and save it
    test_image_path = "/tmp/test_ui_element.png"
    image = QImage(100, 100, QImage.Format_RGB32)
    image.fill(0xFFFFFFFF)

    # Draw some rectangles
    for y in range(10, 30):
        for x in range(10, 50):
            image.setPixel(x, y, 0xFF0000FF)  # Blue rectangle

    image.save(test_image_path)

    try:
        elements = detector.detect_elements(image_path=test_image_path)
        assert isinstance(elements, list), "Should return a list"
        print(f"  ✓ Detected {len(elements)} elements from file")
        return True
    finally:
        # Clean up
        if os.path.exists(test_image_path):
            os.remove(test_image_path)


def test_empty_image() -> bool:
    """Test detection with empty/uniform image."""
    print("Testing detection with empty image...")

    try:
        from PySide6.QtGui import QImage
    except ImportError:
        print("  ⚠ Qt not available, skipping")
        return True

    detector = UI2CodeDetect()

    # Create a completely uniform image (no edges)
    image = QImage(100, 100, QImage.Format_RGB32)
    image.fill(0xFF808080)  # Gray

    elements = detector.detect_elements(image_data=image)

    assert isinstance(elements, list), "Should return a list"
    # May return empty list or very few elements
    print(f"  ✓ Empty image returns {len(elements)} elements")
    return True


def test_filter_small_elements() -> bool:
    """Test filtering of small elements."""
    print("Testing small element filtering...")

    detector = UI2CodeDetect()

    # Create elements with various sizes
    elements = [
        UIElement(
            id="tiny",
            name="Tiny",
            element_type="test",
            category="test",
            color_rgb=(0, 0, 0),
            color_hex="#000000",
            x=0,
            y=0,
            width=2,  # Too small
            height=2,
            confidence=1.0,
            source="test"
        ),
        UIElement(
            id="small",
            name="Small",
            element_type="test",
            category="test",
            color_rgb=(0, 0, 0),
            color_hex="#000000",
            x=0,
            y=0,
            width=5,  # Above minimum
            height=5,
            confidence=1.0,
            source="test"
        ),
    ]

    filtered = detector._filter_elements(elements, 100, 100)

    # Tiny element should be filtered out
    assert len(filtered) < len(elements), "Should filter tiny elements"
    assert not any(e.id == "tiny" for e in filtered), "Tiny element should be filtered"

    print("  ✓ Small element filtering works")
    return True


def test_filter_background_elements() -> bool:
    """Test filtering of background-sized elements."""
    print("Testing background element filtering...")

    detector = UI2CodeDetect()

    # Create an element that covers almost entire image
    elements = [
        UIElement(
            id="background",
            name="Background",
            element_type="test",
            category="test",
            color_rgb=(0, 0, 0),
            color_hex="#000000",
            x=0,
            y=0,
            width=98,  # Covers 98% of 100x100 image
            height=98,
            confidence=1.0,
            source="test"
        ),
        UIElement(
            id="normal",
            name="Normal",
            element_type="test",
            category="test",
            color_rgb=(0, 0, 0),
            color_hex="#000000",
            x=10,
            y=10,
            width=20,
            height=20,
            confidence=1.0,
            source="test"
        ),
    ]

    filtered = detector._filter_elements(elements, 100, 100)

    # Background element should be filtered out
    assert len(filtered) < len(elements), "Should filter background elements"
    assert not any(e.id == "background" for e in filtered), "Background should be filtered"
    assert any(e.id == "normal" for e in filtered), "Normal element should remain"

    print("  ✓ Background element filtering works")
    return True


def test_duplicate_removal() -> bool:
    """Test removal of duplicate elements."""
    print("Testing duplicate removal...")

    detector = UI2CodeDetect()

    # Create overlapping elements
    elements = [
        UIElement(
            id="elem1",
            name="Element 1",
            element_type="test",
            category="test",
            color_rgb=(0, 0, 0),
            color_hex="#000000",
            x=10,
            y=10,
            width=50,
            height=50,
            confidence=1.0,
            source="test"
        ),
        UIElement(
            id="elem2",
            name="Element 2",
            element_type="test",
            category="test",
            color_rgb=(0, 0, 0),
            color_hex="#000000",
            x=12,
            y=12,
            width=48,
            height=48,  # Highly overlapping with elem1
            confidence=0.9,
            source="test"
        ),
    ]

    deduped = detector._remove_duplicates(elements)

    # Should remove one of the highly overlapping elements
    assert len(deduped) < len(elements), "Should remove duplicates"

    print("  ✓ Duplicate removal works")
    return True


def test_color_extraction() -> bool:
    """Test color extraction from regions."""
    print("Testing color extraction...")

    try:
        from PySide6.QtGui import QImage
    except ImportError:
        print("  ⚠ Qt not available, skipping")
        return True

    detector = UI2CodeDetect()

    # Create test image with known color region
    image = QImage(100, 100, QImage.Format_RGB32)
    image.fill(0xFFFFFFFF)  # White background

    # Draw a red rectangle
    for y in range(10, 30):
        for x in range(10, 30):
            image.setPixel(x, y, 0xFFFF0000)  # Red in ARGB

    color = detector._get_region_color(image, 10, 10, 20, 20)

    # Should extract red color (approximately)
    assert color[0] > 200, f"Red component should be high, got {color[0]}"
    assert color[1] < 50, f"Green component should be low, got {color[1]}"
    assert color[2] < 50, f"Blue component should be low, got {color[2]}"

    print(f"  ✓ Color extraction works: {color}")
    return True


def test_no_image_error() -> bool:
    """Test error handling for missing image."""
    print("Testing missing image error...")

    try:
        from PySide6.QtGui import QImage
    except ImportError:
        print("  ⚠ Qt not available, skipping")
        return True

    detector = UI2CodeDetect()

    try:
        elements = detector.detect_elements(image_data=None, image_path=None)
        print("  ✗ Should raise ValueError for missing image")
        return False
    except ValueError as e:
        print(f"  ✓ Correctly raises ValueError: {e}")
        return True
    except Exception as e:
        print(f"  ✗ Wrong exception type: {type(e).__name__}: {e}")
        return False


def test_file_not_found_error() -> bool:
    """Test error handling for non-existent file."""
    print("Testing file not found error...")

    try:
        from PySide6.QtGui import QImage
    except ImportError:
        print("  ⚠ Qt not available, skipping")
        return True

    detector = UI2CodeDetect()

    try:
        elements = detector.detect_elements(image_path="/nonexistent/path/image.png")
        print("  ✗ Should raise FileNotFoundError")
        return False
    except FileNotFoundError as e:
        print(f"  ✓ Correctly raises FileNotFoundError: {e}")
        return True
    except Exception as e:
        print(f"  ✗ Wrong exception type: {type(e).__name__}: {e}")
        return False


def test_element_properties() -> bool:
    """Test that detected elements have correct properties."""
    print("Testing element properties...")

    try:
        from PySide6.QtGui import QImage
    except ImportError:
        print("  ⚠ Qt not available, skipping")
        return True

    detector = UI2CodeDetect()

    # Create test image
    image = QImage(100, 100, QImage.Format_RGB32)
    image.fill(0xFFFFFFFF)

    # Draw a rectangle
    for y in range(20, 40):
        for x in range(30, 70):
            image.setPixel(x, y, 0xFF0000FF)  # Blue

    elements = detector.detect_elements(image_data=image)

    if elements:
        elem = elements[0]
        assert isinstance(elem, UIElement), "Should return UIElement instances"
        assert elem.id != "", "ID should not be empty"
        assert elem.source == "contour", "Source should be 'contour'"
        assert elem.confidence >= 0.0, "Confidence should be >= 0"
        assert elem.confidence <= 1.0, "Confidence should be <= 1"
        assert elem.x >= 0, "X should be >= 0"
        assert elem.y >= 0, "Y should be >= 0"
        assert elem.width > 0, "Width should be > 0"
        assert elem.height > 0, "Height should be > 0"
        print(f"  ✓ Element properties correct: {elem.id}")
    else:
        print("  ⚠ No elements detected (may be OK)")

    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("UI2Code Detection Tests")
    print("=" * 60)

    tests = [
        test_detector_creation,
        test_detect_with_qimage,
        test_detect_with_path,
        test_empty_image,
        test_filter_small_elements,
        test_filter_background_elements,
        test_duplicate_removal,
        test_color_extraction,
        test_no_image_error,
        test_file_not_found_error,
        test_element_properties,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
                print(f"  ✗ {test.__name__} failed")
        except Exception as e:
            failed += 1
            print(f"  ✗ {test.__name__} error: {e}")
            import traceback
            traceback.print_exc()

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
