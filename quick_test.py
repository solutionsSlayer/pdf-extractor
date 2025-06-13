#!/usr/bin/env python3
"""
Test rapide de l'extraction LangChain
"""

from extractor.langchain_extractor import LangChainExtractor
import json

def main():
    print("=== TEST RAPIDE D'EXTRACTION LANGCHAIN ===")
    
    # Test d'extraction
    extractor = LangChainExtractor()
    result = extractor.extract_from_file('extracted_data/3288310840869/extracted_3288310840869.md')
    
    print(f'Succès: {result.success}')
    
    if result.success:
        print(f'Score de confiance: {result.confidence_score:.2f}')
        sheet = result.product_sheet
        print(f'Nom du produit: {sheet.product_name}')
        print(f'Dénomination légale: {sheet.legal_denomination}')
        print(f'Code EAN: {sheet.ean_code}')
        print(f'Nombre d\'ingrédients: {len(sheet.ingredients) if sheet.ingredients else 0}')
        print(f'Nombre d\'allergènes: {len(sheet.allergens) if sheet.allergens else 0}')
        
        # Sauvegarde du résultat
        with open('quick_test_result.json', 'w', encoding='utf-8') as f:
            json.dump({
                "success": result.success,
                "product_sheet": result.product_sheet.model_dump() if result.product_sheet else None,
                "confidence_score": result.confidence_score
            }, f, indent=2, ensure_ascii=False)
        
        print("✅ Résultat sauvegardé dans quick_test_result.json")
    else:
        print(f'❌ Erreurs: {result.errors}')

if __name__ == "__main__":
    main() 