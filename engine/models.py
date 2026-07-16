"""UI2Code Data Models.

Data models for UI elements and related structures.
"""

import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


@dataclass
class UIElement:
    """Data class representing a detected UI element.

    Attributes:
        id: Unique identifier for the element.
        name: Human-readable name for the element.
        element_type: Type of UI element (button, label, input, etc.).
        category: Category classification (controls, containers, etc.).
        color_rgb: RGB color tuple (R, G, B).
        color_hex: Hex color string (#RRGGBB).
        x: X coordinate of top-left corner.
        y: Y coordinate of top-left corner.
        width: Width of the element.
        height: Height of the element.
        confidence: Detection confidence (0.0 to 1.0).
        source: Source of detection (e.g., 'contour', 'manual').
    """

    id: str
    name: str
    element_type: str
    category: str
    color_rgb: Tuple[int, int, int]
    color_hex: str
    x: int
    y: int
    width: int
    height: int
    confidence: float
    source: str = "unknown"

    def __post_init__(self) -> None:
        """Validate and normalize the element data."""
        # Validate ID
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

        # Validate and normalize name
        if not self.name:
            self.name = f"Element_{self.id[:4]}"

        # Validate element_type
        if not self.element_type:
            self.element_type = "unknown"

        # Validate category
        if not self.category:
            self.category = "general"

        # Validate source
        if not self.source:
            self.source = "unknown"

        # Validate and normalize color
        # If color_hex is provided but color_rgb is (0,0,0), try to derive RGB from HEX
        if self.color_rgb == (0, 0, 0) and self.color_hex and self.color_hex != "#000000":
            self.color_rgb = self._hex_to_rgb(self.color_hex)
        
        self.color_rgb = self._normalize_rgb(self.color_rgb)
        self.color_hex = self._rgb_to_hex(self.color_rgb)

        # Validate coordinates and dimensions
        self.x = max(0, int(self.x))
        self.y = max(0, int(self.y))
        self.width = max(1, int(self.width))
        self.height = max(1, int(self.height))

        # Validate confidence
        self.confidence = max(0.0, min(1.0, float(self.confidence)))

    @staticmethod
    def _normalize_rgb(color: Any) -> Tuple[int, int, int]:
        """Normalize color to RGB tuple.

        Args:
            color: Color value (tuple, list, or hex string).

        Returns:
            Normalized RGB tuple (R, G, B) with values 0-255.
        """
        if isinstance(color, str):
            # Try to parse hex string
            return UIElement._hex_to_rgb(color)
        elif isinstance(color, (tuple, list)):
            if len(color) >= 3:
                return (
                    max(0, min(255, int(color[0]))),
                    max(0, min(255, int(color[1]))),
                    max(0, min(255, int(color[2])))
                )
        return (0, 0, 0)

    @staticmethod
    def _rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex string.

        Args:
            rgb: RGB tuple (R, G, B).

        Returns:
            Hex string (#RRGGBB).
        """
        r = max(0, min(255, int(rgb[0])))
        g = max(0, min(255, int(rgb[1])))
        b = max(0, min(255, int(rgb[2])))
        return f"#{r:02X}{g:02X}{b:02X}"

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex string to RGB tuple.

        Args:
            hex_color: Hex color string (#RRGGBB or RRGGBB).

        Returns:
            RGB tuple (R, G, B).
        """
        hex_color = hex_color.strip()
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]

        # Validate hex string
        if not re.match(r'^[0-9A-Fa-f]{6}$', hex_color):
            return (0, 0, 0)

        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return (r, g, b)
        except ValueError:
            return (0, 0, 0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert element to dictionary.

        Returns:
            Dictionary representation of the element.
        """
        return {
            "id": self.id,
            "name": self.name,
            "element_type": self.element_type,
            "category": self.category,
            "color_rgb": list(self.color_rgb),
            "color_hex": self.color_hex,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "confidence": self.confidence,
            "source": self.source
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UIElement":
        """Create element from dictionary.

        Args:
            data: Dictionary containing element data.

        Returns:
            UIElement instance.
        """
        # Handle color_rgb - convert list to tuple if needed
        color_rgb = data.get("color_rgb", (0, 0, 0))
        if isinstance(color_rgb, list):
            color_rgb = tuple(color_rgb)

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            element_type=data.get("element_type", ""),
            category=data.get("category", ""),
            color_rgb=color_rgb,
            color_hex=data.get("color_hex", ""),
            x=data.get("x", 0),
            y=data.get("y", 0),
            width=data.get("width", 0),
            height=data.get("height", 0),
            confidence=data.get("confidence", 0.0),
            source=data.get("source", "unknown")
        )

    def __eq__(self, other: Any) -> bool:
        """Check equality with another element.

        Args:
            other: Another object to compare.

        Returns:
            True if objects are equal.
        """
        if not isinstance(other, UIElement):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Get hash based on ID.

        Returns:
            Hash value.
        """
        return hash(self.id)
