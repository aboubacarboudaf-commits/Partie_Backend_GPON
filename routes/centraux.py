from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from core.audit import log_action
from core.security import get_current_user, require_admin
from core.villes import valider_coordonnees_ville
from database import get_db
from models import Central, Utilisateur
from schemas.central import CentralCreate, CentralUpdate

router = APIRouter(prefix="/centraux", tags=["centraux"])


def _out(c: Central) -> dict:
    return {
        "id": c.id,
        "nom": c.nom,
        "code": c.code,
        "adresse": c.adresse,
        "ville": c.ville,
        "quartier": c.quartier,
        "longitude": c.longitude,
        "latitude": c.latitude,
        "type": c.type,
        "reseau_id": c.reseau_id,
        "position_x": c.position_x,
        "position_y": c.position_y,
    }


@router.get("/")
def lister(reseau_id: Optional[int] = None, db: Session = Depends(get_db), _=Depends(get_current_user)):
    query = db.query(Central).filter(Central.supprime == False)  # noqa: E712
    if reseau_id is not None:
        query = query.filter(Central.reseau_id == reseau_id)
    return [_out(c) for c in query.all()]


@router.post("/", status_code=status.HTTP_201_CREATED)
def creer(
    payload: CentralCreate,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin),
):
    if payload.code:
        existant = db.query(Central).filter(Central.code == payload.code, Central.supprime == False).first()  # noqa: E712
        if existant:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ce code central existe déjà")

    try:
        valider_coordonnees_ville(payload.ville, payload.latitude, payload.longitude)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    central = Central(**payload.model_dump())
    db.add(central)
    db.commit()
    db.refresh(central)
    log_action(db, "creation", "central", central.id, f"Création central: {central.nom}", utilisateur, request)
    return _out(central)


@router.put("/{central_id}")
def modifier(
    central_id: int,
    payload: CentralUpdate,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin),
):
    central = db.query(Central).filter(Central.id == central_id, Central.supprime == False).first()  # noqa: E712
    if not central:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Central introuvable")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(central, field, value)

    try:
        valider_coordonnees_ville(central.ville, central.latitude, central.longitude)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    db.commit()
    db.refresh(central)
    log_action(db, "modification", "central", central.id, f"Modification central: {central.nom}", utilisateur, request)
    return _out(central)


@router.delete("/{central_id}")
def supprimer(
    central_id: int,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin),
):
    central = db.query(Central).filter(Central.id == central_id, Central.supprime == False).first()  # noqa: E712
    if not central:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Central introuvable")
    central.supprime = True
    db.commit()
    log_action(db, "suppression", "central", central.id, f"Suppression central: {central.nom}", utilisateur, request)
    return {"message": "Central supprimé"}
