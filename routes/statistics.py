from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.security import get_current_user
from database import get_db
from models import Central, Utilisateur
from routes.rapports import _compte_equipements, _compte_incidents, _compte_liaisons, _compte_maintenances

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _=Depends(get_current_user)):
    incidents = _compte_incidents(db)
    maintenances = _compte_maintenances(db)
    return {
        "equipements": _compte_equipements(db),
        "liaisons": _compte_liaisons(db),
        "incidents": {
            "ouverts": incidents["ouverts"],
            "en_cours": incidents["en_cours"],
            "critiques": incidents["critiques"],
        },
        "maintenances": {
            "total": maintenances["total"],
            "planifiees": maintenances["planifiees"],
            "en_cours": maintenances["en_cours"],
        },
        "centraux": db.query(Central).filter(Central.supprime == False).count(),  # noqa: E712
        "utilisateurs": db.query(Utilisateur).filter(Utilisateur.supprime == False).count(),  # noqa: E712
    }
