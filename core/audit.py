from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from models import AuditLog, Utilisateur


def log_action(
    db: Session,
    action: str,
    entite: Optional[str] = None,
    entite_id: Optional[int] = None,
    description: Optional[str] = None,
    utilisateur: Optional[Utilisateur] = None,
    request: Optional[Request] = None,
) -> None:
    entry = AuditLog(
        utilisateur_id=utilisateur.id if utilisateur else None,
        action=action,
        entite=entite,
        entite_id=entite_id,
        description=description,
        ip_adresse=request.client.host if request and request.client else None,
    )
    db.add(entry)
    db.commit()
