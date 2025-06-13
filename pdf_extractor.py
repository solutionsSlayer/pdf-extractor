#!/usr/bin/env python3
"""
PDF Content Extractor - Version Avancée

Ce module fournit des fonctionnalités avancées pour extraire le contenu de fiches techniques PDF
en conservant leur structure exacte, incluant les tableaux et la mise en forme complexe.

Auteur: Assistant IA
Date: 2024
Version: 2.0 - Extraction adaptative avec préservation de structure
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import fitz  # PyMuPDF
import re
from dataclasses import dataclass


@dataclass
class TextBlock:
    """Représente un bloc de texte avec ses coordonnées et propriétés."""
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    font_size: float
    font_name: str


class AdvancedPDFExtractor:
    """
    Extracteur PDF avancé qui préserve la structure complexe des documents.
    
    Cette classe utilise plusieurs méthodes d'extraction adaptatives pour gérer
    différents types de PDFs et préserver au maximum leur structure originale.
    """
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialise l'extracteur PDF avancé.
        
        Args:
            output_dir (str): Répertoire de sortie pour les fichiers extraits
        """
        self.output_dir = Path(output_dir)
        self._ensure_output_directory()
        
        # Configuration pour l'analyse adaptative
        self.min_table_rows = 2
        self.column_tolerance = 5.0  # Tolérance pour l'alignement des colonnes
        self.row_tolerance = 3.0     # Tolérance pour l'alignement des lignes
    
    def _ensure_output_directory(self) -> None:
        """
        Crée le répertoire de sortie s'il n'existe pas.
        
        Raises:
            OSError: Si impossible de créer le répertoire
        """
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise OSError(f"Impossible de créer le répertoire de sortie: {e}")
    
    def _extract_text_blocks(self, page) -> List[TextBlock]:
        """
        Extrait les blocs de texte avec leurs positions et propriétés.
        
        Args:
            page: Page PyMuPDF
            
        Returns:
            List[TextBlock]: Liste des blocs de texte avec métadonnées
        """
        blocks = []
        
        # Extraction avec informations de formatage
        text_dict = page.get_text("dict")
        
        for block in text_dict.get("blocks", []):
            if "lines" not in block:
                continue
                
            for line in block["lines"]:
                for span in line["spans"]:
                    if span["text"].strip():
                        blocks.append(TextBlock(
                            text=span["text"],
                            x0=span["bbox"][0],
                            y0=span["bbox"][1],
                            x1=span["bbox"][2],
                            y1=span["bbox"][3],
                            font_size=span["size"],
                            font_name=span["font"]
                        ))
        
        return blocks
    
    def _detect_table_structure(self, blocks: List[TextBlock]) -> List[List[TextBlock]]:
        """
        Détecte automatiquement les structures de tableaux dans les blocs de texte.
        
        Args:
            blocks: Liste des blocs de texte
            
        Returns:
            List[List[TextBlock]]: Lignes de tableau détectées
        """
        if not blocks:
            return []
        
        # Grouper les blocs par lignes (même Y approximatif)
        rows = {}
        for block in blocks:
            row_y = round(block.y0 / self.row_tolerance) * self.row_tolerance
            if row_y not in rows:
                rows[row_y] = []
            rows[row_y].append(block)
        
        # Trier les lignes par position Y
        sorted_rows = [rows[y] for y in sorted(rows.keys())]
        
        # Détecter les colonnes cohérentes
        potential_tables = []
        current_table = []
        
        for row_blocks in sorted_rows:
            # Trier les blocs de la ligne par position X
            row_blocks.sort(key=lambda b: b.x0)
            
            # Vérifier si cette ligne peut faire partie d'un tableau
            if len(row_blocks) >= 2:  # Au moins 2 colonnes
                if self._is_table_row(row_blocks, current_table):
                    current_table.append(row_blocks)
                else:
                    # Sauvegarder le tableau précédent s'il est valide
                    if len(current_table) >= self.min_table_rows:
                        potential_tables.append(current_table)
                    current_table = [row_blocks]
            else:
                # Fin du tableau potentiel
                if len(current_table) >= self.min_table_rows:
                    potential_tables.append(current_table)
                current_table = []
        
        # Ajouter le dernier tableau s'il est valide
        if len(current_table) >= self.min_table_rows:
            potential_tables.append(current_table)
        
        return potential_tables
    
    def _is_table_row(self, row_blocks: List[TextBlock], existing_table: List[List[TextBlock]]) -> bool:
        """
        Détermine si une ligne de blocs peut faire partie d'un tableau existant.
        
        Args:
            row_blocks: Blocs de la ligne courante
            existing_table: Tableau en cours de construction
            
        Returns:
            bool: True si la ligne peut faire partie du tableau
        """
        if not existing_table:
            return True
        
        # Vérifier l'alignement des colonnes avec les lignes précédentes
        last_row = existing_table[-1]
        
        # Tolérance pour l'alignement des colonnes
        if abs(len(row_blocks) - len(last_row)) > 1:
            return False
        
        # Vérifier l'alignement approximatif des positions X
        for i, block in enumerate(row_blocks):
            if i < len(last_row):
                x_diff = abs(block.x0 - last_row[i].x0)
                if x_diff > self.column_tolerance:
                    return False
        
        return True
    
    def _format_table(self, table: List[List[TextBlock]]) -> str:
        """
        Formate un tableau détecté en texte structuré.
        
        Args:
            table: Tableau sous forme de lignes de blocs
            
        Returns:
            str: Tableau formaté en texte
        """
        if not table:
            return ""
        
        # Calculer les largeurs de colonnes
        max_cols = max(len(row) for row in table)
        col_widths = [0] * max_cols
        
        # Préparer les données du tableau
        table_data = []
        for row in table:
            row_data = []
            for i in range(max_cols):
                if i < len(row):
                    text = row[i].text.strip()
                    row_data.append(text)
                    col_widths[i] = max(col_widths[i], len(text))
                else:
                    row_data.append("")
            table_data.append(row_data)
        
        # Générer le tableau formaté
        formatted_lines = []
        
        # Ligne de séparation
        separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
        formatted_lines.append(separator)
        
        # Lignes de données
        for i, row_data in enumerate(table_data):
            row_line = "|"
            for j, cell in enumerate(row_data):
                padded_cell = f" {cell:<{col_widths[j]}} "
                row_line += padded_cell + "|"
            formatted_lines.append(row_line)
            
            # Séparateur après l'en-tête (première ligne)
            if i == 0 and len(table_data) > 1:
                formatted_lines.append(separator)
        
        # Ligne de fermeture
        formatted_lines.append(separator)
        
        return "\n".join(formatted_lines)
    
    def _extract_structured_content(self, page) -> str:
        """
        Extrait le contenu avec préservation de structure avancée.
        
        Args:
            page: Page PyMuPDF
            
        Returns:
            str: Contenu structuré avec tableaux formatés
        """
        # Méthode 1: Extraction avec structure (prioritaire)
        try:
            blocks = self._extract_text_blocks(page)
            if not blocks:
                # Fallback vers extraction simple
                return page.get_text()
            
            # Détecter les tableaux
            tables = self._detect_table_structure(blocks)
            
            # Marquer les blocs qui font partie de tableaux
            table_blocks = set()
            for table in tables:
                for row in table:
                    for block in row:
                        table_blocks.add(id(block))
            
            # Construire le contenu final
            content_parts = []
            
            # Ajouter les tableaux formatés
            for table in tables:
                formatted_table = self._format_table(table)
                if formatted_table:
                    content_parts.append("\n[TABLEAU DÉTECTÉ]")
                    content_parts.append(formatted_table)
                    content_parts.append("[FIN TABLEAU]\n")
            
            # Ajouter le texte non-tabulaire
            non_table_blocks = [b for b in blocks if id(b) not in table_blocks]
            if non_table_blocks:
                # Trier par position (haut vers bas, gauche vers droite)
                non_table_blocks.sort(key=lambda b: (b.y0, b.x0))
                
                content_parts.append("\n[CONTENU TEXTUEL]")
                for block in non_table_blocks:
                    content_parts.append(block.text)
                content_parts.append("[FIN CONTENU TEXTUEL]\n")
            
            return "\n".join(content_parts)
            
        except Exception as e:
            # Fallback vers extraction simple en cas d'erreur
            print(f"⚠️  Extraction structurée échouée, utilisation du mode simple: {e}")
            return page.get_text()
    
    def extract_pdf_content(self, pdf_path: str) -> str:
        """
        Extrait le contenu textuel d'un fichier PDF avec préservation de structure avancée.
        
        Args:
            pdf_path (str): Chemin vers le fichier PDF à traiter
            
        Returns:
            str: Contenu extrait du PDF avec structure préservée
            
        Raises:
            FileNotFoundError: Si le fichier PDF n'existe pas
            Exception: Si erreur lors de l'extraction
        """
        pdf_file = Path(pdf_path)
        
        if not pdf_file.exists():
            raise FileNotFoundError(f"Fichier PDF introuvable: {pdf_path}")
        
        if not pdf_file.suffix.lower() == '.pdf':
            raise ValueError(f"Le fichier doit être un PDF: {pdf_path}")
        
        try:
            # Ouverture du document PDF avec PyMuPDF
            document = fitz.open(pdf_path)
            extracted_content = []
            
            # Traitement page par page avec extraction structurée
            for page_num, page in enumerate(document, 1):
                # Ajout d'un séparateur de page pour la lisibilité
                extracted_content.append(f"\n{'='*80}")
                extracted_content.append(f"PAGE {page_num} - EXTRACTION STRUCTURÉE")
                extracted_content.append(f"{'='*80}\n")
                
                # Extraction avec préservation de structure
                structured_content = self._extract_structured_content(page)
                
                if structured_content.strip():
                    extracted_content.append(structured_content)
                else:
                    extracted_content.append("[Page sans contenu textuel détectable]")
                
                extracted_content.append("\n")
            
            # Fermeture du document
            document.close()
            
            return "\n".join(extracted_content)
            
        except Exception as e:
            raise Exception(f"Erreur lors de l'extraction du PDF {pdf_path}: {e}")
    
    def save_extracted_content(self, content: str, original_filename: str) -> str:
        """
        Sauvegarde le contenu extrait dans un fichier texte.
        
        Args:
            content (str): Contenu à sauvegarder
            original_filename (str): Nom du fichier PDF original
            
        Returns:
            str: Chemin vers le fichier de sortie créé
            
        Raises:
            OSError: Si erreur lors de l'écriture du fichier
        """
        # Génération du nom de fichier de sortie
        base_name = Path(original_filename).stem
        output_filename = f"{base_name}_structured_extracted.txt"
        output_path = self.output_dir / output_filename
        
        try:
            # Écriture du contenu avec encodage UTF-8
            with open(output_path, 'w', encoding='utf-8') as output_file:
                # Ajout d'un en-tête informatif
                header = f"""# EXTRACTION STRUCTURÉE PDF
# Fichier source: {original_filename}
# Date d'extraction: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Méthode: Extraction adaptative avec préservation de structure
# ================================================================================

"""
                output_file.write(header)
                output_file.write(content)
                
            return str(output_path)
            
        except OSError as e:
            raise OSError(f"Erreur lors de la sauvegarde: {e}")
    
    def process_pdf(self, pdf_path: str) -> str:
        """
        Traite un fichier PDF complet: extraction structurée + sauvegarde.
        
        Args:
            pdf_path (str): Chemin vers le fichier PDF à traiter
            
        Returns:
            str: Chemin vers le fichier de sortie créé
            
        Raises:
            Exception: Si erreur lors du traitement
        """
        print(f"🔍 Traitement structuré du fichier: {pdf_path}")
        
        try:
            # Extraction du contenu avec structure
            content = self.extract_pdf_content(pdf_path)
            
            # Sauvegarde du contenu extrait
            output_path = self.save_extracted_content(content, pdf_path)
            
            print(f"✅ Extraction structurée terminée: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Erreur lors du traitement de {pdf_path}: {e}")
            raise
    
    def process_directory(self, directory_path: str) -> List[str]:
        """
        Traite tous les fichiers PDF d'un répertoire avec extraction structurée.
        
        Args:
            directory_path (str): Chemin vers le répertoire contenant les PDFs
            
        Returns:
            List[str]: Liste des chemins vers les fichiers de sortie créés
        """
        directory = Path(directory_path)
        
        if not directory.exists():
            raise FileNotFoundError(f"Répertoire introuvable: {directory_path}")
        
        # Recherche de tous les fichiers PDF
        pdf_files = list(directory.glob("*.pdf"))
        
        if not pdf_files:
            print(f"⚠️  Aucun fichier PDF trouvé dans: {directory_path}")
            return []
        
        print(f"📁 Traitement structuré du répertoire: {directory_path}")
        print(f"📄 {len(pdf_files)} fichier(s) PDF trouvé(s)")
        
        output_files = []
        
        for pdf_file in pdf_files:
            try:
                output_path = self.process_pdf(str(pdf_file))
                output_files.append(output_path)
            except Exception as e:
                print(f"⚠️  Échec du traitement de {pdf_file}: {e}")
                continue
        
        return output_files


