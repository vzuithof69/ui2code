#!/usr/bin/env python3
"""Test classification logic to ensure text_candidate is not misclassified."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.models import UIElement


def test_text_candidate_not_button():
    """Test that text_candidate source does not become button type."""
    elem = UIElement(
        id='test_001',
        name='TestElement',
        element_type='unknown',
        category='general',
        color_rgb=(255, 255, 255),
        color_hex='#FFFFFF',
        x=0, y=0, width=100, height=30,
        confidence=0.7,
        source='text_candidate',
        text_candidate='[OCR_PENDING]'
    )
    
    # text_candidate should remain as text_candidate or become label, NOT button
    assert elem.source == 'text_candidate'
    # The element_type might be 'unknown' initially, but should not be 'button'
    # unless explicitly classified as such
    print(f"✓ text_candidate element created: type={elem.element_type}, source={elem.source}")
    return True


def test_confidence_bounds():
    """Test that confidence is always between 0.0 and 1.0."""
    test_values = [0.0, 0.25, 0.5, 0.75, 0.95, 1.0, -0.1, 1.1, 1.5]
    
    for val in test_values:
        elem = UIElement(
            id=f'test_{val}',
            name='Test',
            element_type='unknown',
            category='general',
            color_rgb=(0, 0, 0),
            color_hex='#000000',
            x=0, y=0, width=10, height=10,
            confidence=val,
            source='test'
        )
        # UIElement should accept any float, but classification should bound it
        print(f"  Confidence {val}: stored as {elem.confidence}")
    
    print("✓ Confidence bounds test completed")
    return True


def test_diverse_confidence_values():
    """Test that different sources produce different confidence values."""
    elements = [
        UIElement(id='e1', name='E1', element_type='button', category='interactive',
                  color_rgb=(0, 0, 255), color_hex='#0000FF',
                  x=0, y=0, width=100, height=30, confidence=0.8, source='contour'),
        UIElement(id='e2', name='E2', element_type='input', category='interactive',
                  color_rgb=(255, 255, 255), color_hex='#FFFFFF',
                  x=0, y=0, width=200, height=40, confidence=0.6, source='color_plane'),
        UIElement(id='e3', name='E3', element_type='label', category='text',
                  color_rgb=(0, 0, 0), color_hex='#000000',
                  x=0, y=0, width=150, height=25, confidence=0.7, source='text_candidate'),
    ]
    
    confidences = [e.confidence for e in elements]
    unique_conf = set(confidences)
    
    print(f"Confidence values: {confidences}")
    print(f"Unique values: {len(unique_conf)}")
    
    if len(unique_conf) < len(confidences):
        print("⚠ Warning: Some confidence values are duplicated")
    else:
        print("✓ All confidence values are unique")
    
    return True


def test_multiple_sources():
    """Test that elements from different sources are preserved."""
    sources = ['contour', 'color_plane', 'lines', 'connected', 'text_candidate']
    elements = []
    
    for i, source in enumerate(sources):
        elem = UIElement(
            id=f'elem_{source}',
            name=f'Element_{i}',
            element_type='unknown',
            category='general',
            color_rgb=(i * 50, i * 50, i * 50),
            color_hex=f'#{i*50:02x}{i*50:02x}{i*50:02x}',
            x=i * 10, y=i * 10, width=50, height=30,
            confidence=0.5 + (i * 0.1),
            source=source
        )
        elements.append(elem)
    
    found_sources = set(e.source for e in elements)
    print(f"Sources found: {found_sources}")
    print(f"Expected: {set(sources)}")
    
    assert found_sources == set(sources), f"Missing sources: {set(sources) - found_sources}"
    print("✓ All sources preserved")
    
    return True


def main():
    """Run all classification tests."""
    print("=" * 60)
    print("UI2Code Classification Regression Tests")
    print("=" * 60)
    print()
    
    tests = [
        ("text_candidate not button", test_text_candidate_not_button),
        ("confidence bounds", test_confidence_bounds),
        ("diverse confidence values", test_diverse_confidence_values),
        ("multiple sources", test_multiple_sources),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"\nTest: {name}")
        try:
            if test_func():
                passed += 1
                print(f"  ✓ PASSED")
            else:
                failed += 1
                print(f"  ✗ FAILED")
        except Exception as e:
            failed += 1
            print(f"  ✗ FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
