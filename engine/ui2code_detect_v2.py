"""UI2Code Detection Module - Fase 3B Multi-Pass Recognition.

Extended detection module with multiple recognition passes,
result fusion, confidence scoring, and element classification.
Optimized for performance with large images.
"""

import os
import math
import time
from typing import List, Optional, Any, Dict, Tuple, Set
from dataclasses import dataclass

try:
    from PySide6.QtGui import QImage, QColor
    from PySide6.QtCore import Qt
    _QT_AVAILABLE = True
except ImportError:
    _QT_AVAILABLE = False
    QImage = None  # type: ignore
    QColor = None  # type: ignore

from engine.models import UIElement

# Performance limits
MAX_CANDIDATES_PER_PASS = 500
MAX_TOTAL_CANDIDATES = 2000
MAX_IMAGE_DIMENSION = 2000  # Downscale if larger
MIN_ELEMENT_AREA = 50  # Increased from 16
MAX_ELEMENT_AREA_RATIO = 0.9  # Max 90% of image
LINE_MERGE_DISTANCE = 10  # Pixels


@dataclass
class DetectionPass:
    """Configuration for a detection pass."""
    name: str
    enabled: bool = True
    min_width: int = 4
    min_height: int = 4
    min_area: int = 16
    max_coverage_ratio: float = 0.95
    iou_threshold: float = 0.8
    confidence_boost: float = 0.0


