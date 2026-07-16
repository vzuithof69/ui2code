"""UI2Code OCR Label Model.

Data model for OCR labels, prepared for future OCR integration.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple, List


@dataclass
class OCRLabel:
    """Data class representing an OCR-detected text label.
    
    Attributes:
        id: Unique identifier for the label.
        text: Recognized text content.
        bbox: Bounding box as (x, y, width, height).
        confidence: OCR confidence score (0.0 to 1.0).
        language: Detected or specified language (e.g., 'nl', 'en').
        linked_element_id: Optional ID of linked UI element.
        manually_corrected: Whether text was manually corrected.
        preprocessing: Applied preprocessing steps.
    """
    
    id: str
    text: str
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    confidence: float
    language: str = "auto"
    linked_element_id: Optional[str] = None
    manually_corrected: bool = False
    preprocessing: List[str] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate and normalize the label data."""
        # Validate confidence
        self.confidence = max(0.0, min(1.0, float(self.confidence)))
        
        # Validate bbox
        if len(self.bbox) != 4:
            raise ValueError("bbox must be (x, y, width, height)")
        
        x, y, w, h = self.bbox
        if w <= 0 or h <= 0:
            raise ValueError("bbox width and height must be positive")
        
        # Normalize language
        if self.language.lower() in ('auto', 'nl', 'en', 'de', 'fr'):
            self.language = self.language.lower()
        else:
            self.language = "auto"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert label to dictionary.
        
        Returns:
            Dictionary representation of the label.
        """
        return {
            "id": self.id,
            "text": self.text,
            "bbox": list(self.bbox),
            "confidence": self.confidence,
            "language": self.language,
            "linked_element_id": self.linked_element_id,
            "manually_corrected": self.manually_corrected,
            "preprocessing": self.preprocessing
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OCRLabel":
        """Create label from dictionary.
        
        Args:
            data: Dictionary containing label data.
        
        Returns:
            OCRLabel instance.
        """
        bbox = data.get("bbox", (0, 0, 0, 0))
        if isinstance(bbox, list):
            bbox = tuple(bbox)
        
        return cls(
            id=data.get("id", ""),
            text=data.get("text", ""),
            bbox=bbox,
            confidence=data.get("confidence", 0.0),
            language=data.get("language", "auto"),
            linked_element_id=data.get("linked_element_id"),
            manually_corrected=data.get("manually_corrected", False),
            preprocessing=data.get("preprocessing", [])
        )


@dataclass
class OCRPreprocessingConfig:
    """Configuration for OCR preprocessing steps.
    
    Attributes:
        grayscale: Convert to grayscale.
        contrast_enhance: Enhance contrast.
        upscale: Scale up image (factor).
        threshold: Apply thresholding.
        denoise: Apply denoising.
    """
    
    grayscale: bool = True
    contrast_enhance: bool = True
    upscale: float = 1.0
    threshold: bool = False
    denoise: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "grayscale": self.grayscale,
            "contrast_enhance": self.contrast_enhance,
            "upscale": self.upscale,
            "threshold": self.threshold,
            "denoise": self.denoise
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OCRPreprocessingConfig":
        """Create from dictionary."""
        return cls(
            grayscale=data.get("grayscale", True),
            contrast_enhance=data.get("contrast_enhance", True),
            upscale=data.get("upscale", 1.0),
            threshold=data.get("threshold", False),
            denoise=data.get("denoise", False)
        )
