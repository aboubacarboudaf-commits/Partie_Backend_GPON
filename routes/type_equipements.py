from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.audit import log_action
from core.security import get_current_user, require_admin
from database import get_db
from models import Equipement, TypeEquipement, Utilisateur
from schemas.type_equipement import TypeEquipementCreate, TypeEquipementUpdate

router = APIRouter(prefix="/type-equipements", tags=["type-equipements"])


def _out(t: TypeEquipement, count: int = 0) -> dict:
    return {
        "id": t.id,
        "libelle": t.libelle,
        "categorie": t.categorie,
        "description": t.description,
        "icone": t.icone,
        "icone_url": t.icone_url,
        "icone_type": t.icone_type,
        "possede_ip": t.possede_ip,
        "possede_port": t.possede_port,
        "possede_ratio": t.possede_ratio,
        "prefixe_port": t.prefixe_port,
        "equipements_count": count,
    }


def _lister(db: Session):
    counts = dict(
        db.query(Equipement.type_equipement_id, func.count(Equipement.id_equipement))
        .filter(Equipement.supprime == False)  # noqa: E712
        .group_by(Equipement.type_equipement_id)
        .all()
    )
    items = db.query(TypeEquipement).filter(TypeEquipement.supprime == False).all()  # noqa: E712
    return [_out(t, counts.get(t.id, 0)) for t in items]


@router.get("")
@router.get("/")
def lister(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return _lister(db)


def _creer(payload: TypeEquipementCreate, request: Request, db: Session, utilisateur: Utilisateur):
    item = TypeEquipement(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    log_action(db, "creation", "type_equipement", item.id, f"Création type équipement: {item.libelle}", utilisateur, request)
    return _out(item)


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED)
def creer(
    payload: TypeEquipementCreate,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin),
):
    return _creer(payload, request, db, utilisateur)


@router.put("/{type_id}")
def modifier(
    type_id: int,
    payload: TypeEquipementUpdate,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin),
):
    item = db.query(TypeEquipement).filter(TypeEquipement.id == type_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Type d'équipement introuvable")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    log_action(db, "modification", "type_equipement", item.id, f"Modification type équipement: {item.libelle}", utilisateur, request)
    return _out(item)


@router.delete("/{type_id}")
def supprimer(
    type_id: int,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin),
):
    item = db.query(TypeEquipement).filter(TypeEquipement.id == type_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Type d'équipement introuvable")
    item.supprime = True
    db.commit()
    log_action(db, "suppression", "type_equipement", item.id, f"Suppression type équipement: {item.libelle}", utilisateur, request)
    return {"message": "Type d'équipement supprimé"}
