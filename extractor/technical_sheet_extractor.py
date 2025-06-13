"""
Main orchestrator for technical sheet extraction
"""

from pathlib import Path
from typing import Union, List, Dict, Any, Optional

from .config import ExtractionConfig
from .pdf_extractor import PDFExtractor
from .file_manager import FileManager


class TechnicalSheetExtractor:
    """
    Main class that orchestrates PDF extraction and file management.
    
    Uses composition pattern with PDFExtractor and FileManager to handle
    different aspects of the extraction process.
    """
    
    def __init__(self, config: Optional[ExtractionConfig] = None):
        """
        Initialize the technical sheet extractor.
        
        Args:
            config: Configuration for extraction. If None, uses default config.
        """
        self.config = config or ExtractionConfig()
        self.pdf_extractor = PDFExtractor(self.config)
        self.file_manager = FileManager(self.config)
    
    def extract_and_save(
        self, 
        pdf_path: Union[str, Path], 
        output_directory: Optional[Union[str, Path]] = None
    ) -> Optional[Dict[str, Path]]:
        """
        Extract a PDF and save the results.
        
        Args:
            pdf_path: Path to the PDF file
            output_directory: Directory to save results. If None, uses config or current dir.
            
        Returns:
            Dictionary with paths to saved files, or None if extraction failed
        """
        print(f"🚀 Starting extraction for: {Path(pdf_path).name}")
        
        try:
            # Extract PDF content
            extracted_data = self.pdf_extractor.extract(pdf_path)
            
            if extracted_data is None:
                print(f"❌ No data extracted from {Path(pdf_path).name}")
                return None
            
            # Save extracted data
            saved_files = self.file_manager.save_extracted_data(
                extracted_data, 
                pdf_path, 
                output_directory
            )
            
            print(f"✅ Extraction completed for: {Path(pdf_path).name}")
            return saved_files
            
        except Exception as e:
            print(f"❌ Extraction failed for {Path(pdf_path).name}: {e}")
            return None
    
    def extract_and_save_multiple(
        self, 
        pdf_paths: List[Union[str, Path]], 
        output_directory: Optional[Union[str, Path]] = None
    ) -> Dict[str, Optional[Dict[str, Path]]]:
        """
        Extract multiple PDFs and save results.
        
        Args:
            pdf_paths: List of PDF file paths
            output_directory: Directory to save results
            
        Returns:
            Dictionary mapping filenames to their saved file paths
        """
        print(f"🚀 Starting batch extraction for {len(pdf_paths)} files")
        
        results = {}
        successful_extractions = 0
        
        for pdf_path in pdf_paths:
            filename = Path(pdf_path).name
            saved_files = self.extract_and_save(pdf_path, output_directory)
            results[filename] = saved_files
            
            if saved_files is not None:
                successful_extractions += 1
        
        print(f"📊 Batch extraction completed: {successful_extractions}/{len(pdf_paths)} successful")
        return results
    
    def extract_only(self, pdf_path: Union[str, Path]) -> Optional[Union[List[Dict[str, Any]], str]]:
        """
        Extract PDF content without saving to files.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted data or None if extraction failed
        """
        return self.pdf_extractor.extract(pdf_path)
    
    def print_extraction_summary(self, results: Dict[str, Optional[Dict[str, Path]]]) -> None:
        """
        Print a summary of extraction results.
        
        Args:
            results: Results from extract_and_save_multiple
        """
        total_files = len(results)
        successful_files = sum(1 for result in results.values() if result is not None)
        failed_files = total_files - successful_files
        
        print("\n" + "="*50)
        print("📋 EXTRACTION SUMMARY")
        print("="*50)
        print(f"📄 Total files processed: {total_files}")
        print(f"✅ Successful extractions: {successful_files}")
        print(f"❌ Failed extractions: {failed_files}")
        
        if successful_files > 0:
            print(f"\n📁 Files saved:")
            for filename, saved_files in results.items():
                if saved_files:
                    print(f"  📋 {filename}:")
                    for file_type, file_path in saved_files.items():
                        print(f"    • {file_type}: {file_path}")
        
        if failed_files > 0:
            print(f"\n❌ Failed files:")
            for filename, saved_files in results.items():
                if saved_files is None:
                    print(f"  • {filename}") 