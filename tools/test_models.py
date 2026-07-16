#!/usr/bin/env python3
"""UI2Code Model Tests.

Tests for the UIElement data model including:
- Serialization (to_dict/from_dict)
- Color conversion (RGB/HEX)
- Validation
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.models import UIElement


def test_ui_element_creation() -> bool:
    """Test basic UIElement creation."""
    print("Testing UIElement creation...")

    # Test with all fields
    elem = UIElement(
        id="test-001",
        name="Test Button",
        element_type="button",
        category="controls",
        color_rgb=(255, 128, 64),
        color_hex="#FF8040",
        x=100,
        y=200,
        width=150,
        height=50,
        confidence=0.95,
        source="test"
    )

    assert elem.id == "test-001", "ID mismatch"
    assert elem.name == "Test Button", "Name mismatch"
    assert elem.element_type == "button", "Type mismatch"
    assert elem.category == "controls", "Category mismatch"
    assert elem.color_rgb == (255, 128, 64), "RGB mismatch"
    assert elem.color_hex == "#FF8040", "HEX mismatch"
    assert elem.x == 100, "X mismatch"
    assert elem.y == 200, "Y mismatch"
    assert elem.width == 150, "Width mismatch"
    assert elem.height == 50, "Height mismatch"
    assert elem.confidence == 0.95, "Confidence mismatch"
    assert elem.source == "test", "Source mismatch"

    print("  ✓ UIElement creation works")
    return True


def test_ui_element_defaults() -> bool:
    """Test UIElement default values."""
    print("Testing UIElement defaults...")

    # Test with minimal fields
    elem = UIElement(
        id="",
        name="",
        element_type="",
        category="",
        color_rgb=(0, 0, 0),
        color_hex="",
        x=0,
        y=0,
        width=0,
        height=0,
        confidence=0.0,
        source=""
    )

    # Should have generated defaults
    assert elem.id != "", "ID should be auto-generated"
    assert elem.name != "", "Name should have default"
    assert elem.element_type == "unknown", "Type should default to 'unknown'"
    assert elem.category == "general", "Category should default to 'general'"
    assert elem.color_rgb == (0, 0, 0), "RGB should default to black"
    assert elem.color_hex == "#000000", "HEX should default to #000000"
    assert elem.width >= 1, "Width should be at least 1"
    assert elem.height >= 1, "Height should be at least 1"
    assert elem.confidence == 0.0, "Confidence should be 0"
    assert elem.source == "unknown", "Source should default to 'unknown'"

    print("  ✓ UIElement defaults work")
    return True


def test_rgb_to_hex() -> bool:
    """Test RGB to HEX conversion."""
    print("Testing RGB to HEX conversion...")

    # Test standard colors
    assert UIElement._rgb_to_hex((255, 0, 0)) == "#FF0000", "Red failed"
    assert UIElement._rgb_to_hex((0, 255, 0)) == "#00FF00", "Green failed"
    assert UIElement._rgb_to_hex((0, 0, 255)) == "#0000FF", "Blue failed"
    assert UIElement._rgb_to_hex((0, 0, 0)) == "#000000", "Black failed"
    assert UIElement._rgb_to_hex((255, 255, 255)) == "#FFFFFF", "White failed"
    assert UIElement._rgb_to_hex((128, 128, 128)) == "#808080", "Gray failed"

    # Test clamping
    assert UIElement._rgb_to_hex((300, -10, 128)) == "#FF0080", "Clamping failed"

    print("  ✓ RGB to HEX conversion works")
    return True


def test_hex_to_rgb() -> bool:
    """Test HEX to RGB conversion."""
    print("Testing HEX to RGB conversion...")

    # Test standard colors
    assert UIElement._hex_to_rgb("#FF0000") == (255, 0, 0), "Red failed"
    assert UIElement._hex_to_rgb("#00FF00") == (0, 255, 0), "Green failed"
    assert UIElement._hex_to_rgb("#0000FF") == (0, 0, 255), "Blue failed"
    assert UIElement._hex_to_rgb("#000000") == (0, 0, 0), "Black failed"
    assert UIElement._hex_to_rgb("#FFFFFF") == (255, 255, 255), "White failed"
    assert UIElement._hex_to_rgb("#808080") == (128, 128, 128), "Gray failed"

    # Test without # prefix
    assert UIElement._hex_to_rgb("FF0000") == (255, 0, 0), "No prefix failed"

    # Test invalid hex
    assert UIElement._hex_to_rgb("invalid") == (0, 0, 0), "Invalid should return black"
    assert UIElement._hex_to_rgb("#GGGGGG") == (0, 0, 0), "Invalid chars should return black"

    print("  ✓ HEX to RGB conversion works")
    return True


def test_color_consistency() -> bool:
    """Test RGB/HEX consistency in UIElement."""
    print("Testing RGB/HEX consistency...")

    # Create with RGB, check HEX
    elem1 = UIElement(
        id="test1",
        name="Test",
        element_type="test",
        category="test",
        color_rgb=(128, 64, 32),
        color_hex="",
        x=0,
        y=0,
        width=10,
        height=10,
        confidence=1.0,
        source="test"
    )
    assert elem1.color_hex == "#804020", f"HEX mismatch: {elem1.color_hex}"

    # Create with HEX, check RGB
    elem2 = UIElement(
        id="test2",
        name="Test",
        element_type="test",
        category="test",
        color_rgb=(0, 0, 0),
        color_hex="#804020",
        x=0,
        y=0,
        width=10,
        height=10,
        confidence=1.0,
        source="test"
    )
    assert elem2.color_rgb == (128, 64, 32), f"RGB mismatch: {elem2.color_rgb}"

    print("  ✓ RGB/HEX consistency works")
    return True


def test_to_dict() -> bool:
    """Test to_dict serialization."""
    print("Testing to_dict serialization...")

    elem = UIElement(
        id="test-001",
        name="Test Element",
        element_type="button",
        category="controls",
        color_rgb=(255, 128, 64),
        color_hex="#FF8040",
        x=100,
        y=200,
        width=150,
        height=50,
        confidence=0.95,
        source="test"
    )

    data = elem.to_dict()

    assert data["id"] == "test-001", "ID mismatch"
    assert data["name"] == "Test Element", "Name mismatch"
    assert data["element_type"] == "button", "Type mismatch"
    assert data["category"] == "controls", "Category mismatch"
    assert data["color_rgb"] == [255, 128, 64], "RGB mismatch"
    assert data["color_hex"] == "#FF8040", "HEX mismatch"
    assert data["x"] == 100, "X mismatch"
    assert data["y"] == 200, "Y mismatch"
    assert data["width"] == 150, "Width mismatch"
    assert data["height"] == 50, "Height mismatch"
    assert data["confidence"] == 0.95, "Confidence mismatch"
    assert data["source"] == "test", "Source mismatch"

    print("  ✓ to_dict serialization works")
    return True


def test_from_dict() -> bool:
    """Test from_dict deserialization."""
    print("Testing from_dict deserialization...")

    data = {
        "id": "test-001",
        "name": "Test Element",
        "element_type": "button",
        "category": "controls",
        "color_rgb": [255, 128, 64],
        "color_hex": "#FF8040",
        "x": 100,
        "y": 200,
        "width": 150,
        "height": 50,
        "confidence": 0.95,
        "source": "test"
    }

    elem = UIElement.from_dict(data)

    assert elem.id == "test-001", "ID mismatch"
    assert elem.name == "Test Element", "Name mismatch"
    assert elem.element_type == "button", "Type mismatch"
    assert elem.category == "controls", "Category mismatch"
    assert elem.color_rgb == (255, 128, 64), "RGB mismatch"
    assert elem.color_hex == "#FF8040", "HEX mismatch"
    assert elem.x == 100, "X mismatch"
    assert elem.y == 200, "Y mismatch"
    assert elem.width == 150, "Width mismatch"
    assert elem.height == 50, "Height mismatch"
    assert elem.confidence == 0.95, "Confidence mismatch"
    assert elem.source == "test", "Source mismatch"

    print("  ✓ from_dict deserialization works")
    return True


def test_roundtrip() -> bool:
    """Test to_dict/from_dict roundtrip."""
    print("Testing roundtrip serialization...")

    original = UIElement(
        id="test-001",
        name="Test Element",
        element_type="button",
        category="controls",
        color_rgb=(255, 128, 64),
        color_hex="#FF8040",
        x=100,
        y=200,
        width=150,
        height=50,
        confidence=0.95,
        source="test"
    )

    data = original.to_dict()
    restored = UIElement.from_dict(data)

    assert restored.id == original.id, "ID mismatch"
    assert restored.name == original.name, "Name mismatch"
    assert restored.element_type == original.element_type, "Type mismatch"
    assert restored.category == original.category, "Category mismatch"
    assert restored.color_rgb == original.color_rgb, "RGB mismatch"
    assert restored.color_hex == original.color_hex, "HEX mismatch"
    assert restored.x == original.x, "X mismatch"
    assert restored.y == original.y, "Y mismatch"
    assert restored.width == original.width, "Width mismatch"
    assert restored.height == original.height, "Height mismatch"
    assert restored.confidence == original.confidence, "Confidence mismatch"
    assert restored.source == original.source, "Source mismatch"

    print("  ✓ Roundtrip serialization works")
    return True


def test_equality() -> bool:
    """Test element equality based on ID."""
    print("Testing element equality...")

    elem1 = UIElement(
        id="test-001",
        name="First",
        element_type="button",
        category="controls",
        color_rgb=(255, 0, 0),
        color_hex="#FF0000",
        x=0,
        y=0,
        width=10,
        height=10,
        confidence=1.0,
        source="test"
    )

    elem2 = UIElement(
        id="test-001",
        name="Second",
        element_type="label",
        category="text",
        color_rgb=(0, 255, 0),
        color_hex="#00FF00",
        x=100,
        y=100,
        width=20,
        height=20,
        confidence=0.5,
        source="test"
    )

    elem3 = UIElement(
        id="test-002",
        name="Third",
        element_type="button",
        category="controls",
        color_rgb=(255, 0, 0),
        color_hex="#FF0000",
        x=0,
        y=0,
        width=10,
        height=10,
        confidence=1.0,
        source="test"
    )

    # Same ID should be equal
    assert elem1 == elem2, "Elements with same ID should be equal"

    # Different ID should not be equal
    assert elem1 != elem3, "Elements with different ID should not be equal"

    # Hash should be based on ID
    assert hash(elem1) == hash(elem2), "Hash should be based on ID"

    print("  ✓ Element equality works")
    return True


def test_validation() -> bool:
    """Test input validation."""
    print("Testing validation...")

    # Test negative coordinates
    elem = UIElement(
        id="test",
        name="Test",
        element_type="test",
        category="test",
        color_rgb=(0, 0, 0),
        color_hex="#000000",
        x=-100,
        y=-50,
        width=-10,
        height=-5,
        confidence=1.5,
        source="test"
    )

    assert elem.x >= 0, "X should be clamped to >= 0"
    assert elem.y >= 0, "Y should be clamped to >= 0"
    assert elem.width >= 1, "Width should be clamped to >= 1"
    assert elem.height >= 1, "Height should be clamped to >= 1"
    assert elem.confidence <= 1.0, "Confidence should be clamped to <= 1.0"
    assert elem.confidence >= 0.0, "Confidence should be clamped to >= 0.0"

    print("  ✓ Validation works")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("UI2Code Model Tests")
    print("=" * 60)

    tests = [
        test_ui_element_creation,
        test_ui_element_defaults,
        test_rgb_to_hex,
        test_hex_to_rgb,
        test_color_consistency,
        test_to_dict,
        test_from_dict,
        test_roundtrip,
        test_equality,
        test_validation,
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
