"""
Document processing pipeline using IBM Granite-Docling.
Supports: PDF, Excel, CSV, JSON, DOCX with password protection.
Uses unified Docling library for consistent extraction across all formats.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
import re

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Unified document processor using IBM Granite-Docling.
    Handles password-protected files and multiple formats.
    """

    def __init__(self, file_path: str, file_type: str, password: Optional[str] = None):
        """
        Initialize document processor.

        Args:
            file_path: Path to the document file
            file_type: File extension (pdf, xlsx, csv, json, docx)
            password: Optional password for protected files
        """
        self.file_path = Path(file_path)
        self.file_type = file_type.lower()
        self.password = password

    def process(self) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Process document using Docling and return (full_text, chunks).

        Returns:
            Tuple of (full_text, list of chunk dicts with text, chunk_index, page_number, section_type)

        Raises:
            ValueError: If file type is unsupported
            Exception: If processing fails (including password-protected errors)
        """
        try:
            from docling.document_converter import DocumentConverter
            from docling.dataclasses.base_models import ConversionStatus
            from docling_core.types.doc import (
                DoclingDocument,
                TextBlock,
                TableBlock,
                ImageBlock,
            )
        except ImportError:
            logger.error("Docling processing requires docling and docling-core packages")
            raise ImportError(
                "Please install IBM Granite-Docling: pip install docling docling-core"
            )

        supported_types = {"pdf", "xlsx", "csv", "json", "docx"}
        if self.file_type not in supported_types:
            raise ValueError(
                f"Unsupported file type: {self.file_type}. "
                f"Supported: {', '.join(supported_types)}"
            )

        try:
            # Initialize Docling converter
            converter = DocumentConverter()

            # Convert document with password support
            try:
                result = self._convert_with_password(converter)
            except Exception as e:
                error_msg = str(e).lower()
                if "password" in error_msg or "encrypted" in error_msg:
                    raise ValueError(
                        "File is password-protected but no password provided. "
                        "Please enter the password and try again."
                    )
                raise

            # Check conversion status
            if result.status != ConversionStatus.SUCCESS:
                raise Exception(f"Conversion failed with status: {result.status}")

            doc = result.document

            # Extract text and chunks
            full_text, chunks = self._extract_content_and_chunks(doc)

            logger.info(
                f"Successfully processed {self.file_type.upper()} file: "
                f"{self.file_path.name} - {len(chunks)} chunks"
            )
            return full_text, chunks

        except ValueError as ve:
            logger.error(f"Password or file error: {ve}")
            raise
        except Exception as e:
            logger.error(f"Error processing document with Docling: {e}", exc_info=True)
            raise

    def _convert_with_password(self, converter):
        """Convert document, handling password-protected files."""
        try:
            from docling.document_converter import DocumentConverter
        except ImportError:
            raise ImportError("Docling not installed")

        # Try conversion without password first
        try:
            result = converter.convert(str(self.file_path))
            return result
        except Exception as e:
            error_msg = str(e).lower()
            # Check if it's a password-related error
            if (
                "password" in error_msg
                or "encrypted" in error_msg
                or "secure" in error_msg
            ):
                if not self.password:
                    raise ValueError(
                        "File is password-protected. Please provide the password."
                    )
                # Try with password for PDF files
                if self.file_type == "pdf":
                    try:
                        result = converter.convert(
                            str(self.file_path), password=self.password
                        )
                        logger.info("Successfully opened password-protected file")
                        return result
                    except Exception as pwd_error:
                        logger.error(f"Password authentication failed: {pwd_error}")
                        raise ValueError(
                            f"Password is incorrect. Please verify and try again. Error: {pwd_error}"
                        )
                else:
                    raise ValueError(
                        f"File format {self.file_type.upper()} does not support password protection in this implementation."
                    )
            # Not a password error, re-raise
            raise

    def _extract_content_and_chunks(self, doc) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Extract text and create chunks from Docling document.

        Args:
            doc: Docling document object

        Returns:
            Tuple of (full_text, chunks_list)
        """
        try:
            from docling_core.types.doc import TextBlock, TableBlock, ImageBlock
        except ImportError:
            raise ImportError("docling-core not installed")

        all_text = []
        chunks = []
        current_page = 0
        page_contents = {}

        # Iterate through document items
        if hasattr(doc, "doc_items"):
            for item in doc.doc_items:
                if isinstance(item, TextBlock):
                    text = item.text or ""
                    if text.strip():
                        # Track page information
                        if hasattr(item, "page_idx"):
                            current_page = item.page_idx
                        all_text.append(text)
                        if current_page not in page_contents:
                            page_contents[current_page] = []
                        page_contents[current_page].append(text)

                elif isinstance(item, TableBlock):
                    # Convert table to readable text
                    table_text = self._format_table(item)
                    if table_text.strip():
                        all_text.append(table_text)
                        if current_page not in page_contents:
                            page_contents[current_page] = []
                        page_contents[current_page].append(table_text)

                elif isinstance(item, ImageBlock):
                    # Add image metadata/caption
                    if hasattr(item, "caption") and item.caption:
                        caption_text = f"[Image: {item.caption}]"
                        all_text.append(caption_text)
                        if current_page not in page_contents:
                            page_contents[current_page] = []
                        page_contents[current_page].append(caption_text)

        # Combine all text
        full_text = "\n\n".join(all_text)

        # Create chunks with page information
        chunk_index = 0
        for page_num in sorted(page_contents.keys()):
            page_text = "\n\n".join(page_contents[page_num])
            page_chunks = self.chunk_text(
                page_text, section_type=f"page_{page_num + 1}"
            )
            for chunk in page_chunks:
                chunk["page_number"] = page_num + 1
                chunk["chunk_index"] = chunk_index
                chunks.append(chunk)
                chunk_index += 1

        return full_text, chunks

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200,
        section_type: str = "text",
    ) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk
            chunk_size: Target chunk size in characters
            overlap: Overlap between chunks in characters
            section_type: Type/category of section

        Returns:
            List of chunk dictionaries
        """
        chunks = []
        chunk_index = 0

        if not text or len(text.strip()) == 0:
            return chunks

        # Split by paragraphs first for semantic coherence
        paragraphs = [p for p in text.split("\n\n") if p.strip()]

        if not paragraphs:
            # Fallback to character-based chunking
            paragraphs = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

        current_chunk = ""

        for para in paragraphs:
            # Check if adding paragraph exceeds chunk size
            if current_chunk and len(current_chunk) + len(para) + 2 > chunk_size:
                # Save current chunk
                if current_chunk.strip():
                    chunks.append(
                        {
                            "text": current_chunk.strip(),
                            "chunk_index": chunk_index,
                            "section_type": section_type,
                        }
                    )
                    chunk_index += 1

                # Create overlap from end of current chunk
                overlap_text = (
                    current_chunk[-overlap:] if len(current_chunk) > overlap else ""
                )
                current_chunk = overlap_text + para

            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para

        # Add final chunk
        if current_chunk.strip():
            chunks.append(
                {
                    "text": current_chunk.strip(),
                    "chunk_index": chunk_index,
                    "section_type": section_type,
                }
            )

        return chunks

    @staticmethod
    def _format_table(table_block) -> str:
        """
        Format table block to readable text.

        Args:
            table_block: Table block from Docling

        Returns:
            Formatted table string
        """
        try:
            rows = []
            if hasattr(table_block, "table") and hasattr(table_block.table, "rows"):
                for row in table_block.table.rows:
                    row_cells = []
                    for cell in row.cells:
                        cell_text = cell.text if hasattr(cell, "text") else str(cell)
                        row_cells.append(cell_text or "")
                    rows.append(" | ".join(row_cells))
                return "\n".join(rows)
            else:
                # Fallback for different table structure
                return str(table_block)
        except Exception as e:
            logger.warning(f"Error formatting table: {e}")
            return str(table_block)


class FinancialDataValidator:
    """Validate financial data integrity."""

    @staticmethod
    def is_valid_financial_document(text: str) -> Tuple[bool, List[str]]:
        """
        Check if document contains financial data.

        Args:
            text: Document text to validate

        Returns:
            Tuple of (is_valid, list of validation issues)
        """
        financial_indicators = [
            r"revenue",
            r"expense",
            r"profit",
            r"assets",
            r"liabilities",
            r"balance sheet",
            r"cash flow",
            r"equity",
            r"\$\d+",
            r"fiscal year",
            r"GAAP",
            r"income statement",
            r"depreciation",
            r"amortization",
        ]

        issues = []
        found_indicators = 0

        text_lower = text.lower()
        for indicator in financial_indicators:
            if re.search(indicator, text_lower):
                found_indicators += 1

        if found_indicators < 2:
            issues.append(
                f"Document has limited financial indicators "
                f"({found_indicators} of {len(financial_indicators)} expected)"
            )

        if len(text.strip()) < 500:
            issues.append("Document seems too short for a financial report")

        # More lenient validation - accept documents with any financial indicators
        return found_indicators > 0, issues