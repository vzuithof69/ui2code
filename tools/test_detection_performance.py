#!/usr/bin/env python3
"""Command-line test for detection performance.

Tests detection on programmatically created images including 2105x1391.
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtGui import QImage, QColor, QPainter, QPen, Qt
from engine.ui2code_detect_v2 import UI2CodeDetect as UI2CodeDetectV2


def create_test_image(width: int, height: int) -> QImage:
    """Create a test image with UI-like elements.
    
    Args:
        width: Image width.
        height: Image height.
    
    Returns:
        QImage with test content.
    """
    print(f"Creating test image {width}x{height}...")
    
    # Create white background
    image = QImage(width, height, QImage.Format_RGB32)
    image.fill(QColor(240, 240, 240))
    
    # Draw some UI-like elements
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Panel
    painter.setPen(QPen(QColor(100, 100, 100), 2))
    painter.setBrush(QColor(255, 255, 255))
    painter.drawRect(50, 50, 400, 300)
    
    # Buttons
    painter.setBrush(QColor(200, 200, 255))
    painter.drawRect(80, 280, 100, 40)
    painter.drawRect(200, 280, 100, 40)
    
    # Input field
    painter.setBrush(QColor(255, 255, 255))
    painter.drawRect(80, 100, 300, 30)
    
    # Labels (text-like regions)
    painter.setPen(QPen(QColor(0, 0, 0), 1))
    for i in range(5):
        y = 150 + i * 25
        painter.drawText(80, y, f"Label {i+1}")
    
    # Separator lines
    painter.drawLine(50, 200, 450, 200)
    
    painter.end()
    
    print(f"Test image created: {width}x{height}")
    return image


def test_detection(width: int, height: int, timeout: float = 30.0) -> bool:
    """Test detection on an image of given size.
    
    Args:
        width: Image width.
        height: Image height.
        timeout: Maximum allowed time in seconds.
    
    Returns:
        True if test completed within timeout.
    """
    print(f"\n{'='*60}")
    print(f"TEST: Detection on {width}x{height} image")
    print(f"Timeout: {timeout}s")
    print(f"{'='*60}\n")
    
    # Create test image
    image = create_test_image(width, height)
    
    # Save to temp file
    temp_path = f"/tmp/test_{width}x{height}.png"
    image.save(temp_path)
    print(f"Saved test image to: {temp_path}\n")
    
    # Run detection
    detector = UI2CodeDetectV2()
    
    class TestLogger:
        def info(self, msg):
            print(f"[LOG] {msg}", flush=True)
        def warning(self, msg):
            print(f"[WARN] {msg}", flush=True)
        def error(self, msg):
            print(f"[ERROR] {msg}", flush=True)
    
    logger = TestLogger()
    
    print("Starting detection...\n")
    start = time.perf_counter()
    
    try:
        elements = detector.detect_elements(
            image_data=temp_path,
            logger=logger
        )
        
        elapsed = time.perf_counter() - start
        
        print(f"\n{'='*60}")
        print(f"RESULT: SUCCESS")
        print(f"Elements detected: {len(elements)}")
        print(f"Total time: {elapsed:.3f}s")
        print(f"Timeout: {timeout}s")
        print(f"Within timeout: {elapsed < timeout}")
        print(f"{'='*60}\n")
        
        # Print element summary
        by_type = {}
        for elem in elements:
            by_type[elem.element_type] = by_type.get(elem.element_type, 0) + 1
        
        print("Element types:")
        for etype, count in sorted(by_type.items()):
            print(f"  {etype}: {count}")
        print()
        
        return elapsed < timeout
        
    except Exception as e:
        elapsed = time.perf_counter() - start
        print(f"\n{'='*60}")
        print(f"RESULT: FAILED")
        print(f"Error: {e}")
        print(f"Time before error: {elapsed:.3f}s")
        print(f"{'='*60}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all performance tests."""
    print("="*60)
    print("UI2Code Detection Performance Tests")
    print("="*60)
    print()
    
    # Test sizes
    test_cases = [
        (800, 600, 10.0),      # Small
        (1920, 1080, 20.0),    # Full HD
        (2105, 1391, 30.0),    # Windows test case
    ]
    
    results = []
    
    for width, height, timeout in test_cases:
        success = test_detection(width, height, timeout)
        results.append((width, height, timeout, success))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for width, height, timeout, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {width}x{height} (timeout {timeout}s)")
    
    all_passed = all(r[3] for r in results)
    
    print()
    if all_passed:
        print("All tests PASSED!")
        return 0
    else:
        print("Some tests FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
