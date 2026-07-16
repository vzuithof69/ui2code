"""UI2Code Import Test.

Test script to verify all module imports work correctly.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_imports():
    """Test all module imports."""
    print("Testing UI2Code module imports...")
    print("-" * 40)

    try:
        print("Importing engine.ui2code_core...")
        from engine.ui2code_core import UI2CodeCore
        print("  ✓ UI2CodeCore imported successfully")

        print("Importing engine.ui2code_detect...")
        from engine.ui2code_detect import UI2CodeDetect
        print("  ✓ UI2CodeDetect imported successfully")

        print("Importing engine.ui2code_layout...")
        from engine.ui2code_layout import UI2CodeLayout
        print("  ✓ UI2CodeLayout imported successfully")

        print("Importing engine.ui2code_export...")
        from engine.ui2code_export import UI2CodeExport
        print("  ✓ UI2CodeExport imported successfully")

        print("Importing ui.ui2code_super_engine...")
        # Note: UI import requires Qt libraries, skip in headless environments
        try:
            from ui.ui2code_super_engine import UI2CodeSuperEngine
            print("  ✓ UI2CodeSuperEngine imported successfully")
            ui_available = True
        except ImportError as ui_err:
            print(f"  ⚠ UI2CodeSuperEngine skipped (Qt libraries not available): {ui_err}")
            ui_available = False

        print("-" * 40)
        print("All imports successful!")
        print("-" * 40)

        # Test instantiation
        print("\nTesting class instantiation...")
        core = UI2CodeCore()
        print("  ✓ UI2CodeCore instantiated")

        detector = UI2CodeDetect()
        print("  ✓ UI2CodeDetect instantiated")

        layout = UI2CodeLayout()
        print("  ✓ UI2CodeLayout instantiated")

        export = UI2CodeExport()
        print("  ✓ UI2CodeExport instantiated")

        if ui_available:
            super_engine = UI2CodeSuperEngine()
            print("  ✓ UI2CodeSuperEngine instantiated")
        else:
            print("  ⚠ UI2CodeSuperEngine instantiation skipped")

        print("-" * 40)
        print("All tests passed!")
        return True

    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
