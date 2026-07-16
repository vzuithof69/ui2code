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
            import sys
            from tools.ui2code_logging import get_logger
            
            # Force flush stdout/stderr for immediate logging
            sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
            sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)
            
            logger = get_logger()
            
            try:
                logger.info("WORKER_RUN_START")
                sys.stdout.flush()
                
                self.started.emit()
                logger.info("WORKER_STARTED_EMITTED")
                sys.stdout.flush()
                
                # Create detector
                detector = UI2CodeDetectV2(config=self.detection_config)
                logger.info("Detector created")
                sys.stdout.flush()
                
                # Custom log handler that emits signals
                class SignalLogger:
                    def __init__(self, worker):
                        self.worker = worker
                    
                    def info(self, msg: str):
                        self.worker.progress.emit(msg)
                        sys.stdout.flush()
                    
                    def warning(self, msg: str):
                        self.worker.progress.emit(f"WARNING: {msg}")
                        sys.stdout.flush()
                    
                    def error(self, msg: str):
                        self.worker.progress.emit(f"ERROR: {msg}")
                        sys.stdout.flush()
                
                signal_logger = SignalLogger(self)
                logger.info("SignalLogger created")
                sys.stdout.flush()
                
                # Run detection
                self.progress.emit(f"Starting detection on: {self.image_path}")
                logger.info(f"Starting detection: {self.image_path}")
                sys.stdout.flush()
                
                if self._cancelled:
                    logger.info("WORKER_CANCELLED_BEFORE_START")
                    sys.stdout.flush()
                    self.finished.emit()
                    return
                
                logger.info("Calling detector.detect_elements()...")
                sys.stdout.flush()
                
                elements = detector.detect_elements(
                    image_data=self.image_path,
                    logger=signal_logger
                )
                
                logger.info(f"Detection returned {len(elements)} elements")
                sys.stdout.flush()
                
                if self._cancelled:
                    logger.info("WORKER_CANCELLED_AFTER_DETECTION")
                    sys.stdout.flush()
                    self.finished.emit()
                    return
                
                # Emit result
                logger.info("Emitting result_ready...")
                sys.stdout.flush()
                self.result_ready.emit(elements)
                logger.info("RESULT_READY_EMITTED")
                sys.stdout.flush()
                
            except BaseException as e:
                # Capture full traceback - use BaseException to catch ALL exceptions
                import traceback
                tb_str = traceback.format_exc()
                logger.exception(f"WORKER_EXCEPTION: {e}")
                logger.error(f"Traceback: {tb_str}")
                sys.stdout.flush()
                
                self.error.emit(str(e), tb_str)
                logger.info("ERROR_SIGNAL_EMITTED")
                sys.stdout.flush()
                
            finally:
                # ALWAYS emit finished - this is critical
                logger.info("WORKER_FINALLY_BLOCK")
                sys.stdout.flush()
                
                try:
                    self.finished.emit()
                    logger.info("FINISHED_SIGNAL_EMITTED")
                except Exception as emit_error:
                    logger.exception(f"Failed to emit finished: {emit_error}")
                
                sys.stdout.flush()
                logger.info("WORKER_RUN_END")
                sys.stdout.flush()
    
    
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
