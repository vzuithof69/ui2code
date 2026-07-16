"""UI2Code Fase 3B Tests.

Deterministic tests for multi-pass detection, hierarchy, JSON schema, and more.
"""

import sys
import os
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set headless platform
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Check Qt availability
_QT_AVAILABLE = False
try:
    from PySide6.QtGui import QImage
    _QT_AVAILABLE = True
except ImportError:
    pass


def create_test_image(width: int, height: int, color: tuple = (255, 255, 255)) -> "QImage":
    """Create a test image programmatically.
    
    Args:
        width: Image width.
        height: Image height.
        color: Background color as RGB tuple.
    
    Returns:
        QImage instance.
    """
    if not _QT_AVAILABLE:
        return None
    
    from PySide6.QtGui import QImage, QColor
    from PySide6.QtCore import Qt
    
    image = QImage(width, height, QImage.Format_RGB32)
    image.fill(QColor(*color))
    
    # Draw some test rectangles
    from PySide6.QtGui import QPainter
    painter = QPainter(image)
    painter.setPen(QColor(0, 0, 0))
    painter.setBrush(Qt.NoBrush)
    
    # Draw a few test rectangles
    painter.drawRect(10, 10, 100, 30)  # Button-like
    painter.drawRect(10, 50, 200, 20)  # Input-like
    painter.drawRect(50, 100, 150, 100)  # Panel-like
    
    painter.end()
    
    return image


def test_iou_calculation():
    """Test Intersection over Union calculation."""
    print("Testing IoU calculation...")
    
    from engine.models import UIElement
    
    # Create two overlapping elements
    elem1 = UIElement(
        id="e1", name="e1", element_type="unknown", category="general",
        color_rgb=(0, 0, 0), color_hex="#000000",
        x=0, y=0, width=100, height=100, confidence=0.8, source="test"
    )
    
    elem2 = UIElement(
        id="e2", name="e2", element_type="unknown", category="general",
        color_rgb=(0, 0, 0), color_hex="#000000",
        x=50, y=50, width=100, height=100, confidence=0.8, source="test"
    )
    
    # Overlap: 50x50 = 2500
    # Union: 10000 + 10000 - 2500 = 17500
    # IoU: 2500 / 17500 = 0.143
    from engine.ui2code_detect_v2 import UI2CodeDetect
    detector = UI2CodeDetect()
    
    iou = detector._calculate_iou(elem1, elem2)
    
    assert 0.14 < iou < 0.15, f"IoU incorrect: {iou}"
    print("  ✓ IoU calculation works")
    return True


def test_overlap_filtering():
    """Test duplicate removal using IoU."""
    print("Testing overlap filtering...")
    
    from engine.models import UIElement
    from engine.ui2code_detect_v2 import UI2CodeDetect
    
    detector = UI2CodeDetect()
    
    # Create overlapping elements
    elem1 = UIElement(
        id="e1", name="e1", element_type="unknown", category="general",
        color_rgb=(0, 0, 0), color_hex="#000000",
        x=0, y=0, width=100, height=100, confidence=0.9, source="test"
    )
    
    elem2 = UIElement(
        id="e2", name="e2", element_type="unknown", category="general",
        color_rgb=(0, 0, 0), color_hex="#000000",
        x=5, y=5, width=100, height=100, confidence=0.7, source="test"
    )
    
    # High overlap - should remove elem2
    filtered = detector._remove_duplicates_iou([elem1, elem2], threshold=0.5)
    
    assert len(filtered) == 1, f"Should remove duplicate, got {len(filtered)}"
    assert filtered[0].id == "e1", "Should keep higher confidence element"
    
    print("  ✓ Overlap filtering works")
    return True


def test_confidence_in_range():
    """Test that confidence scores are between 0.0 and 1.0."""
    print("Testing confidence in range...")
    
    from engine.models import UIElement
    
    # Test various confidence values
    test_values = [0.0, 0.5, 1.0, 1.5, -0.1, 0.999]
    
    for conf in test_values:
        elem = UIElement(
            id="test", name="test", element_type="unknown", category="general",
            color_rgb=(0, 0, 0), color_hex="#000000",
            x=0, y=0, width=10, height=10, confidence=conf, source="test"
        )
        assert 0.0 <= elem.confidence <= 1.0, f"Confidence {conf} out of range after normalization"
    
    print("  ✓ Confidence always in 0.0-1.0 range")
    return True


