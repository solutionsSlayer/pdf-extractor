"""
PDF extraction module for technical sheets
"""

from docling.document_converter import DocumentConverter
from pathlib import Path
from typing import Optional, Union, List, Dict, Any

from .config import ExtractionConfig


class PDFExtractor:
    """
    Handles PDF extraction using Docling library.
    
    Follows Single Responsibility Principle by focusing only on PDF extraction logic.
    """
    
    def __init__(self, config: Optional[ExtractionConfig] = None):
        """
        Initialize the PDF extractor with configuration.
        
        Args:
            config: Extraction configuration. If None, uses default configuration.
        """
        self.config = config or ExtractionConfig()
        
        # Initialize Docling converter with default configuration
        # The new Docling API handles most settings automatically
        self.converter = DocumentConverter()
    
    def extract(self, pdf_path: Union[str, Path]) -> Optional[str]:
        """
        Extract content from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file to extract
            
        Returns:
            Extracted markdown content or None if extraction fails
            
        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            Exception: If extraction fails
        """
        pdf_path = self._validate_pdf_path(pdf_path)
        
        print(f"🔄 Extracting: {pdf_path.name}")
        
        try:
            # Convert PDF to document using Docling
            result = self.converter.convert(str(pdf_path))
            
            # Extract markdown content
            markdown_content = result.document.export_to_markdown()
            
            # Handle images if enabled - simplified approach
            if self.config.write_images:
                self._handle_images(pdf_path)
            
            print(f"✅ Successfully extracted: {pdf_path.name}")
            return markdown_content
            
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
    
    def _handle_images(self, pdf_path: Path) -> None:
        """
        Handle image extraction for the PDF.
        Note: With Docling 2.x, images are handled automatically during conversion
        
        Args:
            pdf_path: Original PDF path for reference
        """
        try:
            # Create image directory structure
            pdf_name = pdf_path.stem
            image_dir = Path(self.config.image_path) / pdf_name
            image_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"🖼️  Image directory prepared: {image_dir}")
                    
        except Exception as e:
            print(f"⚠️  Warning: Could not prepare image directory: {e}")
    
    def extract_multiple(self, pdf_paths: List[Union[str, Path]]) -> Dict[str, Optional[str]]:
        """
        Extract content from multiple PDF files.
        
        Args:
            pdf_paths: List of PDF file paths to extract
            
        Returns:
            Dictionary mapping file names to extracted markdown content
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