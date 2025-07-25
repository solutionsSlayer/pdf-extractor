#!/usr/bin/env python3
"""
CLI for PDF Technical Sheet Extractor

Usage:
    python cli.py --file path/to/file.pdf
    python cli.py --folder FT/unilever
    python cli.py --folder FT/charles_alice
    python cli.py --folder FT --output ./extracted_data --structured
"""

import argparse
import sys
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from extractor import TechnicalSheetExtractor, ExtractionConfig
from extractor.langchain_extractor import LangChainExtractor


def setup_logging(quiet: bool = False) -> logging.Logger:
    """Configure le système de logging."""
    level = logging.WARNING if quiet else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger(__name__)


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


def perform_structured_extraction(
    file_path: Path, 
    langchain_extractor: LangChainExtractor,
    logger: logging.Logger
) -> Optional[Dict[str, Any]]:
    """
    Effectue l'extraction structurée avec LangChain sur un fichier markdown.
    
    Args:
        file_path: Chemin vers le fichier PDF original
        langchain_extractor: Instance de l'extracteur LangChain
        logger: Logger pour les messages
        
    Returns:
        Dictionnaire avec les résultats de l'extraction structurée ou None
    """
    # Recherche du fichier markdown correspondant
    markdown_file = Path("extracted_data") / file_path.stem / f"extracted_{file_path.stem}.md"
    
    if not markdown_file.exists():
        logger.warning(f"Markdown file not found for structured extraction: {markdown_file}")
        return None
    
    try:
        logger.info(f"Performing structured extraction on {markdown_file.name}")
        result = langchain_extractor.extract_from_file(str(markdown_file))
        
        if result.success:
            logger.info(f"Structured extraction successful (confidence: {result.confidence_score:.2f})")
            return {
                "success": True,
                "confidence_score": result.confidence_score,
                "product_sheet": result.product_sheet.model_dump() if result.product_sheet else None,
                "errors": result.errors,
                "warnings": result.warnings
            }
        else:
            logger.error(f"Structured extraction failed: {result.errors}")
            return {
                "success": False,
                "errors": result.errors,
                "warnings": result.warnings
            }
            
    except Exception as e:
        logger.error(f"Error during structured extraction: {e}")
        return {
            "success": False,
            "errors": [str(e)]
        }


