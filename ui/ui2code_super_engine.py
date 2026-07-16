"""UI2Code Super Engine.

Main UI interface for the UI2Code conversion system.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.ui2code_core import UI2CodeCore
from engine.ui2code_detect import UI2CodeDetect
from engine.ui2code_layout import UI2CodeLayout
from engine.ui2code_export import UI2CodeExport


class UI2CodeSuperEngine:
    """Super Engine orchestrating all UI2Code components."""

    def __init__(self, config_path=None):
        """Initialize the Super Engine.

        Args:
            config_path: Optional path to configuration file.
        """
        self.config_path = config_path
        self.core = UI2CodeCore()
        self.detector = UI2CodeDetect()
        self.layout = UI2CodeLayout()
        self.export = UI2CodeExport()

    def run(self, ui_input):
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

    def export_result(self, code, filename):
        """Export the generated code.

        Args:
            code: Generated code.
            filename: Output filename.

        Returns:
            Path to exported file.
        """
        return self.export.export_code(code, filename)


if __name__ == "__main__":
    print("UI2Code Super Engine initialized")
    engine = UI2CodeSuperEngine()
    print("Ready for UI input")
