from datetime import date

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session, joinedload

from core.audit import log_action
from core.auto_maintenance import creer_maintenance_automatique
from core.security import get_current_user, require_admin_ou_technicien
from core.zabbix_client import get_zabbix_client
from database import get_db
from models import Equipement, Incident

router = APIRouter(prefix="/zabbix", tags=["zabbix"])

SEVERITE_VERS_PRIORITE = {
    "0": "basse", "1": "basse", "2": "moyenne", "3": "moyenne", "4": "haute", "5": "critique",
}


@router.get("/mapping")
def mapping(db: Session = Depends(get_db), _=Depends(get_current_user)):
    equipements = db.query(Equipement).options(joinedload(Equipement.type_equipement)).filter(
        Equipement.supprime == False  # noqa: E712
    ).all()

    client = get_zabbix_client()
    if client:
        # Le mapping se fait par adresse IP : un équipement est considéré supervisé dès que
        # Zabbix connaît un host avec cette IP, sans configuration manuelle supplémentaire.
        equipements_avec_ip = [e for e in equipements if e.adresse_ip]
        statuts = client.get_hosts_by_ip([e.adresse_ip for e in equipements_avec_ip])
        return {
            "mapping": [
                {
                    "equipement_id": e.id_equipement,
                    "zabbix_available": bool(statuts[e.adresse_ip]["available"]),
                    "zabbix_host": statuts[e.adresse_ip]["hostid"],
                }
                for e in equipements_avec_ip
                if e.adresse_ip in statuts
            ]
        }

    # Pas de serveur Zabbix configuré (ZABBIX_URL absent du .env) : simulation à partir du
    # type/état de l'équipement, mais uniquement pour les équipements ayant une IP (donc
    # potentiellement supervisables) — les autres ne sont pas supervisés du tout, ils ne
    # doivent donc pas apparaître comme "up".
    return {
        "mapping": [
            {
                "equipement_id": e.id_equipement,
                "zabbix_available": bool(
                    e.type_equipement and e.type_equipement.categorie == "actif" and e.etat == "actif"
                ),
                "zabbix_host": None,
            }
            for e in equipements
            if e.adresse_ip
        ]
    }


@router.get("/sync")
def sync(request: Request, db: Session = Depends(get_db), utilisateur=Depends(require_admin_ou_technicien)):
    client = get_zabbix_client()
    if not client:
        return {"incidents_crees": 0, "incidents_fermes": 0}

    equipements = db.query(Equipement).filter(
        Equipement.supprime == False, Equipement.adresse_ip.isnot(None)  # noqa: E712
    ).all()
    if not equipements:
        return {"incidents_crees": 0, "incidents_fermes": 0}

    statuts = client.get_hosts_by_ip([e.adresse_ip for e in equipements])
    equipement_par_host = {
        statuts[e.adresse_ip]["hostid"]: e for e in equipements if e.adresse_ip in statuts
    }
    if not equipement_par_host:
        return {"incidents_crees": 0, "incidents_fermes": 0}

    problemes = client.get_active_problems(list(equipement_par_host.keys()))
    eventids_actifs = {p["eventid"] for p in problemes}

    incidents_crees = 0
    for probleme in problemes:
        deja_suivi = db.query(Incident).filter(Incident.zabbix_eventid == probleme["eventid"]).first()
        if deja_suivi:
            continue
        hosts = probleme.get("hosts") or []
        hostid = hosts[0]["hostid"] if hosts else None
        equipement = equipement_par_host.get(hostid)
        if not equipement:
            continue  # problème sur un host non mappé à un équipement connu, on l'ignore
        incident = Incident(
            type="panne",
            source="automatique",
            description=f"[ZABBIX] {probleme.get('name', 'Problème détecté')}",
            equipement_id=equipement.id_equipement,
            statut="ouvert",
            priorite=SEVERITE_VERS_PRIORITE.get(str(probleme.get("severity")), "moyenne"),
            date_ouverture=date.today(),
            zabbix_eventid=probleme["eventid"],
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        log_action(db, "creation", "incident", incident.id_incident, incident.description, utilisateur, request)
        creer_maintenance_automatique(db, incident, utilisateur, request)
        incidents_crees += 1

    incidents_a_fermer = db.query(Incident).filter(
        Incident.supprime == False,  # noqa: E712
        Incident.statut.in_(["ouvert", "en_cours"]),
        Incident.zabbix_eventid.isnot(None),
        ~Incident.zabbix_eventid.in_(eventids_actifs) if eventids_actifs else Incident.zabbix_eventid.isnot(None),
    ).all()
    for incident in incidents_a_fermer:
        incident.statut = "resolu"
        incident.date_fermeture = date.today()
    db.commit()

    return {"incidents_crees": incidents_crees, "incidents_fermes": len(incidents_a_fermer)}
