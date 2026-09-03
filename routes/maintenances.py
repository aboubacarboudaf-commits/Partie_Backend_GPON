from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from core.audit import log_action
from core.security import get_current_user, require_admin_ou_technicien
from database import get_db
from models import Equipement, Incident, Maintenance, Utilisateur
from schemas.maintenance import MaintenanceCreate, MaintenanceUpdate

router = APIRouter(prefix="/maintenances", tags=["maintenances"])


def _out(m: Maintenance) -> dict:
    return {
        "id": m.id,
        "titre": m.titre,
        "description": m.description,
        "type": m.type,
        "statut": m.statut,
        "equipement_id": m.equipement_id,
        "equipement_libelle": m.equipement.libelle if m.equipement else None,
        "liaison_id": m.liaison_id,
        "incident_id": m.incident_id,
        "incident_type": m.incident.type if m.incident else None,
        "technicien": m.technicien,
        "notes": m.notes,
        "date_planifiee": m.date_planifiee.isoformat() if m.date_planifiee else None,
        "date_debut": m.date_debut.isoformat() if m.date_debut else None,
        "date_fin": m.date_fin.isoformat() if m.date_fin else None,
    }


@router.get("/equipements/actifs")
def equipements_actifs(db: Session = Depends(get_db), _=Depends(get_current_user)):
    items = db.query(Equipement).filter(
        Equipement.supprime == False, Equipement.etat == "actif"  # noqa: E712
    ).all()
    return [{"id_equipement": e.id_equipement, "libelle": e.libelle, "adresse_ip": e.adresse_ip} for e in items]


@router.get("/incidents/actifs")
def incidents_actifs(db: Session = Depends(get_db), _=Depends(get_current_user)):
    items = db.query(Incident).filter(
        Incident.supprime == False, Incident.statut.in_(["ouvert", "en_cours"])  # noqa: E712
    ).all()
    return [
        {"id_incident": i.id_incident, "type": i.type, "priorite": i.priorite, "description": i.description}
        for i in items
    ]


@router.get("/techniciens/disponibles")
def techniciens_disponibles(db: Session = Depends(get_db), _=Depends(get_current_user)):
    items = db.query(Utilisateur).filter(
        Utilisateur.supprime == False, Utilisateur.role == 2, Utilisateur.est_actif == True  # noqa: E712
    ).all()
    return [{"id": u.id, "nom": u.nom, "matricule": u.matricule} for u in items]


@router.get("/")
def lister(
    statut: Optional[str] = None,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(get_current_user),
):
    query = db.query(Maintenance).options(
        joinedload(Maintenance.equipement), joinedload(Maintenance.incident)
    ).filter(Maintenance.supprime == False)  # noqa: E712
    if statut:
        query = query.filter(Maintenance.statut == statut)
    if utilisateur.role == 2:
        # Un technicien ne voit que les maintenances qui lui sont assignées ; un admin voit tout.
        query = query.filter(Maintenance.technicien == utilisateur.nom)
    return [_out(m) for m in query.order_by(Maintenance.date_planifiee.desc()).all()]


@router.post("/", status_code=status.HTTP_201_CREATED)
def creer(
    payload: MaintenanceCreate,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin_ou_technicien),
):
    maintenance = Maintenance(**payload.model_dump())
    db.add(maintenance)
    db.commit()
    db.refresh(maintenance)
    log_action(db, "creation", "maintenance", maintenance.id, f"Création maintenance: {maintenance.titre}", utilisateur, request)
    return _out(maintenance)


def _get_or_404(db: Session, maintenance_id: int) -> Maintenance:
    maintenance = db.query(Maintenance).filter(
        Maintenance.id == maintenance_id, Maintenance.supprime == False  # noqa: E712
    ).first()
    if not maintenance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance introuvable")
    return maintenance


@router.put("/{maintenance_id}")
def modifier(
    maintenance_id: int,
    payload: MaintenanceUpdate,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin_ou_technicien),
):
    maintenance = _get_or_404(db, maintenance_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(maintenance, field, value)
    db.commit()
    db.refresh(maintenance)
    log_action(db, "modification", "maintenance", maintenance.id, f"Modification maintenance: {maintenance.titre}", utilisateur, request)
    return _out(maintenance)


@router.put("/{maintenance_id}/demarrer")
def demarrer(
    maintenance_id: int,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin_ou_technicien),
):
    maintenance = _get_or_404(db, maintenance_id)
    maintenance.statut = "en_cours"
    maintenance.date_debut = maintenance.date_debut or date.today()
    db.commit()
    db.refresh(maintenance)
    log_action(db, "modification", "maintenance", maintenance.id, f"Démarrage maintenance: {maintenance.titre}", utilisateur, request)
    return _out(maintenance)


@router.put("/{maintenance_id}/terminer")
def terminer(
    maintenance_id: int,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin_ou_technicien),
):
    maintenance = _get_or_404(db, maintenance_id)
    maintenance.statut = "terminee"
    maintenance.date_fin = date.today()
    db.commit()
    db.refresh(maintenance)
    log_action(db, "modification", "maintenance", maintenance.id, f"Fin maintenance: {maintenance.titre}", utilisateur, request)
    return _out(maintenance)


@router.put("/{maintenance_id}/annuler")
def annuler(
    maintenance_id: int,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin_ou_technicien),
):
    maintenance = _get_or_404(db, maintenance_id)
    maintenance.statut = "annulee"
    db.commit()
    db.refresh(maintenance)
    log_action(db, "modification", "maintenance", maintenance.id, f"Annulation maintenance: {maintenance.titre}", utilisateur, request)
    return _out(maintenance)


@router.delete("/{maintenance_id}")
def supprimer(
    maintenance_id: int,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin_ou_technicien),
):
    maintenance = _get_or_404(db, maintenance_id)
    maintenance.supprime = True
    db.commit()
    log_action(db, "suppression", "maintenance", maintenance.id, f"Suppression maintenance: {maintenance.titre}", utilisateur, request)
    return {"message": "Maintenance supprimée"}
