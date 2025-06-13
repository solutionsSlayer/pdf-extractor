#!/usr/bin/env python3
"""
Script d'installation pour l'Extracteur PDF V3.0
Installe PyMuPDF4LLM et vérifie les dépendances
"""

import subprocess
import sys
import importlib

def check_package(package_name):
    """Vérifie si un package est installé"""
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False

def install_package(package_name):
    """Installe un package via pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("🚀 Installation de l'Extracteur PDF V3.0")
    print("="*50)
    
    # Liste des packages requis
    packages = {
        "pymupdf": "PyMuPDF (extraction PDF de base)",
        "pymupdf4llm": "PyMuPDF4LLM (extraction avancée)",
    }
    
    # Vérification et installation
    for package, description in packages.items():
        print(f"\n📦 Vérification de {description}...")
        
        if check_package(package):
            print(f"✅ {package} déjà installé")
        else:
            print(f"⚠️  {package} non trouvé, installation en cours...")
            if install_package(package):
                print(f"✅ {package} installé avec succès")
            else:
                print(f"❌ Erreur lors de l'installation de {package}")
                if package == "pymupdf4llm":
                    print("   L'extracteur fonctionnera en mode fallback uniquement")
                else:
                    print("   Installation critique échouée")
                    return False
    
    print("\n" + "="*50)
    print("🎉 Installation terminée !")
    print("\n📋 Commandes de test disponibles :")
    print("   python pdf_extractor_v3.py ./FT/unilever/")
    print("   python pdf_extractor_v3.py ./FT/unilever/ma_fiche.pdf")
    print("   python pdf_extractor_v3.py --help")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 