from typing import Optional

from pydantic import BaseModel


class TypeLiaisonCreate(BaseModel):
    libelle: str
    couleur: Optional[str] = "#1890ff"
    style_trait: Optional[str] = "solide"
    epaisseur: Optional[int] = 2
    description: Optional[str] = None


class TypeLiaisonUpdate(BaseModel):
    libelle: Optional[str] = None
    couleur: Optional[str] = None
    style_trait: Optional[str] = None
    epaisseur: Optional[int] = None
    description: Optional[str] = None
