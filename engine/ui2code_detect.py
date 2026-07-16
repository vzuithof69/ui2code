"""UI2Code Detection Module.

Module for detecting UI elements and components.
"""

import os
from typing import List, Optional, Any

try:
    from PySide6.QtGui import QImage, QColor
    from PySide6.QtCore import Qt
    _QT_AVAILABLE = True
except ImportError:
    _QT_AVAILABLE = False
    QImage = None  # type: ignore
    QColor = None  # type: ignore

from engine.models import UIElement


class UI2CodeDetect:
    """Detection engine for UI elements."""

    # Minimum element size to filter noise
    MIN_WIDTH = 4
    MIN_HEIGHT = 4

    # Minimum area to filter noise
    MIN_AREA = 16

    # Maximum coverage to filter full-background rectangles
    MAX_COVERAGE_RATIO = 0.95

    def __init__(self) -> None:
        """Initialize the detection engine."""
        self.detectors = []

    def detect_elements(
        self,
        image_data: Any,
        image_path: Optional[str] = None
    ) -> List[UIElement]:
        """Detect UI elements from image data.

        Args:
            image_data: Image data to analyze (QImage, numpy array, or file path).
            image_path: Optional path to image file.

        Returns:
            List of detected UI elements.

        Raises:
            ValueError: If image data is invalid or missing.
            FileNotFoundError: If image file does not exist.
        """
        if not _QT_AVAILABLE:
            raise ImportError(
                "Qt libraries not available. Install PySide6 for detection."
            )

        # Load image from various sources
        image = self._load_image(image_data, image_path)

        if image is None:
            raise ValueError("Failed to load image data")

        # Perform contour-based detection
        elements = self._detect_contours(image)

        # Filter and clean up results
        elements = self._filter_elements(elements, image.width(), image.height())
        elements = self._remove_duplicates(elements)

        return elements

    def _load_image(
        self,
        image_data: Any,
        image_path: Optional[str] = None
    ) -> Optional["QImage"]:
        """Load image from various sources.

        Args:
            image_data: Image data (QImage, path, or None).
            image_path: Optional path to image file.

        Returns:
            QImage or None if loading failed.
        """
        if image_data is None and image_path is None:
            raise ValueError("No image data or path provided")

        # If already a QImage
        if isinstance(image_data, QImage):
            return image_data

        # If image_data is a path string
        if isinstance(image_data, str):
            if os.path.exists(image_data):
                return QImage(image_data)
            raise FileNotFoundError(f"Image file not found: {image_data}")

        # If image_path is provided
        if image_path is not None:
            if os.path.exists(image_path):
                return QImage(image_path)
            raise FileNotFoundError(f"Image file not found: {image_path}")

        return None

    def _detect_contours(self, image: "QImage") -> List[UIElement]:
        """Detect UI elements using contour detection.

        Uses a simple edge-based approach to find rectangular regions
        that likely represent UI elements.

        Args:
            image: QImage to analyze.

        Returns:
            List of detected UI elements.
        """
        elements: List[UIElement] = []

        # Convert to grayscale manually (simple average method)
        width = image.width()
        height = image.height()

        # Create grayscale buffer
        gray = [[0] * width for _ in range(height)]

        for y in range(height):
            for x in range(width):
                pixel = image.pixel(x, y)
                color = QColor(pixel)
                # Simple grayscale conversion
                gray[y][x] = int((color.red() + color.green() + color.blue()) / 3)

        # Find edges using simple gradient detection
        edges = self._find_edges(gray, width, height)

        # Find connected components / rectangular regions
        regions = self._find_rectangular_regions(edges, width, height)

        # Create UI elements from regions
        for idx, region in enumerate(regions):
            x, y, w, h = region

            # Get dominant color from the region
            color_rgb = self._get_region_color(image, x, y, w, h)
            color_hex = UIElement._rgb_to_hex(color_rgb)

            element = UIElement(
                id=f"elem_{idx:04d}",
                name=f"Element_{idx:04d}",
                element_type="unknown",
                category="general",
                color_rgb=color_rgb,
                color_hex=color_hex,
                x=x,
                y=y,
                width=w,
                height=h,
                confidence=0.8,  # Base confidence for contour detection
                source="contour"
            )
            elements.append(element)

        return elements

    def _find_edges(
        self,
        gray: List[List[int]],
        width: int,
        height: int,
        threshold: int = 30
    ) -> List[List[bool]]:
        """Find edges in grayscale image using gradient detection.

        Args:
            gray: 2D grayscale image data.
            width: Image width.
            height: Image height.
            threshold: Edge detection threshold.

        Returns:
            2D boolean array indicating edge pixels.
        """
        edges = [[False] * width for _ in range(height)]

        for y in range(1, height - 1):
            for x in range(1, width - 1):
                # Simple Sobel-like gradient
                gx = abs(gray[y][x + 1] - gray[y][x - 1])
                gy = abs(gray[y + 1][x] - gray[y - 1][x])
                gradient = gx + gy

                if gradient > threshold:
                    edges[y][x] = True

        return edges

    def _find_rectangular_regions(
        self,
        edges: List[List[bool]],
        width: int,
        height: int
    ) -> List[tuple]:
        """Find rectangular regions from edge map.

        Uses a simple scan-line approach to find connected regions
        and approximate them as rectangles.

        Args:
            edges: 2D boolean edge map.
            width: Image width.
            height: Image height.

        Returns:
            List of (x, y, w, h) tuples.
        """
        visited = [[False] * width for _ in range(height)]
        regions = []

        def flood_fill(start_x: int, start_y: int) -> Optional[tuple]:
            """Flood fill to find connected region bounds."""
            if visited[start_y][start_x]:
                return None

            min_x, min_y = start_x, start_y
            max_x, max_y = start_x, start_y

            stack = [(start_x, start_y)]
            visited[start_y][start_x] = True

            while stack:
                x, y = stack.pop()

                # Check 4-connected neighbors
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nx, ny = x + dx, y + dy

                    if 0 <= nx < width and 0 <= ny < height:
                        if not visited[ny][nx] and edges[ny][nx]:
                            visited[ny][nx] = True
                            stack.append((nx, ny))
                            min_x = min(min_x, nx)
                            max_x = max(max_x, nx)
                            min_y = min(min_y, ny)
                            max_y = max(max_y, ny)

            w = max_x - min_x + 1
            h = max_y - min_y + 1

            if w >= self.MIN_WIDTH and h >= self.MIN_HEIGHT:
                return (min_x, min_y, w, h)
            return None

        # Scan for edge pixels
        for y in range(height):
            for x in range(width):
                if edges[y][x] and not visited[y][x]:
                    region = flood_fill(x, y)
                    if region:
                        regions.append(region)

        return regions

    def _get_region_color(
        self,
        image: "QImage",
        x: int,
        y: int,
        width: int,
        height: int
    ) -> tuple:
        """Get average color of a region.

        Args:
            image: Source image.
            x: Region x coordinate.
            y: Region y coordinate.
            width: Region width.
            height: Region height.

        Returns:
            RGB tuple (R, G, B).
        """
        r_sum, g_sum, b_sum = 0, 0, 0
        count = 0

        for dy in range(y, min(y + height, image.height())):
            for dx in range(x, min(x + width, image.width())):
                pixel = image.pixel(dx, dy)
                color = QColor(pixel)
                r_sum += color.red()
                g_sum += color.green()
                b_sum += color.blue()
                count += 1

        if count > 0:
            return (r_sum // count, g_sum // count, b_sum // count)
        return (0, 0, 0)

    def _filter_elements(
        self,
        elements: List[UIElement],
        image_width: int,
        image_height: int
    ) -> List[UIElement]:
        """Filter out invalid or unwanted elements.

        Args:
            elements: List of detected elements.
            image_width: Image width.
            image_height: Image height.

        Returns:
            Filtered list of elements.
        """
        image_area = image_width * image_height
        filtered = []

        for elem in elements:
            elem_area = elem.width * elem.height

            # Filter too small elements
            if elem_area < self.MIN_AREA:
                continue

            # Filter elements that cover almost entire image (likely background)
            coverage = elem_area / image_area if image_area > 0 else 0
            if coverage > self.MAX_COVERAGE_RATIO:
                continue

            # Filter elements outside image bounds
            if elem.x + elem.width > image_width + 10:  # Small tolerance
                continue
            if elem.y + elem.height > image_height + 10:
                continue

            filtered.append(elem)

        return filtered

    def _remove_duplicates(
        self,
        elements: List[UIElement],
        overlap_threshold: float = 0.8
    ) -> List[UIElement]:
        """Remove duplicate or highly overlapping elements.

        Args:
            elements: List of elements.
            overlap_threshold: Overlap ratio threshold for removal.

        Returns:
            List with duplicates removed.
        """
        if not elements:
            return []

        # Sort by area (larger first) to keep bigger elements
        sorted_elements = sorted(
            elements,
            key=lambda e: e.width * e.height,
            reverse=True
        )

        result = []
        for elem in sorted_elements:
            is_duplicate = False

            for kept in result:
                overlap = self._calculate_overlap(elem, kept)
                smaller_area = min(
                    elem.width * elem.height,
                    kept.width * kept.height
                )

                if smaller_area > 0 and overlap / smaller_area > overlap_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                result.append(elem)

        return result

    def _calculate_overlap(
        self,
        elem1: UIElement,
        elem2: UIElement
    ) -> int:
        """Calculate overlap area between two elements.

        Args:
            elem1: First element.
            elem2: Second element.

        Returns:
            Overlap area in pixels.
        """
        # Calculate intersection rectangle
        x1 = max(elem1.x, elem2.x)
        y1 = max(elem1.y, elem2.y)
        x2 = min(elem1.x + elem1.width, elem2.x + elem2.width)
        y2 = min(elem1.y + elem1.height, elem2.y + elem2.height)

        if x1 < x2 and y1 < y2:
            return (x2 - x1) * (y2 - y1)
        return 0

    def classify_component(self, element: UIElement) -> Optional[str]:
        """Classify a UI element.

        Args:
            element: UI element to classify.

        Returns:
            Component type classification.
        """
        # Placeholder for future classification logic
        return None
