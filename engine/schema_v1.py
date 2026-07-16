"""UI2Code Schema v1 - Versionable JSON Schema.

Defines schema version 1 for UI2Code project data.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from engine.models import UIElement
from engine.ocr_models import OCRLabel

# Current schema version
SCHEMA_VERSION = "1.0"

# Engine version
ENGINE_VERSION = "0.3.0"  # Fase 3B


class UI2CodeSchema:
    """Handler for UI2Code JSON schema version 1.
    
    Schema structure:
    {
        "schema_version": "1.0",
        "engine_version": "0.3.0",
        "created_at": "ISO timestamp",
        "updated_at": "ISO timestamp",
        "image": {
            "path": "path/to/image.png",
            "width": 800,
            "height": 600,
            "format": "PNG"
        },
        "detection_settings": {
            "min_width": 4,
            "min_height": 4,
            "min_area": 16,
            "max_coverage_ratio": 0.95,
            "iou_threshold": 0.8,
            "enabled_passes": ["contour", "color", "lines", "connected", "text_zones"]
        },
        "elements": [...],
        "ocr_labels": [...],
        "statistics": {
            "total_elements": 10,
            "by_type": {...},
            "by_category": {...},
            "confidence_stats": {...}
        }
    }
    """
    
    def __init__(self) -> None:
        """Initialize schema handler."""
        self.schema_version = SCHEMA_VERSION
        self.engine_version = ENGINE_VERSION
        self.created_at: Optional[str] = None
        self.updated_at: Optional[str] = None
        self.image_info: Dict[str, Any] = {}
        self.detection_settings: Dict[str, Any] = {}
        self.elements: List[UIElement] = []
        self.ocr_labels: List[OCRLabel] = []
    
    def create(
        self,
        image_path: str,
        image_width: int,
        image_height: int,
        image_format: str = "PNG",
        detection_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create a new schema instance.
        
        Args:
            image_path: Path to the source image.
            image_width: Image width in pixels.
            image_height: Image height in pixels.
            image_format: Image format (PNG, JPG, etc.).
            detection_config: Detection configuration.
        """
        now = datetime.now().isoformat()
        self.created_at = now
        self.updated_at = now
        
        self.image_info = {
            "path": image_path,
            "width": image_width,
            "height": image_height,
            "format": image_format
        }
        
        self.detection_settings = detection_config or {
            "min_width": 4,
            "min_height": 4,
            "min_area": 16,
            "max_coverage_ratio": 0.95,
            "iou_threshold": 0.8,
            "enabled_passes": ["contour", "color", "lines", "connected", "text_zones"]
        }
        
        self.elements = []
        self.ocr_labels = []
    
    def add_element(self, element: UIElement) -> None:
        """Add an element to the schema.
        
        Args:
            element: UIElement to add.
        """
        self.elements.append(element)
        self.updated_at = datetime.now().isoformat()
    
    def add_elements(self, elements: List[UIElement]) -> None:
        """Add multiple elements.
        
        Args:
            elements: List of UIElements to add.
        """
        self.elements.extend(elements)
        self.updated_at = datetime.now().isoformat()
    
    def add_ocr_label(self, label: OCRLabel) -> None:
        """Add an OCR label.
        
        Args:
            label: OCRLabel to add.
        """
        self.ocr_labels.append(label)
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary.
        
        Returns:
            Dictionary representation of the schema.
        """
        # Calculate statistics
        by_type: Dict[str, int] = {}
        by_category: Dict[str, int] = {}
        confidence_sum = 0.0
        
        for elem in self.elements:
            by_type[elem.element_type] = by_type.get(elem.element_type, 0) + 1
            by_category[elem.category] = by_category.get(elem.category, 0) + 1
            confidence_sum += elem.confidence
        
        avg_confidence = confidence_sum / len(self.elements) if self.elements else 0.0
        
        return {
            "schema_version": self.schema_version,
            "engine_version": self.engine_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "image": self.image_info,
            "detection_settings": self.detection_settings,
            "elements": [elem.to_dict() for elem in self.elements],
            "ocr_labels": [label.to_dict() for label in self.ocr_labels],
            "statistics": {
                "total_elements": len(self.elements),
                "by_type": by_type,
                "by_category": by_category,
                "confidence_stats": {
                    "average": round(avg_confidence, 3),
                    "min": round(min((e.confidence for e in self.elements), default=0.0), 3),
                    "max": round(max((e.confidence for e in self.elements), default=0.0), 3)
                }
            }
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert schema to JSON string.
        
        Args:
            indent: JSON indentation level.
        
        Returns:
            JSON string representation.
        """
        return json.dumps(self.to_dict(), indent=indent)
    
    def save(self, filepath: str) -> str:
        """Save schema to JSON file.
        
        Args:
            filepath: Path to save the JSON file.
        
        Returns:
            Path to saved file.
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
        return filepath
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UI2CodeSchema":
        """Create schema from dictionary.
        
        Args:
            data: Dictionary containing schema data.
        
        Returns:
            UI2CodeSchema instance.
        """
        schema = cls()
        
        # Validate version
        schema.schema_version = data.get("schema_version", "1.0")
        schema.engine_version = data.get("engine_version", "0.3.0")
        schema.created_at = data.get("created_at")
        schema.updated_at = data.get("updated_at")
        
        # Load image info
        schema.image_info = data.get("image", {})
        
        # Load detection settings
        schema.detection_settings = data.get("detection_settings", {})
        
        # Load elements
        elements_data = data.get("elements", [])
        for elem_data in elements_data:
            element = UIElement.from_dict(elem_data)
            schema.elements.append(element)
        
        # Load OCR labels
        ocr_data = data.get("ocr_labels", [])
        for label_data in ocr_data:
            label = OCRLabel.from_dict(label_data)
            schema.ocr_labels.append(label)
        
        return schema
    
    @classmethod
    def from_json(cls, json_string: str) -> "UI2CodeSchema":
        """Create schema from JSON string.
        
        Args:
            json_string: JSON string representation.
        
        Returns:
            UI2CodeSchema instance.
        """
        data = json.loads(json_string)
        return cls.from_dict(data)
    
    @classmethod
    def load(cls, filepath: str) -> "UI2CodeSchema":
        """Load schema from JSON file.
        
        Args:
            filepath: Path to JSON file.
        
        Returns:
            UI2CodeSchema instance.
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def validate(self) -> List[str]:
        """Validate schema data.
        
        Returns:
            List of validation errors (empty if valid).
        """
        errors = []
        
        # Check required fields
        if not self.schema_version:
            errors.append("schema_version is required")
        
        if not self.created_at:
            errors.append("created_at is required")
        
        # Validate image info
        if self.image_info:
            if "width" not in self.image_info or "height" not in self.image_info:
                errors.append("image width and height are required")
        
        # Validate elements
        for i, elem in enumerate(self.elements):
            if not elem.id:
                errors.append(f"element {i} missing id")
            if elem.confidence < 0.0 or elem.confidence > 1.0:
                errors.append(f"element {i} confidence out of range")
        
        # Validate OCR labels
        for i, label in enumerate(self.ocr_labels):
            if not label.id:
                errors.append(f"ocr_label {i} missing id")
            if label.confidence < 0.0 or label.confidence > 1.0:
                errors.append(f"ocr_label {i} confidence out of range")
        
        return errors
