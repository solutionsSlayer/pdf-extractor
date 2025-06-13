#!/usr/bin/env python3
"""
CLI for PDF Technical Sheet Extractor

Usage:
    python cli.py --file path/to/file.pdf
    python cli.py --folder FT/unilever
    python cli.py --folder FT/charles_alice
    python cli.py --folder FT --output ./extracted_data
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from extractor import TechnicalSheetExtractor, ExtractionConfig


def get_pdf_files_from_folder(folder_path: Path) -> List[Path]:
    """
    Get all PDF files from a folder.
    
    Args:
        folder_path: Path to the folder
        
    Returns:
        List of PDF file paths
    """
    if not folder_path.exists():
        print(f"❌ Folder not found: {folder_path}")
        return []
    
    if not folder_path.is_dir():
        print(f"❌ Path is not a directory: {folder_path}")
        return []
    
    pdf_files = list(folder_path.glob("*.pdf"))
    
    if not pdf_files:
        print(f"⚠️  No PDF files found in: {folder_path}")
        return []
    
    print(f"📁 Found {len(pdf_files)} PDF files in: {folder_path}")
    return pdf_files


def extract_single_file(
    file_path: Path, 
    output_dir: Optional[Path] = None,
    config: Optional[ExtractionConfig] = None
) -> bool:
    """
    Extract a single PDF file.
    
    Args:
        file_path: Path to the PDF file
        output_dir: Output directory
        config: Extraction configuration
        
    Returns:
        True if successful, False otherwise
    """
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    if file_path.suffix.lower() != '.pdf':
        print(f"❌ File is not a PDF: {file_path}")
        return False
    
    extractor = TechnicalSheetExtractor(config)
    saved_files = extractor.extract_and_save(file_path, output_dir)
    
    return saved_files is not None


def extract_folder(
    folder_path: Path, 
    output_dir: Optional[Path] = None,
    config: Optional[ExtractionConfig] = None
) -> bool:
    """
    Extract all PDF files from a folder.
    
    Args:
        folder_path: Path to the folder
        output_dir: Output directory
        config: Extraction configuration
        
    Returns:
        True if at least one file was successfully extracted
    """
    pdf_files = get_pdf_files_from_folder(folder_path)
    
    if not pdf_files:
        return False
    
    extractor = TechnicalSheetExtractor(config)
    results = extractor.extract_and_save_multiple(pdf_files, output_dir)
    
    # Print summary
    extractor.print_extraction_summary(results)
    
    # Return True if at least one extraction was successful
    successful_count = sum(1 for result in results.values() if result is not None)
    return successful_count > 0


def create_config(args) -> ExtractionConfig:
    """
    Create extraction configuration from CLI arguments.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        ExtractionConfig instance
    """
    config = ExtractionConfig()
    
    # Set output directory if provided
    if args.output:
        config.output_directory = str(args.output)
    
    # Set image extraction options
    if hasattr(args, 'no_images') and args.no_images:
        config.write_images = False
    
    # Set progress display
    if hasattr(args, 'quiet') and args.quiet:
        config.show_progress = False
    
    return config


def validate_ft_path(path_str: str) -> Path:
    """
    Validate and resolve FT folder paths.
    
    Args:
        path_str: Path string from command line
        
    Returns:
        Resolved Path object
    """
    path = Path(path_str)
    
    # If it's a relative path starting with FT, make it absolute
    if not path.is_absolute() and path.parts[0] == 'FT':
        # Assume FT is in the current working directory
        path = Path.cwd() / path
    
    return path


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Extract technical sheets from PDF files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract a single file
  python cli.py --file FT/unilever/3011360006707.pdf
  
  # Extract all files from unilever folder
  python cli.py --folder FT/unilever
  
  # Extract with custom output directory
  python cli.py --folder FT/unilever --output ./extracted_data
  
  # Extract without images (faster processing)
  python cli.py --folder FT/charles_alice --no-images
        """
    )
    
    # Main action group (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        '--file', '-f',
        type=str,
        help='Extract a single PDF file'
    )
    action_group.add_argument(
        '--folder', '-d',
        type=str,
        help='Extract all PDF files from a folder (e.g., FT/unilever, FT/charles_alice)'
    )
    
    # Optional arguments
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output directory for extracted files (default: current directory)'
    )
    
    parser.add_argument(
        '--no-images',
        action='store_true',
        help='Skip image extraction (faster processing)'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress output'
    )
    
    args = parser.parse_args()
    
    # Create configuration
    config = create_config(args)
    
    # Resolve output directory
    output_dir = None
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Output directory: {output_dir.absolute()}")
    
    success = False
    
    try:
        if args.file:
            # Extract single file
            file_path = validate_ft_path(args.file)
            print(f"🎯 Extracting single file: {file_path}")
            success = extract_single_file(file_path, output_dir, config)
            
        elif args.folder:
            # Extract folder
            folder_path = validate_ft_path(args.folder)
            print(f"🎯 Extracting folder: {folder_path}")
            success = extract_folder(folder_path, output_dir, config)
    
    except KeyboardInterrupt:
        print(f"\n⚠️  Extraction interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
    
    # Exit with appropriate code
    if success:
        print(f"\n🎉 Extraction completed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ Extraction failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 