def save_structured_results(
    results: Dict[str, Any], 
    output_file: Path,
    logger: logging.Logger
) -> bool:
    """
    Sauvegarde les résultats structurés au format JSON.
    
    Args:
        results: Résultats à sauvegarder
        output_file: Fichier de sortie
        logger: Logger pour les messages
        
    Returns:
        True si la sauvegarde a réussi
    """
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Structured results saved to: {output_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to save structured results: {e}")
        return False


def display_structured_results(results: Dict[str, Any]) -> None:
    """Affiche un résumé des résultats structurés."""
    if not results or not results.get("success"):
        print("❌ Structured extraction failed")
        if results and results.get("errors"):
            for error in results["errors"]:
                print(f"   Error: {error}")
        return
    
    print("✅ Structured extraction successful!")
    print(f"📊 Confidence score: {results.get('confidence_score', 0):.2f}")
    
    product_sheet = results.get("product_sheet")
    if product_sheet:
        print(f"📋 Product: {product_sheet.get('product_name', 'N/A')}")
        print(f"🏷️  EAN: {product_sheet.get('ean_code', 'N/A')}")
        
        ingredients = product_sheet.get('ingredients', [])
        print(f"🥘 Ingredients: {len(ingredients)} found")
        
        allergens = product_sheet.get('allergens', [])
        allergen_count = len([a for a in allergens if a.get('status') in ['Oui', 'Traces']])
        print(f"⚠️  Allergens: {allergen_count} found")
        
        nutritional_values = product_sheet.get('nutritional_values', [])
        print(f"📈 Nutritional values: {len(nutritional_values)} found")


def extract_single_file(
    file_path: Path, 
    output_dir: Optional[Path] = None,
    config: Optional[ExtractionConfig] = None,
    enable_structured: bool = False,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Extract a single PDF file.
    
    Args:
        file_path: Path to the PDF file
        output_dir: Output directory
        config: Extraction configuration
        enable_structured: Whether to perform structured extraction with LangChain
        logger: Logger instance
        
    Returns:
        True if successful, False otherwise
    """
    if logger is None:
        logger = logging.getLogger(__name__)
        
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    if file_path.suffix.lower() != '.pdf':
        print(f"❌ File is not a PDF: {file_path}")
        return False
    
    print(f"🎯 Processing: {file_path.name}")
    
    # Étape 1: Extraction PDF avec Docling
    extractor = TechnicalSheetExtractor(config)
    saved_files = extractor.extract_and_save(file_path, output_dir)
    
    if saved_files is None:
        print(f"❌ PDF extraction failed for: {file_path.name}")
        return False
    
    print(f"✅ PDF extraction completed for: {file_path.name}")
    for file_type, file_path_saved in saved_files.items():
        print(f"   📁 {file_type}: {file_path_saved}")
    
    # Étape 2: Extraction structurée (optionnelle)
    structured_results = None
    if enable_structured:
        try:
            print(f"🧠 Performing structured extraction...")
            langchain_extractor = LangChainExtractor()
            structured_results = perform_structured_extraction(file_path, langchain_extractor, logger)
            
            if structured_results:
                display_structured_results(structured_results)
                
                # Sauvegarde des résultats structurés
                if output_dir:
                    structured_file = output_dir / file_path.stem / f"structured_{file_path.stem}.json"
                else:
                    structured_file = Path("extracted_data") / file_path.stem / f"structured_{file_path.stem}.json"
                
                save_structured_results(structured_results, structured_file, logger)
                
        except Exception as e:
            logger.error(f"Structured extraction error: {e}")
            print(f"❌ Structured extraction failed: {e}")
    
    return True


def extract_folder(
    folder_path: Path, 
    output_dir: Optional[Path] = None,
    config: Optional[ExtractionConfig] = None,
    enable_structured: bool = False,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Extract all PDF files from a folder.
    
    Args:
        folder_path: Path to the folder
        output_dir: Output directory
        config: Extraction configuration
        enable_structured: Whether to perform structured extraction with LangChain
        logger: Logger instance
        
    Returns:
        True if at least one file was successfully extracted
    """
    if logger is None:
        logger = logging.getLogger(__name__)
        
    pdf_files = get_pdf_files_from_folder(folder_path)
    
    if not pdf_files:
        return False
    
    extractor = TechnicalSheetExtractor(config)
    results = extractor.extract_and_save_multiple(pdf_files, output_dir)
    
    # Print summary
    extractor.print_extraction_summary(results)
    
    # Extraction structurée en lot si demandée
    if enable_structured:
        print(f"\n🧠 Performing structured extraction on {len(pdf_files)} files...")
        
        try:
            langchain_extractor = LangChainExtractor()
            structured_results = {}
            successful_structured = 0
            
            for pdf_file in pdf_files:
                if results.get(str(pdf_file)) is not None:  # PDF extraction réussie
                    structured_result = perform_structured_extraction(pdf_file, langchain_extractor, logger)
                    structured_results[str(pdf_file)] = structured_result
                    
                    if structured_result and structured_result.get("success"):
                        successful_structured += 1
                        
                        # Sauvegarde individuelle
                        if output_dir:
                            structured_file = output_dir / pdf_file.stem / f"structured_{pdf_file.stem}.json"
                        else:
                            structured_file = Path("extracted_data") / pdf_file.stem / f"structured_{pdf_file.stem}.json"
                        
                        save_structured_results(structured_result, structured_file, logger)
            
            # Résumé de l'extraction structurée
            print(f"\n📊 Structured extraction summary:")
            print(f"   ✅ Successful: {successful_structured}")
            print(f"   ❌ Failed: {len(pdf_files) - successful_structured}")
            
            # Sauvegarde du résumé global
            if output_dir:
                batch_results_file = output_dir / "batch_structured_results.json"
            else:
                batch_results_file = Path("extracted_data") / "batch_structured_results.json"
            
            batch_summary = {
                "total_files": len(pdf_files),
                "successful_pdf_extractions": sum(1 for r in results.values() if r is not None),
                "successful_structured_extractions": successful_structured,
                "results": structured_results
            }
            
            save_structured_results(batch_summary, batch_results_file, logger)
            
        except Exception as e:
            logger.error(f"Batch structured extraction error: {e}")
            print(f"❌ Batch structured extraction failed: {e}")
    
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
    
    # Set DPI for image extraction
    if hasattr(args, 'dpi') and args.dpi:
        config.dpi = args.dpi
    
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
        description="Extract technical sheets from PDF files with optional structured extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract a single file (PDF only)
  python cli.py --file FT/unilever/3011360006707.pdf
  
  # Extract with structured analysis (PDF + LangChain)
  python cli.py --file FT/unilever/3011360006707.pdf --structured
  
  # Extract all files from unilever folder with structured analysis
  python cli.py --folder FT/unilever --structured
  
  # Extract with custom output directory
  python cli.py --folder FT/unilever --output ./extracted_data --structured
  
  # Extract without images (faster processing)
  python cli.py --folder FT/charles_alice --no-images --structured
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
        help='Output directory for extracted files (default: ./extracted_data)'
    )
    
    parser.add_argument(
        '--structured', '-s',
        action='store_true',
        help='Enable structured extraction with LangChain (requires Ollama with llama3.1)'
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
    
    parser.add_argument(
        '--dpi',
        type=int,
        default=150,
        help='DPI for image extraction (default: 150)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.quiet)
    
    # Create configuration
    config = create_config(args)
    
    # Resolve output directory
    output_dir = None
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Output directory: {output_dir.absolute()}")
    
    # Vérification des prérequis pour l'extraction structurée
    if args.structured:
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                llama_models = [m for m in models if 'llama3.1' in m.get('name', '').lower()]
                if llama_models:
                    print(f"✅ Ollama available with {len(llama_models)} Llama 3.1 model(s)")
                else:
                    print("⚠️  Ollama available but no Llama 3.1 model found")
                    print("   Install with: ollama pull llama3.1:latest")
                    print("   Continuing with PDF extraction only...")
                    args.structured = False
            else:
                print("❌ Ollama not accessible - structured extraction disabled")
                args.structured = False
        except Exception:
            print("❌ Ollama not available - structured extraction disabled")
            print("   Start Ollama with: ollama serve")
            args.structured = False
    
    success = False
    
    try:
        if args.file:
            # Extract single file
            file_path = validate_ft_path(args.file)
            print(f"🎯 Extracting single file: {file_path}")
            success = extract_single_file(file_path, output_dir, config, args.structured, logger)
            
        elif args.folder:
            # Extract folder
            folder_path = validate_ft_path(args.folder)
            print(f"🎯 Extracting folder: {folder_path}")
            success = extract_folder(folder_path, output_dir, config, args.structured, logger)
    
    except KeyboardInterrupt:
        print(f"\n⚠️  Extraction interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    
    # Exit with appropriate code
    if success:
        print(f"\n🎉 Extraction completed successfully!")
        if args.structured:
            print("📊 Structured data available in JSON files")
        sys.exit(0)
    else:
        print(f"\n❌ Extraction failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 