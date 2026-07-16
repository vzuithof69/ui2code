"""QImage to NumPy conversion utilities.

Provides safe, tested conversion from QImage to numpy arrays
compatible with PySide6 6.11+.
"""

from typing import Tuple, Optional
import numpy as np

try:
    from PySide6.QtGui import QImage
    from PySide6.QtCore import Qt
    _QT_AVAILABLE = True
except ImportError:
    _QT_AVAILABLE = False
    QImage = type(None)  # type: ignore


def qimage_to_numpy(image: QImage) -> Tuple[np.ndarray, QImage]:
    """Convert QImage to numpy array safely.
    
    This function handles PySide6 6.11+ compatibility by:
    - Converting to explicit format (RGBA8888)
    - Using constBits() instead of bits()
    - Using sizeInBytes() instead of byteCount()
    - Handling bytesPerLine for proper scanline padding
    - Creating a contiguous copy to avoid buffer lifetime issues
    
    Args:
        image: QImage to convert.
        
    Returns:
        Tuple of (numpy_array, converted_image).
        numpy_array is shape (height, width, 4) with RGBA channels.
        converted_image is the RGBA8888 QImage that owns the buffer.
        The caller must keep converted_image alive while using the array.
        
    Raises:
        ImportError: If PySide6 is not available.
        ValueError: If image is invalid.
    """
    if not _QT_AVAILABLE:
        raise ImportError("PySide6 is required for QImage conversion")
    
    if image.isNull():
        raise ValueError("Cannot convert null QImage")
    
    # Convert to explicit RGBA format for consistent handling
    # This ensures we know the exact byte layout
    converted = image.convertToFormat(QImage.Format_RGBA8888)
    
    if converted.isNull():
        raise ValueError("Failed to convert image to RGBA8888 format")
    
    height = converted.height()
    width = converted.width()
    bytes_per_line = converted.bytesPerLine()
    
    # Get the raw buffer
    # constBits() returns a memoryview in PySide6 6.11+
    buffer = converted.constBits()
    
    # Get total size
    total_size = converted.sizeInBytes()
    
    # Convert to numpy array
    # frombuffer works with memoryview objects
    flat = np.frombuffer(buffer, dtype=np.uint8, count=total_size)
    
    # Reshape accounting for bytesPerLine (may include padding)
    # Each row has bytes_per_line bytes, but we only want width * 4
    rows = flat.reshape((height, bytes_per_line))
    
    # Extract only the pixel data (remove padding)
    rgba = rows[:, :width * 4].reshape((height, width, 4))
    
    # Create a contiguous copy to avoid buffer lifetime issues
    # The converted QImage must stay alive while using the original array,
    # but the copy is safe to use independently
    rgba_copy = rgba.copy()
    
    return rgba_copy, converted


def qimage_to_bgr(image: QImage) -> Tuple[np.ndarray, QImage]:
    """Convert QImage to BGR numpy array for OpenCV.
    
    OpenCV uses BGR color order by default. This function converts
    from QImage (RGBA) to BGR format suitable for OpenCV operations.
    
    Args:
        image: QImage to convert.
        
    Returns:
        Tuple of (bgr_array, converted_image).
        bgr_array is shape (height, width, 3) with BGR channels.
        
    Raises:
        ImportError: If PySide6 is not available.
        ValueError: If image is invalid.
    """
    rgba, converted = qimage_to_numpy(image)
    
    # Convert RGBA to BGR (drop alpha, swap R and B)
    # rgba is [R, G, B, A], OpenCV wants [B, G, R]
    bgr = rgba[:, :, :3]  # Drop alpha
    bgr = bgr[:, :, ::-1]  # RGB -> BGR
    
    # Ensure contiguous array
    bgr = np.ascontiguousarray(bgr)
    
    return bgr, converted


def qimage_to_grayscale(image: QImage) -> Tuple[np.ndarray, QImage]:
    """Convert QImage to grayscale numpy array.
    
    Args:
        image: QImage to convert.
        
    Returns:
        Tuple of (gray_array, converted_image).
        gray_array is shape (height, width) with uint8 values.
        
    Raises:
        ImportError: If PySide6 is not available.
        ValueError: If image is invalid.
    """
    try:
        import cv2
    except ImportError:
        raise ImportError("OpenCV is required for grayscale conversion")
    
    bgr, converted = qimage_to_bgr(image)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    
    return gray, converted
