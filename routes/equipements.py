from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from core.audit import log_action
from core.security import get_current_user, require_admin_ou_technicien
from core.villes import valider_coordonnees_ville
from database import get_db
from models import Equipement, Liaison, TypeEquipement, Utilisateur
from schemas.equipement import EquipementCreate, EquipementUpdate

router = APIRouter(prefix="/equipements", tags=["equipements"])


def _out(e: Equipement) -> dict:
    t = e.type_equipement
    return {
        "id_equipement": e.id_equipement,
        "libelle": e.libelle,
        "etat": e.etat,
        "adresse_ip": e.adresse_ip,
        "adresse_mac": e.adresse_mac,
        "ville": e.ville,
        "quartier": e.quartier,
        "longitude": e.longitude,
        "latitude": e.latitude,
        "position_x": e.position_x,
        "position_y": e.position_y,
        "nbre_port_pon": e.nbre_port_pon,
        "nbre_port": e.nbre_port,
        "ratio": e.ratio,
        "type_equipement_id": e.type_equipement_id,
        "type_equipement_libelle": t.libelle if t else None,
        "icone": (t.icone if t and t.icone else e.icone),
        "icone_url": t.icone_url if t else None,
        "icone_type": t.icone_type if t else None,
        "possede_ip": t.possede_ip if t else True,
        "possede_port": t.possede_port if t else False,
        "possede_ratio": t.possede_ratio if t else False,
        "central_id": e.central_id,
        "reseau_id": e.reseau_id,
    }


@router.get("/")
def lister(
    type_equipement_id: Optional[int] = None,
    etat: Optional[str] = None,
    ville: Optional[str] = None,
    reseau_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    query = db.query(Equipement).options(joinedload(Equipement.type_equipement)).filter(
        Equipement.supprime == False  # noqa: E712
    )
    if type_equipement_id is not None:
        query = query.filter(Equipement.type_equipement_id == type_equipement_id)
    if etat:
        query = query.filter(Equipement.etat == etat)
    if ville:
        query = query.filter(Equipement.ville == ville)
    if reseau_id is not None:
        query = query.filter(Equipement.reseau_id == reseau_id)
    return [_out(e) for e in query.all()]


@router.get("/{equipement_id}/ports")
def ports(equipement_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    equipement = db.query(Equipement).filter(
        Equipement.id_equipement == equipement_id, Equipement.supprime == False  # noqa: E712
    ).first()
    if not equipement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Équipement introuvable")

    total_ports = equipement.nbre_port_pon or equipement.nbre_port or 0
    liaisons = db.query(Liaison).filter(
        Liaison.supprime == False,  # noqa: E712
        (Liaison.source_id == equipement_id) | (Liaison.destination_id == equipement_id),
    ).all()
    ports_occupes = set()
    for liaison in liaisons:
        if liaison.source_id == equipement_id and liaison.port_source:
            ports_occupes.add(liaison.port_source)
        if liaison.destination_id == equipement_id and liaison.port_destination:
            ports_occupes.add(liaison.port_destination)

    return {
        "ports": [
            {"numero": str(n), "occupe": str(n) in ports_occupes}
            for n in range(1, total_ports + 1)
        ]
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
def creer(
    payload: EquipementCreate,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin_ou_technicien),
):
    type_equipement = db.query(TypeEquipement).filter(TypeEquipement.id == payload.type_equipement_id).first()
    if not type_equipement:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Type d'équipement invalide")

    try:
        valider_coordonnees_ville(payload.ville, payload.latitude, payload.longitude)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    equipement = Equipement(**payload.model_dump())
    db.add(equipement)
    db.commit()
    db.refresh(equipement)
    log_action(db, "creation", "equipement", equipement.id_equipement, f"Création équipement: {equipement.libelle}", utilisateur, request)
    return _out(equipement)


@router.put("/{equipement_id}")
def modifier(
    equipement_id: int,
    payload: EquipementUpdate,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin_ou_technicien),
):
    equipement = db.query(Equipement).filter(
        Equipement.id_equipement == equipement_id, Equipement.supprime == False  # noqa: E712
    ).first()
    if not equipement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Équipement introuvable")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(equipement, field, value)

    try:
        valider_coordonnees_ville(equipement.ville, equipement.latitude, equipement.longitude)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    db.commit()
    db.refresh(equipement)
    log_action(db, "modification", "equipement", equipement.id_equipement, f"Modification équipement: {equipement.libelle}", utilisateur, request)
    return _out(equipement)


@router.patch("/{equipement_id}/etat")
def changer_etat(
    equipement_id: int,
    etat: str,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin_ou_technicien),
):
    equipement = db.query(Equipement).filter(
        Equipement.id_equipement == equipement_id, Equipement.supprime == False  # noqa: E712
    ).first()
    if not equipement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Équipement introuvable")
    equipement.etat = etat
    db.commit()
    db.refresh(equipement)
    log_action(db, "modification", "equipement", equipement.id_equipement, f"Changement d'état équipement: {equipement.libelle} -> {etat}", utilisateur, request)
    return _out(equipement)


@router.delete("/{equipement_id}")
def supprimer(
    equipement_id: int,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin_ou_technicien),
):
    equipement = db.query(Equipement).filter(
        Equipement.id_equipement == equipement_id, Equipement.supprime == False  # noqa: E712
    ).first()
    if not equipement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Équipement introuvable")
    equipement.supprime = True
    db.commit()
    log_action(db, "suppression", "equipement", equipement.id_equipement, f"Suppression équipement: {equipement.libelle}", utilisateur, request)
    return {"message": "Équipement supprimé"}
