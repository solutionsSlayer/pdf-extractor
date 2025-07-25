"""
Main orchestrator for technical sheet extraction using Docling and LangChain
"""

from pathlib import Path
from typing import Union, List, Dict, Any, Optional
import json

from .config import ExtractionConfig
from .pdf_extractor import PDFExtractor
from .langchain_extractor import LangChainExtractor
from .file_manager import FileManager


class TechnicalSheetExtractor:
    """
    Main class that orchestrates PDF extraction and file management.
    
    Uses composition pattern with PDFExtractor, LangChainExtractor and FileManager 
    to handle different aspects of the extraction process.
    """
    
    def __init__(self, config: Optional[ExtractionConfig] = None):
        """
        Initialize the technical sheet extractor.
        
        Args:
            config: Configuration for extraction. If None, uses default config.
        """
        self.config = config or ExtractionConfig()
        self.pdf_extractor = PDFExtractor(self.config)
        self.langchain_extractor = LangChainExtractor()
        self.file_manager = FileManager(self.config)
    
    def extract_and_save(
        self, 
        pdf_path: Union[str, Path], 
        output_directory: Optional[Union[str, Path]] = None,
        include_langchain: bool = True
    ) -> Optional[Dict[str, Path]]:
        """
        Extract a PDF and save the results.
        
        Args:
            pdf_path: Path to the PDF file
            output_directory: Directory to save results. If None, uses config or current dir.
            include_langchain: Whether to include LangChain structured extraction
            
        Returns:
            Dictionary with paths to saved files, or None if extraction failed
        """
        print(f"🚀 Starting extraction for: {Path(pdf_path).name}")
        
        try:
            # Step 1: Extract PDF content with Docling
            extracted_data = self.pdf_extractor.extract(pdf_path)
            
            if extracted_data is None:
                print(f"❌ No data extracted from {Path(pdf_path).name}")
                return None
            
            # Step 2: Save extracted data (markdown + metadata)
            saved_files = self.file_manager.save_extracted_data(
                extracted_data, 
                pdf_path, 
                output_directory
            )
            
            # Step 3: LangChain structured extraction (if enabled)
            if include_langchain and saved_files and 'markdown' in saved_files:
                try:
                    print(f"🧠 Running LangChain analysis...")
                    
                    # Extract structured data from markdown
                    langchain_result = self.langchain_extractor.extract_from_text(
                        extracted_data, 
                        str(Path(pdf_path).name)
                    )
                    
                    if langchain_result.success and langchain_result.product_sheet:
                        # Save structured JSON
                        json_path = self._save_langchain_json(
                            langchain_result, 
                            pdf_path, 
                            output_directory
                        )
                        
                        if json_path:
                            saved_files['structured_json'] = json_path
                            print(f"📊 Structured data saved: {json_path}")
                            print(f"🎯 Confidence score: {langchain_result.confidence_score:.2f}")
                    else:
                        print(f"⚠️  LangChain extraction failed: {langchain_result.errors}")
                        
                except Exception as e:
                    print(f"⚠️  LangChain analysis failed: {e}")
            
            print(f"✅ Extraction completed for: {Path(pdf_path).name}")
            return saved_files
            
        except Exception as e:
            print(f"❌ Extraction failed for {Path(pdf_path).name}: {e}")
            return None
    
    def _save_langchain_json(
        self, 
        langchain_result, 
        pdf_path: Union[str, Path], 
        output_directory: Optional[Union[str, Path]] = None
    ) -> Optional[Path]:
        """
        Save LangChain structured result as JSON.
        
        Args:
            langchain_result: Result from LangChain extraction
            pdf_path: Original PDF path
            output_directory: Output directory
            
        Returns:
            Path to saved JSON file or None if failed
        """
        try:
            pdf_path = Path(pdf_path)
            pdf_name = pdf_path.stem
            
            # Determine output directory
            if output_directory:
                output_dir = Path(output_directory) / pdf_name
            else:
                output_dir = Path(self.config.output_directory) / pdf_name
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create structured JSON
            json_data = {
                "extraction_metadata": {
                    "success": langchain_result.success,
                    "confidence_score": langchain_result.confidence_score,
                    "errors": langchain_result.errors,
                    "warnings": langchain_result.warnings
                },
                "product_data": langchain_result.product_sheet.model_dump() if langchain_result.product_sheet else None
            }
            
            # Save JSON file
            json_file = output_dir / f"structured_{pdf_name}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            return json_file
            
        except Exception as e:
            print(f"❌ Failed to save LangChain JSON: {e}")
            return None
    
    def extract_and_save_multiple(
        self, 
        pdf_paths: List[Union[str, Path]], 
        output_directory: Optional[Union[str, Path]] = None,
        include_langchain: bool = True
    ) -> Dict[str, Optional[Dict[str, Path]]]:
        """
        Extract multiple PDFs and save results.
        
        Args:
            pdf_paths: List of PDF file paths
            output_directory: Directory to save results
            include_langchain: Whether to include LangChain structured extraction
            
        Returns:
            Dictionary mapping filenames to their saved file paths
        """
        print(f"🚀 Starting batch extraction for {len(pdf_paths)} files")
        
        results = {}
        successful_extractions = 0
        
        for pdf_path in pdf_paths:
            filename = Path(pdf_path).name
            saved_files = self.extract_and_save(pdf_path, output_directory, include_langchain)
            results[filename] = saved_files
            
            if saved_files is not None:
                successful_extractions += 1
        
        print(f"📊 Batch extraction completed: {successful_extractions}/{len(pdf_paths)} successful")
        return results
    
    def extract_only(self, pdf_path: Union[str, Path]) -> Optional[str]:
        """
        Extract PDF content without saving to files.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted markdown content or None if extraction failed
        """
        return self.pdf_extractor.extract(pdf_path)
    
    def extract_structured_only(self, pdf_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """
        Extract PDF and return only the structured JSON data.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Structured data dictionary or None if extraction failed
        """
        try:
            # Extract markdown with Docling
            extracted_data = self.pdf_extractor.extract(pdf_path)
            
            if not extracted_data:
                return None
            
            # Extract structured data with LangChain
            langchain_result = self.langchain_extractor.extract_from_text(
                extracted_data, 
                str(Path(pdf_path).name)
            )
            
            if langchain_result.success and langchain_result.product_sheet:
                return {
                    "extraction_metadata": {
                        "success": langchain_result.success,
                        "confidence_score": langchain_result.confidence_score,
                        "errors": langchain_result.errors,
                        "warnings": langchain_result.warnings
                    },
                    "product_data": langchain_result.product_sheet.model_dump()
                }
            
            return None
            
        except Exception as e:
            print(f"❌ Structured extraction failed: {e}")
            return None

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