# Extraction Structurée avec LangChain et Llama 3.1

Cette solution intègre LangChain avec votre modèle Llama 3.1 local pour transformer vos données markdown extraites en JSON structuré.

## 🚀 Fonctionnalités

- **Extraction structurée** : Conversion automatique du texte en données JSON structurées
- **Schémas Pydantic** : Validation et typage strict des données extraites
- **Modèle local** : Utilisation de Llama 3.1 via Ollama (pas de dépendance cloud)
- **Score de confiance** : Évaluation automatique de la qualité de l'extraction
- **Traitement en lot** : Traitement de multiples fichiers simultanément
- **Configuration flexible** : Personnalisation via variables d'environnement

## 📋 Prérequis

### 1. Ollama et Llama 3.1

```bash
# Installation d'Ollama (si pas déjà fait)
curl -fsSL https://ollama.ai/install.sh | sh

# Téléchargement du modèle Llama 3.1
ollama pull llama3.1:latest

# Démarrage du serveur Ollama
ollama serve
```

### 2. Dépendances Python

```bash
pip install -r requirements.txt
```

## 🏗️ Architecture

```
├── extractor/
│   ├── schemas.py              # Schémas Pydantic pour la structure des données
│   ├── langchain_extractor.py  # Extracteur LangChain principal
│   └── pdf_extractor.py        # Extracteur PDF existant
├── config.py                   # Configuration centralisée
├── main_langchain.py          # Script principal intégré
├── test_langchain_extraction.py # Script de test
└── README_LANGCHAIN.md        # Cette documentation
```

## 📊 Structure des Données Extraites

### Schéma Principal : `ProductSheet`

```json
{
  "product_name": "KNORR ROUX BRUN 1KG",
  "legal_denomination": "Roux brun instantané déshydraté",
  "ean_code": "3011360006707",
  "ingredients": ["Farine de BLÉ", "graisse de palme", "colorant caramel E150c"],
  "allergens": [
    {
      "name": "Céréales contenant du gluten",
      "status": "Oui"
    }
  ],
  "nutritional_values": [
    {
      "name": "Valeur énergétique",
      "per_100g": "2451kJ - 592kcal",
      "per_100ml_prepared": "245kJ - 59kcal"
    }
  ],
  "product_benefits": [
    "Maîtrisez à 100% la consistance de vos sauces",
    "Apporte onctuosité et brillance à toutes vos préparations"
  ],
  "vegetarian_suitable": true,
  "vegan_suitable": true,
  "gmo_free": true,
  "extraction_date": "2024-01-15T10:30:00",
  "source_file": "extracted_3011360006707.txt"
}
```

### Types de Données Supportés

- **Informations générales** : nom, dénomination légale, EAN
- **Composition** : ingrédients, additifs
- **Allergènes** : avec statut (Oui/Traces/Non)
- **Nutrition** : valeurs nutritionnelles complètes
- **Caractéristiques** : végétarien, bio, sans OGM, etc.
- **Logistique** : poids, dimensions, codes EAN
- **Qualité** : certifications, normes
- **Contact** : informations fabricant

## 🔧 Configuration

### Variables d'Environnement

```bash
# Configuration Ollama
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_MODEL="llama3.1:latest"
export OLLAMA_TEMPERATURE="0.1"
export OLLAMA_NUM_PREDICT="4096"

# Configuration extraction
export MAX_RETRIES="3"
export BATCH_SIZE="5"
export ENABLE_CONFIDENCE_SCORING="true"

# Chemins
export EXTRACTED_DATA_DIR="extracted_data"
export OUTPUT_DIR="structured_output"
export LOGS_DIR="logs"

# Logging
export LOG_LEVEL="INFO"
export LOG_TO_FILE="true"
export LOG_TO_CONSOLE="true"
```

### Fichier `.env` (optionnel)

```env
OLLAMA_MODEL=llama3.1:latest
OLLAMA_TEMPERATURE=0.1
OUTPUT_DIR=structured_output
LOG_LEVEL=INFO
```

## 🚀 Utilisation

### 1. Script Principal Intégré

```bash
python main_langchain.py
```

Menu interactif avec options :
1. Traiter un fichier PDF unique
2. Traiter tous les PDFs d'un répertoire
3. Traiter les fichiers texte déjà extraits
4. Afficher la configuration
5. Quitter

### 2. Script de Test

```bash
python test_langchain_extraction.py
```

Options de test :
1. Test sur un fichier unique
2. Test en lot
3. Affichage des résultats détaillés

### 3. Utilisation Programmatique

```python
from extractor.langchain_extractor import LangChainExtractor

# Initialisation
extractor = LangChainExtractor(
    model_name="llama3.1:latest",
    base_url="http://localhost:11434"
)

# Extraction depuis un fichier
result = extractor.extract_from_file("extracted_data/product.txt")

if result.success:
    print(f"Produit : {result.product_sheet.product_name}")
    print(f"Confiance : {result.confidence_score:.2f}")
else:
    print(f"Erreurs : {result.errors}")

# Extraction en lot
file_paths = ["file1.txt", "file2.txt", "file3.txt"]
results = extractor.batch_extract(file_paths)

# Sauvegarde
extractor.save_results_to_json(results, "results.json")
```

