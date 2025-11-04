"""
Main entry point for Financial Report Analyzer application.
"""

import logging
import os
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Ensure required directories exist
Path("uploads").mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)

logger.info("Starting Financial Report Analyzer")

try:
    # Import and run Gradio app
    from app import create_interface

    logger.info("Creating Gradio interface...")
    interface = create_interface()

    logger.info("Launching application at http://0.0.0.0:7860")
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )

except Exception as e:
    logger.error(f"Failed to start application: {e}", exc_info=True)
    sys.exit(1)