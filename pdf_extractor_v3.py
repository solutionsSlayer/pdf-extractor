#!/usr/bin/env python3
"""
Extracteur PDF Avancé - Version 3.0
Utilise PyMuPDF4LLM pour une extraction optimisée avec fallback intelligent
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
import fitz  # PyMuPDF
from typing import List, Optional, Tuple, Dict, Any
import re

# Import PyMuPDF4LLM si disponible
try:
    import pymupdf4llm
    PYMUPDF4LLM_AVAILABLE = True
    print("✅ PyMuPDF4LLM détecté - Extraction avancée activée")
except ImportError:
    PYMUPDF4LLM_AVAILABLE = False
    print("⚠️  PyMuPDF4LLM non disponible - Utilisation du mode fallback")
    print("   Installation recommandée : pip install pymupdf4llm")

class TextBlock:
    """Représente un bloc de texte avec ses propriétés spatiales"""
    def __init__(self, text: str, bbox: Tuple[float, float, float, float], 
                 font_size: float = 0, font_name: str = ""):
        self.text = text.strip()
        self.bbox = bbox  # (x0, y0, x1, y1)
        self.font_size = font_size
        self.font_name = font_name
        self.x0, self.y0, self.x1, self.y1 = bbox
        self.width = self.x1 - self.x0
        self.height = self.y1 - self.y0

class AdvancedPDFExtractorV3:
    """
    Extracteur PDF Version 3.0 - Extraction hybride avec PyMuPDF4LLM
    """
    
    def __init__(self, use_pymupdf4llm: bool = True):
        self.use_pymupdf4llm = use_pymupdf4llm and PYMUPDF4LLM_AVAILABLE
        self.extraction_method = "PyMuPDF4LLM" if self.use_pymupdf4llm else "Fallback"
        
    def extract_with_pymupdf4llm(self, pdf_path: str, pages: Optional[List[int]] = None) -> str:
        """
        Extraction principale avec PyMuPDF4LLM
        """
        try:
            # Extraction avec PyMuPDF4LLM
            if pages:
                md_text = pymupdf4llm.to_markdown(pdf_path, pages=pages)
            else:
                md_text = pymupdf4llm.to_markdown(pdf_path)
            
            # Post-traitement pour améliorer la lisibilité
            processed_text = self._post_process_markdown(md_text)
            return processed_text
            
        except Exception as e:
            print(f"⚠️  Erreur PyMuPDF4LLM: {e}")
            print("🔄 Basculement vers la méthode fallback...")
            return None
    
    def _post_process_markdown(self, md_text: str) -> str:
        """
        Post-traitement du Markdown pour améliorer la lisibilité
        """
        # Conversion des tableaux Markdown en format plus lisible
        processed = md_text
        
        # Amélioration des tableaux
        processed = self._enhance_markdown_tables(processed)
        
        # Nettoyage des espaces multiples
        processed = re.sub(r'\n\s*\n\s*\n', '\n\n', processed)
        
        return processed
    
    def _enhance_markdown_tables(self, text: str) -> str:
        """
        Améliore le formatage des tableaux Markdown
        """
        lines = text.split('\n')
        enhanced_lines = []
        in_table = False
        
        for line in lines:
            # Détection de tableau Markdown
            if '|' in line and line.strip().startswith('|'):
                if not in_table:
                    enhanced_lines.append('\n' + '='*60)
                    enhanced_lines.append('TABLEAU DÉTECTÉ')
                    enhanced_lines.append('='*60)
                    in_table = True
                
                # Amélioration du formatage des lignes de tableau
                enhanced_line = line.replace('|', ' | ').strip()
                enhanced_lines.append(enhanced_line)
                
            elif in_table and line.strip() == '':
                enhanced_lines.append('='*60 + '\n')
                enhanced_lines.append(line)
                in_table = False
            else:
                enhanced_lines.append(line)
                if in_table and '|' not in line:
                    in_table = False
        
        return '\n'.join(enhanced_lines)
    
    def extract_with_fallback(self, pdf_path: str) -> str:
        """
        Méthode fallback utilisant notre algorithme V2
        """
        try:
            doc = fitz.open(pdf_path)
            all_content = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Extraction des blocs de texte
                blocks = self._extract_text_blocks(page)
                
                if not blocks:
                    continue
                
                # Tentative de détection de tableaux
                tables = self._detect_tables(blocks)
                
                page_content = [f"\n{'='*60}"]
                page_content.append(f"PAGE {page_num + 1}")
                page_content.append('='*60)
                
                if tables:
                    page_content.append("🔍 STRUCTURES DÉTECTÉES (Méthode Fallback)")
                    for i, table in enumerate(tables, 1):
                        page_content.append(f"\n--- Tableau {i} ---")
                        page_content.extend(self._format_table_ascii(table))
                else:
                    page_content.append("📄 EXTRACTION SIMPLE (Méthode Fallback)")
                    page_content.append(page.get_text())
                
                all_content.extend(page_content)
            
            doc.close()
            return '\n'.join(all_content)
            
        except Exception as e:
            return f"❌ Erreur lors de l'extraction fallback: {e}"
    
    def _extract_text_blocks(self, page) -> List[TextBlock]:
        """Extrait les blocs de texte avec métadonnées"""
        blocks = []
        text_dict = page.get_text("dict")
        
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        if span["text"].strip():
                            blocks.append(TextBlock(
                                text=span["text"],
                                bbox=span["bbox"],
                                font_size=span["size"],
                                font_name=span["font"]
                            ))
        
        return blocks
    
    def _detect_tables(self, blocks: List[TextBlock], 
                      tolerance: float = 10.0) -> List[List[List[TextBlock]]]:
        """Détection de tableaux basée sur l'alignement spatial"""
        if len(blocks) < 4:
            return []
        
        # Groupement par lignes
        lines = self._group_blocks_by_lines(blocks, tolerance)
        
        if len(lines) < 2:
            return []
        
        # Détection de colonnes alignées
        tables = []
        current_table = []
        
        for line in lines:
            if len(line) > 1:  # Ligne avec plusieurs colonnes
                if self._is_aligned_with_previous(current_table, line, tolerance):
                    current_table.append(line)
                else:
                    if len(current_table) >= 2:
                        tables.append(current_table)
                    current_table = [line]
            else:
                if len(current_table) >= 2:
                    tables.append(current_table)
                current_table = []
        
        if len(current_table) >= 2:
            tables.append(current_table)
        
        return tables
    
    def _group_blocks_by_lines(self, blocks: List[TextBlock], 
                              tolerance: float) -> List[List[TextBlock]]:
        """Groupe les blocs par lignes horizontales"""
        sorted_blocks = sorted(blocks, key=lambda b: (b.y0, b.x0))
        lines = []
        current_line = []
        current_y = None
        
        for block in sorted_blocks:
            if current_y is None or abs(block.y0 - current_y) <= tolerance:
                current_line.append(block)
                current_y = block.y0 if current_y is None else current_y
            else:
                if current_line:
                    lines.append(sorted(current_line, key=lambda b: b.x0))
                current_line = [block]
                current_y = block.y0
        
        if current_line:
            lines.append(sorted(current_line, key=lambda b: b.x0))
        
        return lines
    
    def _is_aligned_with_previous(self, table: List[List[TextBlock]], 
                                 line: List[TextBlock], tolerance: float) -> bool:
        """Vérifie si une ligne est alignée avec le tableau existant"""
        if not table:
            return True
        
        last_line = table[-1]
        
        if abs(len(line) - len(last_line)) > 1:
            return False
        
        # Vérification de l'alignement des colonnes
        for i, block in enumerate(line):
            if i < len(last_line):
                if abs(block.x0 - last_line[i].x0) > tolerance:
                    return False
        
        return True
    
    def _format_table_ascii(self, table: List[List[TextBlock]]) -> List[str]:
        """Formate un tableau en ASCII"""
        if not table:
            return []
        
        # Calcul des largeurs de colonnes
        max_cols = max(len(row) for row in table)
        col_widths = [0] * max_cols
        
        # Préparation des données
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
        
        # Largeur minimale
        col_widths = [max(w, 8) for w in col_widths]
        
        # Formatage
        formatted_lines = []
        separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
        
        formatted_lines.append(separator)
        
        for i, row in enumerate(table_data):
            row_line = "|"
            for j, cell in enumerate(row):
                row_line += f" {cell:<{col_widths[j]}} |"
            formatted_lines.append(row_line)
            
            if i == 0:  # Séparateur après l'en-tête
                formatted_lines.append(separator)
        
        formatted_lines.append(separator)
        
        return formatted_lines
    
    def extract_pdf(self, pdf_path: str, output_dir: str = "resultats_v3", save_as_markdown: bool = False) -> str:
        """
        Extraction principale avec méthode hybride
        """
        # Création du répertoire de sortie
        Path(output_dir).mkdir(exist_ok=True)
        
        # Génération du nom de fichier de sortie
        pdf_name = Path(pdf_path).stem
        extension = ".md" if save_as_markdown else ".txt"
        output_file = Path(output_dir) / f"{pdf_name}_extracted{extension}"
        
        print(f"🔄 Extraction de: {pdf_path}")
        print(f"📁 Méthode: {self.extraction_method}")
        print(f"📄 Format de sortie: {'Markdown' if save_as_markdown else 'Texte'}")
        
        # Tentative d'extraction avec PyMuPDF4LLM
        content = None
        if self.use_pymupdf4llm:
            content = self.extract_with_pymupdf4llm(pdf_path)
        
        # Fallback si nécessaire
        if content is None:
            print("🔄 Utilisation de la méthode fallback...")
            self.extraction_method = "Fallback"
            content = self.extract_with_fallback(pdf_path)
        
        # Ajout des métadonnées
        if save_as_markdown:
            header = self._generate_markdown_header(pdf_path)
        else:
            header = self._generate_header(pdf_path)
        
        final_content = header + "\n\n" + content
        
        # Sauvegarde avec encodage UTF-8 approprié
        if save_as_markdown:
            # Sauvegarde optimisée pour Markdown
            Path(output_file).write_bytes(final_content.encode('utf-8'))
        else:
            # Sauvegarde texte classique
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_content)
        
        print(f"✅ Extraction terminée: {output_file}")
        return str(output_file)
    
    def _generate_header(self, pdf_path: str) -> str:
        """Génère l'en-tête informatif"""
        return f"""{'='*80}
EXTRACTEUR PDF AVANCÉ - VERSION 3.0
{'='*80}
📄 Fichier source: {pdf_path}
🕒 Date d'extraction: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔧 Méthode utilisée: {self.extraction_method}
🚀 Moteur: {'PyMuPDF4LLM + Fallback' if PYMUPDF4LLM_AVAILABLE else 'Fallback uniquement'}
{'='*80}"""

    def _generate_markdown_header(self, pdf_path: str) -> str:
        """Génère l'en-tête au format Markdown"""
        return f"""# 📄 Extraction PDF - Version 3.0

**Fichier source:** `{pdf_path}`  
**Date d'extraction:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Méthode utilisée:** {self.extraction_method}  
**Moteur:** {'PyMuPDF4LLM + Fallback' if PYMUPDF4LLM_AVAILABLE else 'Fallback uniquement'}  

---
"""

