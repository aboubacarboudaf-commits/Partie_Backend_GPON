from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from core.audit import log_action
from core.auto_maintenance import creer_maintenance_automatique
from core.security import get_current_user, require_admin_ou_technicien
from database import get_db
from models import Incident, Utilisateur
from schemas.incident import IncidentCreate, IncidentUpdate

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _out(i: Incident) -> dict:
    return {
        "id_incident": i.id_incident,
        "type": i.type,
        "source": i.source,
        "description": i.description,
        "equipement_id": i.equipement_id,
        "equipement_libelle": i.equipement.libelle if i.equipement else None,
        "liaison_id": i.liaison_id,
        "statut": i.statut,
        "priorite": i.priorite,
        "date_ouverture": i.date_ouverture.isoformat() if i.date_ouverture else None,
        "date_fermeture": i.date_fermeture.isoformat() if i.date_fermeture else None,
    }


@router.get("/")
def lister(
    statut: Optional[str] = None,
    priorite: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    query = db.query(Incident).options(joinedload(Incident.equipement)).filter(
        Incident.supprime == False  # noqa: E712
    )
    if statut:
        query = query.filter(Incident.statut == statut)
    if priorite:
        query = query.filter(Incident.priorite == priorite)
    return [_out(i) for i in query.order_by(Incident.date_ouverture.desc()).all()]


@router.post("/", status_code=status.HTTP_201_CREATED)
def creer(
    payload: IncidentCreate,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin_ou_technicien),
):
    incident = Incident(**payload.model_dump())
    db.add(incident)
    db.commit()
    db.refresh(incident)
    log_action(db, "creation", "incident", incident.id_incident, f"Création incident: {incident.type} - {incident.description}", utilisateur, request)
    creer_maintenance_automatique(db, incident, utilisateur, request)
    return _out(incident)


@router.put("/{incident_id}")
def modifier(
    incident_id: int,
    payload: IncidentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin_ou_technicien),
):
    incident = db.query(Incident).filter(
        Incident.id_incident == incident_id, Incident.supprime == False  # noqa: E712
    ).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident introuvable")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(incident, field, value)
    db.commit()
    db.refresh(incident)
    log_action(db, "modification", "incident", incident.id_incident, f"Modification incident ID:{incident.id_incident}", utilisateur, request)
    return _out(incident)


@router.delete("/{incident_id}")
def supprimer(
    incident_id: int,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin_ou_technicien),
):
    incident = db.query(Incident).filter(
        Incident.id_incident == incident_id, Incident.supprime == False  # noqa: E712
    ).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident introuvable")
    incident.supprime = True
    db.commit()
    log_action(db, "suppression", "incident", incident.id_incident, f"Suppression incident ID:{incident.id_incident}", utilisateur, request)
    return {"message": "Incident supprimé"}
