# Extracted Data Directory

Ce dossier contient les résultats d'extraction des fiches techniques PDF, organisés par fichier.

## Structure des fichiers générés

Pour chaque PDF extrait, un dossier portant le nom du fichier (sans extension) est créé :

```
extracted_data/
├── 8710522647561/                    # Nom du fichier PDF
│   ├── extracted_8710522647561.txt   # Contenu textuel extrait
│   └── metadata_8710522647561.json   # Métadonnées de l'extraction
├── 3011360006707/
│   ├── extracted_3011360006707.txt
│   └── metadata_3011360006707.json
└── ...
```

## Images extraites

Les images sont également organisées par fichier PDF dans le dossier `extracted_images/` :

```
extracted_images/
├── 8710522647561/                    # Images du PDF 8710522647561.pdf
│   ├── 8710522647561.pdf-0-0.png
│   ├── 8710522647561.pdf-0-1.png
│   └── ...
├── 3011360006707/                    # Images du PDF 3011360006707.pdf
│   ├── 3011360006707.pdf-0-0.png
│   └── ...
└── ...
```

## Contenu des fichiers

- **`extracted_[nom].txt`** : Le contenu textuel complet extrait du PDF, organisé par chunks
- **`metadata_[nom].json`** : Métadonnées incluant :
  - Timestamp d'extraction
  - Taille du fichier original
  - Nombre de chunks, tableaux et images
  - Longueur totale du texte extrait

## Organisation par marque (optionnel)

Vous pouvez utiliser l'option `--output` pour organiser par marque :

```bash
# Extraire dans un sous-dossier unilever
python cli.py --folder FT/unilever --output extracted_data/unilever

# Extraire dans un sous-dossier charles_alice  
python cli.py --folder FT/charles_alice --output extracted_data/charles_alice
```

Cela créera une structure comme :

```
extracted_data/
├── unilever/
│   ├── 8710522647561/
│   │   ├── extracted_8710522647561.txt
│   │   └── metadata_8710522647561.json
│   └── ...
├── charles_alice/
│   ├── 3288310846038/
│   │   ├── extracted_3288310846038.txt
│   │   └── metadata_3288310846038.json
│   └── ...
└── ...
```

## Nettoyage

Ce dossier peut être vidé périodiquement selon vos besoins. Les fichiers générés sont des copies des données extraites et peuvent être régénérés à tout moment. 