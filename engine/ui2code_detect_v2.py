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
        import sys
        start_time = time.time()
        
        def log(msg: str):
            if logger:
                logger.info(msg)
            else:
                print(msg, flush=True)
            # Force flush
            sys.stdout.flush()
            sys.stderr.flush()
        
        if not _QT_AVAILABLE:
            raise ImportError(
                "Qt libraries not available. Install PySide6 for detection."
            )

        # Load image
        log("DETECT_START: Loading image...")
        image = self._load_image(image_data, image_path)
        log("DETECT: Image loaded")

        if image is None:
            raise ValueError("Failed to load image data")

        # Check if downscaling is needed for performance
        original_width = image.width()
        original_height = image.height()
        scale_factor = 1.0
        
        log(f"DETECT: Original image size: {original_width}x{original_height}")
        
        if original_width > MAX_IMAGE_DIMENSION or original_height > MAX_IMAGE_DIMENSION:
            scale_factor = min(MAX_IMAGE_DIMENSION / original_width, MAX_IMAGE_DIMENSION / original_height)
            log(f"Downscaling image from {original_width}x{original_height} by factor {scale_factor:.2f}")
            image = image.scaled(
                int(original_width * scale_factor),
                int(original_height * scale_factor),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            log(f"DETECT: Image downscaled to {image.width()}x{image.height()}")
        
        log(f"Processing image: {image.width()}x{image.height()} pixels")
        log("DETECT: Starting multi-pass detection...")

        # Run multi-pass detection
        all_elements: List[UIElement] = []
        pass_times = {}

        # Pass A: Contour detection
        try:
            t0 = time.time()
            log("PASS_CONTOUR_START")
            sys.stdout.flush()
            contour_elements = self._detect_contours(image)
            log(f"PASS_CONTOUR_END: {len(contour_elements)} candidates in {time.time()-t0:.3f}s")
            all_elements.extend(contour_elements)
            pass_times['contour'] = time.time() - t0
        except Exception as e:
            log(f"PASS_CONTOUR_FAILED: {e}")
            import traceback
            log(f"Traceback: {traceback.format_exc()}")

        # Pass B: Color plane detection
        try:
            t0 = time.time()
            log("PASS_COLOR_START")
            sys.stdout.flush()
            color_elements = self._detect_color_planes(image)
            log(f"PASS_COLOR_END: {len(color_elements)} candidates in {time.time()-t0:.3f}s")
            all_elements.extend(color_elements)
            pass_times['color'] = time.time() - t0
        except Exception as e:
            log(f"PASS_COLOR_FAILED: {e}")

        # Pass C: Line detection (LIMITED - this was likely the culprit)
        try:
            t0 = time.time()
            log("PASS_LINES_START")
            sys.stdout.flush()
            line_elements = self._detect_lines_limited(image, max_candidates=100)
            log(f"PASS_LINES_END: {len(line_elements)} candidates in {time.time()-t0:.3f}s")
            all_elements.extend(line_elements)
            pass_times['lines'] = time.time() - t0
        except Exception as e:
            log(f"PASS_LINES_FAILED: {e}")

        # Pass D: Connected components (LIMITED)
        try:
            t0 = time.time()
            log("PASS_CONNECTED_START")
            sys.stdout.flush()
            connected_elements = self._detect_connected_components_limited(image, max_candidates=200)
            log(f"PASS_CONNECTED_END: {len(connected_elements)} candidates in {time.time()-t0:.3f}s")
            all_elements.extend(connected_elements)
            pass_times['connected'] = time.time() - t0
        except Exception as e:
            log(f"PASS_CONNECTED_FAILED: {e}")

        # Pass E: Text zone candidates (LIMITED)
        try:
            t0 = time.time()
            log("PASS_TEXT_START")
            sys.stdout.flush()
            text_elements = self._detect_text_zones_limited(image, max_candidates=100)
            log(f"PASS_TEXT_END: {len(text_elements)} candidates in {time.time()-t0:.3f}s")
            all_elements.extend(text_elements)
            pass_times['text'] = time.time() - t0
        except Exception as e:
            log(f"PASS_TEXT_FAILED: {e}")

        log(f"Total candidates before fusion: {len(all_elements)}")
        sys.stdout.flush()

        # Limit total candidates before expensive operations
        if len(all_elements) > MAX_TOTAL_CANDIDATES:
            log(f"Limiting candidates from {len(all_elements)} to {MAX_TOTAL_CANDIDATES}")
            all_elements.sort(key=lambda e: -e.confidence)
            all_elements = all_elements[:MAX_TOTAL_CANDIDATES]

        # Fuse results: remove duplicates, filter, sort
        try:
            t0 = time.time()
            log("PASS_FUSION_START")
            sys.stdout.flush()
            fused_elements = self._fuse_results(all_elements, image.width(), image.height(), logger=logger)
            pass_times['fusion'] = time.time() - t0
            log(f"PASS_FUSION_END: {len(fused_elements)} elements after filtering in {pass_times['fusion']:.3f}s")
        except Exception as e:
            log(f"PASS_FUSION_FAILED: {e}")
            fused_elements = all_elements

        # Classify elements
        try:
            t0 = time.time()
            log("PASS_CLASSIFICATION_START")
            sys.stdout.flush()
            classified_elements = self._classify_elements(fused_elements)
            pass_times['classification'] = time.time() - t0
            log(f"PASS_CLASSIFICATION_END: {len(classified_elements)} elements in {pass_times['classification']:.3f}s")
        except Exception as e:
            log(f"PASS_CLASSIFICATION_FAILED: {e}")
            classified_elements = fused_elements

        # Build hierarchy
        try:
            t0 = time.time()
            log("PASS_HIERARCHY_START")
            sys.stdout.flush()
            hierarchical_elements = self._build_hierarchy(classified_elements)
            pass_times['hierarchy'] = time.time() - t0
            log(f"PASS_HIERARCHY_END: completed in {pass_times['hierarchy']:.3f}s")
        except Exception as e:
            log(f"PASS_HIERARCHY_FAILED: {e}")
            hierarchical_elements = classified_elements

        # Scale coordinates back to original image size
        if scale_factor != 1.0:
            log(f"Scaling coordinates back by factor {1/scale_factor:.2f}")
            for elem in hierarchical_elements:
                elem.x = int(elem.x / scale_factor)
                elem.y = int(elem.y / scale_factor)
                elem.width = int(elem.width / scale_factor)
                elem.height = int(elem.height / scale_factor)
            log("PASS_RESCALE_END")

        total_time = time.time() - start_time
        log(f"DETECT_COMPLETE: Total detection time: {total_time:.3f}s")
        log(f"Pass times: {pass_times}")
        log(f"Final element count: {len(hierarchical_elements)}")
        sys.stdout.flush()

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

    def _detect_contours(
        self,
        image: "QImage",
        max_candidates_per_tile: int = 300,
        tile_size: int = 1024,
        tile_overlap: int = 50
    ) -> List[UIElement]:
        """Detect UI elements using OpenCV with tiled processing.
        
        Uses OpenCV for fast contour detection and tiling for memory efficiency.
        Processes large images in overlapping tiles to avoid memory issues.
        
        Args:
            image: QImage to process.
            max_candidates_per_tile: Maximum candidates per tile.
            tile_size: Size of each tile in pixels.
            tile_overlap: Overlap between tiles in pixels.
        
        Returns:
            List of detected UI elements.
        """
        import sys
        import numpy as np
        
        # Try to import OpenCV
        try:
            import cv2
            _OPENCV_AVAILABLE = True
        except ImportError:
            _OPENCV_AVAILABLE = False
            print("CONTOUR_WARNING: OpenCV not available, falling back to basic detection", flush=True)
            return self._detect_contours_basic(image)
        
        elements: List[UIElement] = []
        width = image.width()
        height = image.height()
        
        print(f"CONTOUR_INFO: Image size {width}x{height}, tile_size={tile_size}, overlap={tile_overlap}", flush=True)
        sys.stdout.flush()
        
        # Convert QImage to numpy array - COMPATIBLE WITH PySide6 6.11+
        # DO NOT use ptr.setsize() - it's deprecated
        # Method: copy image data to bytes, then to numpy
        
        # Get image format info
        fmt = image.format()
        
        # For Format_RGB32 or Format_ARGB32_Premultiplied
        if fmt in (QImage.Format_RGB32, QImage.Format_ARGB32, QImage.Format_ARGB32_Premultiplied):
            # Get raw bytes
            img_bytes = bytearray(image.bits().asarray(height * width * 4))
            
            # Reshape to (height, width, 4) - BGRA or RGBA depending on platform
            img_array = np.frombuffer(img_bytes, dtype=np.uint8).reshape((height, width, 4))
            
            # Qt stores as BGRA on most platforms, convert to RGB
            # img_array is now [B, G, R, A] or [R, G, B, A]
            # OpenCV expects BGR, so we use the array directly if it's BGRA
            img_bgr = img_array[:, :, :3]  # Drop alpha channel
            
        else:
            # Convert to RGB32 first for other formats
            image_rgb = image.convertToFormat(QImage.Format_RGB32)
            img_bytes = bytearray(image_rgb.bits().asarray(height * width * 4))
            img_array = np.frombuffer(img_bytes, dtype=np.uint8).reshape((height, width, 4))
            img_bgr = img_array[:, :, :3]
        
        print(f"CONTOUR_INFO: QImage converted to numpy array {img_array.shape}", flush=True)
        sys.stdout.flush()
        
        # Convert RGB to BGR for OpenCV (if needed - Qt uses BGRA on Windows)
        # Check if we need to swap channels by looking at a known color
        img_bgr = cv2.cvtColor(img_array[:, :, :3], cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray_full = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        print(f"CONTOUR_INFO: Grayscale created", flush=True)
        sys.stdout.flush()
        
        # Determine if tiling is needed
        use_tiles = width > tile_size or height > tile_size
        
        if use_tiles:
            print(f"CONTOUR_INFO: Using tiled processing", flush=True)
            sys.stdout.flush()
            
            # Process image in overlapping tiles
            all_tile_elements: List[Tuple[int, int, List[UIElement]]] = []
            
            y_tiles = []
            y = 0
            while y < height:
                tile_h = min(tile_size, height - y)
                y_tiles.append((y, tile_h))
                y += tile_size - tile_overlap if y + tile_size < height else tile_size
            
            x_tiles = []
            x = 0
            while x < width:
                tile_w = min(tile_size, width - x)
                x_tiles.append((x, tile_w))
                x += tile_size - tile_overlap if x + tile_size < width else tile_size
            
            print(f"CONTOUR_INFO: Grid {len(x_tiles)}x{len(y_tiles)} tiles", flush=True)
            sys.stdout.flush()
            
            total_candidates = 0
            tile_count = 0
            
            for tile_idx, (tile_x, tile_w) in enumerate(x_tiles):
                for tile_y_idx, (tile_y, tile_h) in enumerate(y_tiles):
                    tile_count += 1
                    
                    # Extract tile
                    tile_gray = gray_full[tile_y:tile_y+tile_h, tile_x:tile_x+tile_w]
                    
                    # Process tile
                    tile_elements = self._process_contour_tile(
                        tile_gray,
                        tile_x,
                        tile_y,
                        img_bgr[tile_y:tile_y+tile_h, tile_x:tile_x+tile_w],
                        max_candidates_per_tile,
                        tile_count
                    )
                    
                    if tile_elements:
                        all_tile_elements.append((tile_x, tile_y, tile_elements))
                        total_candidates += len(tile_elements)
                        print(f"CONTOUR_TILE_{tile_count}: {len(tile_elements)} candidates (total={total_candidates})", flush=True)
                    else:
                        print(f"CONTOUR_TILE_{tile_count}: 0 candidates", flush=True)
                    sys.stdout.flush()
            
            # Merge and deduplicate tile results
            print(f"CONTOUR_INFO: Merging {len(all_tile_elements)} tile results", flush=True)
            sys.stdout.flush()
            
            elements = self._merge_tile_elements(all_tile_elements, width, height)
            
            print(f"CONTOUR_INFO: After merge: {len(elements)} unique elements", flush=True)
            sys.stdout.flush()
            
        else:
            # Process full image at once
            print(f"CONTOUR_INFO: Processing full image without tiling", flush=True)
            sys.stdout.flush()
            
            elements = self._process_contour_tile(
                gray_full,
                0,
                0,
                img_bgr,
                max_candidates_per_tile * 4,  # Higher limit for full image
                0
            )
        
        print(f"CONTOUR_INFO: Final element count: {len(elements)}", flush=True)
        sys.stdout.flush()
        
        return elements
    
    def _process_contour_tile(
        self,
        gray: "np.ndarray",
        offset_x: int,
        offset_y: int,
        img_bgr: "np.ndarray",
        max_candidates: int,
        tile_id: int
    ) -> List[UIElement]:
        """Process a single tile for contour detection.
        
        Args:
            gray: Grayscale numpy array of tile.
            offset_x: X offset in original image.
            offset_y: Y offset in original image.
            img_bgr: BGR numpy array of tile.
            max_candidates: Maximum candidates to return.
            tile_id: Tile identifier for logging.
        
        Returns:
            List of UI elements detected in tile.
        """
        import cv2
        import numpy as np
        import sys
        
        start_time = time.time()
        
        tile_h, tile_w = gray.shape
        
        # Apply Canny edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(
            edges,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        print(f"CONTOUR_TILE_{tile_id}: Found {len(contours)} raw contours", flush=True)
        sys.stdout.flush()
        
        elements: List[UIElement] = []
        
        for idx, contour in enumerate(contours):
            if len(elements) >= max_candidates:
                print(f"CONTOUR_TILE_{tile_id}: Hit max_candidates limit ({max_candidates})", flush=True)
                sys.stdout.flush()
                break
            
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter small contours
            if w < 10 or h < 10:
                continue
            
            # Filter very large contours (likely background)
            if w > tile_w * 0.95 and h > tile_h * 0.95:
                continue
            
            # Get average color from BGR image
            tile_region = img_bgr[y:y+h, x:x+w]
            if tile_region.size > 0:
                avg_color = np.mean(tile_region, axis=(0, 1))
                color_rgb = (int(avg_color[2]), int(avg_color[1]), int(avg_color[0]))  # BGR -> RGB
            else:
                color_rgb = (0, 0, 0)
            
            color_hex = UIElement._rgb_to_hex(color_rgb)
            
            # Calculate confidence based on rectangularity
            area = cv2.contourArea(contour)
            rect_area = w * h
            rectangularity = area / rect_area if rect_area > 0 else 0
            confidence = min(0.95, 0.5 + rectangularity * 0.3)
            
            # Create element with global coordinates
            element = UIElement(
                id=self._generate_element_id("contour"),
                name=f"Tile{tile_id}_Elem_{len(elements):04d}",
                element_type="unknown",
                category="general",
                color_rgb=color_rgb,
                color_hex=color_hex,
                x=offset_x + x,
                y=offset_y + y,
                width=w,
                height=h,
                confidence=confidence,
                source="contour"
            )
            elements.append(element)
        
        elapsed = time.time() - start_time
        print(f"CONTOUR_TILE_{tile_id}: Processed in {elapsed:.3f}s, returning {len(elements)} elements", flush=True)
        sys.stdout.flush()
        
        return elements
    
    def _merge_tile_elements(
        self,
        tile_elements: List[Tuple[int, int, List[UIElement]]],
        image_width: int,
        image_height: int
    ) -> List[UIElement]:
        """Merge and deduplicate elements from overlapping tiles.
        
        Args:
            tile_elements: List of (offset_x, offset_y, elements) tuples.
            image_width: Full image width.
            image_height: Full image height.
        
        Returns:
            Merged and deduplicated element list.
        """
        import sys
        
        print(f"CONTOUR_MERGE: Starting merge of {len(tile_elements)} tile results", flush=True)
        sys.stdout.flush()
        
        # Flatten all elements
        all_elements: List[UIElement] = []
        for _, _, elements in tile_elements:
            all_elements.extend(elements)
        
        print(f"CONTOUR_MERGE: Total candidates before dedup: {len(all_elements)}", flush=True)
        sys.stdout.flush()
        
        # Use IoU-based deduplication
        deduplicated = self._remove_duplicates_iou_optimized(all_elements, 0.7)
        
        print(f"CONTOUR_MERGE: After IoU dedup: {len(deduplicated)} elements", flush=True)
        sys.stdout.flush()
        
        # Filter background-sized elements
        image_area = image_width * image_height
        filtered = [
            e for e in deduplicated
            if (e.width * e.height) / image_area <= 0.9
        ]
        
        print(f"CONTOUR_MERGE: After background filter: {len(filtered)} elements", flush=True)
        sys.stdout.flush()
        
        return filtered
    
    def _detect_contours_basic(self, image: "QImage") -> List[UIElement]:
        """Fallback contour detection without OpenCV.
        
        Uses sampling for performance.
        """
        import sys
        
        elements: List[UIElement] = []
        width = image.width()
        height = image.height()
        
        # Use aggressive sampling for large images
        sample_rate = max(1, min(width, height) // 800)
        
        sampled_w = (width - 1) // sample_rate + 1
        sampled_h = (height - 1) // sample_rate + 1
        
        gray = [[0] * sampled_w for _ in range(sampled_h)]
        for y in range(0, height, sample_rate):
            for x in range(0, width, sample_rate):
                pixel = image.pixel(x, y)
                color = QColor(pixel)
                gray[y // sample_rate][x // sample_rate] = int(
                    (color.red() + color.green() + color.blue()) / 3
                )
        
        edges = self._find_edges(gray, sampled_w, sampled_h)
        regions = self._find_rectangular_regions(edges, sampled_w, sampled_h)
        
        for idx, region in enumerate(regions):
            x, y, w, h = region
            x *= sample_rate
            y *= sample_rate
            w = max(w * sample_rate, sample_rate)
            h = max(h * sample_rate, sample_rate)
            
            color_rgb = self._get_region_color(image, x, y, w, h)
            color_hex = UIElement._rgb_to_hex(color_rgb)
            confidence = 0.5
            
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

    def _detect_color_planes(
        self,
        image: "QImage",
        max_candidates: int = 200,
        tile_size: int = 1024
    ) -> List[UIElement]:
        """Detect UI elements based on color plane differences.
        
        Vectorized implementation using OpenCV/numpy - NO Python pixel loops.
        Finds rectangular regions with distinct colors from their surroundings.
        """
        import sys
        import numpy as np
        
        try:
            import cv2
        except ImportError:
            print("COLOR_WARNING: OpenCV not available, skipping color detection", flush=True)
            return []
        
        elements: List[UIElement] = []
        width = image.width()
        height = image.height()
        
        if width < 10 or height < 10:
            return elements
        
        print(f"COLOR_INFO: Image size {width}x{height}", flush=True)
        sys.stdout.flush()
        
        start_time = time.time()
        
        # Convert QImage to numpy (same as contour detection)
        fmt = image.format()
        if fmt in (QImage.Format_RGB32, QImage.Format_ARGB32, QImage.Format_ARGB32_Premultiplied):
            img_bytes = bytearray(image.bits().asarray(height * width * 4))
            img_array = np.frombuffer(img_bytes, dtype=np.uint8).reshape((height, width, 4))
            img_bgr = img_array[:, :, :3]
        else:
            image_rgb = image.convertToFormat(QImage.Format_RGB32)
            img_bytes = bytearray(image_rgb.bits().asarray(height * width * 4))
            img_array = np.frombuffer(img_bytes, dtype=np.uint8).reshape((height, width, 4))
            img_bgr = img_array[:, :, :3]
        
        # Convert to grayscale for edge detection
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # Use OpenCV to find color boundaries
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Use Canny edge detection
        edges = cv2.Canny(blurred, 30, 100)
        
        # Dilate edges to connect nearby regions
        kernel = np.ones((3, 3), np.uint8)
        dilated_edges = cv2.dilate(edges, kernel, iterations=2)
        eroded_edges = cv2.erode(dilated_edges, kernel, iterations=1)
        
        # Find contours of color regions
        contours, _ = cv2.findContours(eroded_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        print(f"COLOR_INFO: Found {len(contours)} raw contours", flush=True)
        sys.stdout.flush()
        
        # Process contours into rectangular regions
        for idx, contour in enumerate(contours):
            if len(elements) >= max_candidates:
                print(f"COLOR_INFO: Hit max_candidates limit ({max_candidates})", flush=True)
                break
            
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter small regions
            if w < 20 or h < 20:
                continue
            
            # Filter very large regions (likely background)
            if w > width * 0.9 and h > height * 0.9:
                continue
            
            # Get average color from the region
            region = img_bgr[y:y+h, x:x+w]
            if region.size > 0:
                avg_color = np.mean(region, axis=(0, 1))
                color_rgb = (int(avg_color[2]), int(avg_color[1]), int(avg_color[0]))  # BGR -> RGB
            else:
                color_rgb = (0, 0, 0)
            
            color_hex = UIElement._rgb_to_hex(color_rgb)
            
            # Calculate confidence based on region size and color uniformity
            region_std = np.std(region)
            uniformity = 1.0 / (1.0 + region_std / 50)  # Higher std = lower uniformity
            confidence = min(0.95, 0.5 + uniformity * 0.3 + min(w * h / 10000, 0.2))
            
            element = UIElement(
                id=self._generate_element_id("color"),
                name=f"ColorPlane_{len(elements):04d}",
                element_type="unknown",
                category="general",
                color_rgb=color_rgb,
                color_hex=color_hex,
                x=x,
                y=y,
                width=w,
                height=h,
                confidence=confidence,
                source="color_plane"
            )
            elements.append(element)
        
        elapsed = time.time() - start_time
        print(f"COLOR_INFO: Processed in {elapsed:.3f}s, returning {len(elements)} elements", flush=True)
        sys.stdout.flush()
        
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
