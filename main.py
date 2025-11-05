"""
Main entry point for Financial Report Analyzer application with Multi-Agent System.
"""

import sys
from pathlib import Path

# Import centralized logging
from utils.logger import setup_logging, get_logger

# Setup comprehensive logging
setup_logging(
    log_level="INFO",
    log_to_file=True,
    log_to_console=True,
    json_logs=False,
)

logger = get_logger(__name__)

# Ensure required directories exist
Path("uploads").mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)
Path("config").mkdir(exist_ok=True)

logger.info("=" * 80)
logger.info("Starting Financial Report Analyzer with Multi-Agent System")
logger.info("=" * 80)

try:
    # Import and run Multi-Agent Gradio app
    from app_multiagent import create_interface

    logger.info("Creating Multi-Agent Gradio interface...")
    interface = create_interface()

    logger.info("Launching application at http://0.0.0.0:7860")
    logger.info("Multi-Agent System: ACTIVE")
    logger.info("Available Agents: Document Analysis, Financial Metrics, Trend Analysis")
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )

except Exception as e:
    logger.error(f"Failed to start application: {e}", exc_info=True)
    sys.exit(1)