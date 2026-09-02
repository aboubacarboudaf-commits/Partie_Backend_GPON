from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from core.security import require_admin
from database import get_db
from models import AuditLog

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


def _out(a: AuditLog) -> dict:
    return {
        "id_auditlog": a.id_auditlog,
        "date_action": a.date_action.isoformat() if a.date_action else None,
        "utilisateur_nom": a.utilisateur.nom if a.utilisateur else "Système",
        "action": a.action,
        "entite": a.entite,
        "entite_id": a.entite_id,
        "description": a.description,
        "ip_adresse": a.ip_adresse,
    }


@router.get("/")
def lister(
    limit: int = 200,
    action: Optional[str] = None,
    entite: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    query = db.query(AuditLog).options(joinedload(AuditLog.utilisateur))
    if action:
        query = query.filter(AuditLog.action == action)
    if entite:
        query = query.filter(AuditLog.entite == entite)
    items = query.order_by(AuditLog.date_action.desc()).limit(limit).all()
    return [_out(a) for a in items]
