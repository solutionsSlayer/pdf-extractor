"""
File management module for saving extracted data
"""

import json
from pathlib import Path
from typing import Union, List, Dict, Any, Optional
from datetime import datetime

from .config import ExtractionConfig


class FileManager:
    """
    Handles file operations for saving extracted PDF data.
    
    Follows Single Responsibility Principle by focusing only on file operations.
    """
    
    def __init__(self, config: Optional[ExtractionConfig] = None):
        """
        Initialize the file manager with configuration.
        
        Args:
            config: Extraction configuration. If None, uses default configuration.
        """
        self.config = config or ExtractionConfig()
    
    def save_extracted_data(
        self, 
        extracted_data: str, 
        original_file_path: Union[str, Path],
        output_directory: Optional[Union[str, Path]] = None
    ) -> Dict[str, Path]:
        """
        Save extracted data to files in a dedicated folder named after the PDF file.
        
        Args:
            extracted_data: The extracted data to save
            original_file_path: Path to the original PDF file
            output_directory: Directory to save files. If None, uses current directory.
            
        Returns:
            Dictionary with paths to saved files
        """
        original_path = Path(original_file_path)
        base_name = original_path.stem
        
        # Create a dedicated folder for this PDF file
        output_dir = self._get_output_directory(output_directory)
        pdf_folder = output_dir / base_name
        pdf_folder.mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        
        # Save as Markdown file (default and recommended)
        if self.config.save_as_markdown:
            markdown_file_path = self._save_as_markdown(extracted_data, base_name, pdf_folder)
            saved_files['markdown'] = markdown_file_path
        
        # Save raw extracted data as text (optional, for backup)
        if self.config.save_raw_text:
            text_file_path = self._save_as_text(extracted_data, base_name, pdf_folder)
            saved_files['text'] = text_file_path
        
        # Save metadata
        metadata_file_path = self._save_metadata(extracted_data, original_path, pdf_folder)
        saved_files['metadata'] = metadata_file_path
        
        return saved_files
    
    def _get_output_directory(self, output_directory: Optional[Union[str, Path]]) -> Path:
        """Get and ensure output directory exists."""
        if output_directory:
            output_dir = Path(output_directory)
        elif self.config.output_directory:
            output_dir = Path(self.config.output_directory)
        else:
            output_dir = Path.cwd()
        
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
    
    def _save_as_markdown(
        self, 
        extracted_data: str, 
        base_name: str, 
        output_dir: Path
    ) -> Path:
        """Save extracted data as Markdown file."""
        markdown_file = output_dir / f"extracted_{base_name}.md"
        
        with open(markdown_file, 'w', encoding='utf-8') as f:
            # Add title and metadata
            f.write(f"# {base_name}\n\n")
            f.write(f"*Extracted on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            f.write("---\n\n")
            
            # Direct markdown content from Docling
            f.write(str(extracted_data))
        
        print(f"📄 Markdown saved: {markdown_file}")
        return markdown_file
    
    def _save_as_text(
        self, 
        extracted_data: str, 
        base_name: str, 
        output_dir: Path
    ) -> Path:
        """Save extracted data as plain text file."""
        text_file = output_dir / f"extracted_{base_name}.txt"
        
        with open(text_file, 'w', encoding='utf-8') as f:
            # Convert markdown to plain text by removing markdown syntax
            plain_text = self._markdown_to_text(extracted_data)
            f.write(plain_text)
        
        print(f"💾 Text saved: {text_file}")
        return text_file
    
    def _save_metadata(
        self, 
        extracted_data: Union[List[Dict[str, Any]], str], 
        original_path: Path, 
        output_dir: Path
    ) -> Path:
        """Save extraction metadata as JSON."""
        metadata = self._generate_metadata(extracted_data, original_path)
        metadata_file = output_dir / f"metadata_{original_path.stem}.json"
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Metadata saved: {metadata_file}")
        return metadata_file
    
    def _generate_metadata(
        self, 
        extracted_data: str, 
        original_path: Path
    ) -> Dict[str, Any]:
        """Generate metadata about the extraction."""
        metadata = {
            "extraction_timestamp": datetime.now().isoformat(),
            "original_file": str(original_path),
            "file_size_bytes": original_path.stat().st_size if original_path.exists() else None,
            "extractor_used": "Docling",
            "output_format": "markdown"
        }
        
        # Add data statistics
        content = str(extracted_data)
        metadata.update({
            "total_text_length": len(content),
            "lines_count": len(content.split('\n')),
            "tables_detected": content.count('|'),  # Rough estimate based on markdown table syntax
            "images_detected": content.count('!['),  # Count markdown image references
        })
        
        return metadata
    
    def _markdown_to_text(self, markdown_content: str) -> str:
        """
        Convert markdown to plain text by removing markdown syntax.
        
        Args:
            markdown_content: Markdown content to convert
            
        Returns:
            Plain text content
        """
        import re
        
        # Remove markdown headers
        text = re.sub(r'^#{1,6}\s+', '', markdown_content, flags=re.MULTILINE)
        
        # Remove markdown emphasis
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
        
        # Remove markdown links but keep text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # Remove markdown images
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'[Image: \1]', text)
        
        # Clean up table formatting
        text = re.sub(r'\|', ' ', text)
        text = re.sub(r'-{3,}', '', text)
        
        return text
    
    def save_multiple_extractions(
        self, 
        extractions: Dict[str, str], 
        original_paths: Dict[str, Union[str, Path]],
        output_directory: Optional[Union[str, Path]] = None
    ) -> Dict[str, Dict[str, Path]]:
        """
        Save multiple extraction results.
        
        Args:
            extractions: Dictionary mapping filenames to extracted data
            original_paths: Dictionary mapping filenames to original file paths
            output_directory: Directory to save files
            
        Returns:
            Dictionary mapping filenames to their saved file paths
        """
        all_saved_files = {}
        
        for filename, extracted_data in extractions.items():
            if extracted_data is not None and filename in original_paths:
                saved_files = self.save_extracted_data(
                    extracted_data, 
                    original_paths[filename], 
                    output_directory
                )
                all_saved_files[filename] = saved_files
        
        return all_saved_files 