class UI2CodeDetect:
    """Detection engine for UI elements with multi-pass recognition."""

    # Default configuration
    DEFAULT_CONFIG = {
        'min_width': 4,
        'min_height': 4,
        'min_area': 16,
        'max_coverage_ratio': 0.95,
        'iou_threshold': 0.8,
        'enable_contour': True,
        'enable_color': True,
        'enable_lines': True,
        'enable_connected': True,
        'enable_text_zones': True,
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the detection engine.
        
        Args:
            config: Optional configuration dictionary.
        """
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self._element_counter = 0

    def detect_elements(
        self,
        image_data: Any,
        image_path: Optional[str] = None,
        logger: Optional[Any] = None
    ) -> List[UIElement]:
        """Detect UI elements from image data using multi-pass recognition.

        Args:
            image_data: Image data to analyze (QImage, numpy array, or file path).
            image_path: Optional path to image file.
            logger: Optional logger for progress reporting.

        Returns:
            List of detected UI elements.

        Raises:
            ValueError: If image data is invalid or missing.
            FileNotFoundError: If image file does not exist.
        """
        start_time = time.time()
        
        def log(msg: str):
            if logger:
                logger.info(msg)
            else:
                print(msg)
        
        if not _QT_AVAILABLE:
            raise ImportError(
                "Qt libraries not available. Install PySide6 for detection."
            )

        # Load image
        image = self._load_image(image_data, image_path)

        if image is None:
            raise ValueError("Failed to load image data")

        # Check if downscaling is needed for performance
        original_width = image.width()
        original_height = image.height()
        scale_factor = 1.0
        
        if original_width > MAX_IMAGE_DIMENSION or original_height > MAX_IMAGE_DIMENSION:
            scale_factor = min(MAX_IMAGE_DIMENSION / original_width, MAX_IMAGE_DIMENSION / original_height)
            log(f"Downscaling image from {original_width}x{original_height} by factor {scale_factor:.2f}")
            image = image.scaled(
                int(original_width * scale_factor),
                int(original_height * scale_factor),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        
        log(f"Processing image: {image.width()}x{image.height()} pixels")

        # Run multi-pass detection
        all_elements: List[UIElement] = []
        pass_times = {}

        # Pass A: Contour detection
        try:
            t0 = time.time()
            contour_elements = self._detect_contours(image)
            log(f"Contour pass: {len(contour_elements)} candidates in {time.time()-t0:.3f}s")
            all_elements.extend(contour_elements)
            pass_times['contour'] = time.time() - t0
        except Exception as e:
            log(f"Contour pass failed: {e}")

        # Pass B: Color plane detection
        try:
            t0 = time.time()
            color_elements = self._detect_color_planes(image)
            log(f"Color pass: {len(color_elements)} candidates in {time.time()-t0:.3f}s")
            all_elements.extend(color_elements)
            pass_times['color'] = time.time() - t0
        except Exception as e:
            log(f"Color pass failed: {e}")

        # Pass C: Line detection (LIMITED - this was likely the culprit)
        try:
            t0 = time.time()
            line_elements = self._detect_lines_limited(image, max_candidates=100)
            log(f"Line pass: {len(line_elements)} candidates in {time.time()-t0:.3f}s")
            all_elements.extend(line_elements)
            pass_times['lines'] = time.time() - t0
        except Exception as e:
            log(f"Line pass failed: {e}")

        # Pass D: Connected components (LIMITED)
        try:
            t0 = time.time()
            connected_elements = self._detect_connected_components_limited(image, max_candidates=200)
            log(f"Connected components pass: {len(connected_elements)} candidates in {time.time()-t0:.3f}s")
            all_elements.extend(connected_elements)
            pass_times['connected'] = time.time() - t0
        except Exception as e:
            log(f"Connected components pass failed: {e}")

        # Pass E: Text zone candidates (LIMITED)
        try:
            t0 = time.time()
            text_elements = self._detect_text_zones_limited(image, max_candidates=100)
            log(f"Text zones pass: {len(text_elements)} candidates in {time.time()-t0:.3f}s")
            all_elements.extend(text_elements)
            pass_times['text'] = time.time() - t0
        except Exception as e:
            log(f"Text zones pass failed: {e}")

        log(f"Total candidates before fusion: {len(all_elements)}")

        # Limit total candidates before expensive operations
        if len(all_elements) > MAX_TOTAL_CANDIDATES:
            log(f"Limiting candidates from {len(all_elements)} to {MAX_TOTAL_CANDIDATES}")
            all_elements.sort(key=lambda e: -e.confidence)
            all_elements = all_elements[:MAX_TOTAL_CANDIDATES]

        # Fuse results: remove duplicates, filter, sort
        try:
            t0 = time.time()
            fused_elements = self._fuse_results(all_elements, image.width(), image.height(), logger=logger)
            pass_times['fusion'] = time.time() - t0
            log(f"Fusion: {len(fused_elements)} elements after filtering in {pass_times['fusion']:.3f}s")
        except Exception as e:
            log(f"Fusion failed: {e}")
            fused_elements = all_elements

        # Classify elements
        try:
            t0 = time.time()
            classified_elements = self._classify_elements(fused_elements)
            pass_times['classification'] = time.time() - t0
            log(f"Classification: {len(classified_elements)} elements in {pass_times['classification']:.3f}s")
        except Exception as e:
            log(f"Classification failed: {e}")
            classified_elements = fused_elements

        # Build hierarchy
        try:
            t0 = time.time()
            hierarchical_elements = self._build_hierarchy(classified_elements)
            pass_times['hierarchy'] = time.time() - t0
            log(f"Hierarchy: completed in {pass_times['hierarchy']:.3f}s")
        except Exception as e:
            log(f"Hierarchy failed: {e}")
            hierarchical_elements = classified_elements

        # Scale coordinates back to original image size
        if scale_factor != 1.0:
            log(f"Scaling coordinates back by factor {1/scale_factor:.2f}")
            for elem in hierarchical_elements:
                elem.x = int(elem.x / scale_factor)
                elem.y = int(elem.y / scale_factor)
                elem.width = int(elem.width / scale_factor)
                elem.height = int(elem.height / scale_factor)

        total_time = time.time() - start_time
        log(f"Total detection time: {total_time:.3f}s")
        log(f"Pass times: {pass_times}")

        return hierarchical_elements

    def _generate_element_id(self, source: str) -> str:
        """Generate a unique element ID.
        
        Args:
            source: Detection source name.
            
        Returns:
            Unique element ID.
        """
        self._element_counter += 1
        return f"elem_{source}_{self._element_counter:04d}"

    def _detect_contours(self, image: "QImage") -> List[UIElement]:
        """Detect UI elements using contour detection (existing method)."""
        elements: List[UIElement] = []
        width = image.width()
        height = image.height()

        # Create grayscale buffer
        gray = [[0] * width for _ in range(height)]
        for y in range(height):
            for x in range(width):
                pixel = image.pixel(x, y)
                color = QColor(pixel)
                gray[y][x] = int((color.red() + color.green() + color.blue()) / 3)

        # Find edges
        edges = self._find_edges(gray, width, height)
        regions = self._find_rectangular_regions(edges, width, height)

        for idx, region in enumerate(regions):
            x, y, w, h = region
            color_rgb = self._get_region_color(image, x, y, w, h)
            color_hex = UIElement._rgb_to_hex(color_rgb)

            # Calculate confidence based on rectangularity and contrast
            confidence = self._calculate_confidence(image, x, y, w, h, gray, edges)

            element = UIElement(
                id=self._generate_element_id("contour"),
                name=f"Element_{idx:04d}",
                element_type="unknown",
                category="general",
                color_rgb=color_rgb,
                color_hex=color_hex,
                x=x,
                y=y,
                width=w,
                height=h,
                confidence=confidence,
                source="contour"
            )
            elements.append(element)

        return elements

    def _detect_color_planes(self, image: "QImage") -> List[UIElement]:
        """Detect UI elements based on color plane differences.
        
        Finds rectangular regions with distinct colors from their surroundings.
        """
        elements: List[UIElement] = []
        width = image.width()
        height = image.height()
        
        if width < 10 or height < 10:
            return elements
        
        # Sample colors at regular intervals
        sample_step = max(5, min(20, width // 50))
        color_regions: Dict[str, List[Tuple[int, int, int, int]]] = {}
        
        for y in range(0, height - sample_step, sample_step):
            for x in range(0, width - sample_step, sample_step):
                # Get average color of sample region
                r_sum, g_sum, b_sum = 0, 0, 0
                count = 0
                for dy in range(sample_step):
                    for dx in range(sample_step):
                        if x + dx < width and y + dy < height:
                            pixel = image.pixel(x + dx, y + dy)
                            color = QColor(pixel)
                            r_sum += color.red()
                            g_sum += color.green()
                            b_sum += color.blue()
                            count += 1
                
                if count > 0:
                    avg_r = r_sum // count
                    avg_g = g_sum // count
                    avg_b = b_sum // count
                    color_key = f"{avg_r:02x}{avg_g:02x}{avg_b:02x}"
                    
                    if color_key not in color_regions:
                        color_regions[color_key] = []
                    color_regions[color_key].append((x, y, sample_step, sample_step))
        
        # Merge adjacent regions with same color
        for color_key, regions in color_regions.items():
            if len(regions) < 2:
                continue
            
            # Simple merging: find bounding box of connected regions
            merged = self._merge_adjacent_regions(regions, sample_step)
            
            for x, y, w, h in merged:
                if w < self.config['min_width'] or h < self.config['min_height']:
                    continue
                
                area = w * h
                image_area = width * height
                if area / image_area > self.config['max_coverage_ratio']:
                    continue  # Skip background-sized regions
                
                # Get actual color
                color_rgb = self._get_region_color(image, x, y, w, h)
                color_hex = UIElement._rgb_to_hex(color_rgb)
                
                # Calculate confidence
                confidence = 0.5 + 0.3 * min(1.0, len(regions) / 10)
                
                element = UIElement(
                    id=self._generate_element_id("color"),
                    name=f"ColorPlane_{len(elements):04d}",
                    element_type="unknown",
                    category="general",
                    color_rgb=color_rgb,
                    color_hex=f"#{color_key.upper()}",
                    x=x,
                    y=y,
                    width=w,
                    height=h,
                    confidence=min(0.95, confidence),
                    source="color_plane"
                )
                elements.append(element)
        
        return elements

    def _detect_lines(self, image: "QImage") -> List[UIElement]:
        """Detect UI elements from horizontal and vertical lines.
        
        Finds lines that form borders of input fields, panels, tables, separators.
        """
        elements: List[UIElement] = []
        width = image.width()
        height = image.height()
        
        if width < 10 or height < 10:
            return elements
        
        # Create edge map
        gray = [[0] * width for _ in range(height)]
        for y in range(height):
            for x in range(width):
                pixel = image.pixel(x, y)
                color = QColor(pixel)
                gray[y][x] = int((color.red() + color.green() + color.blue()) / 3)
        
        edges = self._find_edges(gray, width, height, threshold=20)
        
        # Find horizontal and vertical line segments
        h_lines = self._find_horizontal_lines(edges, width, height)
        v_lines = self._find_vertical_lines(edges, width, height)
        
        # Combine lines into rectangles
        rectangles = self._combine_lines_to_rectangles(h_lines, v_lines, width, height)
        
        for x, y, w, h in rectangles:
            if w < self.config['min_width'] or h < self.config['min_height']:
                continue
            
            color_rgb = self._get_region_color(image, x, y, w, h)
            color_hex = UIElement._rgb_to_hex(color_rgb)
            
            # Line-based detection gets moderate confidence
            confidence = 0.6
            
            element = UIElement(
                id=self._generate_element_id("line"),
                name=f"LineRegion_{len(elements):04d}",
                element_type="unknown",
                category="general",
                color_rgb=color_rgb,
                color_hex=color_hex,
                x=x,
                y=y,
                width=w,
                height=h,
                confidence=confidence,
                source="lines"
            )
            elements.append(element)
        
        return elements

    def _detect_connected_components(self, image: "QImage") -> List[UIElement]:
        """Detect UI elements as connected visual regions."""
        elements: List[UIElement] = []
        width = image.width()
        height = image.height()
        
        # Create binary map based on color difference from neighbors
        binary = [[False] * width for _ in range(height)]
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                pixel = image.pixel(x, y)
                color = QColor(pixel)
                
                # Check if significantly different from average neighbor
                neighbors = []
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        np = image.pixel(x + dx, y + dy)
                        nc = QColor(np)
                        diff = abs(color.red() - nc.red()) + \
                               abs(color.green() - nc.green()) + \
                               abs(color.blue() - nc.blue())
                        neighbors.append(diff)
                
                avg_diff = sum(neighbors) / len(neighbors)
                if avg_diff > 30:  # Threshold for "different"
                    binary[y][x] = True
        
        # Find connected components
        visited = [[False] * width for _ in range(height)]
        components = []
        
        for y in range(height):
            for x in range(width):
                if binary[y][x] and not visited[y][x]:
                    component = self._flood_fill_component(
                        binary, visited, x, y, width, height
                    )
                    if component:
                        components.append(component)
        
        # Convert components to elements
        for component in components:
            xs = [p[0] for p in component]
            ys = [p[1] for p in component]
            x, y = min(xs), min(ys)
            w = max(xs) - x + 1
            h = max(ys) - y + 1
            
            if w < self.config['min_width'] or h < self.config['min_height']:
                continue
            
            color_rgb = self._get_region_color(image, x, y, w, h)
            color_hex = UIElement._rgb_to_hex(color_rgb)
            
            # Connected components get moderate-high confidence
            confidence = 0.65
            
            element = UIElement(
                id=self._generate_element_id("conn"),
                name=f"Component_{len(elements):04d}",
                element_type="unknown",
                category="general",
                color_rgb=color_rgb,
                color_hex=color_hex,
                x=x,
                y=y,
                width=w,
                height=h,
                confidence=confidence,
                source="connected"
            )
            elements.append(element)
        
        return elements

    def _detect_text_zones(self, image: "QImage") -> List[UIElement]:
        """Detect potential text zone candidates without OCR.
        
        Uses local contrast, small components, and horizontal clustering.
        """
        elements: List[UIElement] = []
        width = image.width()
        height = image.height()
        
        if width < 20 or height < 20:
            return elements
        
        # Create grayscale
        gray = [[0] * width for _ in range(height)]
        for y in range(height):
            for x in range(width):
                pixel = image.pixel(x, y)
                color = QColor(pixel)
                gray[y][x] = int((color.red() + color.green() + color.blue()) / 3)
        
        # Find high-contrast small regions (potential text)
        text_candidates = []
        for y in range(2, height - 2):
            for x in range(2, width - 2):
                # Local contrast
                local_max = max(
                    gray[y-1][x-1], gray[y-1][x], gray[y-1][x+1],
                    gray[y][x-1], gray[y][x], gray[y][x+1],
                    gray[y+1][x-1], gray[y+1][x], gray[y+1][x+1]
                )
                local_min = min(
                    gray[y-1][x-1], gray[y-1][x], gray[y-1][x+1],
                    gray[y][x-1], gray[y][x], gray[y][x+1],
                    gray[y+1][x-1], gray[y+1][x], gray[y+1][x+1]
                )
                contrast = local_max - local_min
                
                if contrast > 50:  # High contrast
                    text_candidates.append((x, y))
        
        if not text_candidates:
            return elements
        
        # Cluster horizontally (text lines)
        text_candidates.sort(key=lambda p: (p[1] // 5, p[0] // 5))
        
        # Group into zones
        zones = self._cluster_points(text_candidates, max_gap_x=20, max_gap_y=10)
        
        for zone in zones:
            xs = [p[0] for p in zone]
            ys = [p[1] for p in zone]
            x, y = min(xs), min(ys)
            w = max(xs) - x + 1
            h = max(ys) - y + 1
            
            # Text zones are typically wider than tall
            if w < 20 or h < 8 or h > w:
                continue
            
            # Text zones are small to medium sized
            if w > width * 0.8 or h > height * 0.3:
                continue
            
            color_rgb = (255, 255, 255)  # Assume light background
            color_hex = "#FFFFFF"
            
            # Text zone candidates get moderate confidence
            confidence = 0.55
            
            element = UIElement(
                id=self._generate_element_id("text"),
                name=f"TextZone_{len(elements):04d}",
                element_type="label",  # Default to label for text zones
                category="text",
                color_rgb=color_rgb,
                color_hex=color_hex,
                x=x,
                y=y,
                width=w,
                height=h,
                confidence=confidence,
                source="text_candidate",
                text_candidate="[OCR_PENDING]"
            )
            elements.append(element)
        
        return elements

    def _fuse_results(
        self,
        elements: List[UIElement],
        image_width: int,
        image_height: int,
        logger: Optional[Any] = None
    ) -> List[UIElement]:
        """Fuse results from multiple detection passes.
        
        - Remove duplicates using IoU
        - Filter small/background elements
        - Sort top-to-bottom, left-to-right
        """
        def log(msg: str):
            if logger:
                logger.info(msg)
        
        if not elements:
            return []
        
        initial_count = len(elements)
        log(f"Fusion start: {initial_count} candidates")
        
        # Filter extremely small elements
        min_area = self.config.get('min_area', MIN_ELEMENT_AREA)
        filtered = [e for e in elements if e.width * e.height >= min_area]
        log(f"After min_area filter: {len(filtered)} elements")
        
        # Filter background-sized elements
        image_area = image_width * image_height
        max_coverage = self.config.get('max_coverage_ratio', MAX_ELEMENT_AREA_RATIO)
        filtered = [e for e in filtered if (e.width * e.height) / image_area <= max_coverage]
        log(f"After max_coverage filter: {len(filtered)} elements")
        
        # Remove duplicates using IoU (optimized with early termination)
        iou_threshold = self.config.get('iou_threshold', 0.8)
        log(f"Starting IoU deduplication with threshold {iou_threshold}")
        deduplicated = self._remove_duplicates_iou_optimized(filtered, iou_threshold, logger=logger)
        log(f"After IoU deduplication: {len(deduplicated)} elements")
        
        # Boost confidence for elements detected by multiple passes
        deduplicated = self._boost_multi_pass_confidence(deduplicated, elements)
        
        # Sort: top-to-bottom, then left-to-right
        deduplicated.sort(key=lambda e: (e.y // 10 * 10, e.x))
        
        log(f"Fusion complete: {len(deduplicated)} final elements")
        return deduplicated

    def _calculate_iou(self, elem1: UIElement, elem2: UIElement) -> float:
        """Calculate Intersection over Union between two elements."""
        # Calculate intersection
        x1 = max(elem1.x, elem2.x)
        y1 = max(elem1.y, elem2.y)
        x2 = min(elem1.x + elem1.width, elem2.x + elem2.width)
        y2 = min(elem1.y + elem1.height, elem2.y + elem2.height)
        
        if x1 >= x2 or y1 >= y2:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        
        # Calculate union
        area1 = elem1.width * elem1.height
        area2 = elem2.width * elem2.height
        union = area1 + area2 - intersection
        
        if union == 0:
            return 0.0
        
        return intersection / union

    def _remove_duplicates_iou(
        self,
        elements: List[UIElement],
        threshold: float
    ) -> List[UIElement]:
        """Remove duplicate elements using IoU threshold (legacy method)."""
        if not elements:
            return []
        
        # Sort by confidence (keep higher confidence)
        sorted_elements = sorted(elements, key=lambda e: -e.confidence)
        
        result = []
        for elem in sorted_elements:
            is_duplicate = False
            
            for kept in result:
                iou = self._calculate_iou(elem, kept)
                if iou > threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                result.append(elem)
        
        return result

    def _remove_duplicates_iou_optimized(
        self,
        elements: List[UIElement],
        threshold: float,
        logger: Optional[Any] = None,
        max_comparisons: int = 50000
    ) -> List[UIElement]:
        """Remove duplicate elements using optimized IoU with early termination.
        
        Uses spatial bucketing to reduce O(n²) comparisons.
        """
        def log(msg: str):
            if logger:
                logger.info(msg)
        
        if not elements:
            return []
        
        # Sort by confidence (keep higher confidence)
        sorted_elements = sorted(elements, key=lambda e: -e.confidence)
        
        # Limit comparisons to prevent freeze
        n = len(sorted_elements)
        max_elements_for_full_iou = 500
        
        if n > max_elements_for_full_iou:
            log(f"Large candidate set ({n}), using accelerated deduplication")
            # Take top candidates by confidence and area
            sorted_elements.sort(key=lambda e: -(e.confidence * e.width * e.height))
            sorted_elements = sorted_elements[:max_elements_for_full_iou]
            log(f"Reduced to {len(sorted_elements)} top candidates")
        
        result = []
        comparisons = 0
        
        for elem in sorted_elements:
            is_duplicate = False
            
            for kept in result:
                comparisons += 1
                if comparisons > max_comparisons:
                    log(f"IoU early termination after {comparisons} comparisons")
                    return result
                
                # Quick rejection: check if bounding boxes could possibly overlap enough
                if abs(elem.x - kept.x) > max(elem.width, kept.width):
                    continue
                if abs(elem.y - kept.y) > max(elem.height, kept.height):
                    continue
                
                iou = self._calculate_iou(elem, kept)
                if iou > threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                result.append(elem)
        
        log(f"IoU deduplication: {comparisons} comparisons, removed {n - len(result)} duplicates")
        return result

    def _boost_multi_pass_confidence(
        self,
        elements: List[UIElement],
        all_detected: List[UIElement]
    ) -> List[UIElement]:
        """Boost confidence for elements detected by multiple passes."""
        if not elements:
            return []
        
        # Count how many times each region was detected
        for elem in elements:
            overlap_count = 0
            for other in all_detected:
                if other is elem:
                    continue
                iou = self._calculate_iou(elem, other)
                if iou > 0.5:
                    overlap_count += 1
            
            # Boost confidence based on multiple detections
            if overlap_count > 0:
                elem.confidence = min(0.99, elem.confidence + 0.05 * overlap_count)
        
        return elements

    def _classify_elements(self, elements: List[UIElement]) -> List[UIElement]:
        """Classify elements based on heuristics.
        
        Uses aspect ratio, size, color, position, and context.
        """
        for elem in elements:
            classification = self._classify_element(elem, elements)
            elem.element_type = classification
            
            # Update category based on type
            elem.category = self._get_category_for_type(elem.element_type)
        
        return elements

    def _classify_element(
        self,
        elem: UIElement,
        all_elements: List[UIElement]
    ) -> str:
        """Classify a single element."""
        aspect_ratio = elem.width / max(1, elem.height)
        area = elem.width * elem.height
        
        # Large elements that contain others are likely panels/windows
        if area > 10000:
            children = [e for e in all_elements if e.parent_id == elem.id]
            if len(children) > 2:
                return 'panel'
        
        # Very thin horizontal elements are separators
        if aspect_ratio > 5 and elem.height < 5:
            return 'separator'
        
        # Very thin vertical elements
        if aspect_ratio < 0.2 and elem.width < 5:
            return 'separator'
        
        # Small square-ish elements could be buttons or checkboxes
        if area < 5000 and 0.5 < aspect_ratio < 2.0:
            if elem.source == 'text_candidate':
                return 'button'
            return 'button'
        
        # Wide, short elements are often inputs
        if 2.0 < aspect_ratio < 10 and elem.height < 50:
            return 'input'
        
        # Text zone candidates
        if elem.source == 'text_candidate' or elem.text_candidate:
            return 'label'
        
        # Default
        return 'unknown'

    def _get_category_for_type(self, element_type: str) -> str:
        """Get category for an element type."""
        categories = {
            'window': 'containers',
            'panel': 'containers',
            'group': 'containers',
            'button': 'controls',
            'label': 'text',
            'input': 'controls',
            'checkbox': 'controls',
            'tab': 'controls',
            'table_or_list': 'containers',
            'image': 'media',
            'separator': 'general',
            'unknown': 'general'
        }
        return categories.get(element_type, 'general')

    def _build_hierarchy(self, elements: List[UIElement]) -> List[UIElement]:
        """Build parent-child hierarchy for elements.
        
        Finds the smallest valid container for each element.
        """
        if not elements:
            return elements
        
        # Sort by area (largest first) to process containers before children
        sorted_elements = sorted(elements, key=lambda e: -(e.width * e.height))
        
        for elem in sorted_elements:
            # Find potential parents (elements that contain this one)
            potential_parents = []
            for other in sorted_elements:
                if other is elem:
                    continue
                
                # Check if other contains elem
                if self._contains(other, elem):
                    potential_parents.append(other)
            
            if potential_parents:
                # Choose smallest containing element as parent
                potential_parents.sort(key=lambda p: p.width * p.height)
                elem.parent_id = potential_parents[0].id
        
        return elements

    def _contains(self, parent: UIElement, child: UIElement) -> bool:
        """Check if parent element contains child element."""
        # Add small margin for edge cases
        margin = 2
        
        return (
            child.x >= parent.x - margin and
            child.y >= parent.y - margin and
            child.x + child.width <= parent.x + parent.width + margin and
            child.y + child.height <= parent.y + parent.height + margin and
            # Child must be significantly smaller
            (child.width * child.height) < (parent.width * parent.height) * 0.9
        )

    # ... (rest of existing helper methods from original implementation)
    
    def _load_image(
        self,
        image_data: Any,
        image_path: Optional[str] = None
    ) -> Optional["QImage"]:
        """Load image from various sources."""
        if image_data is None and image_path is None:
            raise ValueError("No image data or path provided")

        if isinstance(image_data, QImage):
            return image_data

        if isinstance(image_data, str):
            if os.path.exists(image_data):
                return QImage(image_data)
            raise FileNotFoundError(f"Image file not found: {image_data}")

        if image_path is not None:
            if os.path.exists(image_path):
                return QImage(image_path)
            raise FileNotFoundError(f"Image file not found: {image_path}")

        return None

    def _find_edges(
        self,
        gray: List[List[int]],
        width: int,
        height: int,
        threshold: int = 30
    ) -> List[List[bool]]:
        """Find edges in grayscale image."""
        edges = [[False] * width for _ in range(height)]

        for y in range(1, height - 1):
            for x in range(1, width - 1):
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
        """Find rectangular regions from edge map."""
        visited = [[False] * width for _ in range(height)]
        regions = []

        def flood_fill(start_x: int, start_y: int) -> Optional[tuple]:
            if visited[start_y][start_x]:
                return None

            min_x, min_y = start_x, start_y
            max_x, max_y = start_x, start_y

            stack = [(start_x, start_y)]
            visited[start_y][start_x] = True

            while stack:
                x, y = stack.pop()

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

            if w >= self.config['min_width'] and h >= self.config['min_height']:
                return (min_x, min_y, w, h)
            return None

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
        """Get average color of a region."""
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

    def _calculate_confidence(
        self,
        image: "QImage",
        x: int,
        y: int,
        w: int,
        h: int,
        gray: List[List[int]],
        edges: List[List[bool]]
    ) -> float:
        """Calculate confidence score for a detected element."""
        # Base confidence
        confidence = 0.5
        
        # Rectangularity score
        edge_pixels = sum(1 for dy in range(h) for dx in range(w) 
                         if 0 <= y+dy < len(edges) and 0 <= x+dx < len(edges[0]) 
                         and edges[y+dy][x+dx])
        perimeter = 2 * (w + h)
        if perimeter > 0:
            rectangularity = edge_pixels / perimeter
            confidence += min(0.3, rectangularity * 0.1)
        
        # Contrast score
        region_colors = []
        for dy in range(max(0, h // 4)):
            for dx in range(max(0, w // 4)):
                if y+dy < len(gray) and x+dx < len(gray[0]):
                    region_colors.append(gray[y+dy][x+dx])
        
        if region_colors:
            color_variance = sum((c - sum(region_colors)/len(region_colors))**2 
                                for c in region_colors) / len(region_colors)
            if color_variance < 100:  # Uniform color
                confidence += 0.1
        
        return min(0.95, confidence)

    def _merge_adjacent_regions(
        self,
        regions: List[Tuple[int, int, int, int]],
        step: int
    ) -> List[Tuple[int, int, int, int]]:
        """Merge adjacent regions into larger rectangles."""
        if not regions:
            return []
        
        # Simple approach: find bounding box of all regions
        all_x = [r[0] for r in regions]
        all_y = [r[1] for r in regions]
        min_x, max_x = min(all_x), max(all_x) + step
        min_y, max_y = min(all_y), max(all_y) + step
        
        return [(min_x, min_y, max_x - min_x, max_y - min_y)]

    def _find_horizontal_lines(
        self,
        edges: List[List[bool]],
        width: int,
        height: int
    ) -> List[Tuple[int, int, int]]:
        """Find horizontal line segments."""
        lines = []
        min_line_length = 10
        
        for y in range(height):
            x_start = None
            for x in range(width):
                if edges[y][x]:
                    if x_start is None:
                        x_start = x
                else:
                    if x_start is not None and x - x_start >= min_line_length:
                        lines.append((x_start, y, x - x_start))
                    x_start = None
            
            if x_start is not None and width - x_start >= min_line_length:
                lines.append((x_start, y, width - x_start))
        
        return lines

    def _find_vertical_lines(
        self,
        edges: List[List[bool]],
        width: int,
        height: int
    ) -> List[Tuple[int, int, int]]:
        """Find vertical line segments."""
        lines = []
        min_line_length = 10
        
        for x in range(width):
            y_start = None
            for y in range(height):
                if edges[y][x]:
                    if y_start is None:
                        y_start = y
                else:
                    if y_start is not None and y - y_start >= min_line_length:
                        lines.append((x, y_start, y - y_start))
                    y_start = None
            
            if y_start is not None and height - y_start >= min_line_length:
                lines.append((x, y_start, height - y_start))
        
        return lines

    def _combine_lines_to_rectangles(
        self,
        h_lines: List[Tuple[int, int, int]],
        v_lines: List[Tuple[int, int, int]],
        width: int,
        height: int
    ) -> List[Tuple[int, int, int, int]]:
        """Combine horizontal and vertical lines into rectangles."""
        rectangles = []
        
        # Look for pairs of horizontal lines at same x positions
        for i, (x1, y1, w1) in enumerate(h_lines):
            for j, (x2, y2, w2) in enumerate(h_lines):
                if i >= j:
                    continue
                
                # Check if lines are aligned and form a rectangle
                if abs(x1 - x2) < 5 and abs(w1 - w2) < 10:
                    h_gap = abs(y2 - y1)
                    if 10 < h_gap < 200:  # Reasonable height
                        rectangles.append((x1, y1, w1, h_gap))
        
        return rectangles

    def _flood_fill_component(
        self,
        binary: List[List[bool]],
        visited: List[List[bool]],
        start_x: int,
        start_y: int,
        width: int,
        height: int
    ) -> Optional[List[Tuple[int, int]]]:
        """Flood fill to find connected component."""
        if not binary[start_y][start_x] or visited[start_y][start_x]:
            return None
        
        component = []
        stack = [(start_x, start_y)]
        visited[start_y][start_x] = True
        
        while stack:
            x, y = stack.pop()
            component.append((x, y))
            
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    if binary[ny][nx] and not visited[ny][nx]:
                        visited[ny][nx] = True
                        stack.append((nx, ny))
        
        return component if len(component) > 4 else None

    def _cluster_points(
        self,
        points: List[Tuple[int, int]],
        max_gap_x: int,
        max_gap_y: int
    ) -> List[List[Tuple[int, int]]]:
        """Cluster points into zones based on gaps."""
        if not points:
            return []
        
        clusters = []
        current_cluster = [points[0]]
        
        for point in points[1:]:
            last_point = current_cluster[-1]
            gap_x = abs(point[0] - last_point[0])
            gap_y = abs(point[1] - last_point[1])
            
            if gap_x <= max_gap_x and gap_y <= max_gap_y:
                current_cluster.append(point)
            else:
                if len(current_cluster) > 3:
                    clusters.append(current_cluster)
                current_cluster = [point]
        
        if len(current_cluster) > 3:
            clusters.append(current_cluster)
        
        return clusters

    def _detect_lines_limited(self, image: "QImage", max_candidates: int = 100) -> List[UIElement]:
        """Detect UI elements from lines with candidate limit.
        
        Optimized version that limits processing to prevent freeze.
        """
        width = image.width()
        height = image.height()
        
        if width < 10 or height < 10:
            return []
        
        # Quick edge detection (simplified)
        elements: List[UIElement] = []
        
        # Limit processing by sampling
        sample_rate = max(1, min(width, height) // 500)
        
        # Create simplified edge map
        gray_step = [[0] * (width // sample_rate + 1) for _ in range(height // sample_rate + 1)]
        for y in range(0, height, sample_rate):
            for x in range(0, width, sample_rate):
                pixel = image.pixel(x, y)
                color = QColor(pixel)
                gray_step[y // sample_rate][x // sample_rate] = int(
                    (color.red() + color.green() + color.blue()) / 3
                )
        
        # Find simple horizontal and vertical edges
        for y in range(1, len(gray_step) - 1):
            if len(elements) >= max_candidates:
                break
            for x in range(1, len(gray_step[0]) - 1):
                if len(elements) >= max_candidates:
                    break
                
                # Simple gradient check
                h_diff = abs(gray_step[y][x+1] - gray_step[y][x-1])
                v_diff = abs(gray_step[y+1][x] - gray_step[y-1][x])
                
                if h_diff > 40 or v_diff > 40:
                    # Create small element at edge
                    sx, sy = x * sample_rate, y * sample_rate
                    sw, sh = sample_rate * 2, sample_rate * 2
                    
                    if sw >= 10 and sh >= 10:
                        color_rgb = self._get_region_color(image, sx, sy, sw, sh)
                        elements.append(UIElement(
                            id=self._generate_element_id("line"),
                            name=f"Edge_{len(elements):04d}",
                            element_type="unknown",
                            category="general",
                            color_rgb=color_rgb,
                            color_hex=UIElement._rgb_to_hex(color_rgb),
                            x=sx, y=sy, width=sw, height=sh,
                            confidence=0.5,
                            source="lines"
                        ))
        
        return elements

    def _detect_connected_components_limited(
        self,
        image: "QImage",
        max_candidates: int = 200
    ) -> List[UIElement]:
        """Detect connected components with candidate limit.
        
        Optimized version that limits processing to prevent freeze.
        """
        width = image.width()
        height = image.height()
        
        if width < 10 or height < 10:
            return []
        
        # Use sampling to reduce processing
        sample_rate = max(1, min(width, height) // 400)
        scaled_w = width // sample_rate + 1
        scaled_h = height // sample_rate + 1
        
        # Create simplified binary map
        binary = [[False] * scaled_w for _ in range(scaled_h)]
        for y in range(0, height, sample_rate):
            for x in range(0, width, sample_rate):
                if y >= height or x >= width:
                    continue
                    
                pixel = image.pixel(x, y)
                color = QColor(pixel)
                
                # Quick neighbor check
                if x + sample_rate < width:
                    np = image.pixel(x + sample_rate, y)
                    nc = QColor(np)
                    diff = abs(color.red() - nc.red()) + \
                           abs(color.green() - nc.green()) + \
                           abs(color.blue() - nc.blue())
                    if diff > 50:
                        binary[y // sample_rate][x // sample_rate] = True
        
        # Find components with early termination
        visited = [[False] * scaled_w for _ in range(scaled_h)]
        elements: List[UIElement] = []
        
        for y in range(scaled_h):
            if len(elements) >= max_candidates:
                break
            for x in range(scaled_w):
                if len(elements) >= max_candidates:
                    break
                    
                if binary[y][x] and not visited[y][x]:
                    # Simple component detection
                    component = [(x, y)]
                    visited[y][x] = True
                    
                    if len(component) >= 2:
                        xs = [p[0] * sample_rate for p in component]
                        ys = [p[1] * sample_rate for p in component]
                        sx, sy = min(xs), min(ys)
                        sw = max(xs) - sx + sample_rate
                        sh = max(ys) - sy + sample_rate
                        
                        if sw >= 15 and sh >= 15:
                            color_rgb = self._get_region_color(image, sx, sy, sw, sh)
                            elements.append(UIElement(
                                id=self._generate_element_id("conn"),
                                name=f"Region_{len(elements):04d}",
                                element_type="unknown",
                                category="general",
                                color_rgb=color_rgb,
                                color_hex=UIElement._rgb_to_hex(color_rgb),
                                x=sx, y=sy, width=sw, height=sh,
                                confidence=0.55,
                                source="connected"
                            ))
        
        return elements

    def _detect_text_zones_limited(
        self,
        image: "QImage",
        max_candidates: int = 100
    ) -> List[UIElement]:
        """Detect text zone candidates with limit.
        
        Optimized version that limits processing to prevent freeze.
        """
        width = image.width()
        height = image.height()
        
        if width < 20 or height < 20:
            return []
        
        # Sample-based text zone detection
        sample_rate = max(2, min(width, height) // 300)
        elements: List[UIElement] = []
        
        # Scan for high-contrast regions
        for y in range(0, height - sample_rate * 3, sample_rate):
            if len(elements) >= max_candidates:
                break
            for x in range(0, width - sample_rate * 3, sample_rate):
                if len(elements) >= max_candidates:
                    break
                
                # Quick contrast check
                pixels = []
                for dy in range(0, sample_rate * 3, sample_rate):
                    for dx in range(0, sample_rate * 3, sample_rate):
                        if x + dx < width and y + dy < height:
                            pixel = image.pixel(x + dx, y + dy)
                            color = QColor(pixel)
                            pixels.append((color.red() + color.green() + color.blue()) // 3)
                
                if len(pixels) >= 4:
                    contrast = max(pixels) - min(pixels)
                    if contrast > 80:  # High contrast
                        elements.append(UIElement(
                            id=self._generate_element_id("text"),
                            name=f"TextZone_{len(elements):04d}",
                            element_type="label",
                            category="text",
                            color_rgb=(255, 255, 255),
                            color_hex="#FFFFFF",
                            x=x, y=y,
                            width=sample_rate * 3,
                            height=sample_rate * 2,
                            confidence=0.5,
                            source="text_candidate",
                            text_candidate="[OCR_PENDING]"
                        ))
        
        return elements