def test_parent_child_hierarchy():
    """Test parent-child relationship building."""
    print("Testing parent-child hierarchy...")
    
    from engine.models import UIElement
    from engine.ui2code_detect_v2 import UI2CodeDetect
    
    detector = UI2CodeDetect()
    
    # Create parent and child elements
    parent = UIElement(
        id="parent", name="Panel", element_type="panel", category="containers",
        color_rgb=(200, 200, 200), color_hex="#C8C8C8",
        x=0, y=0, width=300, height=200, confidence=0.8, source="test"
    )
    
    child = UIElement(
        id="child", name="Button", element_type="button", category="controls",
        color_rgb=(100, 100, 255), color_hex="#6464FF",
        x=50, y=50, width=100, height=30, confidence=0.85, source="test"
    )
    
    # Test containment
    assert detector._contains(parent, child), "Parent should contain child"
    
    # Build hierarchy
    elements = [child, parent]
    hierarchical = detector._build_hierarchy(elements)
    
    child_elem = next(e for e in hierarchical if e.id == "child")
    assert child_elem.parent_id == "parent", f"Child should have parent_id, got {child_elem.parent_id}"
    
    print("  ✓ Parent-child hierarchy works")
    return True


def test_no_hierarchy_cycles():
    """Test that hierarchy has no cycles."""
    print("Testing no hierarchy cycles...")
    
    from engine.models import UIElement
    from engine.ui2code_detect_v2 import UI2CodeDetect
    
    detector = UI2CodeDetect()
    
    # Create nested elements
    outer = UIElement(
        id="outer", name="Outer", element_type="panel", category="containers",
        color_rgb=(200, 200, 200), color_hex="#C8C8C8",
        x=0, y=0, width=500, height=400, confidence=0.8, source="test"
    )
    
    middle = UIElement(
        id="middle", name="Middle", element_type="panel", category="containers",
        color_rgb=(180, 180, 180), color_hex="#B4B4B4",
        x=50, y=50, width=300, height=200, confidence=0.8, source="test"
    )
    
    inner = UIElement(
        id="inner", name="Inner", element_type="button", category="controls",
        color_rgb=(100, 100, 255), color_hex="#6464FF",
        x=100, y=100, width=100, height=30, confidence=0.85, source="test"
    )
    
    elements = [inner, middle, outer]
    hierarchical = detector._build_hierarchy(elements)
    
    # Check no cycles: follow parent chain
    for elem in hierarchical:
        visited = set()
        current = elem
        while current.parent_id:
            if current.parent_id in visited:
                raise AssertionError(f"Cycle detected involving {current.id}")
            visited.add(current.parent_id)
            current = next((e for e in hierarchical if e.id == current.parent_id), None)
            if current is None:
                break
    
    print("  ✓ No hierarchy cycles")
    return True


def test_json_serialization():
    """Test JSON serialization and deserialization."""
    print("Testing JSON serialization...")
    
    from engine.models import UIElement
    from engine.schema_v1 import UI2CodeSchema
    
    # Create schema with elements
    schema = UI2CodeSchema()
    schema.create(
        image_path="/test/image.png",
        image_width=800,
        image_height=600,
        detection_config={"min_width": 5}
    )
    
    elem = UIElement(
        id="test-001",
        name="TestButton",
        element_type="button",
        category="controls",
        color_rgb=(255, 128, 64),
        color_hex="#FF8040",
        x=100,
        y=200,
        width=150,
        height=50,
        confidence=0.92,
        source="test",
        parent_id="parent-001",
        manually_corrected={"name", "type"},
        text_candidate=None
    )
    
    schema.add_element(elem)
    
    # Serialize
    json_str = schema.to_json()
    assert "test-001" in json_str
    assert "TestButton" in json_str
    
    # Deserialize
    schema2 = UI2CodeSchema.from_json(json_str)
    
    assert len(schema2.elements) == 1
    restored_elem = schema2.elements[0]
    
    assert restored_elem.id == "test-001"
    assert restored_elem.name == "TestButton"
    assert restored_elem.parent_id == "parent-001"
    assert "name" in restored_elem.manually_corrected
    
    print("  ✓ JSON serialization/deserialization works")
    return True


def test_schema_version():
    """Test that schema includes version information."""
    print("Testing schema version...")
    
    from engine.schema_v1 import UI2CodeSchema, SCHEMA_VERSION
    
    schema = UI2CodeSchema()
    schema.create("/test.png", 100, 100)
    
    data = schema.to_dict()
    
    assert "schema_version" in data
    assert data["schema_version"] == SCHEMA_VERSION
    assert "engine_version" in data
    
    print("  ✓ Schema version present")
    return True


