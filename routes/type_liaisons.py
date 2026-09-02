from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from core.audit import log_action
from core.security import get_current_user, require_admin
from database import get_db
from models import TypeLiaison, Utilisateur
from schemas.type_liaison import TypeLiaisonCreate, TypeLiaisonUpdate

router = APIRouter(prefix="/type-liaisons", tags=["type-liaisons"])


def _out(t: TypeLiaison) -> dict:
    return {
        "id": t.id,
        "libelle": t.libelle,
        "couleur": t.couleur,
        "style": t.style_trait,
        "epaisseur": t.epaisseur,
        "description": t.description,
    }


@router.get("/")
def lister(db: Session = Depends(get_db), _=Depends(get_current_user)):
    items = db.query(TypeLiaison).filter(TypeLiaison.supprime == False).all()  # noqa: E712
    return [_out(t) for t in items]


@router.post("/", status_code=status.HTTP_201_CREATED)
def creer(
    payload: TypeLiaisonCreate,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin),
):
    item = TypeLiaison(
        libelle=payload.libelle,
        couleur=payload.couleur,
        style_trait=payload.style_trait,
        epaisseur=payload.epaisseur,
        description=payload.description,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    log_action(db, "creation", "type_liaison", item.id, f"Création type liaison: {item.libelle}", utilisateur, request)
    return _out(item)


@router.put("/{type_id}")
def modifier(
    type_id: int,
    payload: TypeLiaisonUpdate,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin),
):
    item = db.query(TypeLiaison).filter(TypeLiaison.id == type_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Type de liaison introuvable")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    log_action(db, "modification", "type_liaison", item.id, f"Modification type liaison: {item.libelle}", utilisateur, request)
    return _out(item)


@router.delete("/{type_id}")
def supprimer(
    type_id: int,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin),
):
    item = db.query(TypeLiaison).filter(TypeLiaison.id == type_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Type de liaison introuvable")
    item.supprime = True
    db.commit()
    log_action(db, "suppression", "type_liaison", item.id, f"Suppression type liaison: {item.libelle}", utilisateur, request)
    return {"message": "Type de liaison supprimé"}
