from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from core.audit import log_action
from core.security import get_current_user, require_admin_ou_technicien
from database import get_db
from models import Liaison, Utilisateur
from schemas.liaison import LiaisonCreate, LiaisonUpdate

router = APIRouter(prefix="/liaisons", tags=["liaisons"])


def _out(l: Liaison) -> dict:
    t = l.type_liaison
    return {
        "id": l.id,
        "source_id": l.source_id,
        "destination_id": l.destination_id,
        "source_libelle": l.source.libelle if l.source else None,
        "destination_libelle": l.destination.libelle if l.destination else None,
        "type_liaison_id": l.type_liaison_id,
        "type_liaison_libelle": t.libelle if t else None,
        "type_liaison_couleur": t.couleur if t else None,
        "type_liaison_epaisseur": t.epaisseur if t else None,
        "type_liaison_style": t.style_trait if t else None,
        "port_source": l.port_source,
        "port_destination": l.port_destination,
        "longueur_m": float(l.longueur_m) if l.longueur_m is not None else None,
        "statut": l.statut,
        "reseau_id": l.reseau_id,
    }


@router.get("/")
def lister(
    statut: Optional[str] = None,
    equipement_id: Optional[int] = None,
    reseau_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    query = db.query(Liaison).options(
        joinedload(Liaison.source), joinedload(Liaison.destination), joinedload(Liaison.type_liaison)
    ).filter(Liaison.supprime == False)  # noqa: E712
    if statut:
        query = query.filter(Liaison.statut == statut)
    if equipement_id is not None:
        query = query.filter((Liaison.source_id == equipement_id) | (Liaison.destination_id == equipement_id))
    if reseau_id is not None:
        query = query.filter(Liaison.reseau_id == reseau_id)
    return [_out(l) for l in query.all()]


@router.post("/", status_code=status.HTTP_201_CREATED)
def creer(
    payload: LiaisonCreate,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin_ou_technicien),
):
    liaison = Liaison(**payload.model_dump())
    db.add(liaison)
    db.commit()
    db.refresh(liaison)
    log_action(db, "creation", "liaison", liaison.id, f"Création liaison: {liaison.source_id} → {liaison.destination_id}", utilisateur, request)
    return _out(liaison)


@router.put("/{liaison_id}")
def modifier(
    liaison_id: int,
    payload: LiaisonUpdate,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin_ou_technicien),
):
    liaison = db.query(Liaison).filter(Liaison.id == liaison_id, Liaison.supprime == False).first()  # noqa: E712
    if not liaison:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Liaison introuvable")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(liaison, field, value)
    db.commit()
    db.refresh(liaison)
    log_action(db, "modification", "liaison", liaison.id, f"Modification liaison ID:{liaison.id}", utilisateur, request)
    return _out(liaison)


@router.delete("/{liaison_id}")
def supprimer(
    liaison_id: int,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin_ou_technicien),
):
    liaison = db.query(Liaison).filter(Liaison.id == liaison_id, Liaison.supprime == False).first()  # noqa: E712
    if not liaison:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Liaison introuvable")
    liaison.supprime = True
    db.commit()
    log_action(db, "suppression", "liaison", liaison.id, f"Suppression liaison ID:{liaison.id}", utilisateur, request)
    return {"message": "Liaison supprimée"}