def test_element_classification():
    """Test element classification heuristics."""
    print("Testing element classification...")
    
    from engine.models import UIElement
    from engine.ui2code_detect_v2 import UI2CodeDetect
    
    detector = UI2CodeDetect()
    
    # Test separator (thin horizontal)
    separator = UIElement(
        id="sep", name="Sep", element_type="unknown", category="general",
        color_rgb=(0, 0, 0), color_hex="#000000",
        x=0, y=0, width=200, height=2, confidence=0.8, source="test"
    )
    
    classified_type = detector._classify_element(separator, [])
    assert classified_type == "separator", f"Expected separator, got {classified_type}"
    
    # Test button (small square-ish)
    button = UIElement(
        id="btn", name="Btn", element_type="unknown", category="general",
        color_rgb=(100, 100, 255), color_hex="#6464FF",
        x=0, y=0, width=60, height=50, confidence=0.8, source="test"
    )
    
    classified_type = detector._classify_element(button, [])
    assert classified_type == "button", f"Expected button, got {classified_type}"
    
    # Test input (wide, short)
    input_elem = UIElement(
        id="inp", name="Input", element_type="unknown", category="general",
        color_rgb=(255, 255, 255), color_hex="#FFFFFF",
        x=0, y=0, width=200, height=30, confidence=0.8, source="test"
    )
    
    classified_type = detector._classify_element(input_elem, [])
    assert classified_type == "input", f"Expected input, got {classified_type}"
    
    print("  ✓ Element classification works")
    return True


def test_manual_corrections_preserved():
    """Test that manual corrections are tracked."""
    print("Testing manual corrections preservation...")
    
    from engine.models import UIElement
    
    elem = UIElement(
        id="test", name="Original", element_type="unknown", category="general",
        color_rgb=(0, 0, 0), color_hex="#000000",
        x=0, y=0, width=10, height=10, confidence=0.8, source="test"
    )
    
    # Simulate manual correction
    elem.manually_corrected.add("name")
    elem.name = "ManuallyCorrected"
    
    # Serialize and deserialize
    data = elem.to_dict()
    restored = UIElement.from_dict(data)
    
    assert "name" in restored.manually_corrected
    assert restored.name == "ManuallyCorrected"
    
    print("  ✓ Manual corrections preserved")
    return True


def test_background_filtering():
    """Test that background-sized elements are filtered."""
    print("Testing background filtering...")
    
    from engine.models import UIElement
    from engine.ui2code_detect_v2 import UI2CodeDetect
    
    detector = UI2CodeDetect(config={"max_coverage_ratio": 0.95})
    
    # Create background-sized element
    background = UIElement(
        id="bg", name="Background", element_type="unknown", category="general",
        color_rgb=(255, 255, 255), color_hex="#FFFFFF",
        x=0, y=0, width=1000, height=1000, confidence=0.8, source="test"
    )
    
    image_width, image_height = 1000, 1000
    
    # Filter
    filtered = detector._fuse_results([background], image_width, image_height)
    
    # Background should be filtered out
    assert len(filtered) == 0, f"Background should be filtered, got {len(filtered)} elements"
    
    print("  ✓ Background filtering works")
    return True


def test_nested_elements_preserved():
    """Test that nested elements are preserved after fusion."""
    print("Testing nested elements preservation...")
    
    from engine.models import UIElement
    from engine.ui2code_detect_v2 import UI2CodeDetect
    
    detector = UI2CodeDetect()
    
    # Create parent and child
    parent = UIElement(
        id="parent", name="Parent", element_type="panel", category="containers",
        color_rgb=(200, 200, 200), color_hex="#C8C8C8",
        x=0, y=0, width=300, height=200, confidence=0.8, source="test"
    )
    
    child = UIElement(
        id="child", name="Child", element_type="button", category="controls",
        color_rgb=(100, 100, 255), color_hex="#6464FF",
        x=50, y=50, width=100, height=30, confidence=0.85, source="test"
    )
    
    # Fuse (should preserve both)
    fused = detector._fuse_results([parent, child], 500, 500)
    
    assert len(fused) == 2, f"Should preserve nested elements, got {len(fused)}"
    
    print("  ✓ Nested elements preserved")
    return True


def run_all_tests():
    """Run all Fase 3B tests.
    
    Returns:
        True if all tests passed.
    """
    print("=" * 60)
    print("UI2Code Fase 3B Tests")
    print("=" * 60)
    print()
    
    tests = [
        test_iou_calculation,
        test_overlap_filtering,
        test_confidence_in_range,
        test_parent_child_hierarchy,
        test_no_hierarchy_cycles,
        test_json_serialization,
        test_schema_version,
        test_element_classification,
        test_manual_corrections_preserved,
        test_background_filtering,
        test_nested_elements_preserved,
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test in tests:
        try:
            print()
            if _QT_AVAILABLE or test.__name__ not in [
                'test_color_plane_detection',
                'test_line_detection',
                'test_connected_components',
                'test_text_zone_detection'
            ]:
                if test():
                    passed += 1
                else:
                    failed += 1
            else:
                print(f"  ⚠ Skipping {test.__name__} (requires Qt)")
                skipped += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
