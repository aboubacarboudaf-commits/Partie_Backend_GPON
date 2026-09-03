import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from core.audit import log_action
from core.security import get_current_user, require_admin_ou_technicien
from database import get_db
from models import Central, Equipement, Incident, Liaison, Maintenance, Rapport, Utilisateur

router = APIRouter(prefix="/rapports", tags=["rapports"])


def _out(r: Rapport) -> dict:
    contenu = None
    if r.contenu:
        try:
            contenu = json.loads(r.contenu)
        except (TypeError, ValueError):
            contenu = None
    return {
        "id_rapport": r.id_rapport,
        "type": r.type,
        "titre": r.titre,
        "description": r.description,
        "date_rapport": r.date_rapport.isoformat() if r.date_rapport else None,
        "format": r.format,
        "contenu": contenu,
    }


def _compte_equipements(db: Session) -> dict:
    base = db.query(Equipement).filter(Equipement.supprime == False)  # noqa: E712
    return {
        "total": base.count(),
        "actifs": base.filter(Equipement.etat == "actif").count(),
        "inactifs": base.filter(Equipement.etat == "inactif").count(),
        "maintenance": base.filter(Equipement.etat == "maintenance").count(),
    }


def _compte_incidents(db: Session) -> dict:
    base = db.query(Incident).filter(Incident.supprime == False)  # noqa: E712
    return {
        "total": base.count(),
        "ouverts": base.filter(Incident.statut == "ouvert").count(),
        "en_cours": base.filter(Incident.statut == "en_cours").count(),
        "resolus": base.filter(Incident.statut.in_(["resolu", "ferme"])).count(),
        "critiques": base.filter(Incident.priorite == "critique").count(),
    }


def _compte_liaisons(db: Session) -> dict:
    base = db.query(Liaison).filter(Liaison.supprime == False)  # noqa: E712
    return {
        "total": base.count(),
        "ok": base.filter(Liaison.statut == "ok").count(),
        "rompues": base.filter(Liaison.statut == "rompu").count(),
        "degradees": base.filter(Liaison.statut == "degrade").count(),
    }


def _compte_maintenances(db: Session) -> dict:
    base = db.query(Maintenance).filter(Maintenance.supprime == False)  # noqa: E712
    return {
        "total": base.count(),
        "planifiees": base.filter(Maintenance.statut == "planifiee").count(),
        "en_cours": base.filter(Maintenance.statut == "en_cours").count(),
        "terminees": base.filter(Maintenance.statut == "terminee").count(),
    }


def _contenu_pour_type(db: Session, type_rapport: str) -> dict:
    if type_rapport == "equipements":
        return _compte_equipements(db)
    if type_rapport == "incidents":
        return _compte_incidents(db)
    if type_rapport == "liaisons":
        return _compte_liaisons(db)
    if type_rapport == "maintenances":
        return _compte_maintenances(db)
    if type_rapport == "global":
        return {
            "equipements": _compte_equipements(db),
            "incidents": _compte_incidents(db),
            "liaisons": _compte_liaisons(db),
            "maintenances": _compte_maintenances(db),
            "centraux": db.query(Central).filter(Central.supprime == False).count(),  # noqa: E712
        }
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Type de rapport invalide")


@router.get("/")
def lister(db: Session = Depends(get_db), _=Depends(get_current_user)):
    items = db.query(Rapport).filter(Rapport.supprime == False).order_by(Rapport.date_rapport.desc()).all()  # noqa: E712
    return [_out(r) for r in items]


@router.post("/generer", status_code=status.HTTP_201_CREATED)
def generer(
    type: str,
    titre: str,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin_ou_technicien),
    description: str = None,
):
    contenu = _contenu_pour_type(db, type)
    rapport = Rapport(
        type=type,
        titre=titre,
        description=description,
        date_rapport=date.today(),
        format="pdf",
        contenu=json.dumps(contenu),
    )
    db.add(rapport)
    db.commit()
    db.refresh(rapport)
    log_action(db, "creation", "rapport", rapport.id_rapport, f"Génération rapport: {rapport.titre} ({rapport.type})", utilisateur, request)
    return _out(rapport)


@router.delete("/{rapport_id}")
def supprimer(
    rapport_id: int,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin_ou_technicien),
):
    rapport = db.query(Rapport).filter(Rapport.id_rapport == rapport_id, Rapport.supprime == False).first()  # noqa: E712
    if not rapport:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rapport introuvable")
    rapport.supprime = True
    db.commit()
    log_action(db, "suppression", "rapport", rapport.id_rapport, f"Suppression rapport: {rapport.titre}", utilisateur, request)
    return {"message": "Rapport supprimé"}
