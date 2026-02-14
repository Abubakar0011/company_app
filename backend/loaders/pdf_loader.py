"""
PDF Loader Module
Extracts text from multi-page bank statement PDFs using PyMuPDF (fitz).
"""

import fitz  # PyMuPDF
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class PDFLoadError(Exception):
    """Custom exception for PDF loading errors."""
    pass


def load_pdf(file_path: str) -> str:
    """
    Extract text from all pages of a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Combined text from all pages as a single string
        
    Raises:
        PDFLoadError: If the PDF cannot be loaded or read
    """
    # Validate file exists
    pdf_path = Path(file_path)
    if not pdf_path.exists():
        logger.error(f"PDF file not found: {file_path}")
        raise PDFLoadError(f"PDF file not found: {file_path}")
    
    if not pdf_path.suffix.lower() == '.pdf':
        logger.error(f"File is not a PDF: {file_path}")
        raise PDFLoadError(f"File is not a PDF: {file_path}")
    
    doc = None
    try:
        # Open PDF document
        doc = fitz.open(file_path)
        
        # Check if PDF has pages
        if doc.page_count == 0:
            logger.error(f"PDF has no pages: {file_path}")
            raise PDFLoadError(f"PDF has no pages: {file_path}")
        
        logger.info(f"Loading PDF: {file_path} ({doc.page_count} pages)")
        
        # Extract text from each page
        text_chunks = []
        empty_pages = 0
        
        for page_num in range(doc.page_count):
            try:
                page = doc[page_num]
                text = page.get_text()
                
                if text.strip():
                    text_chunks.append(text)
                    logger.debug(f"Page {page_num + 1}: extracted {len(text)} characters")
                else:
                    empty_pages += 1
                    logger.warning(f"Page {page_num + 1}: empty or no extractable text")
                    
            except Exception as e:
                logger.error(f"Error extracting text from page {page_num + 1}: {e}")
                continue
        
        if not text_chunks:
            raise PDFLoadError(f"No text could be extracted from PDF: {file_path}")
        
        # Combine all text
        combined_text = "\n".join(text_chunks)
        
        logger.info(
            f"Extraction complete: {len(combined_text)} characters from "
            f"{len(text_chunks)} pages ({empty_pages} empty pages skipped)"
        )
        
        return combined_text
        
    except fitz.FileDataError as e:
        logger.error(f"Invalid or corrupted PDF file: {file_path}", exc_info=True)
        raise PDFLoadError(f"Invalid or corrupted PDF file: {file_path}") from e
        
    except PDFLoadError:
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error loading PDF {file_path}: {e}", exc_info=True)
        raise PDFLoadError(f"Failed to load PDF {file_path}: {str(e)}") from e
        
    finally:
        # Ensure PDF is always closed
        if doc is not None:
            try:
                doc.close()
                logger.debug(f"PDF document closed: {file_path}")
            except Exception as e:
                logger.warning(f"Error closing PDF document: {e}")


def load_multiple_pdfs(file_paths: list[str]) -> str:
    """
    Load and combine text from multiple PDF files.
    
    Args:
        file_paths: List of PDF file paths
        
    Returns:
        Combined text from all PDFs
        
    Raises:
        PDFLoadError: If any PDF cannot be loaded
    """
    if not file_paths:
        logger.error("No PDF files provided")
        raise PDFLoadError("No PDF files provided")
    
    if not isinstance(file_paths, list):
        logger.error("file_paths must be a list")
        raise PDFLoadError("file_paths must be a list")
    
    all_text = []
    failed_files = []
    
    for idx, file_path in enumerate(file_paths, 1):
        try:
            logger.info(f"Processing PDF {idx}/{len(file_paths)}: {file_path}")
            text = load_pdf(file_path)
            all_text.append(text)
            
        except PDFLoadError as e:
            logger.error(f"Failed to load {file_path}: {e}")
            failed_files.append((file_path, str(e)))
            continue
    
    if not all_text:
        raise PDFLoadError(f"Failed to load any PDFs. All {len(file_paths)} files failed.")
    
    if failed_files:
        logger.warning(
            f"Loaded {len(all_text)}/{len(file_paths)} PDFs. "
            f"Failed: {', '.join(f[0] for f in failed_files)}"
        )
    
    combined = "\n\n--- NEXT DOCUMENT ---\n\n".join(all_text)
    logger.info(f"Successfully loaded {len(all_text)} PDF files ({len(combined)} total characters)")
    
    return combined


# For future v2: OCR support for scanned PDFs
# def load_pdf_with_ocr(file_path: str) -> str:
#     """Load PDF with OCR support for scanned documents."""
#     # Implementation with pytesseract
#     pass