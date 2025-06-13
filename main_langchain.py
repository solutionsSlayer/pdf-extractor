#!/usr/bin/env python3
"""
Script principal pour l'extraction structurée avec LangChain
Intègre l'extraction PDF existante avec la structuration LangChain
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Import des modules existants
from extractor.pdf_extractor import PDFExtractor
from extractor.langchain_extractor import LangChainExtractor
from config import get_config, validate_config, PATHS_CONFIG, LOGGING_CONFIG

def setup_logging():
    """Configure le système de logging"""
    config = LOGGING_CONFIG
    
    # Création du répertoire de logs
    if config["file_enabled"]:
        Path(PATHS_CONFIG["logs_dir"]).mkdir(parents=True, exist_ok=True)
    
    # Configuration du logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config["level"]))
    
    # Format
    formatter = logging.Formatter(config["format"])
    
    # Handler console
    if config["console_enabled"]:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Handler fichier
    if config["file_enabled"]:
        log_file = Path(PATHS_CONFIG["logs_dir"]) / "extraction.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def process_single_pdf(pdf_path: str, output_dir: str, langchain_extractor: LangChainExtractor) -> Dict[str, Any]:
    """
    Traite un seul fichier PDF avec extraction complète
    
    Args:
        pdf_path: Chemin vers le fichier PDF
        output_dir: Répertoire de sortie
        langchain_extractor: Instance de l'extracteur LangChain
        
    Returns:
        Dict contenant les résultats de l'extraction
    """
    logger = logging.getLogger(__name__)
    pdf_path_obj = Path(pdf_path)
    
    if not pdf_path_obj.exists():
        return {"error": f"Fichier PDF non trouvé : {pdf_path}"}
    
    logger.info(f"Traitement de {pdf_path_obj.name}")
    
    try:
        # Étape 1 : Extraction PDF avec l'extracteur existant
        pdf_extractor = PDFExtractor()
        extraction_result = pdf_extractor.extract_from_pdf(pdf_path, output_dir)
        
        if not extraction_result.get("success", False):
            return {
                "pdf_file": pdf_path,
                "success": False,
                "error": "Échec de l'extraction PDF",
                "details": extraction_result
            }
        
        # Étape 2 : Récupération du fichier texte extrait
        extracted_text_file = extraction_result.get("text_file")
        if not extracted_text_file or not Path(extracted_text_file).exists():
            return {
                "pdf_file": pdf_path,
                "success": False,
                "error": "Fichier texte extrait non trouvé"
            }
        
        # Étape 3 : Extraction structurée avec LangChain
        logger.info(f"Extraction structurée de {Path(extracted_text_file).name}")
        langchain_result = langchain_extractor.extract_from_file(extracted_text_file)
        
        # Étape 4 : Compilation des résultats
        result = {
            "pdf_file": pdf_path,
            "success": langchain_result.success,
            "extraction_steps": {
                "pdf_extraction": extraction_result,
                "structured_extraction": {
                    "success": langchain_result.success,
                    "confidence_score": langchain_result.confidence_score,
                    "errors": langchain_result.errors,
                    "warnings": langchain_result.warnings
                }
            }
        }
        
        if langchain_result.success and langchain_result.product_sheet:
            result["structured_data"] = langchain_result.product_sheet.model_dump()
        
        return result
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement de {pdf_path} : {e}")
        return {
            "pdf_file": pdf_path,
            "success": False,
            "error": f"Erreur générale : {str(e)}"
        }

def process_batch_pdfs(pdf_directory: str, output_dir: str) -> Dict[str, Any]:
    """
    Traite tous les fichiers PDF d'un répertoire
    
    Args:
        pdf_directory: Répertoire contenant les PDFs
        output_dir: Répertoire de sortie
        
    Returns:
        Dict contenant les résultats de tous les traitements
    """
    logger = logging.getLogger(__name__)
    pdf_dir = Path(pdf_directory)
    
    if not pdf_dir.exists():
        return {"error": f"Répertoire PDF non trouvé : {pdf_directory}"}
    
    # Recherche des fichiers PDF
    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        return {"error": f"Aucun fichier PDF trouvé dans {pdf_directory}"}
    
    logger.info(f"Traitement de {len(pdf_files)} fichiers PDF")
    
    # Initialisation de l'extracteur LangChain
    config = get_config()
    langchain_extractor = LangChainExtractor(
        model_name=config["ollama"]["model_name"],
        base_url=config["ollama"]["base_url"]
    )
    
    # Traitement de chaque PDF
    results = {}
    successful = 0
    failed = 0
    
    for pdf_file in pdf_files:
        result = process_single_pdf(str(pdf_file), output_dir, langchain_extractor)
        results[str(pdf_file)] = result
        
        if result.get("success", False):
            successful += 1
        else:
            failed += 1
        
        logger.info(f"Progression : {successful + failed}/{len(pdf_files)} - Réussis: {successful}, Échoués: {failed}")
    
    # Statistiques finales
    summary = {
        "total_files": len(pdf_files),
        "successful": successful,
        "failed": failed,
        "success_rate": successful / len(pdf_files) if pdf_files else 0,
        "results": results
    }
    
    return summary

def save_results(results: Dict[str, Any], output_file: str):
    """Sauvegarde les résultats au format JSON"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logging.getLogger(__name__).info(f"Résultats sauvegardés dans {output_file}")
    except Exception as e:
        logging.getLogger(__name__).error(f"Erreur lors de la sauvegarde : {e}")

