"""
PDF extraction utilities for CV analysis
"""
import pdfplumber
from typing import Tuple
import io


class PDFExtractor:
    """Extract text content from PDF files."""

    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                    text += "\n"
                return text.strip()
        except Exception as e:
            raise Exception(f"Failed to extract PDF: {str(e)}")

    @staticmethod
    def extract_text_from_bytes(file_bytes: bytes) -> str:
        """
        Extract text from PDF bytes.
        
        Args:
            file_bytes: PDF file as bytes
            
        Returns:
            Extracted text content
        """
        if not file_bytes or not isinstance(file_bytes, bytes):
            raise Exception("Invalid file bytes provided")
        
        try:
            pdf_file = io.BytesIO(file_bytes)
            with pdfplumber.open(pdf_file) as pdf:
                if not pdf.pages:
                    raise Exception("PDF has no pages")
                
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
                        text += "\n"
                
                if not text.strip():
                    raise Exception("No text could be extracted from PDF")
                
                return text.strip()
        except Exception as e:
            raise Exception(f"Failed to extract PDF from bytes: {str(e)}")

    @staticmethod
    def validate_pdf(file_bytes: bytes) -> bool:
        """
        Validate if bytes represent a valid PDF.
        
        Args:
            file_bytes: File bytes to validate
            
        Returns:
            True if valid PDF, False otherwise
        """
        try:
            pdf_file = io.BytesIO(file_bytes)
            with pdfplumber.open(pdf_file) as pdf:
                return len(pdf.pages) > 0
        except Exception:
            return False
