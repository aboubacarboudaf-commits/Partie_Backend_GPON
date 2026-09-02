from typing import Optional

from pydantic import BaseModel


class IncidentCreate(BaseModel):
    type: str
    description: str
    statut: Optional[str] = "ouvert"
    priorite: Optional[str] = "moyenne"
    date_ouverture: str
    date_fermeture: Optional[str] = None
    equipement_id: Optional[int] = None
    liaison_id: Optional[int] = None
    source: Optional[str] = "manuel"


class IncidentUpdate(BaseModel):
    type: Optional[str] = None
    description: Optional[str] = None
    statut: Optional[str] = None
    priorite: Optional[str] = None
    date_ouverture: Optional[str] = None
    date_fermeture: Optional[str] = None
    equipement_id: Optional[int] = None
    liaison_id: Optional[int] = None
