"""
Centralized logging configuration for financial analyzer.
Provides structured logging with rotation, levels, and formatting.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import json


# Create logs directory
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "session_id"):
            log_data["session_id"] = record.session_id
        if hasattr(record, "query"):
            log_data["query"] = record.query
        if hasattr(record, "agent"):
            log_data["agent"] = record.agent
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
        "RESET": "\033[0m",       # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]
        
        # Color the level name
        record.levelname = f"{color}{record.levelname}{reset}"
        
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    json_logs: bool = False,
) -> None:
    """
    Setup centralized logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to files
        log_to_console: Whether to log to console
        json_logs: Whether to use JSON format for file logs
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        
        # Use colored formatter for console
        console_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        console_formatter = ColoredFormatter(
            console_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # File handlers
    if log_to_file:
        # Main application log (rotating)
        app_log_file = LOGS_DIR / "app.log"
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        app_handler.setLevel(getattr(logging, log_level.upper()))
        
        if json_logs:
            app_formatter = JSONFormatter()
        else:
            app_format = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
            app_formatter = logging.Formatter(app_format, datefmt="%Y-%m-%d %H:%M:%S")
        
        app_handler.setFormatter(app_formatter)
        root_logger.addHandler(app_handler)
        
        # Error log (only errors and above)
        error_log_file = LOGS_DIR / "error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        
        if json_logs:
            error_formatter = JSONFormatter()
        else:
            error_format = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s\n%(message)s"
            error_formatter = logging.Formatter(error_format, datefmt="%Y-%m-%d %H:%M:%S")
        
        error_handler.setFormatter(error_formatter)
        root_logger.addHandler(error_handler)
        
        # Agent-specific log
        agent_log_file = LOGS_DIR / "agents.log"
        agent_handler = logging.handlers.RotatingFileHandler(
            agent_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        agent_handler.setLevel(logging.DEBUG)
        
        if json_logs:
            agent_formatter = JSONFormatter()
        else:
            agent_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            agent_formatter = logging.Formatter(agent_format, datefmt="%Y-%m-%d %H:%M:%S")
        
        agent_handler.setFormatter(agent_formatter)
        
        # Add filter to only log agent-related messages
        agent_handler.addFilter(lambda record: "agent" in record.name.lower())
        root_logger.addHandler(agent_handler)
    
    # Suppress verbose third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("gradio").setLevel(logging.INFO)
    
    logging.info(f"Logging configured: level={log_level}, file={log_to_file}, console={log_to_console}, json={json_logs}")


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (usually module name)
        level: Optional logging level override
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if level:
        logger.setLevel(getattr(logging, level.upper()))
    
    return logger


# Context manager for logging with extra fields
class LogContext:
    """Context manager for adding extra fields to log records."""
    
    def __init__(self, logger: logging.Logger, **kwargs):
        """
        Initialize log context.
        
        Args:
            logger: Logger instance
            **kwargs: Extra fields to add to log records
        """
        self.logger = logger
        self.extra = kwargs
        self.old_factory = logging.getLogRecordFactory()
    
    def __enter__(self):
        """Enter context."""
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.extra.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        logging.setLogRecordFactory(self.old_factory)


# Performance logging decorator
def log_performance(logger: Optional[logging.Logger] = None):
    """
    Decorator to log function performance.
    
    Args:
        logger: Logger instance (uses function's module logger if not provided)
    """
    def decorator(func):
        import functools
        import time
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
            
            start_time = time.time()
            logger.debug(f"Starting {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.info(f"{func.__name__} completed in {elapsed:.3f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"{func.__name__} failed after {elapsed:.3f}s: {e}", exc_info=True)
                raise
        
        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    # Setup logging
    setup_logging(log_level="DEBUG", json_logs=False)
    
    # Get logger
    logger = get_logger("test")
    
    # Log messages
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Log with context
    with LogContext(logger, user_id="user123", session_id="session456"):
        logger.info("User action performed")
    
    # Test performance logging
    @log_performance()
    def slow_function():
        import time
        time.sleep(0.1)
        return "Done"
    
    slow_function()
