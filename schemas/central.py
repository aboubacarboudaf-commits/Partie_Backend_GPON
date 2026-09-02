from typing import Optional

from pydantic import BaseModel


class CentralCreate(BaseModel):
    nom: str
    code: Optional[str] = None
    adresse: Optional[str] = None
    ville: Optional[str] = None
    quartier: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    type: Optional[str] = "central"
    reseau_id: Optional[int] = None
    position_x: Optional[int] = 100
    position_y: Optional[int] = 100


class CentralUpdate(BaseModel):
    nom: Optional[str] = None
    code: Optional[str] = None
    adresse: Optional[str] = None
    ville: Optional[str] = None
    quartier: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    type: Optional[str] = None
    reseau_id: Optional[int] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
