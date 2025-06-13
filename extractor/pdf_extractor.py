"""
PDF extraction module for technical sheets
"""

import pymupdf4llm
from pathlib import Path
from typing import Optional, Union, List, Dict, Any

from .config import ExtractionConfig


class PDFExtractor:
    """
    Handles PDF extraction using pymupdf4llm library.
    
    Follows Single Responsibility Principle by focusing only on PDF extraction logic.
    """
    
    def __init__(self, config: Optional[ExtractionConfig] = None):
        """
        Initialize the PDF extractor with configuration.
        
        Args:
            config: Extraction configuration. If None, uses default configuration.
        """
        self.config = config or ExtractionConfig()
    
    def extract(self, pdf_path: Union[str, Path]) -> Optional[Union[List[Dict[str, Any]], str]]:
        """
        Extract content from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file to extract
            
        Returns:
            Extracted data structure or None if extraction fails
            
        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            Exception: If extraction fails
        """
        pdf_path = self._validate_pdf_path(pdf_path)
        
        print(f"🔄 Extracting: {pdf_path.name}")
        
        try:
            # Use PDF name for organized image storage
            pdf_name = pdf_path.stem
            
            extracted_data = pymupdf4llm.to_markdown(
                str(pdf_path),
                **self.config.to_pymupdf_kwargs(pdf_name)
            )
            
            print(f"✅ Successfully extracted: {pdf_path.name}")
            return extracted_data
            
        except Exception as e:
            print(f"❌ Extraction failed for {pdf_path.name}: {e}")
            raise
    
    def _validate_pdf_path(self, pdf_path: Union[str, Path]) -> Path:
        """
        Validate and convert PDF path to Path object.
        
        Args:
            pdf_path: Path to validate
            
        Returns:
            Validated Path object
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a PDF
        """
        path = Path(pdf_path)
        
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {path}")
        
        if path.suffix.lower() != '.pdf':
            raise ValueError(f"File is not a PDF: {path}")
        
        return path
    
    def extract_multiple(self, pdf_paths: List[Union[str, Path]]) -> Dict[str, Optional[Union[List[Dict[str, Any]], str]]]:
        """
        Extract content from multiple PDF files.
        
        Args:
            pdf_paths: List of PDF file paths to extract
            
        Returns:
            Dictionary mapping file names to extracted data
        """
        results = {}
        
        for pdf_path in pdf_paths:
            try:
                path = Path(pdf_path)
                results[path.name] = self.extract(pdf_path)
            except Exception as e:
                print(f"❌ Failed to extract {pdf_path}: {e}")
                results[Path(pdf_path).name] = None
        
        return results 