def main():
    """Fonction principale"""
    print("🚀 Extracteur PDF + LangChain avec Llama 3.1")
    print("=" * 50)
    
    # Validation de la configuration
    if not validate_config():
        print("❌ Configuration invalide")
        sys.exit(1)
    
    # Configuration du logging
    logger = setup_logging()
    logger.info("Démarrage de l'extraction")
    
    # Création des répertoires de sortie
    Path(PATHS_CONFIG["output_dir"]).mkdir(parents=True, exist_ok=True)
    
    # Menu interactif
    while True:
        print("\nOptions disponibles :")
        print("1. Traiter un fichier PDF unique")
        print("2. Traiter tous les PDFs d'un répertoire")
        print("3. Traiter les fichiers texte déjà extraits")
        print("4. Afficher la configuration")
        print("5. Quitter")
        
        choice = input("\nVotre choix (1-5) : ").strip()
        
        if choice == "1":
            pdf_path = input("Chemin vers le fichier PDF : ").strip()
            if pdf_path:
                config = get_config()
                langchain_extractor = LangChainExtractor(
                    model_name=config["ollama"]["model_name"],
                    base_url=config["ollama"]["base_url"]
                )
                
                result = process_single_pdf(pdf_path, PATHS_CONFIG["output_dir"], langchain_extractor)
                
                if result.get("success"):
                    print("✅ Traitement réussi !")
                    if "structured_data" in result:
                        data = result["structured_data"]
                        print(f"📋 Produit : {data.get('product_name', 'N/A')}")
                        print(f"📊 Score de confiance : {result['extraction_steps']['structured_extraction']['confidence_score']:.2f}")
                else:
                    print("❌ Échec du traitement")
                    print(f"Erreur : {result.get('error', 'Erreur inconnue')}")
                
                # Sauvegarde
                output_file = Path(PATHS_CONFIG["output_dir"]) / f"single_extraction_{Path(pdf_path).stem}.json"
                save_results(result, str(output_file))
        
        elif choice == "2":
            pdf_dir = input("Répertoire contenant les PDFs : ").strip()
            if pdf_dir:
                results = process_batch_pdfs(pdf_dir, PATHS_CONFIG["output_dir"])
                
                if "error" in results:
                    print(f"❌ Erreur : {results['error']}")
                else:
                    print(f"✅ Traitement terminé !")
                    print(f"📊 Fichiers traités : {results['total_files']}")
                    print(f"✅ Réussis : {results['successful']}")
                    print(f"❌ Échoués : {results['failed']}")
                    print(f"📈 Taux de réussite : {results['success_rate']:.1%}")
                    
                    # Sauvegarde
                    output_file = Path(PATHS_CONFIG["output_dir"]) / "batch_extraction_results.json"
                    save_results(results, str(output_file))
        
        elif choice == "3":
            # Traitement des fichiers texte déjà extraits
            extracted_dir = Path(PATHS_CONFIG["extracted_data_dir"])
            if not extracted_dir.exists():
                print(f"❌ Répertoire {extracted_dir} non trouvé")
                continue
            
            txt_files = list(extracted_dir.rglob("*.txt"))
            if not txt_files:
                print("❌ Aucun fichier texte trouvé")
                continue
            
            print(f"🔍 {len(txt_files)} fichiers texte trouvés")
            
            config = get_config()
            langchain_extractor = LangChainExtractor(
                model_name=config["ollama"]["model_name"],
                base_url=config["ollama"]["base_url"]
            )
            
            file_paths = [str(f) for f in txt_files]
            results = langchain_extractor.batch_extract(file_paths)
            
            successful = sum(1 for r in results.values() if r.success)
            print(f"✅ Extractions réussies : {successful}/{len(results)}")
            
            # Sauvegarde
            output_file = Path(PATHS_CONFIG["output_dir"]) / "text_extraction_results.json"
            langchain_extractor.save_results_to_json(results, str(output_file))
        
        elif choice == "4":
            config = get_config()
            print("\n📋 Configuration actuelle :")
            print(f"  • Modèle Ollama : {config['ollama']['model_name']}")
            print(f"  • URL Ollama : {config['ollama']['base_url']}")
            print(f"  • Température : {config['ollama']['temperature']}")
            print(f"  • Répertoire de sortie : {config['paths']['output_dir']}")
            print(f"  • Niveau de log : {config['logging']['level']}")
        
        elif choice == "5":
            print("👋 Au revoir !")
            break
        
        else:
            print("❌ Choix invalide, veuillez réessayer")

if __name__ == "__main__":
    main() 