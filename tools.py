"""
PDF Processing Tools for CBSE Multi-Agent System

This module provides tools for downloading and extracting text from PDF documents,
particularly useful for processing educational materials and NCERT textbooks.
"""

import os
import requests
import tempfile
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import PyPDF2
import pdfplumber
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    A class to handle PDF downloading and text extraction operations.
    """
    
    def __init__(self):
        self.session = requests.Session()
        # Set a user agent to avoid blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def download_pdf(self, url: str, timeout: int = 30) -> Optional[bytes]:
        """
        Download PDF from a URL and return bytes content.
        
        Args:
            url (str): The URL of the PDF to download
            timeout (int): Request timeout in seconds
            
        Returns:
            Optional[bytes]: PDF content as bytes, or None if failed
        """
        try:
            logger.info(f"Downloading PDF from: {url}")
            
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                logger.error(f"Invalid URL format: {url}")
                return None
            
            # Download the PDF
            response = self.session.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            
            # Check if response is actually a PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and not url.lower().endswith('.pdf'):
                logger.warning(f"URL might not be a PDF. Content-Type: {content_type}")
            
            # Read content
            pdf_content = response.content
            logger.info(f"Successfully downloaded PDF ({len(pdf_content)} bytes)")
            
            return pdf_content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading PDF from {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading PDF: {str(e)}")
            return None
    
    def extract_text_pypdf2(self, pdf_content: bytes) -> str:
        """
        Extract text from PDF using PyPDF2 library.
        
        Args:
            pdf_content (bytes): PDF content as bytes
            
        Returns:
            str: Extracted text content
        """
        try:
            text_content = []
            pdf_file = BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            logger.info(f"Processing PDF with {len(pdf_reader.pages)} pages using PyPDF2")
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content.append(f"\n--- Page {page_num} ---\n")
                        text_content.append(page_text)
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num}: {str(e)}")
                    continue
            
            return '\n'.join(text_content)
            
        except Exception as e:
            logger.error(f"Error extracting text with PyPDF2: {str(e)}")
            return ""
    
    def extract_text_pdfplumber(self, pdf_content: bytes) -> str:
        """
        Extract text from PDF using pdfplumber library (more accurate).
        
        Args:
            pdf_content (bytes): PDF content as bytes
            
        Returns:
            str: Extracted text content
        """
        try:
            text_content = []
            pdf_file = BytesIO(pdf_content)
            
            with pdfplumber.open(pdf_file) as pdf:
                logger.info(f"Processing PDF with {len(pdf.pages)} pages using pdfplumber")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            text_content.append(f"\n--- Page {page_num} ---\n")
                            text_content.append(page_text)
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num}: {str(e)}")
                        continue
            
            return '\n'.join(text_content)
            
        except Exception as e:
            logger.error(f"Error extracting text with pdfplumber: {str(e)}")
            return ""
    
    def process_pdf_from_url(self, url: str, method: str = "pdfplumber") -> Dict[str, Any]:
        """
        Download and extract text from a PDF URL.
        
        Args:
            url (str): The URL of the PDF to process
            method (str): Extraction method ("pdfplumber" or "pypdf2")
            
        Returns:
            Dict[str, Any]: Result containing success status, text content, and metadata
        """
        result = {
            "success": False,
            "text": "",
            "error": None,
            "metadata": {
                "url": url,
                "method": method,
                "pages_processed": 0,
                "content_length": 0
            }
        }
        
        try:
            # Download PDF
            pdf_content = self.download_pdf(url)
            if not pdf_content:
                result["error"] = "Failed to download PDF"
                return result
            
            # Extract text based on method
            if method.lower() == "pdfplumber":
                extracted_text = self.extract_text_pdfplumber(pdf_content)
            else:
                extracted_text = self.extract_text_pypdf2(pdf_content)
            
            if not extracted_text.strip():
                result["error"] = "No text could be extracted from PDF"
                return result
            
            # Update result
            result["success"] = True
            result["text"] = extracted_text
            result["metadata"]["content_length"] = len(extracted_text)
            result["metadata"]["pages_processed"] = extracted_text.count("--- Page")
            
            logger.info(f"Successfully processed PDF: {len(extracted_text)} characters extracted")
            
            return result
            
        except Exception as e:
            result["error"] = f"Unexpected error processing PDF: {str(e)}"
            logger.error(result["error"])
            return result


# Global PDF processor instance
pdf_processor = PDFProcessor()


def download_and_parse_pdf(url: str, extraction_method: str = "pdfplumber") -> str:
    """
    Main tool function: Download a PDF from URL and return extracted text.
    
    This tool is designed to be used by agents in the CBSE multi-agent system
    to process educational PDFs and extract text content for analysis.
    
    Args:
        url (str): The URL of the PDF to download and parse
        extraction_method (str): Method to use for text extraction 
                               ("pdfplumber" or "pypdf2"). Default: "pdfplumber"
    
    Returns:
        str: The complete text content extracted from the PDF
    
    Examples:
        # Download and parse an NCERT textbook
        text = download_and_parse_pdf("https://ncert.nic.in/textbook/pdf/hemg108.pdf")
        
        # Use alternative extraction method
        text = download_and_parse_pdf("https://example.com/book.pdf", "pypdf2")
    """
    try:
        logger.info(f"Processing PDF from URL: {url}")
        
        # Validate inputs
        if not url or not isinstance(url, str):
            return "Error: Invalid URL provided"
        
        if extraction_method not in ["pdfplumber", "pypdf2"]:
            extraction_method = "pdfplumber"
            logger.warning(f"Invalid extraction method, using default: {extraction_method}")
        
        # Process the PDF
        result = pdf_processor.process_pdf_from_url(url, extraction_method)
        
        if result["success"]:
            metadata = result["metadata"]
            header = f"""
