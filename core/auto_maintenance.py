from datetime import date
from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from core.audit import log_action
from models import Incident, Maintenance, Utilisateur


def _technicien_moins_charge(db: Session) -> Optional[Utilisateur]:
    techniciens = db.query(Utilisateur).filter(
        Utilisateur.supprime == False,  # noqa: E712
        Utilisateur.role == 2,
        Utilisateur.est_actif == True,  # noqa: E712
    ).all()
    if not techniciens:
        return None

    charges = {
        t.id: db.query(Maintenance).filter(
            Maintenance.supprime == False,  # noqa: E712
            Maintenance.technicien == t.nom,
            Maintenance.statut.in_(["planifiee", "en_cours"]),
        ).count()
        for t in techniciens
    }
    return min(techniciens, key=lambda t: charges[t.id])


def creer_maintenance_automatique(
    db: Session,
    incident: Incident,
    utilisateur: Optional[Utilisateur] = None,
    request: Optional[Request] = None,
) -> Maintenance:
    technicien = _technicien_moins_charge(db)

    maintenance = Maintenance(
        titre=f"Résolution incident: {incident.type}",
        description=incident.description,
        type="corrective",
        statut="planifiee",
        equipement_id=incident.equipement_id,
        liaison_id=incident.liaison_id,
        incident_id=incident.id_incident,
        technicien=technicien.nom if technicien else None,
        date_planifiee=date.today(),
    )
    db.add(maintenance)
    db.commit()
    db.refresh(maintenance)

    description = f"Maintenance auto-créée pour incident #{incident.id_incident}"
    if technicien:
        description += f", affectée à {technicien.nom}"
    log_action(db, "creation", "maintenance", maintenance.id, description, utilisateur, request)

    return maintenance
