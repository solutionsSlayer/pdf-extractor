"""
Configuration settings for PDF extraction using Docling
"""

from dataclasses import dataclass
from typing import Tuple, Optional
from pathlib import Path


@dataclass
class ExtractionConfig:
    """Configuration for PDF extraction parameters using Docling"""
    
    # Extraction options
    extract_tables: bool = True
    extract_images: bool = True
    
    # Image extraction
    write_images: bool = True
    image_format: str = "png"
    dpi: int = 200
    image_path: str = "./extracted_images"
    
    # Layout and processing options
    ocr_enabled: bool = True
    table_structure_recognition: bool = True
    show_progress: bool = True
    
    # Output settings
    output_directory: Optional[str] = "./extracted_data"
    save_as_markdown: bool = True  # Save as .md files
    save_raw_text: bool = False    # Default to False since we prefer markdown
    
    def to_docling_kwargs(self, pdf_name: Optional[str] = None) -> dict:
        """
        Convert config to Docling DocumentConverter keyword arguments.
        
        Args:
            pdf_name: Name of the PDF file (without extension) to create organized image folders
            
        Returns:
            Dictionary of Docling parameters optimized for markdown output
        """
        # Organize images by PDF file name if provided
        image_path = self.image_path
        if pdf_name and self.write_images:
            image_path = str(Path(self.image_path) / pdf_name)
        
        return {
            "extract_tables": self.extract_tables,
            "extract_images": self.extract_images,
            "images_scale": self.dpi / 72.0,  # Convert DPI to scale factor
            "generate_page_images": self.write_images,
            "image_format": self.image_format,
            "image_path": image_path,
            "ocr_enabled": self.ocr_enabled,
            "table_structure_recognition": self.table_structure_recognition,
            "show_progress": self.show_progress
        } 