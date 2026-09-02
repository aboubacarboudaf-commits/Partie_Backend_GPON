from typing import Optional

from pydantic import BaseModel


class LiaisonCreate(BaseModel):
    source_id: int
    destination_id: int
    type_liaison_id: Optional[int] = None
    reseau_id: Optional[int] = None
    port_source: Optional[str] = None
    port_destination: Optional[str] = None
    longueur_m: Optional[float] = None
    statut: Optional[str] = "ok"


class LiaisonUpdate(BaseModel):
    source_id: Optional[int] = None
    destination_id: Optional[int] = None
    type_liaison_id: Optional[int] = None
    reseau_id: Optional[int] = None
    port_source: Optional[str] = None
    port_destination: Optional[str] = None
    longueur_m: Optional[float] = None
    statut: Optional[str] = None
