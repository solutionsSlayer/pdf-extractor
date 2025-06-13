#!/usr/bin/env python3
"""
Script de test pour l'extraction LangChain avec Llama 3.1
"""

import json
import logging
from pathlib import Path
from extractor.langchain_extractor import LangChainExtractor

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_single_extraction():
    """Test d'extraction sur un fichier unique"""
    
    # Initialisation de l'extracteur
    extractor = LangChainExtractor(
        model_name="llama3.1:latest",
        base_url="http://localhost:11434"
    )
    
    # Fichier de test
    test_file = "extracted_data/3011360006707/extracted_3011360006707.txt"
    
    if not Path(test_file).exists():
        print(f"❌ Fichier de test non trouvé : {test_file}")
        return
    
    print(f"🔍 Test d'extraction sur : {test_file}")
    
    # Extraction
    result = extractor.extract_from_file(test_file)
    
    # Affichage des résultats
    if result.success:
        print("✅ Extraction réussie !")
        print(f"📊 Score de confiance : {result.confidence_score:.2f}")
        
        # Affichage des informations principales
        if result.product_sheet:
            sheet = result.product_sheet
            print("\n📋 Informations extraites :")
            print(f"  • Nom du produit : {sheet.product_name}")
            print(f"  • Dénomination légale : {sheet.legal_denomination}")
            print(f"  • Code EAN : {sheet.ean_code}")
            print(f"  • Nombre d'ingrédients : {len(sheet.ingredients) if sheet.ingredients else 0}")
            print(f"  • Nombre d'allergènes : {len(sheet.allergens) if sheet.allergens else 0}")
            print(f"  • Nombre de valeurs nutritionnelles : {len(sheet.nutritional_values) if sheet.nutritional_values else 0}")
            
            # Sauvegarde du résultat
            output_file = "test_extraction_result.json"
            extractor.save_results_to_json({test_file: result}, output_file)
            print(f"💾 Résultat sauvegardé dans : {output_file}")
    else:
        print("❌ Échec de l'extraction")
        if result.errors:
            for error in result.errors:
                print(f"  • Erreur : {error}")

def test_batch_extraction():
    """Test d'extraction en lot sur tous les fichiers disponibles"""
    
    # Recherche des fichiers d'extraction
    extracted_data_dir = Path("extracted_data")
    
    if not extracted_data_dir.exists():
        print("❌ Répertoire extracted_data non trouvé")
        return
    
    # Collecte des fichiers .txt
    txt_files = list(extracted_data_dir.rglob("*.txt"))
    
    if not txt_files:
        print("❌ Aucun fichier .txt trouvé dans extracted_data")
        return
    
    print(f"🔍 Test d'extraction en lot sur {len(txt_files)} fichiers")
    
    # Initialisation de l'extracteur
    extractor = LangChainExtractor()
    
    # Extraction en lot
    file_paths = [str(f) for f in txt_files]
    results = extractor.batch_extract(file_paths)
    
    # Analyse des résultats
    successful = sum(1 for r in results.values() if r.success)
    failed = len(results) - successful
    
    print(f"✅ Extractions réussies : {successful}")
    print(f"❌ Extractions échouées : {failed}")
    
    # Calcul du score de confiance moyen
    confidence_scores = [r.confidence_score for r in results.values() if r.success and r.confidence_score]
    if confidence_scores:
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        print(f"📊 Score de confiance moyen : {avg_confidence:.2f}")
    
    # Sauvegarde des résultats
    output_file = "batch_extraction_results.json"
    extractor.save_results_to_json(results, output_file)
    print(f"💾 Résultats sauvegardés dans : {output_file}")

def display_extraction_details(result_file: str):
    """Affiche les détails d'un résultat d'extraction"""
    
    if not Path(result_file).exists():
        print(f"❌ Fichier de résultats non trouvé : {result_file}")
        return
    
    with open(result_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    for file_path, result in results.items():
        print(f"\n📄 Fichier : {Path(file_path).name}")
        print(f"   Succès : {'✅' if result['success'] else '❌'}")
        
        if result['success'] and result['product_sheet']:
            sheet = result['product_sheet']
            print(f"   Score de confiance : {result['confidence_score']:.2f}")
            print(f"   Produit : {sheet.get('product_name', 'N/A')}")
            print(f"   EAN : {sheet.get('ean_code', 'N/A')}")
            
            # Allergènes
            allergens = sheet.get('allergens', [])
            if allergens:
                print(f"   Allergènes présents :")
                for allergen in allergens:
                    if allergen.get('status') == 'Oui':
                        print(f"     • {allergen.get('name')}")
        
        if result.get('errors'):
            print(f"   Erreurs :")
            for error in result['errors']:
                print(f"     • {error}")

if __name__ == "__main__":
    print("🚀 Test de l'extracteur LangChain avec Llama 3.1")
    print("=" * 50)
    
    # Vérification de la disponibilité d'Ollama
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            llama_models = [m for m in models if 'llama3.1' in m.get('name', '').lower()]
            if llama_models:
                print(f"✅ Ollama disponible avec {len(llama_models)} modèle(s) Llama 3.1")
            else:
                print("⚠️  Ollama disponible mais aucun modèle Llama 3.1 trouvé")
                print("   Exécutez : ollama pull llama3.1:latest")
        else:
            print("❌ Ollama non accessible")
            print("   Vérifiez qu'Ollama est démarré : ollama serve")
    except Exception as e:
        print(f"❌ Impossible de vérifier Ollama : {e}")
        print("   Assurez-vous qu'Ollama est installé et démarré")
    
    print("\n" + "=" * 50)
    
    # Menu interactif
    while True:
        print("\nOptions disponibles :")
        print("1. Test d'extraction sur un fichier unique")
        print("2. Test d'extraction en lot")
        print("3. Afficher les détails d'un résultat")
        print("4. Quitter")
        
        choice = input("\nVotre choix (1-4) : ").strip()
        
        if choice == "1":
            test_single_extraction()
        elif choice == "2":
            test_batch_extraction()
        elif choice == "3":
            result_file = input("Fichier de résultats (ex: test_extraction_result.json) : ").strip()
            display_extraction_details(result_file)
        elif choice == "4":
            print("👋 Au revoir !")
            break
        else:
            print("❌ Choix invalide, veuillez réessayer") 