def process_single_file(pdf_path: str, output_dir: str = "resultats_v3", save_as_markdown: bool = False) -> None:
    """Traite un seul fichier PDF"""
    if not os.path.exists(pdf_path):
        print(f"❌ Fichier non trouvé: {pdf_path}")
        return
    
    extractor = AdvancedPDFExtractorV3()
    extractor.extract_pdf(pdf_path, output_dir, save_as_markdown)

def process_directory(input_dir: str, output_dir: str = "resultats_v3", save_as_markdown: bool = False) -> None:
    """Traite tous les PDFs d'un répertoire"""
    if not os.path.exists(input_dir):
        print(f"❌ Répertoire non trouvé: {input_dir}")
        return
    
    pdf_files = list(Path(input_dir).glob("*.pdf"))
    
    if not pdf_files:
        print(f"❌ Aucun fichier PDF trouvé dans: {input_dir}")
        return
    
    print(f"📁 Traitement de {len(pdf_files)} fichier(s) PDF...")
    
    extractor = AdvancedPDFExtractorV3()
    
    for pdf_file in pdf_files:
        try:
            extractor.extract_pdf(str(pdf_file), output_dir, save_as_markdown)
        except Exception as e:
            print(f"❌ Erreur lors du traitement de {pdf_file}: {e}")
    
    print(f"✅ Traitement terminé. Résultats dans: {output_dir}")

def main():
    parser = argparse.ArgumentParser(
        description="Extracteur PDF Avancé V3.0 - Extraction hybride avec PyMuPDF4LLM"
    )
    parser.add_argument("input", help="Fichier PDF ou répertoire à traiter")
    parser.add_argument("-o", "--output", default="resultats_v3", 
                       help="Répertoire de sortie (défaut: resultats_v3)")
    parser.add_argument("--no-pymupdf4llm", action="store_true",
                       help="Forcer l'utilisation de la méthode fallback")
    parser.add_argument("--markdown", action="store_true",
                       help="Sauvegarder au format Markdown (.md) au lieu de texte (.txt)")
    
    args = parser.parse_args()
    
    # Vérification de la disponibilité de PyMuPDF4LLM
    if args.no_pymupdf4llm:
        print("🔧 Mode fallback forcé par l'utilisateur")
    
    if args.markdown:
        print("📝 Format de sortie: Markdown (.md)")
    
    if os.path.isfile(args.input):
        process_single_file(args.input, args.output, args.markdown)
    elif os.path.isdir(args.input):
        process_directory(args.input, args.output, args.markdown)
    else:
        print(f"❌ Chemin invalide: {args.input}")
        sys.exit(1)

if __name__ == "__main__":
    main() 