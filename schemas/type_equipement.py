from typing import Optional

from pydantic import BaseModel


class TypeEquipementCreate(BaseModel):
    libelle: str
    description: Optional[str] = None
    categorie: Optional[str] = "actif"
    icone_type: Optional[str] = "antd"
    icone: Optional[str] = None
    icone_url: Optional[str] = None
    possede_ip: Optional[bool] = True
    possede_port: Optional[bool] = False
    possede_ratio: Optional[bool] = False
    prefixe_port: Optional[str] = "Port"


class TypeEquipementUpdate(BaseModel):
    libelle: Optional[str] = None
    description: Optional[str] = None
    categorie: Optional[str] = None
    icone_type: Optional[str] = None
    icone: Optional[str] = None
    icone_url: Optional[str] = None
    possede_ip: Optional[bool] = None
    possede_port: Optional[bool] = None
    possede_ratio: Optional[bool] = None
    prefixe_port: Optional[str] = None