def main():
    """
    Point d'entrée principal du script.
    
    Gère les arguments de ligne de commande et orchestre l'extraction structurée.
    """
    parser = argparse.ArgumentParser(
        description="Extracteur PDF avancé avec préservation de structure et tableaux",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python pdf_extractor.py -f fichier.pdf
  python pdf_extractor.py -d ./FT/unilever/
  python pdf_extractor.py -f fichier.pdf -o results/
  
Fonctionnalités avancées:
  - Détection automatique de tableaux
  - Préservation de la structure complexe
  - Adaptation générique à différents formats PDF
  - Extraction avec fallback sécurisé
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--file', 
                       help='Chemin vers un fichier PDF spécifique')
    group.add_argument('-d', '--directory', 
                       help='Chemin vers un répertoire contenant des PDFs')
    
    parser.add_argument('-o', '--output', 
                        default='output',
                        help='Répertoire de sortie (défaut: output)')
    
    args = parser.parse_args()
    
    try:
        # Initialisation de l'extracteur avancé
        extractor = AdvancedPDFExtractor(output_dir=args.output)
        
        if args.file:
            # Traitement d'un fichier unique
            extractor.process_pdf(args.file)
            
        elif args.directory:
            # Traitement d'un répertoire
            output_files = extractor.process_directory(args.directory)
            
            if output_files:
                print(f"\n🎉 Traitement structuré terminé avec succès!")
                print(f"📊 {len(output_files)} fichier(s) traité(s)")
                print(f"🔧 Fonctionnalités utilisées: Détection de tableaux, préservation de structure")
            else:
                print("\n⚠️  Aucun fichier n'a pu être traité")
                
    except KeyboardInterrupt:
        print("\n⏹️  Traitement interrompu par l'utilisateur")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 