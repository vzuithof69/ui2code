"""UI2Code Logging Module.

Centralized logging configuration for the UI2Code GUI application.
"""

import logging
import os
import sys
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional

# Log directory
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Log file names
TIMESTAMP = datetime.now().strftime("%Y%m%d-%H%M%S")
MAIN_LOG_FILE = os.path.join(LOG_DIR, f"ui2code-{TIMESTAMP}.log")
LATEST_ERROR_LOG = os.path.join(LOG_DIR, "latest-error.log")

# Global logger instance
_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """Get the global logger instance.
    
    Returns:
        Configured logger instance.
    """
    global _logger
    if _logger is not None:
        return _logger
    
    _logger = logging.getLogger("ui2code")
    _logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    _logger.handlers.clear()
    
    # Rotating file handler for main log
    # 10MB max size, keep 5 backup files
    file_handler = RotatingFileHandler(
        MAIN_LOG_FILE,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    _logger.addHandler(file_handler)
    _logger.addHandler(console_handler)
    
    return _logger


def log_exception_to_file(exc_type, exc_value, exc_traceback) -> None:
    """Log an exception to the latest-error.log file.
    
    Args:
        exc_type: Exception type.
        exc_value: Exception value.
        exc_traceback: Exception traceback.
    """
    try:
        with open(LATEST_ERROR_LOG, 'w', encoding='utf-8') as f:
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Exception Type: {exc_type.__name__}\n")
            f.write(f"Exception Value: {exc_value}\n")
            f.write("\nTraceback:\n")
            f.write(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    except Exception as e:
        # If we can't write to log, print to stderr
        print(f"Failed to write error log: {e}", file=sys.stderr)


def setup_exception_hooks() -> None:
    """Set up global exception hooks for logging."""
    logger = get_logger()
    
    # Store original excepthook
    original_excepthook = sys.excepthook
    
    def excepthook(exc_type, exc_value, exc_traceback):
        """Global exception hook for unhandled exceptions."""
        # Log to file
        log_exception_to_file(exc_type, exc_value, exc_traceback)
        
        # Log with logger
        logger.critical(
            "Unhandled exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        
        # Call original hook
        original_excepthook(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = excepthook
    
    # Set up Qt message handler if Qt is available
    try:
        from PySide6.QtCore import qInstallMessageHandler, QtMsgType
        from PySide6.QtWidgets import QApplication
        
        def qt_message_handler(msg_type, context, msg):
            """Qt message handler for logging Qt messages."""
            if msg_type == QtMsgType.QtDebugMsg:
                logger.debug(f"Qt: {msg}")
            elif msg_type == QtMsgType.QtInfoMsg:
                logger.info(f"Qt: {msg}")
            elif msg_type == QtMsgType.QtWarningMsg:
                logger.warning(f"Qt: {msg}")
            elif msg_type in (QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
                logger.error(f"Qt: {msg}")
        
        qInstallMessageHandler(qt_message_handler)
        logger.info("Qt message handler installed")
        
    except ImportError:
        logger.info("Qt not available, skipping Qt message handler")
    
    logger.info("Global exception hooks installed")


def initialize_logging() -> logging.Logger:
    """Initialize logging for the application.
    
    Returns:
        Configured logger instance.
    """
    logger = get_logger()
    logger.info("=" * 60)
    logger.info("UI2Code Application Start")
    logger.info(f"Log file: {MAIN_LOG_FILE}")
    logger.info(f"Error log: {LATEST_ERROR_LOG}")
    logger.info("=" * 60)
    
    # Set up exception hooks
    setup_exception_hooks()
    
    return logger
