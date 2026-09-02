from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from core.audit import log_action
from core.security import get_current_user, require_admin
from database import get_db
from models import Reseau, Utilisateur
from schemas.reseau import ReseauCreate

router = APIRouter(prefix="/reseaux", tags=["reseaux"])


def _out(r: Reseau) -> dict:
    return {"id": r.id, "nom": r.nom, "description": r.description}


@router.get("/")
def lister(db: Session = Depends(get_db), _=Depends(get_current_user)):
    reseaux = db.query(Reseau).filter(Reseau.supprime == False).all()  # noqa: E712
    return [_out(r) for r in reseaux]


@router.post("/", status_code=status.HTTP_201_CREATED)
def creer(
    payload: ReseauCreate,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin),
):
    reseau = Reseau(nom=payload.nom, description=payload.description)
    db.add(reseau)
    db.commit()
    db.refresh(reseau)
    log_action(db, "creation", "reseau", reseau.id, f"Création réseau: {reseau.nom}", utilisateur, request)
    return _out(reseau)


@router.delete("/{reseau_id}")
def supprimer(
    reseau_id: int,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin),
):
    reseau = db.query(Reseau).filter(Reseau.id == reseau_id).first()
    if not reseau:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Réseau introuvable")
    reseau.supprime = True
    db.commit()
    log_action(db, "suppression", "reseau", reseau.id, f"Suppression réseau: {reseau.nom}", utilisateur, request)
    return {"message": "Réseau supprimé"}
