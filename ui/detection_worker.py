"""UI2Code Detection Worker Thread.

Runs detection in a background thread to prevent GUI freezing.
"""

import sys
import os
import traceback
from typing import Optional, List, Any, Dict

try:
    from PySide6.QtCore import QThread, Signal, QObject
    from PySide6.QtWidgets import QApplication
    _QT_AVAILABLE = True
except ImportError:
    _QT_AVAILABLE = False
    QThread = object  # type: ignore
    Signal = object  # type: ignore
    QObject = object  # type: ignore

from engine.models import UIElement
from engine.ui2code_detect_v2 import UI2CodeDetect as UI2CodeDetectV2


if _QT_AVAILABLE:
    
    class DetectionWorker(QObject):
        """Worker object that runs detection in a background thread.
        
        Signals:
            started: Emitted when detection starts.
            progress: Emitted with progress messages.
            pass_started: Emitted when a detection pass starts.
            pass_completed: Emitted when a pass completes.
            result_ready: Emitted with detected elements on success.
            error: Emitted with error message on failure.
            finished: Emitted when detection completes (success or failure).
        """
        
        started = Signal()
        progress = Signal(str)
        pass_started = Signal(str)
        pass_completed = Signal(str, int, float)  # pass_name, count, duration
        result_ready = Signal(object)  # List[UIElement]
        error = Signal(str, str)  # message, traceback
        finished = Signal()
        
        def __init__(
            self,
            image_path: str,
            detection_config: Optional[Dict[str, Any]] = None
        ) -> None:
            """Initialize the detection worker.
            
            Args:
                image_path: Path to the image file to analyze.
                detection_config: Optional configuration for the detector.
            """
            super().__init__()
            self.image_path = image_path
            self.detection_config = detection_config or {}
            self._cancelled = False
        
        def cancel(self) -> None:
            """Request cancellation of the detection."""
            self._cancelled = True
        
        def run(self) -> None:
            """Run the detection process.
            
            This method is called by the QThread and runs in the worker thread.
            """
            import logging
            from tools.ui2code_logging import get_logger
            
            logger = get_logger()
            
            try:
                self.started.emit()
                
                # Create detector
                detector = UI2CodeDetectV2(config=self.detection_config)
                
                # Custom log handler that emits signals
                class SignalLogger:
                    def __init__(self, worker):
                        self.worker = worker
                    
                    def info(self, msg: str):
                        self.worker.progress.emit(msg)
                    
                    def warning(self, msg: str):
                        self.worker.progress.emit(f"WARNING: {msg}")
                    
                    def error(self, msg: str):
                        self.worker.progress.emit(f"ERROR: {msg}")
                
                signal_logger = SignalLogger(self)
                
                # Run detection
                self.progress.emit(f"Starting detection on: {self.image_path}")
                
                if self._cancelled:
                    self.finished.emit()
                    return
                
                elements = detector.detect_elements(
                    image_data=self.image_path,
                    logger=signal_logger
                )
                
                if self._cancelled:
                    self.finished.emit()
                    return
                
                # Emit result
                self.result_ready.emit(elements)
                
            except Exception as e:
                # Capture full traceback
                tb_str = traceback.format_exc()
                self.error.emit(str(e), tb_str)
                
                # Also log to file
                if logger:
                    logger.exception(f"Detection failed: {e}")
            
            finally:
                self.finished.emit()
    
    
    class DetectionThread(QThread):
        """QThread wrapper for detection worker.
        
        Manages the worker thread lifecycle and ensures proper cleanup.
        """
        
        # Forward worker signals
        started = Signal()
        progress = Signal(str)
        pass_started = Signal(str)
        pass_completed = Signal(str, int, float)
        result_ready = Signal(object)
        error = Signal(str, str)
        finished = Signal()
        
        def __init__(
            self,
            image_path: str,
            detection_config: Optional[Dict[str, Any]] = None,
            parent: Optional[QObject] = None
        ) -> None:
            """Initialize the detection thread.
            
            Args:
                image_path: Path to the image file to analyze.
                detection_config: Optional configuration for the detector.
                parent: Parent QObject.
            """
            super().__init__(parent)
            
            self.worker = DetectionWorker(image_path, detection_config)
            
            # Connect worker signals to thread signals
            self.worker.started.connect(self.started)
            self.worker.progress.connect(self.progress)
            self.worker.pass_started.connect(self.pass_started)
            self.worker.pass_completed.connect(self.pass_completed)
            self.worker.result_ready.connect(self.result_ready)
            self.worker.error.connect(self.error)
            self.worker.finished.connect(self.finished)
            self.worker.finished.connect(self._cleanup)
        
        def run(self) -> None:
            """Run the worker."""
            self.worker.run()
        
        def _cleanup(self) -> None:
            """Clean up worker resources."""
            self.worker.deleteLater()
        
        def cancel(self) -> None:
            """Request cancellation."""
            self.worker.cancel()
            self.quit()
            self.wait(3000)  # Wait up to 3 seconds
        
        def get_image_path(self) -> str:
            """Get the image path being processed."""
            return self.worker.image_path

else:
    # Stubs for non-Qt environments
    class DetectionWorker:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass
        def run(self):
            pass
        def cancel(self):
            pass
    
    class DetectionThread:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass
        def start(self):
            pass
        def quit(self):
            pass
        def wait(self, *args):
            pass
        def deleteLater(self):
            pass
