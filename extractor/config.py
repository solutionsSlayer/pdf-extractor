"""
Configuration settings for PDF extraction
"""

from dataclasses import dataclass
from typing import Tuple, Optional
from pathlib import Path


@dataclass
class ExtractionConfig:
    """Configuration for PDF extraction parameters"""
    
    # Extraction options
    page_chunks: bool = True
    extract_words: bool = True
    
    # Table extraction
    table_strategy: str = "lines_strict"
    
    # Image extraction
    write_images: bool = True
    image_format: str = "png"
    dpi: int = 200
    image_path: str = "./extracted_images"
    
    # Layout options
    margins: Tuple[int, int, int, int] = (5, 5, 5, 5)
    show_progress: bool = True
    
    # Output settings
    output_directory: Optional[str] = "./extracted_data"
    save_raw_text: bool = True
    
    def to_pymupdf_kwargs(self, pdf_name: Optional[str] = None) -> dict:
        """
        Convert config to pymupdf4llm keyword arguments.
        
        Args:
            pdf_name: Name of the PDF file (without extension) to create organized image folders
            
        Returns:
            Dictionary of pymupdf4llm parameters
        """
        # Organize images by PDF file name if provided
        image_path = self.image_path
        if pdf_name and self.write_images:
            image_path = str(Path(self.image_path) / pdf_name)
        
        return {
            "page_chunks": self.page_chunks,
            "extract_words": self.extract_words,
            "table_strategy": self.table_strategy,
            "write_images": self.write_images,
            "image_format": self.image_format,
            "dpi": self.dpi,
            "image_path": image_path,
            "margins": self.margins,
            "show_progress": self.show_progress
        } 