## 📈 Score de Confiance

Le système calcule automatiquement un score de confiance (0-1) basé sur :

- **Complétude des données** : nombre de champs remplis
- **Qualité des extractions** : cohérence des données
- **Complexité des structures** : allergènes, nutrition, logistique

**Interprétation** :
- `0.8-1.0` : Extraction excellente
- `0.6-0.8` : Extraction bonne
- `0.4-0.6` : Extraction moyenne
- `0.0-0.4` : Extraction faible

## 🔍 Exemple de Résultat Complet

```json
{
  "pdf_file": "product_sheet.pdf",
  "success": true,
  "extraction_steps": {
    "pdf_extraction": {
      "success": true,
      "text_file": "extracted_data/product/extracted_product.txt",
      "images_extracted": 5
    },
    "structured_extraction": {
      "success": true,
      "confidence_score": 0.85,
      "errors": null,
      "warnings": null
    }
  },
  "structured_data": {
    "product_name": "KNORR ROUX BRUN 1KG",
    "legal_denomination": "Roux brun instantané déshydraté",
    "ean_code": "3011360006707",
    "ingredients": ["Farine de BLÉ", "graisse de palme", "colorant caramel E150c"],
    "allergens": [
      {
        "name": "Céréales contenant du gluten",
        "status": "Oui"
      }
    ],
    "nutritional_values": [
      {
        "name": "Valeur énergétique",
        "per_100g": "2451kJ - 592kcal",
        "per_100ml_prepared": "245kJ - 59kcal"
      }
    ],
    "vegetarian_suitable": true,
    "vegan_suitable": true,
    "organic_product": false,
    "gmo_free": true,
    "extraction_date": "2024-01-15T10:30:00.123456",
    "source_file": "extracted_product.txt"
  }
}
```

## 🛠️ Personnalisation

### Modification des Schémas

Éditez `extractor/schemas.py` pour ajouter/modifier les champs :

```python
class ProductSheet(BaseModel):
    # Ajout d'un nouveau champ
    custom_field: Optional[str] = Field(None, description="Champ personnalisé")
    
    # Modification d'un champ existant
    product_name: str = Field(description="Nom du produit (obligatoire)")
```

### Personnalisation des Prompts

Modifiez `extractor/langchain_extractor.py` dans la méthode `_get_system_prompt()` :

```python
def _get_system_prompt(self) -> str:
    return f"""Tu es un expert spécialisé dans MES fiches produits.
    
    INSTRUCTIONS SPÉCIFIQUES :
    - Attention particulière aux allergènes
    - Extraction précise des valeurs nutritionnelles
    - Respect des formats de dates français
    
    {self.parser.get_format_instructions()}"""
```

## 🐛 Dépannage

### Problèmes Courants

1. **Ollama non accessible**
   ```bash
   # Vérifier le statut
   curl http://localhost:11434/api/tags
   
   # Redémarrer si nécessaire
   ollama serve
   ```

2. **Modèle non trouvé**
   ```bash
   # Lister les modèles
   ollama list
   
   # Télécharger Llama 3.1
   ollama pull llama3.1:latest
   ```

3. **Erreurs de parsing JSON**
   - Réduire la température : `OLLAMA_TEMPERATURE=0.05`
   - Augmenter `num_predict` : `OLLAMA_NUM_PREDICT=8192`
   - Vérifier les prompts pour la cohérence

4. **Performance lente**
   - Réduire `batch_size` : `BATCH_SIZE=3`
   - Utiliser un modèle plus petit : `llama3.1:8b`
   - Optimiser les prompts

### Logs et Debugging

```bash
# Activer les logs détaillés
export LOG_LEVEL=DEBUG

# Consulter les logs
tail -f logs/extraction.log

# Tester la connectivité Ollama
python -c "
from langchain_ollama import ChatOllama
llm = ChatOllama(model='llama3.1:latest')
print(llm.invoke('Test de connexion'))
"
```

## 📊 Performance

### Benchmarks Typiques

- **Fichier simple** (1-2 pages) : 10-30 secondes
- **Fichier complexe** (3-5 pages) : 30-60 secondes
- **Lot de 10 fichiers** : 5-15 minutes

### Optimisations

1. **Modèle** : Utiliser `llama3.1:8b` pour plus de rapidité
2. **Température** : Réduire à 0.05 pour plus de cohérence
3. **Parallélisation** : Traiter plusieurs fichiers simultanément
4. **Cache** : Réutiliser les extractions déjà réalisées

## 🤝 Contribution

Pour contribuer à l'amélioration :

1. Testez sur vos propres fiches produits
2. Signalez les erreurs d'extraction
3. Proposez des améliorations de schémas
4. Partagez vos optimisations de prompts

## 📝 Licence

Ce projet utilise les mêmes conditions que votre projet principal. 