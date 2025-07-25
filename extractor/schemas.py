from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class AllergenStatus(str, Enum):
    """Status des allergènes"""
    PRESENT = "Oui"
    TRACES = "Traces"
    ABSENT = "Non"


class Allergen(BaseModel):
    """Modèle pour un allergène"""
    name: str = Field(description="Nom de l'allergène")
    status: AllergenStatus = Field(description="Statut de l'allergène (Oui/Traces/Non)")


class NutritionalValue(BaseModel):
    """Valeur nutritionnelle"""
    name: str = Field(description="Nom de la valeur nutritionnelle")
    per_100g: Optional[str] = Field(None, description="Valeur pour 100g de produit")
    percentage_reference: Optional[str] = Field(None, description="Pourcentage de l'apport de référence")


class ManufacturerContact(BaseModel):
    """Informations de contact du fabricant"""
    nom: Optional[str] = Field(None, description="Nom du fabricant")
    adresse: Optional[str] = Field(None, description="Adresse du fabricant")
    telephone: Optional[str] = Field(None, description="Numéro de téléphone")
    email: Optional[str] = Field(None, description="Adresse email")
    website: Optional[str] = Field(None, description="Site web")


class ProductSheet(BaseModel):
    """Schéma principal pour une fiche produit"""
    
    # Informations générales
    product_name: Optional[str] = Field(None, description="Nom du produit")
    legal_denomination: Optional[str] = Field(None, description="Dénomination légale")
    ean_code: Optional[str] = Field(None, description="Code EAN principal du produit")
    ean_carton: Optional[str] = Field(None, description="Code EAN carton/couche (DUN 14)")
    ean_palette: Optional[str] = Field(None, description="Code EAN palette (DUN 14)")
    
    # Ingrédients et composition
    ingredients: Optional[List[str]] = Field(None, description="Liste des ingrédients")
    additives: Optional[List[str]] = Field(None, description="Liste des additifs")
    
    # Allergènes
    allergens: Optional[List[Allergen]] = Field(None, description="Liste des allergènes avec leur statut")
    
    shelf_life: Optional[str] = Field(None, description="DDM garantie réception entrepôt")
    storage_conditions: Optional[str] = Field(None, description="Mode de conservation")
    packaging_country: Optional[str] = Field(None, description="Pays de conditionnement")
    
    # Informations nutritionnelles
    nutritional_values: Optional[List[NutritionalValue]] = Field(None, description="Valeurs nutritionnelles")
    
    # Contact
    manufacturer_contact: Optional[ManufacturerContact] = Field(None, description="Informations de contact du fabricant")
    
    # Métadonnées
    extraction_date: Optional[str] = Field(None, description="Date d'extraction des données")
    source_file: Optional[str] = Field(None, description="Fichier source")


class ExtractionResult(BaseModel):
    """Résultat de l'extraction avec métadonnées"""
    success: bool = Field(description="Succès de l'extraction")
    product_sheet: Optional[ProductSheet] = Field(None, description="Fiche produit extraite")
    errors: Optional[List[str]] = Field(None, description="Liste des erreurs rencontrées")
    warnings: Optional[List[str]] = Field(None, description="Liste des avertissements")
    confidence_score: Optional[float] = Field(None, description="Score de confiance de l'extraction (0-1)") 