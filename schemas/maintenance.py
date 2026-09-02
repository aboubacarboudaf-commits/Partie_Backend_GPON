from typing import Optional

from pydantic import BaseModel


class MaintenanceCreate(BaseModel):
    titre: str
    description: Optional[str] = None
    type: Optional[str] = "corrective"
    statut: Optional[str] = "planifiee"
    equipement_id: Optional[int] = None
    liaison_id: Optional[int] = None
    incident_id: Optional[int] = None
    technicien: Optional[str] = None
    notes: Optional[str] = None
    date_planifiee: str
    date_debut: Optional[str] = None
    date_fin: Optional[str] = None


class MaintenanceUpdate(BaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    statut: Optional[str] = None
    equipement_id: Optional[int] = None
    liaison_id: Optional[int] = None
    incident_id: Optional[int] = None
    technicien: Optional[str] = None
    notes: Optional[str] = None
    date_planifiee: Optional[str] = None
    date_debut: Optional[str] = None
    date_fin: Optional[str] = None