=== PDF Processing Results ===
Source URL: {metadata['url']}
Pages Processed: {metadata['pages_processed']}
Content Length: {metadata['content_length']} characters
Extraction Method: {metadata['method']}
=== Text Content ===

"""
            return header + result["text"]
        else:
            error_msg = f"Failed to process PDF: {result['error']}"
            logger.error(error_msg)
            return error_msg
            
    except Exception as e:
        error_msg = f"Unexpected error in download_and_parse_pdf: {str(e)}"
        logger.error(error_msg)
        return error_msg


def get_pdf_metadata(url: str) -> Dict[str, Any]:
    """
    Get metadata about a PDF without downloading the full content.
    
    Args:
        url (str): The URL of the PDF
        
    Returns:
        Dict[str, Any]: Metadata information about the PDF
    """
    try:
        response = pdf_processor.session.head(url, timeout=10)
        response.raise_for_status()
        
        return {
            "content_type": response.headers.get('content-type', ''),
            "content_length": response.headers.get('content-length', ''),
            "last_modified": response.headers.get('last-modified', ''),
            "status_code": response.status_code,
            "url": url
        }
    except Exception as e:
        return {"error": str(e), "url": url}


# Tool registry for easy integration with agents
AVAILABLE_TOOLS = {
    "download_and_parse_pdf": {
        "function": download_and_parse_pdf,
        "description": "Download a PDF from a URL and extract all text content",
        "parameters": {
            "url": "The URL of the PDF to download and parse",
            "extraction_method": "Text extraction method (pdfplumber or pypdf2)"
        }
    },
    "get_pdf_metadata": {
        "function": get_pdf_metadata,
        "description": "Get metadata about a PDF without downloading full content",
        "parameters": {
            "url": "The URL of the PDF to analyze"
        }
    }
}


if __name__ == "__main__":
    # Test the PDF processing functionality
    test_url = "https://ncert.nic.in/textbook/pdf/hemg108.pdf"  # NCERT Hindi Class 8
    print("Testing PDF processing...")
    
    # Test metadata
    metadata = get_pdf_metadata(test_url)
    print(f"Metadata: {metadata}")
    
    # Test text extraction
    text = download_and_parse_pdf(test_url)
    print(f"Extracted text length: {len(text)}")
    print("First 500 characters:")
    print(text[:500]) 
