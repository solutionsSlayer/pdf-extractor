import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException

from .schemas import ProductSheet, ExtractionResult, Allergen, NutritionalValue, ManufacturerContact


class LangChainExtractor:
    """Extracteur de données structurées utilisant LangChain avec Llama 3.1"""
    
    def __init__(self, model_name: str = "llama3.1:latest", base_url: str = "http://localhost:11434"):
        """
        Initialise l'extracteur LangChain
        
        Args:
            model_name: Nom du modèle Ollama à utiliser
            base_url: URL de base du serveur Ollama
        """
        self.logger = logging.getLogger(__name__)
        
        # Configuration du modèle Ollama
        self.llm = ChatOllama(
            model=model_name,
            base_url=base_url,
            temperature=0.1,  # Faible température pour plus de cohérence
            num_predict=4096,  # Limite de tokens de sortie
            format="json"  # Force le format JSON
        )
        
        # Parser Pydantic pour la structure de sortie
        self.parser = PydanticOutputParser(pydantic_object=ProductSheet)
        
        # Template de prompt optimisé pour l'extraction de fiches produits
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("human", "Voici le contenu d'une fiche produit à analyser :\n\n{content}\n\nExtrait les informations selon le schéma JSON demandé.")
        ])
        
        # Chaîne complète avec post-traitement
        self.chain = self.prompt_template | self.llm | self._custom_parser
    
    def _get_system_prompt(self) -> str:
        """Génère le prompt système optimisé pour l'extraction"""
        # Instructions de format avec accolades échappées pour éviter les conflits de template
        format_instructions = """Réponds avec un JSON valide suivant exactement cette structure :

{{
  "product_name": "string ou null",
  "legal_denomination": "string ou null", 
  "ean_code": "string ou null",
  "ean_carton": "string ou null",
  "ean_palette": "string ou null",
  "ingredients": ["liste de strings"] ou null,
  "additives": ["liste de strings"] ou null,
  "allergens": [{{"name": "string", "status": "Oui|Traces|Non"}}] ou null,
  "shelf_life": "string ou null",
  "storage_conditions": "string ou null",
  "packaging_country": "string ou null",
  "nutritional_values": [{{"name": "string", "per_100g": "string", "percentage_reference": "string"}}] ou null,
  "manufacturer_contact": {{"nom": "string", "adresse": "string", "telephone": "string", "email": "string", "website": "string"}} ou null,
  "extraction_date": "string ISO",
  "source_file": "string"
}}

RÈGLE CRUCIALE POUR LES ALLERGÈNES : Dans la liste finale "allergens", ne mets QUE les allergènes avec status "Oui" ou "Traces". 
Ignore complètement ceux avec status "Non" - ne les inclus pas du tout dans la liste finale."""
        
        return f"""Tu es un expert en extraction de données de fiches produits alimentaires.

Ton rôle est d'analyser le contenu de fiches produits et d'extraire toutes les informations pertinentes dans un format JSON structuré.

INSTRUCTIONS SPÉCIFIQUES POUR LES CODES EAN :

1. CODES EAN À EXTRAIRE :
   - ean_code : Code EAN principal du produit (EAN 13 GENCOD Produit) - généralement 13 chiffres
   - ean_carton : Code EAN carton/couche (DUN 14 Unité Logistique Carton) - généralement commence par 1
   - ean_palette : Code EAN palette (DUN 14 Unité Logistique Palette) - généralement commence par 2

2. OÙ CHERCHER LES CODES EAN :
   - Sections "Etiquetage", "Marquage", "Colisage", "Palettisation"
   - Tableaux de codes-barres ou identifiants
   - Lignes mentionnant "EAN", "GENCOD", "DUN 14"
   - Exemples de formats :
     * EAN 13 GENCOD Produit : 3288310840869
     * DUN 14 Unité Logistique Carton : 13288310840866
     * DUN 14 Unité Logistique Palette : 23288310840863

INSTRUCTIONS CRITIQUES POUR LES ALLERGÈNES :

1. ANALYSE MÉTHODIQUE DES TABLEAUX D'ALLERGÈNES :
   
   Quand tu vois un tableau comme :
   |Allergènes|Oui|Traces|Non|
   |Céréales contenant du gluten|x|||
   |Lupin et produits à base de lupin|||x|
   
   PROCÉDURE STRICTE :
   - Identifie d'abord les colonnes : "Oui", "Traces", "Non"
   - Pour chaque allergène, regarde EXACTEMENT dans quelle colonne se trouve le "x"
   - Si "x" est dans colonne "Oui" → status: "Oui" → INCLURE dans la liste finale
   - Si "x" est dans colonne "Traces" → status: "Traces" → INCLURE dans la liste finale  
   - Si "x" est dans colonne "Non" → status: "Non" → NE PAS INCLURE du tout
   
   EXEMPLE CONCRET :
   - "Céréales contenant du gluten" avec "x" dans "Oui" → À INCLURE avec status "Oui"
   - "Lupin" avec "x" dans "Non" → NE PAS INCLURE (ignorer complètement)

2. VÉRIFICATION DOUBLE :
   - Compte les colonnes depuis la gauche
   - Vérifie que tu lis la bonne ligne pour chaque allergène
   - Ne te fie pas aux noms similaires, lis ligne par ligne

3. RÈGLE FINALE ABSOLUE :
   Dans le JSON final, la liste "allergens" ne doit contenir QUE les allergènes avec "x" dans les colonnes "Oui" ou "Traces".
   Tous les autres sont à ignorer complètement.

AUTRES INSTRUCTIONS :
- Analyse attentivement tout le contenu fourni
- Extrait TOUTES les informations disponibles, même partielles
- Pour les valeurs booléennes, utilise true/false ou null si non spécifié
- Pour les listes vides, utilise [] plutôt que null
- Sois précis avec les unités et les valeurs numériques
- Si une information n'est pas disponible, utilise null

TYPES DE DONNÉES À EXTRAIRE :
- Informations générales (nom, dénomination légale, EAN)
- Codes EAN pour tous les niveaux de conditionnement
- Ingrédients et additifs
- Allergènes avec leur statut (SEULEMENT ceux présents ou en traces)
- Informations nutritionnelles complètes
- Certifications qualité
- Informations de contact

{format_instructions}

Réponds UNIQUEMENT avec le JSON structuré, sans texte supplémentaire."""

    def _custom_parser(self, ai_message):
        """Parser personnalisé avec post-traitement"""
        try:
            # Parse le JSON brut
            if hasattr(ai_message, 'content'):
                content = ai_message.content
            else:
                content = str(ai_message)
            
            raw_result = json.loads(content)
            
            # Post-traitement
            processed_result = self._post_process_result(raw_result)
            
            # Validation Pydantic
            return ProductSheet(**processed_result)
            
        except json.JSONDecodeError as e:
            raise OutputParserException(f"Erreur de parsing JSON : {e}")
        except Exception as e:
            raise OutputParserException(f"Erreur de validation : {e}")

    def _post_process_result(self, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post-traite le résultat brut pour corriger les problèmes de format courants
        
        Args:
            raw_result: Résultat brut du modèle
            
        Returns:
            Dict[str, Any]: Résultat corrigé
        """
        # Copie pour éviter de modifier l'original
        result = raw_result.copy()
        
        # Correction des champs qui doivent être des listes
        list_fields = ['ingredients', 'additives']
        for field in list_fields:
            if field in result and isinstance(result[field], str):
                # Convertit la chaîne en liste avec un seul élément
                result[field] = [result[field]]
        
        # Filtrage des allergènes - ne garde que ceux avec statut "Oui" ou "Traces"
        if 'allergens' in result and result['allergens']:
            filtered_allergens = []
            for allergen in result['allergens']:
                if isinstance(allergen, dict) and allergen.get('status') in ['Oui', 'Traces']:
                    filtered_allergens.append(allergen)
            result['allergens'] = filtered_allergens if filtered_allergens else None
        
        return result

    def extract_from_text(self, content: str, source_file: Optional[str] = None) -> ExtractionResult:
        """
        Extrait les données structurées à partir du contenu textuel
        
        Args:
            content: Contenu textuel de la fiche produit
            source_file: Nom du fichier source (optionnel)
            
        Returns:
            ExtractionResult: Résultat de l'extraction avec métadonnées
        """
        try:
            self.logger.info(f"Début de l'extraction pour {source_file or 'contenu fourni'}")
            
            # Exécution de la chaîne LangChain
            result = self.chain.invoke({
                "content": content
            })
            
            # Le parser personnalisé retourne déjà un ProductSheet
            # Ajout des métadonnées
            if isinstance(result, ProductSheet):
                result.extraction_date = datetime.now().isoformat()
                result.source_file = source_file
                
                self.logger.info("Extraction réussie")
                return ExtractionResult(
                    success=True,
                    product_sheet=result,
                    confidence_score=self._calculate_confidence_score(result)
                )
            else:
                raise ValueError("Le résultat n'est pas du type ProductSheet attendu")
                
        except OutputParserException as e:
            self.logger.error(f"Erreur de parsing : {e}")
            return ExtractionResult(
                success=False,
                errors=[f"Erreur de parsing JSON : {str(e)}"]
            )
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'extraction : {e}")
            return ExtractionResult(
                success=False,
                errors=[f"Erreur générale : {str(e)}"]
            )
    
    def extract_from_file(self, file_path: str) -> ExtractionResult:
        """
        Extrait les données à partir d'un fichier texte
        
        Args:
            file_path: Chemin vers le fichier à analyser
            
        Returns:
            ExtractionResult: Résultat de l'extraction
        """
        try:
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                return ExtractionResult(
                    success=False,
                    errors=[f"Le fichier {file_path} n'existe pas"]
                )
            
            # Lecture du contenu
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.extract_from_text(content, file_path_obj.name)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la lecture du fichier {file_path} : {e}")
            return ExtractionResult(
                success=False,
                errors=[f"Erreur de lecture du fichier : {str(e)}"]
            )
    
    def _calculate_confidence_score(self, product_sheet: ProductSheet) -> float:
        """
        Calcule un score de confiance basé sur la complétude des données extraites
        
        Args:
            product_sheet: Fiche produit extraite
            
        Returns:
            float: Score de confiance entre 0 et 1
        """
        total_fields = 0
        filled_fields = 0
        
        # Comptage des champs principaux
        main_fields = [
            'product_name', 'legal_denomination', 'ean_code', 'ean_carton', 'ean_palette',
            'ingredients', 'allergens', 'nutritional_values',
        ]
        
        for field in main_fields:
            total_fields += 1
            value = getattr(product_sheet, field, None)
            if value is not None:
                if isinstance(value, list) and len(value) > 0:
                    filled_fields += 1
                elif isinstance(value, str) and value.strip():
                    filled_fields += 1
                elif not isinstance(value, (list, str)):
                    filled_fields += 1
        
        # Bonus pour les champs complexes bien remplis
        if product_sheet.allergens and len(product_sheet.allergens) > 0:
            filled_fields += 0.5
        
        if product_sheet.nutritional_values and len(product_sheet.nutritional_values) > 0:
            filled_fields += 0.5
        
        return min(filled_fields / total_fields, 1.0) if total_fields > 0 else 0.0
    
    def batch_extract(self, file_paths: list[str]) -> Dict[str, ExtractionResult]:
        """
        Extrait les données de plusieurs fichiers en lot
        
        Args:
            file_paths: Liste des chemins de fichiers à traiter
            
        Returns:
            Dict[str, ExtractionResult]: Dictionnaire des résultats par fichier
        """
        results = {}
        
        for file_path in file_paths:
            self.logger.info(f"Traitement de {file_path}")
            results[file_path] = self.extract_from_file(file_path)
        
        return results
    
    def save_results_to_json(self, results: Dict[str, ExtractionResult], output_file: str):
        """
        Sauvegarde les résultats d'extraction au format JSON
        
        Args:
            results: Résultats d'extraction
            output_file: Fichier de sortie JSON
        """
        try:
            # Conversion en dictionnaire sérialisable
            serializable_results = {}
            
            for file_path, result in results.items():
                serializable_results[file_path] = {
                    "success": result.success,
                    "product_sheet": result.product_sheet.model_dump() if result.product_sheet else None,
                    "errors": result.errors,
                    "warnings": result.warnings,
                    "confidence_score": result.confidence_score
                }
            
            # Sauvegarde
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Résultats sauvegardés dans {output_file}")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde : {e}")
            raise 