from typing import Optional

from pydantic import BaseModel


class EquipementCreate(BaseModel):
    libelle: str
    type_equipement_id: int
    adresse_ip: Optional[str] = None
    ville: Optional[str] = None
    quartier: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    nbre_port_pon: Optional[int] = 0
    nbre_port: Optional[int] = 0
    ratio: Optional[int] = 0
    etat: Optional[str] = "actif"
    position_x: Optional[int] = 100
    position_y: Optional[int] = 100
    central_id: Optional[int] = None
    reseau_id: Optional[int] = None


class EquipementUpdate(BaseModel):
    libelle: Optional[str] = None
    type_equipement_id: Optional[int] = None
    adresse_ip: Optional[str] = None
    ville: Optional[str] = None
    quartier: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    nbre_port_pon: Optional[int] = None
    nbre_port: Optional[int] = None
    ratio: Optional[int] = None
    etat: Optional[str] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    central_id: Optional[int] = None
    reseau_id: Optional[int] = None
