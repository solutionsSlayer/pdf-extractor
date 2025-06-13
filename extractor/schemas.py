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
    per_100ml_sold: Optional[str] = Field(None, description="Valeur pour 100ml de produit tel que vendu")
    per_100ml_prepared: Optional[str] = Field(None, description="Valeur pour 100ml de produit préparé")
    per_portion: Optional[str] = Field(None, description="Valeur par portion")
    percentage_reference: Optional[str] = Field(None, description="Pourcentage d'apport de référence")


class LogisticsInfo(BaseModel):
    """Informations logistiques"""
    element_type: str = Field(description="Type d'élément (UNITE CONSOMMATEUR, CARTON, PALETTE)")
    ean: Optional[str] = Field(None, description="Code EAN")
    description: Optional[str] = Field(None, description="Description du produit")
    net_weight: Optional[str] = Field(None, description="Poids net en kg")
    gross_weight: Optional[str] = Field(None, description="Poids brut en kg")
    dimensions: Optional[Dict[str, str]] = Field(None, description="Dimensions (longueur, largeur, hauteur)")
    volume: Optional[str] = Field(None, description="Volume en dm3")


class ProductSheet(BaseModel):
    """Schéma principal pour une fiche produit"""
    
    # Informations générales
    product_name: Optional[str] = Field(None, description="Nom du produit")
    legal_denomination: Optional[str] = Field(None, description="Dénomination légale")
    ean_code: Optional[str] = Field(None, description="Code EAN principal du produit")
    
    # Ingrédients et composition
    ingredients: Optional[List[str]] = Field(None, description="Liste des ingrédients")
    additives: Optional[List[str]] = Field(None, description="Liste des additifs")
    
    # Allergènes
    allergens: Optional[List[Allergen]] = Field(None, description="Liste des allergènes avec leur statut")
    
    # Avantages produit
    product_benefits: Optional[List[str]] = Field(None, description="Liste des avantages du produit")
    
    # Informations techniques
    preparation_instructions: Optional[str] = Field(None, description="Mode d'emploi/préparation")
    dosage_instructions: Optional[str] = Field(None, description="Instructions de dosage")
    shelf_life: Optional[str] = Field(None, description="DDM garantie réception entrepôt")
    storage_conditions: Optional[str] = Field(None, description="Mode de conservation")
    packaging_country: Optional[str] = Field(None, description="Pays de conditionnement")
    
    # Informations nutritionnelles
    nutritional_values: Optional[List[NutritionalValue]] = Field(None, description="Valeurs nutritionnelles")
    
    # Caractéristiques diététiques
    vegetarian_suitable: Optional[bool] = Field(None, description="Convient aux végétariens")
    vegan_suitable: Optional[bool] = Field(None, description="Convient aux végétaliens")
    organic_product: Optional[bool] = Field(None, description="Produit biologique")
    ionized_product: Optional[bool] = Field(None, description="Produit ionisé")
    gmo_free: Optional[bool] = Field(None, description="Sans OGM")
    alcohol_free: Optional[bool] = Field(None, description="Sans alcool")
    kosher: Optional[bool] = Field(None, description="Kasher")
    halal: Optional[bool] = Field(None, description="Halal")
    
    # Informations logistiques
    logistics_info: Optional[List[LogisticsInfo]] = Field(None, description="Informations logistiques")
    customs_code: Optional[str] = Field(None, description="Code douanier")
    
    # Qualité et certifications
    quality_standards: Optional[List[str]] = Field(None, description="Normes qualité (FSSC 22000, HACCP, etc.)")
    requires_health_approval: Optional[bool] = Field(None, description="Nécessite un agrément sanitaire")
    
    # Contact
    manufacturer_contact: Optional[Dict[str, str]] = Field(None, description="Informations de contact du fabricant")
    
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